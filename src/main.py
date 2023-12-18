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
from adafruit_led_animation.animation.pulse import Pulse
from adafruit_led_animation.animation.rainbow import Rainbow
from adafruit_led_animation.animation.rainbowsparkle import RainbowSparkle
from adafruit_led_animation.animation.solid import Solid
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
    """LED Controller

    This class controls the LEDs on the Raspberry Pi. It contains methods
    for activating different animations, and for cleaning up the pixels
    when the program exits.
    """

    def __init__(self, pixels, config, logger):
        self.pixels = pixels
        self.config = config
        self.logger = logger
        self.should_stop_animation = asyncio.Event()
        self.last_color_change = None

        # Create Animation Sequence
        self.animations = AnimationSequence(
            Rainbow(
                pixels,
                speed=RAINBOW_SPEED,
                period=RAINBOW_PERIOD,
                name="rainbow",
            ),
            RainbowSparkle(
                pixels,
                speed=SPARKLE_SPEED,
                period=SPARKLE_PERIOD,
                num_sparkles=SPARKLE_NUM_SPARKLES,
                name="sparkle",
            ),
            *[
                Pulse(
                    pixels,
                    speed=PULSE_SPEED,
                    color=color.value,
                    period=PULSE_PERIOD,
                    name=color.name.lower() + "_pulse",
                )
                for color in ColorList
            ],
            *[
                Solid(pixels, color=color.value, name=color.name.lower())
                for color in ColorList
            ],
            advance_interval=None,
            auto_clear=True,
        )

    async def animation_loop(self):
        """Animation loop"""
        try:
            while not self.should_stop_animation.is_set():
                # Check if the set time has passed since the last color change
                if (
                    self.last_color_change
                    and datetime.now() - self.last_color_change
                    > timedelta(seconds=COLOR_TIMEOUT)
                ):
                    # Reset to default animation if time has elapsed
                    self.logger.info("Color timeout reached")
                    await self.activate_animation(BACKGROUND_ANIMATION)
                    # Reset the timestamp to None as the default animation is now active
                    self.last_color_change = None

                # Continue with the current animation
                self.animations.animate()
                await asyncio.sleep(ANIMATION_LOOP_SPEED)

            self.logger.debug("Animation loop stopped.")

        except RuntimeError as error:
            self.logger.error(f"Error in animation loop: {error}")
        except KeyboardInterrupt as error:
            self.logger.error(f"Keyboard interrupt: {error}")

    async def stop_animation(self):
        """Stop the current animation"""
        self.logger.debug("Stopping animation.")
        self.should_stop_animation.set()

    async def cleanup_pixels(self):
        """Clean up the pixels"""
        await self.stop_animation()
        self.logger.debug("Cleaning up pixels.")
        self.pixels.deinit()

    async def activate_animation(self, color):
        """Activate the specified animation"""
        self.animations.activate(color)


class EventClient:
    """Event Client

    This class connects to the events API and processes
    events as they are received.
    """

    def __init__(self, config, led_controller, logger):
        self.logger = logger
        self.config = config
        self.led_controller = led_controller
        self.session = aiohttp.ClientSession()
        self.should_stop_processing = asyncio.Event()
        self.user_color = None

    async def get_events(self):
        """Get events from the events API with retry mechanism for certain HTTP responses."""
        url = self.config["initial_url"]
        self.logger.debug("Starting event client.")
        self.logger.debug(f"Initial URL: {url}")
        max_retries = HTTP_MAX_RETRIES
        retry_delay = HTTP_RETRY_DELAY

        while url and not self.should_stop_processing.is_set():
            retry_count = 0
            while retry_count < max_retries:
                try:
                    async with self.session.get(
                        url, timeout=HTTP_REQUEST_TIMEOUT
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            await self.process_events(data.get("events", []))
                            url = data.get(
                                "nextUrl"
                            )  # Update the URL for the next request
                            self.logger.debug(f"Next URL: {url}")
                            break  # Break the retry loop if successful
                        elif response.status in {520, 521}:
                            self.logger.warning(
                                f"Received HTTP {response.status} response. Retrying in {retry_delay} seconds..."
                            )
                            retry_count += 1
                            await asyncio.sleep(retry_delay)
                        elif response.status == 401:
                            self.logger.error(
                                "Invalid credentials. Please check your credentials.ini file."
                            )
                            return
                        elif response.status == 404:
                            self.logger.error(
                                "Invalid URL. Please check your config.py file."
                            )
                            return
                        else:
                            self.logger.error(f"Unhandled error: {response.status}")
                            return  # Stop processing on other errors
                except aiohttp.ClientResponseError as error:
                    self.logger.error(f"Client error occurred: {error}")
                    return  # Stop processing on client error
                except KeyboardInterrupt as error:
                    self.logger.error(f"Keyboard interrupt: {error}")
                    return

            if retry_count == max_retries:
                self.logger.error(
                    "Maximum retry attempts reached. Stopping event processing."
                )
                return

    async def process_events(self, events):
        """Process events from the events API"""
        for event in events:
            if event.get("method") == "tip":
                await self.process_tips(event)

    async def process_tips(self, tip_event):
        """Process tip events from the events API"""
        try:
            tip = tip_event["object"]["tip"]
            user = tip_event["object"]["user"]
            tip_amount, tip_message = tip["tokens"], tip["message"]
            tip_username = user["username"]

            # Strip the unwanted prefix from the tip_message
            prefix = "-- Select One -- | "
            if tip_message.startswith(prefix):
                tip_message = tip_message[len(prefix) :]

            tip_info = f"{tip_username} tipped {tip_amount} tokens"
            if tip_message:
                tip_info += f" with message: {tip_message}"
            self.logger.debug(tip_info)

            await self.handle_tip_action(tip_amount, tip_message)
        except KeyError as error:
            self.logger.error(f"KeyError in process_tips: {error}")

    async def handle_tip_action(self, tip_amount, tip_message):
        """Handle tip actions"""
        if tip_amount >= COLOR_TIP_AMOUNT:
            await self.handle_color_tip(tip_message)
        else:
            await self.activate_alert_animation()

        if self.led_controller.last_color_change:
            self.logger.debug("Resuming color background animation.")
            await self.activate_color_background_animation(self.user_color)
        else:
            await self.activate_background_animation()

    async def handle_color_tip(self, tip_message):
        """Handle color tip actions"""

        # Rest of your function
        color_names = [color.name.lower() for color in ColorList]
        if tip_message.lower() in color_names:
            self.user_color = tip_message.lower()
            self.led_controller.last_color_change = None  # Reset the timestamp
            self.led_controller.last_color_change = datetime.now()
            await self.activate_color_alert_animation(self.user_color)
            await self.activate_color_background_animation(self.user_color)
        else:
            await self.activate_alert_animation()

    async def activate_alert_animation(self):
        """Activate the alert animation"""
        await self.led_controller.activate_animation(ALERT_ANIMATION)
        await asyncio.sleep(ALERT_DURATION)

    async def activate_color_alert_animation(self, user_color):
        """Activate the color alert animation"""
        self.logger.info(f"Changing lights to {user_color}")
        pulse_color = f"{user_color}_pulse"
        await self.led_controller.activate_animation(pulse_color)
        await asyncio.sleep(ALERT_DURATION)

    async def activate_color_background_animation(self, user_color):
        """Activate the color background animation"""
        await self.led_controller.activate_animation(user_color)

    async def activate_background_animation(self):
        """Activate the background animation"""
        self.logger.debug("Resuming background animation")
        await self.led_controller.activate_animation(BACKGROUND_ANIMATION)

    async def stop_processing(self):
        """Stop processing events"""
        self.logger.debug("Stopping event client.")
        self.should_stop_processing.set()

    async def close_session(self):
        """Close the session"""
        await self.stop_processing()
        self.logger.debug("Closing session.")
        await self.session.close()


async def main():
    """Main entry point for the application"""
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
        asyncio.CancelledError,
    ) as error:
        logger_obj.error("An error occurred: %s", error)
    except KeyboardInterrupt as error:
        logger_obj.error("Keyboard interrupt: %s", error)

    finally:
        await event_client.close_session()
        await led_controller.cleanup_pixels()
        logger_obj.info("Program exited.")


if __name__ == "__main__":
    asyncio.run(main())
