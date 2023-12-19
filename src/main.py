"""
Main module for the application.

This module contains the main entry point for the application. It
creates the LED controller and event client, and starts them in
separate tasks.
"""
# src/main.py
import asyncio
from datetime import datetime, timedelta

import aiohttp
import neopixel
from adafruit_led_animation.animation import pulse, rainbow, rainbowsparkle, solid
from adafruit_led_animation.sequence import AnimationSequence

from config import Config
from constants import (
    ALERT_ANIMATION,
    ALERT_DURATION,
    ANIMATION_LOOP_SPEED,
    BACKGROUND_ANIMATION,
    COLOR_TIMEOUT,
    COLOR_TIP_AMOUNT,
    HTTP_MAX_RETRIES,
    HTTP_REQUEST_TIMEOUT,
    HTTP_RETRY_DELAY,
    NUM_PIXELS,
    PIXEL_BRIGHTNESS,
    PIXEL_PIN,
    PULSE_PERIOD,
    PULSE_SPEED,
    RAINBOW_PERIOD,
    RAINBOW_SPEED,
    SPARKLE_NUM_SPARKLES,
    SPARKLE_PERIOD,
    SPARKLE_SPEED,
    ColorList,
)


class LEDController:
    """
    LEDController class

    Manages the LED strip and animations.
    """

    def __init__(self, pixels, config, logger):
        """
        Initialize the LEDController with NeoPixel object, configuration data, and logger.

        :param pixels: NeoPixel object representing the LED strip.
        :param config: Configuration data.
        :param logger: Logger object for logging messages.
        """
        self.pixels = pixels
        self.config = config
        self.logger = logger
        self.should_stop_animation = asyncio.Event()
        self.last_color_change = None

        # Create Animation Sequence
        self.animations = AnimationSequence(
            rainbow.Rainbow(
                pixels,
                speed=RAINBOW_SPEED,
                period=RAINBOW_PERIOD,
                name="rainbow",
            ),
            rainbowsparkle.RainbowSparkle(
                pixels,
                speed=SPARKLE_SPEED,
                period=SPARKLE_PERIOD,
                num_sparkles=SPARKLE_NUM_SPARKLES,
                name="sparkle",
            ),
            *[
                pulse.Pulse(
                    pixels,
                    speed=PULSE_SPEED,
                    color=color.value,
                    period=PULSE_PERIOD,
                    name=f"{color.name.lower()}_pulse",
                )
                for color in ColorList
            ],
            *[
                solid.Solid(pixels, color=color.value, name=color.name.lower())
                for color in ColorList
            ],
            advance_interval=None,
            auto_clear=True,
        )

    async def animation_loop(self):
        """
        Continuously animate the LEDs until the animation is stopped.
        """
        while not self.should_stop_animation.is_set():
            if self.last_color_change and datetime.now() - self.last_color_change > timedelta(
                seconds=COLOR_TIMEOUT
            ):
                self.logger.info("Color timeout reached")
                await self.activate_animation(BACKGROUND_ANIMATION)
                self.last_color_change = None
            self.animations.animate()
            await asyncio.sleep(ANIMATION_LOOP_SPEED)

    async def stop_animation(self):
        """
        Set the flag to stop the animation loop.
        """
        self.logger.debug("Stopping animation.")
        self.should_stop_animation.set()

    async def cleanup_pixels(self):
        """
        Clean up the pixels when the program exits.
        """
        await self.stop_animation()
        self.logger.debug("Cleaning up pixels.")
        self.pixels.deinit()

    async def activate_animation(self, animation_name):
        """
        Activate a specific animation by its name.

        :param animation_name: The name of the animation to activate.
        """
        self.animations.activate(animation_name)
        self.last_color_change = datetime.now() if animation_name != BACKGROUND_ANIMATION else None


class EventClient:
    """
    EventClient class

    Manages the events API and processes events.
    """

    def __init__(self, config, led_controller, logger):
        """
        Initialize the EventClient with configuration data, an LED controller, and a logger.

        :param config: Configuration data.
        :param led_controller: LEDController object to control LED animations.
        :param logger: Logger object for logging messages.
        """
        self.logger = logger
        self.config = config
        self.led_controller = led_controller
        self.session = aiohttp.ClientSession()
        self.should_stop_processing = asyncio.Event()
        self.user_color = None

    async def get_events(self):
        """
        Retrieve and process events from the events API, with a retry mechanism for HTTP errors.
        """
        url = self.config["initial_url"]
        self.logger.debug(f"Starting event client. Initial URL: {url}")
        max_retries = HTTP_MAX_RETRIES
        retry_delay = HTTP_RETRY_DELAY

        while url and not self.should_stop_processing.is_set():
            retry_count = 0
            while retry_count < max_retries:
                try:
                    async with self.session.get(url, timeout=HTTP_REQUEST_TIMEOUT) as response:
                        if response.status == 200:
                            data = await response.json()
                            await self.process_events(data.get("events", []))
                            url = data.get("nextUrl")
                            break
                        if response.status in {502, 520, 521}:
                            self.logger.warning(
                                f"Received HTTP {response.status} response. \
                                    Retrying in {retry_delay} seconds..."
                            )
                            retry_count += 1
                            await asyncio.sleep(retry_delay)
                        elif response.status == 401:
                            self.logger.error("Invalid credentials.")
                            return
                        elif response.status == 404:
                            self.logger.error("Invalid URL.")
                            return
                        else:
                            self.logger.error(f"Unhandled HTTP response: {response.status}")
                            return
                except aiohttp.ClientResponseError as error:
                    self.logger.error(f"Client error: {error}")
                    return
                except KeyboardInterrupt:
                    return

            if retry_count == max_retries:
                self.logger.error("Maximum retry attempts reached.")
                return

    async def process_events(self, events):
        """
        Process events retrieved from the API.

        :param events: List of events to process.
        """
        for event in events:
            if event.get("method") == "tip":
                await self.process_tips(event)

    async def process_tips(self, tip_event):
        """
        Process tip events.

        :param tip_event: The tip event to process.
        """
        try:
            tip = tip_event["object"]["tip"]
            user = tip_event["object"]["user"]
            tip_amount, tip_message = tip["tokens"], tip["message"]
            tip_username = user["username"]
            tip_message = tip_message.split(" | ", 1)[-1]  # Handle message format

            self.logger.debug(
                f"{tip_username} tipped {tip_amount} tokens with message: {tip_message}"
            )
            await self.handle_tip_action(tip_amount, tip_message)
        except KeyError as error:
            self.logger.error(f"KeyError in process_tips: {error}")

    async def handle_tip_action(self, tip_amount, tip_message):
        """
        Handle actions based on the tip amount and message.

        :param tip_amount: The amount of the tip.
        :param tip_message: The message associated with the tip.
        """
        if tip_amount >= COLOR_TIP_AMOUNT:
            await self.handle_color_tip(tip_message)
        else:
            await self.activate_alert_animation()

        if self.led_controller.last_color_change:
            await self.activate_color_background_animation(self.user_color)
        else:
            await self.activate_background_animation()

    async def handle_color_tip(self, tip_message):
        """
        Handle a tip that includes a color change request.

        :param tip_message: The message associated with the tip.
        """
        color_names = [color.name.lower() for color in ColorList]
        if tip_message.lower() in color_names:
            self.user_color = tip_message.lower()
            self.led_controller.last_color_change = datetime.now()
            await self.activate_color_alert_animation(self.user_color)
            await self.activate_color_background_animation(self.user_color)
        else:
            await self.activate_alert_animation()

    async def activate_alert_animation(self):
        """
        Activate the alert animation.
        """
        await self.led_controller.activate_animation(ALERT_ANIMATION)
        await asyncio.sleep(ALERT_DURATION)

    async def activate_color_alert_animation(self, user_color):
        """
        Activate the color alert animation.

        :param user_color: The color to use for the alert animation.
        """
        self.logger.info(f"Changing lights to {user_color}")
        await self.led_controller.activate_animation(f"{user_color}_pulse")
        await asyncio.sleep(ALERT_DURATION)

    async def activate_color_background_animation(self, user_color):
        """
        Activate the color background animation.

        :param user_color: The color to use for the background animation.
        """
        await self.led_controller.activate_animation(user_color)

    async def activate_background_animation(self):
        """
        Activate the default background animation.
        """
        self.logger.debug("Resuming background animation")
        await self.led_controller.activate_animation(BACKGROUND_ANIMATION)

    async def stop_processing(self):
        """
        Signal to stop processing events.
        """
        self.logger.debug("Stopping event client.")
        self.should_stop_processing.set()

    async def close_session(self):
        """
        Close the network session and stop processing events.
        """
        await self.stop_processing()
        self.logger.debug("Closing session.")
        await self.session.close()


async def main():
    """
    Main entry point for the application.
    """
    pixel_obj = neopixel.NeoPixel(
        PIXEL_PIN,  # type: ignore
        NUM_PIXELS,
        brightness=PIXEL_BRIGHTNESS,
        auto_write=True,
    )

    # Initialize the Config object and read the configuration
    config_obj = Config()
    config_data = config_obj.read_configuration()
    logger_obj = config_obj.logger  # Use the logger from the config object

    # Initialize the LEDController and EventClient with the configuration data
    led_controller = LEDController(pixel_obj, config_data, logger_obj)
    event_client = EventClient(config_data, led_controller, logger_obj)

    try:
        # Create tasks for the event client and LED controller
        event_task = asyncio.create_task(event_client.get_events())
        led_task = asyncio.create_task(led_controller.animation_loop())

        logger_obj.info("Starting program.")

        await asyncio.gather(led_task, event_task)

    except (
        aiohttp.ClientError,
        aiohttp.ClientConnectionError,
    ) as error:
        logger_obj.error("An error occurred: %s", error)
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger_obj.warning("Keyboard interrupt. Exiting...")

    finally:
        await event_client.close_session()
        await led_controller.cleanup_pixels()
        logger_obj.info("Program exited.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
