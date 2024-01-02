"""
This module demonstrates an example usage of the Chaturbate Events API to process tips
and control LED animations based on the events.
"""

import asyncio
import json
import logging
import logging.config
import os
import time
from enum import Enum

import aiohttp
import board
import neopixel
from adafruit_led_animation.animation import pulse, rainbow, rainbowsparkle, solid
from adafruit_led_animation.sequence import AnimationSequence
from dotenv import load_dotenv

from log_formatter import align_logs

# Constants
ALERT_LENGTH = int(3)
COLOR_ACTIVE_TIME = 600
ALERT_TOKENS = 35
LED_COUNT = 100
LED_PIN = board.D18
LED_BRIGHTNESS = 0.1
ANIMATION_SPEED = 0.01
MAX_RETRY_DELAY = 60
RETRY_FACTOR = 2
INITIAL_RETRY_DELAY = 2
TIMEOUT_BUFFER_FACTOR = 2
RAINBOW_PERIOD = 60
RAINBOW_SPEED = 0.01
SPARKLE_PERIOD = 60
SPARKLE_SPEED = 0.1
SPARKLE_NUM_SPARKLES = 5
SPARKLE_BRIGHTNESS = 0.5
# Pulse period should be 2/3 of the ALERT_LENGTH to allow for a full pulse cycle
PULSE_PERIOD = int(ALERT_LENGTH * 2 / 3)
PULSE_PERIOD = 1 if PULSE_PERIOD < 1 else PULSE_PERIOD
PULSE_SPEED = 0.01
PULSE_BRIGHTNESS = 0.5
ONE_MINUTE = 60


# Configure logging
def setup_logging():
    """
    Setup logging configuration from a JSON file if it exists, otherwise use basic
    logging configuration.
    """
    logging_config_file = "logging_config.json"
    if os.path.isfile(logging_config_file):
        with open(logging_config_file, "r", encoding="utf-8") as f:
            config = json.load(f)
            logging.config.dictConfig(config)
    else:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )


setup_logging()


class AppConfig:
    """
    Class to store application configuration.

    Attributes:
        api_username (str): Chaturbate API username.
        api_token (str): Chaturbate API token.
        base_url (str): Base URL for the Chaturbate Events API.
        request_timeout (int): Timeout for HTTP requests in seconds.
        api_timeout (int): Timeout for Chaturbate Events API in seconds.
        led_strip (neopixel.NeoPixel): NeoPixel LED strip.
        logger (logging.Logger): Logger instance.
    """

    def __init__(self):
        load_dotenv()
        self.api_username = os.getenv("USERNAME", "")
        self.api_token = os.getenv("TOKEN", "")
        self.base_url = os.getenv(
            "BASE_URL", "https://eventsapi.chaturbate.com/events/"
        )
        self.request_timeout = int(os.getenv("TIMEOUT", "10"))
        self.api_timeout = self.request_timeout // TIMEOUT_BUFFER_FACTOR
        self.led_strip = self.setup_led_strip()
        self.logger = logging.getLogger(self.__class__.__name__)

    def setup_led_strip(self):
        """
        Setup the NeoPixel LED strip.

        Returns:
            neopixel.NeoPixel: NeoPixel LED strip.
        """
        try:
            return neopixel.NeoPixel(LED_PIN, LED_COUNT, brightness=LED_BRIGHTNESS, auto_write=False)  # type: ignore
        except RuntimeError as error:
            self.logger.error(f"Error initializing LED strip: {error}")
            raise

    def get_base_url(self):
        """
        Get the base URL for the Chaturbate Events API.

        Returns:
            str: Base URL for the Chaturbate Events API.
        """
        return f"{self.base_url}{self.api_username}/{self.api_token}/?timeout={self.api_timeout}"


class AlertColor(Enum):
    """
    Enum for alert colors.

    Attributes:
        RED (tuple): RGB value for red.
        ORANGE (tuple): RGB value for orange.
        YELLOW (tuple): RGB value for yellow.
        GREEN (tuple): RGB value for green.
        BLUE (tuple): RGB value for blue.
        INDIGO (tuple): RGB value for indigo.
        VIOLET (tuple): RGB value for violet.
        BLACK (tuple): RGB value for black.
    """

    RED = (255, 0, 0)
    ORANGE = (255, 165, 0)
    YELLOW = (255, 255, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    INDIGO = (75, 0, 130)
    VIOLET = (148, 0, 211)
    BLACK = (0, 0, 0)

    @staticmethod
    def from_string(color_str):
        """
        Get the AlertColor enum value from a string.

        Args:
            color_str (str): Color name.

        Returns:
            AlertColor: AlertColor enum value.
        """
        return AlertColor.__members__.get(color_str.upper(), None)


class LEDController:
    """
    Class to control the LED animations.

    Attributes:
        pixels (neopixel.NeoPixel): NeoPixel LED strip.
        animations (AnimationSequence): Animation sequence.
        current_color (AlertColor): Current color alert.
        color_set_time (float): Time when the current color alert was set.
        logger (logging.Logger): Logger instance.
    """

    def __init__(self, pixels):
        self.pixels = pixels
        self.animations = self.create_animations()
        self.current_color = None
        self.color_set_time = None
        self.logger = logging.getLogger(self.__class__.__name__)

    def create_animations(self):
        """
        Create the animation sequence.

        Returns:
            AnimationSequence: Animation sequence.
        """
        rainbow_animation = rainbow.Rainbow(
            self.pixels, speed=RAINBOW_SPEED, period=RAINBOW_PERIOD, name="rainbow"
        )
        sparkle_animation = rainbowsparkle.RainbowSparkle(
            self.pixels,
            speed=SPARKLE_SPEED,
            period=SPARKLE_PERIOD,
            num_sparkles=SPARKLE_NUM_SPARKLES,
            background_brightness=SPARKLE_BRIGHTNESS,
            name="sparkle",
        )
        pulse_animations = [
            pulse.Pulse(
                self.pixels,
                speed=PULSE_SPEED,
                color=color.value,
                period=PULSE_PERIOD,
                name=f"{color.name}_pulse",
            )
            for color in AlertColor
        ]
        solid_animations = [
            solid.Solid(self.pixels, color=color.value, name=f"{color.name}")
            for color in AlertColor
        ]

        return AnimationSequence(
            rainbow_animation,
            sparkle_animation,
            *pulse_animations,
            *solid_animations,
            advance_interval=None,
            auto_clear=True,
        )

    async def run_animation_loop(self):
        """Run the animation loop."""
        while True:
            if (
                self.current_color
                and self.color_set_time
                and (time.time() - self.color_set_time > COLOR_ACTIVE_TIME)
            ):
                self.current_color = None
                self.logger.info("Color alert duration expired. Resetting to rainbow.")
                self.animations.activate("rainbow")
            self.animations.animate()
            await asyncio.sleep(ANIMATION_SPEED)

    async def activate_normal_alert(self):
        """Activate the normal alert."""
        previous_state = self.animations.current_animation.name
        self.logger.debug("Activating normal alert.")
        self.animations.activate("sparkle")
        await asyncio.sleep(ALERT_LENGTH)
        self.animations.activate(previous_state)

    async def activate_color_alert(self, color):
        """
        Activate the color alert.

        Args:
            color (AlertColor): Color alert to activate.
        """
        self.current_color = color
        self.color_set_time = time.time()
        self.logger.debug(f"Activating color alert: {color.name.lower()}.")
        self.animations.activate(f"{color.name}_pulse")
        await asyncio.sleep(ALERT_LENGTH)
        color_time = (
            f"{COLOR_ACTIVE_TIME} seconds"
            if COLOR_ACTIVE_TIME < ONE_MINUTE
            else f"{COLOR_ACTIVE_TIME // ONE_MINUTE} minutes"
        )
        self.logger.info(f"Setting lights to {color.name.lower()} for {color_time}.")
        self.animations.activate(color.name)

    async def stop_animation(self):
        """Stop the animation loop."""
        self.animations.freeze()
        self.pixels.fill((0, 0, 0))
        self.pixels.show()
        self.pixels.deinit()
        await asyncio.sleep(0)


class EventPoller:
    """
    Class to poll the Chaturbate Events API for events.

    Attributes:
        base_url (str): Base URL for the Chaturbate Events API.
        timeout (int): Timeout for HTTP requests in seconds.
        retry_delay (int): Delay between retries in seconds.
        logger (logging.Logger): Logger instance.
    """

    def __init__(self, base_url, timeout):
        self.base_url = base_url
        self.timeout = timeout
        self.retry_delay = INITIAL_RETRY_DELAY
        self.logger = logging.getLogger(self.__class__.__name__)

    async def fetch_events(self):
        """
        Fetch events from the Chaturbate Events API.

        Yields:
            list: List of events.
        """
        async with aiohttp.ClientSession() as session:
            url = self.base_url
            while True:
                try:
                    async with session.get(
                        url, timeout=aiohttp.ClientTimeout(total=self.timeout)
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            url = data["nextUrl"]
                            self.retry_delay = INITIAL_RETRY_DELAY
                            yield data["events"]
                        else:
                            self.logger.error(
                                f"Error fetching events: Status {response.status}"
                            )
                            await self.handle_error()
                except aiohttp.ClientError as error:
                    self.logger.error(f"Client error: {error}")
                    await self.handle_error()

    async def handle_error(self):
        """Handle errors by waiting and increasing the retry delay."""
        await asyncio.sleep(self.retry_delay)
        self.retry_delay = min(self.retry_delay * RETRY_FACTOR, MAX_RETRY_DELAY)


class EventProcessor:
    """
    Class to process events.

    Attributes:
        logger (logging.Logger): Logger instance.
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    async def process_events(self, events_gen, led_controller):
        """
        Process events.

        Args:
            events_gen (generator): Generator for events.
            led_controller (LEDController): LED controller instance.
        """
        async for events in events_gen:
            for event in events:
                if event["method"] == "tip":
                    await self.process_tip(event, led_controller)

    async def process_tip(self, event, led_controller):
        """
        Process tip events.

        Args:
            event (dict): Tip event.
            led_controller (LEDController): LED controller instance.
        """
        tip = event["object"]["tip"]
        tokens = tip.get("tokens", 0)
        message = self.clean_message(tip.get("message", ""))
        color = AlertColor.from_string(message)
        if tokens == ALERT_TOKENS and color:
            await led_controller.activate_color_alert(color)
        else:
            await led_controller.activate_normal_alert()

        # If log level is DEBUG, log tip details
        if self.logger.isEnabledFor(logging.DEBUG):
            self.log_tip_details(tip, event["object"]["user"])

    def clean_message(self, message):
        """
        Clean the message by removing the "-- Select One --" option.

        Args:
            message (str): Message to clean.

        Returns:
            str: Cleaned message.
        """
        return message.replace("-- Select One -- | ", "").replace(
            "-- Select One --", ""
        )

    def log_tip_details(self, tip, user):
        """
        Log tip details.

        Args:
            tip (dict): Tip details.
            user (dict): User details.
        """
        tokens = tip.get("tokens", 0)
        message = tip.get("message", "")
        username = user.get("username", "Unknown")
        self.logger.debug(
            f"Tip received from {username}: {tokens} tokens. Message: '{message}'"
        )


async def main():
    """Main function."""

    # Log startup message
    logger = logging.getLogger("StripAlerts")

    logger.debug("Setting up application.")

    config = AppConfig()
    led_controller = LEDController(config.led_strip)
    poller = EventPoller(config.get_base_url(), config.request_timeout)
    processor = EventProcessor()

    animation_task = asyncio.create_task(led_controller.run_animation_loop())
    processing_task = asyncio.create_task(
        processor.process_events(poller.fetch_events(), led_controller)
    )
    logger.debug("Application setup complete.")
    try:
        logger.info("Starting application.")
        await asyncio.gather(animation_task, processing_task)
    except KeyboardInterrupt:
        logger.warning("Keyboard interrupt received. Stopping application.")
        pass
    finally:
        animation_task.cancel()
        processing_task.cancel()
        await asyncio.gather(animation_task, processing_task, return_exceptions=True)
        await led_controller.stop_animation()
        align_logs("app.log", delete_original=True)
        logger.info("Application stopped.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
