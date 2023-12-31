"""
This is a simple example of how to use the Chaturbate Events API to process tips.
It will fetch events from the API and log any tips.
"""
import asyncio
import logging
import os
import time
from enum import Enum

import aiohttp
import board
import neopixel
from adafruit_led_animation.animation import pulse, rainbow, rainbowsparkle, solid
from adafruit_led_animation.sequence import AnimationSequence
from dotenv import load_dotenv

# Alert settings
ALERT_LENGTH = 5  # Alert animation length in seconds
COLOR_ACTIVE_TIME = 600  # Duration for which color remains active (10 minutes)
ALERT_TOKENS = 35  # Number of tokens to trigger a color alert

# LED settings
LED_COUNT = 100  # Number of LED pixels.
LED_PIN = board.D18  # GPIO pin connected to the pixels (18 is PCM).
LED_BRIGHTNESS = 0.1  # Float from 0.0 (min) to 1.0 (max)

# Setup module-level logger
logger = logging.getLogger(__name__)


class AlertColorList(Enum):
    """
    Enum of colors

    Each color is represented as a tuple of three integers, corresponding to
    the red, green, and blue values of the color. For example, the color
    "red" is represented as (255, 0, 0).
    """

    RED = (255, 0, 0)
    ORANGE = (255, 165, 0)
    YELLOW = (255, 255, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    INDIGO = (75, 0, 130)
    VIOLET = (148, 0, 211)
    BLACK = (0, 0, 0)


class LEDController:
    """
    Controls the LED strip.

    Args:
        pixels (neopixel.NeoPixel): The LED strip.
    """

    def __init__(self, pixels):
        self.pixels = pixels
        self.animations = self._create_animations()
        self.current_color = None
        self.color_set_time = None
        self.logger = logging.getLogger(__name__)

    def _create_animations(self):
        """
        Create the animations.

        Returns:
            AnimationSequence: The animation sequence.
        """
        animations = [
            rainbow.Rainbow(self.pixels, speed=0.01, period=60, name="rainbow"),
            rainbowsparkle.RainbowSparkle(
                self.pixels,
                speed=0.1,
                period=60,
                num_sparkles=5,
                name="sparkle",
                background_brightness=0.5,
            ),
        ]
        animations += [
            pulse.Pulse(
                self.pixels,
                speed=0.01,
                color=color.value,
                period=2,
                name=f"{color.name}_pulse",
            )
            for color in AlertColorList
        ]
        animations += [
            solid.Solid(self.pixels, color=color.value, name=color.name) for color in AlertColorList
        ]
        return AnimationSequence(*animations, advance_interval=None, auto_clear=True)

    async def animation_loop(self):
        """
        Run the animation loop.
        """
        while True:
            # Check if a color is currently set and if the set duration has expired
            if (
                self.current_color
                and self.color_set_time is not None
                and (time.time() - self.color_set_time > COLOR_ACTIVE_TIME)
            ):
                self.current_color = None  # Reset the color after the duration
                self.logger.info("Color alert duration expired. Resetting to rainbow.")
                self.animations.activate("rainbow")

            self.animations.animate()
            await asyncio.sleep(0)

    async def activate_normal_alert(self):
        """
        Activate a normal alert.
        """
        previous_state = self.animations.current_animation.name

        self.logger.debug("Activating normal alert.")
        self.animations.activate("sparkle")
        await asyncio.sleep(ALERT_LENGTH)

        self.animations.activate(previous_state)

    async def activate_color_alert(self, color):
        """
        Activate a color alert.

        Args:
            color (str): The color to activate.
        """
        self.current_color = color
        self.color_set_time = time.time()

        self.logger.debug(f"Activating color alert: {color}.")
        self.animations.activate(f"{color}_pulse")
        await asyncio.sleep(ALERT_LENGTH)

        if COLOR_ACTIVE_TIME < 60:
            # Convert to seconds if less than 60 seconds
            color_time = f"{COLOR_ACTIVE_TIME} seconds"
        else:
            # Convert to minutes if longer than 60 seconds
            color_time = f"{COLOR_ACTIVE_TIME // 60} minutes"

        self.logger.info(f"Setting lights to {color.lower()} for {color_time}.")
        self.animations.activate(color)

    async def stop_animation(self):
        """
        Stop the animation loop.
        """
        self.animations.freeze()
        self.pixels.fill((0, 0, 0))
        self.pixels.show()
        self.pixels.deinit()
        await asyncio.sleep(0)


class EventPoller:
    """
    Polls the Chaturbate Events API for events.

    Args:
        base_url (str): The base URL to poll.
        timeout (int): The timeout in seconds.
    """

    def __init__(self, base_url: str, timeout: int):
        self.base_url = base_url
        self.timeout = timeout
        self.retry_delay = 1
        self.logger = logging.getLogger(__name__)

    async def fetch_events(self):
        """
        Fetch events from the API.

        Yields:
            dict: The events object.
        """
        async with aiohttp.ClientSession() as session:
            url = self.base_url
            while True:
                try:
                    async with session.get(
                        url, timeout=aiohttp.ClientTimeout(total=self.timeout)
                    ) as response:
                        self.logger.debug(f"Fetching events from {url}")
                        if response.status == 200:
                            data = await response.json()
                            url = data["nextUrl"]
                            self.retry_delay = 1
                            yield data["events"]
                        else:
                            self.logger.error(f"Failed to fetch events: {response.status}")
                            await self.handle_error()
                except KeyboardInterrupt:
                    self.logger.info("Keyboard interrupt received, stopping event poller.")
                    break
                except aiohttp.ClientError as client_error:
                    self.logger.error(f"Error during event fetching: {client_error}")
                    await self.handle_error()

    async def handle_error(self):
        """
        Handle an error while fetching events.
        """
        await asyncio.sleep(self.retry_delay)

        # Double the retry delay, up to a maximum of 60 seconds
        self.retry_delay = min(self.retry_delay * 2, 60)


class EventProcessor:
    """
    Processes events, specifically focusing on tip events.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def process_events(self, events_gen, led_controller):
        """
        Process events.

        Args:
            events_gen (generator): The events generator.
            led_controller (LEDController): The LED controller.
        """
        async for events_obj in events_gen:
            for event in events_obj:
                if event["method"] == "tip":
                    await self.process_tip(event, led_controller)

    async def process_tip(self, event, led_controller):
        """
        Process a tip event.

        Args:
            event (dict): The event object.
            led_controller (LEDController): The LED controller.
        """
        tip_obj = event["object"]
        tip_details = tip_obj.get("tip", {})
        user_details = tip_obj.get("user", {})
        tokens = tip_details.get("tokens", 0)
        message = self.clean_message(tip_details.get("message", ""))
        is_anon = tip_details.get("isAnon", False)
        username = user_details.get("username", "Anonymous" if is_anon else "Unknown")

        self.log_tip_details(tokens, message, username)

        if tokens == ALERT_TOKENS and message.upper() in [color.name for color in AlertColorList]:
            await led_controller.activate_color_alert(message.upper())
        else:
            await led_controller.activate_normal_alert()

    def clean_message(self, message):
        """
        Clean the message.

        Args:
            message (str): The message to clean.

        Returns:
            str: The cleaned message.
        """
        prefix = "-- Select One -- | "
        if message.startswith(prefix):
            return message[len(prefix) :]
        if message == "-- Select One --":
            return ""
        return message

    def log_tip_details(self, tokens, message, username):
        """
        Log the tip details.

        Args:
            tokens (int): The number of tokens.
            message (str): The message.
            username (str): The username.
        """
        log_message = f"Tip received from {username}: {tokens} tokens."
        if message:
            log_message += f" Message: '{message}'"
        self.logger.debug(log_message)


async def main():
    """
    Main application entry point.
    """
    led_strip = neopixel.NeoPixel(
        LED_PIN, n=LED_COUNT, brightness=LED_BRIGHTNESS, auto_write=True  # type: ignore
    )

    led_controller = LEDController(led_strip)

    load_dotenv()
    request_timeout = int(os.getenv("TIMEOUT", "10"))
    api_username = os.getenv("USERNAME", "")
    api_token = os.getenv("TOKEN", "")
    api_timeout = int(request_timeout / 2)
    base_url = (
        f"https://events.testbed.cb.dev/events/{api_username}/{api_token}/?timeout={api_timeout}"
    )

    poller = EventPoller(base_url, request_timeout)
    processor = EventProcessor()

    animation_loop_task = asyncio.create_task(led_controller.animation_loop())
    process_events_task = asyncio.create_task(
        processor.process_events(poller.fetch_events(), led_controller)
    )

    try:
        await asyncio.gather(animation_loop_task, process_events_task)

    except asyncio.CancelledError:
        logger.info("Cancelling tasks.")
    finally:
        await led_controller.stop_animation()


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        filename="app.log",
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s",
        filemode="w",
    )

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application stopped by user.")
