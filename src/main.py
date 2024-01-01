"""
This is a simple example of how to use the Chaturbate Events API to process tips.
It will fetch events from the API and log any tips.
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

# Alert settings
ALERT_LENGTH = 3  # Alert animation length in seconds
COLOR_ACTIVE_TIME = 600  # Duration for which color remains active (10 minutes)
ALERT_TOKENS = 35  # Number of tokens to trigger a color alert

# LED settings
LED_COUNT = 100  # Number of LED pixels.
LED_PIN = board.D18  # GPIO pin connected to the pixels (18 is PCM).
LED_BRIGHTNESS = 0.1  # Float from 0.0 (min) to 1.0 (max)
ANIMATION_SPEED = 0.01  # Animation speed

# Web request settings
MAX_RETRY_DELAY = 60  # Maximum retry delay in seconds
RETRY_FACTOR = 2  # Factor by which to increase retry delay
INITIAL_RETRY_DELAY = 2  # Initial retry delay in seconds
TIMEOUT_BUFFER_FACTOR = 2  # Factor by which to decrease api timeout

# Animation settings
RAINBOW_PERIOD = 60  # Rainbow animation period in seconds
RAINBOW_SPEED = 0.01  # Rainbow animation speed
SPARKLE_PERIOD = 60  # Sparkle animation period in seconds
SPARKLE_SPEED = 0.1  # Sparkle animation speed
SPARKLE_NUM_SPARKLES = 5  # Sparkle animation number of sparkles
SPARKLE_BRIGHTNESS = 0.5  # Sparkle animation brightness
PULSE_PERIOD = int(ALERT_LENGTH / (2 / 3))
PULSE_SPEED = 0.01  # Pulse animation speed
PULSE_BRIGHTNESS = 0.5  # Pulse animation brightness

# Time constants
ONE_MINUTE = 60  # Number of seconds in one minute


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
        self.logger = logging.getLogger(f"{__name__}.LEDController")

    def _create_animations(self):
        """
        Create the animations.

        Returns:
            AnimationSequence: The animation sequence.
        """
        animations = [
            rainbow.Rainbow(
                self.pixels, speed=RAINBOW_SPEED, period=RAINBOW_PERIOD, name="rainbow"
            ),
            rainbowsparkle.RainbowSparkle(
                self.pixels,
                speed=SPARKLE_SPEED,
                period=SPARKLE_PERIOD,
                num_sparkles=SPARKLE_NUM_SPARKLES,
                name="sparkle",
                background_brightness=SPARKLE_BRIGHTNESS,
            ),
        ]
        animations += [
            pulse.Pulse(
                self.pixels,
                speed=PULSE_SPEED,
                color=color.value,
                period=PULSE_PERIOD,
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
                # If so, reset the animation and clear the current color
                self.current_color = None
                self.logger.info("Color alert duration expired. Resetting to rainbow.")
                self.animations.activate("rainbow")

            self.animations.animate()
            await asyncio.sleep(ANIMATION_SPEED)

    async def activate_normal_alert(self):
        """
        Activate a normal alert.
        """

        # Store the previous state so we can return to it after the alert
        previous_state = self.animations.current_animation.name

        self.logger.debug("Activating normal alert.")

        # Activate the sparkle animation
        self.animations.activate("sparkle")
        await asyncio.sleep(ALERT_LENGTH)

        # Return to the previous state stored above
        self.animations.activate(previous_state)

    async def activate_color_alert(self, color):
        """
        Activate a color alert.

        Args:
            color (str): The color to activate.
        """
        self.current_color = color
        self.color_set_time = time.time()

        self.logger.debug("Activating color alert: %s", color.lower())

        # Activate the pulse animation for the selected color
        self.animations.activate(f"{color}_pulse")
        await asyncio.sleep(ALERT_LENGTH)

        # Convert to seconds if less than 60 seconds
        if COLOR_ACTIVE_TIME < ONE_MINUTE:
            color_time = f"{COLOR_ACTIVE_TIME} seconds"

        # Convert to minutes if longer than 60 seconds
        else:
            color_time = f"{COLOR_ACTIVE_TIME // ONE_MINUTE} minutes"

        self.logger.info("Settings lights to %s for %s.", color.lower(), color_time)

        # Activate the solid animation for the selected color
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
        self.retry_delay = INITIAL_RETRY_DELAY
        self.logger = logging.getLogger(f"{__name__}.EventPoller")

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
                        self.logger.debug("Fetching events from %s", url)
                        if response.status == 200:
                            data = await response.json()
                            url = data["nextUrl"]
                            self.retry_delay = 1
                            yield data["events"]
                        else:
                            self.logger.error(
                                "Error fetching events: %s. Status: %s",
                                url,
                                response.status,
                            )
                            await self.handle_error()
                except KeyboardInterrupt:
                    self.logger.info("Keyboard interrupt received, stopping event poller.")
                    break
                except aiohttp.ClientError as client_error:
                    self.logger.error(
                        "Error fetching events from %s: %s",
                        url,
                        client_error.__class__.__name__,
                    )
                    await self.handle_error()

    async def handle_error(self):
        """
        Handle an error.
        """

        # Wait for initial retry delay before retrying
        self.logger.info("Waiting %s seconds before retrying.", self.retry_delay)
        await asyncio.sleep(self.retry_delay)

        # Check if the maximum retry delay has been reached
        if self.retry_delay == MAX_RETRY_DELAY:
            self.logger.warning(
                "Maximum retry delay of %s reached. Will not increase further.",
                MAX_RETRY_DELAY,
            )

        else:
            # Double the retry delay, up to a maximum of 60 seconds
            self.retry_delay = min(self.retry_delay * RETRY_FACTOR, MAX_RETRY_DELAY)
            self.logger.debug("Retry delay is now %s seconds.", self.retry_delay)


class EventProcessor:
    """
    Processes events, specifically focusing on tip events.
    """

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.EventProcessor")

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

    # Setup logging
    with open("logging_config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
        logging.config.dictConfig(config)
        logger = logging.getLogger(__name__)
        logger = logging.getLogger(f"{__name__}.StripAlerts")

    logger.debug("Beginning application setup.")

    # Load environment variables
    load_dotenv()

    # Setup LED strip
    led_strip = neopixel.NeoPixel(
        LED_PIN, n=LED_COUNT, brightness=LED_BRIGHTNESS, auto_write=True  # type: ignore
    )

    # Setup request parameters
    request_timeout = int(os.getenv("TIMEOUT", "10"))
    api_username = str(os.getenv("USERNAME", ""))
    api_token = str(os.getenv("TOKEN", ""))
    base_url_env = str(os.getenv("BASE_URL", "https://eventsapi.chaturbate.com/events/"))
    api_timeout = int(request_timeout // TIMEOUT_BUFFER_FACTOR)
    base_url = f"{base_url_env}{api_username}/{api_token}/?timeout={api_timeout}"

    # Setup application objects using LED strip and request parameters
    led_controller = LEDController(led_strip)
    poller = EventPoller(base_url, request_timeout)
    processor = EventProcessor()

    # Create tasks to run concurrently
    animation_loop_task = asyncio.create_task(led_controller.animation_loop())
    process_events_task = asyncio.create_task(
        processor.process_events(poller.fetch_events(), led_controller)
    )

    logger.debug("Application setup complete.")
    logger.info("Starting application.")

    # Run task loops and await completion (should never happen)
    try:
        await asyncio.gather(animation_loop_task, process_events_task)

    # Handle keyboard interrupt and shutdown gracefully
    except KeyboardInterrupt:
        logger.warning("KeyboardInterrupt received.")

    # Stop the animation loop and tasks and await completion
    finally:
        logger.debug("Stopping application...")
        animation_loop_task.cancel()
        process_events_task.cancel()
        await asyncio.gather(animation_loop_task, process_events_task, return_exceptions=True)
        await led_controller.stop_animation()
        logger.info("Application stopped.")

        # Format the log file
        align_logs("./app.log")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
