"""
Main entry point for the application.
"""
import asyncio
import json
import logging
import logging.config
import os
import signal
from dataclasses import dataclass

import board
import neopixel
from dotenv import load_dotenv

from constants import API_TIMEOUT
from event_handler import EventHandler
from event_poller import EventPoller
from led_controller import LEDController
from log_formatter import LogAligner


@dataclass
class APIConfig:
    """
    Class to hold API configuration.

    Attributes:
        username (str): Chaturbate username.
        token (str): Chaturbate API token.
        base_url (str): Base URL for the API.
        request_timeout (int): Timeout for API requests.
    """

    username: str = os.getenv("USERNAME", "")
    token: str = os.getenv("TOKEN", "")
    base_url: str = os.getenv("BASE_URL", "https://eventsapi.chaturbate.com/events/")
    request_timeout: int = int(os.getenv("TIMEOUT", "30"))


@dataclass
class LEDConfig:
    """
    Class to hold LED configuration.

    Attributes:
        pin (str): GPIO pin for the LED strip.
        count (int): Number of LEDs in the strip.
        brightness (float): Brightness of the LEDs.
    """

    pin: str = str(os.getenv("LED_PIN", "D18"))
    count: int = int(os.getenv("LED_COUNT", "5"))
    brightness: float = float(os.getenv("LED_BRIGHTNESS", "0.1"))


class AppConfig:
    """
    Application configuration.

    Attributes:
        api_config (APIConfig): API configuration.
        led_config (LEDConfig): LED configuration.
        logger (logging.Logger): Logger instance.
        pixel_pin (board.DigitalInOut): GPIO pin for the LED strip.
    """

    def __init__(self):
        self.api_config = APIConfig()
        self.led_config = LEDConfig()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.pixel_pin = getattr(board, self.led_config.pin)

    def initialize_led_strip(
        self,
    ):
        """
        Initialize the NeoPixel LED strip.

        Args:
            led_config (LEDConfig): Configuration for the LED strip.

        Returns:
            neopixel.NeoPixel: The configured NeoPixel LED strip.
        """
        try:
            return neopixel.NeoPixel(
                pin=self.pixel_pin,
                n=self.led_config.count,
                auto_write=False,
                brightness=self.led_config.brightness,
            )
        except Exception as error:
            self.logger.exception(error)
            raise

    def get_base_url(self):
        """
        Get the base URL for the API.

        Returns:
            str: Base URL for the API.
        """
        return f"{self.api_config.base_url}{self.api_config.username}/{self.api_config.token}/?timeout={API_TIMEOUT}"


def setup_logging():
    """Setup logging configuration from JSON file."""
    with open("logging_config.json", "r", encoding="utf-8") as config_file:
        config = json.load(config_file)
        logging.config.dictConfig(config)


def validate_env_vars():
    """Validate that all required environment variables are set."""
    required_vars = ["USERNAME", "TOKEN"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logging.error("Missing environment variables: %s", missing_vars)
        raise ValueError(f"Missing environment variables: {', '.join(missing_vars)}")


async def main():
    """Main entry point for the application."""

    # Initialize logging
    setup_logging()
    logger = logging.getLogger("StripAlerts")
    logger.info("Starting StripAlerts.")

    # Load environment variables and validate required variables are set
    logger.debug("Loading environment variables and validating.")
    load_dotenv()
    validate_env_vars()

    # Create the application configuration
    app_config = AppConfig()
    logger.debug("Application configuration created.")

    # Setup the LED strip
    logger.debug("Setting up LED strip.")
    led_strip = app_config.initialize_led_strip()

    # Create a shutdown event for signal handling
    shutdown_event = asyncio.Event()

    # Define a signal handler that sets the shutdown event
    def signal_handler(sig, _):
        logger.debug(f"Signal {sig} received, initiating shutdown.")
        shutdown_event.set()

    # Register the signal handler for interrupt and termination signals
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, signal_handler)

    # Create the LED controller, event poller, and event processor
    led_controller = LEDController(led_strip)
    poller = EventPoller(app_config.get_base_url(), app_config.api_config.request_timeout)
    processor = EventHandler()
    logger.debug("Application objects created, starting tasks.")

    # Create and start tasks for LED animation and event processing
    animation_task = asyncio.create_task(led_controller.run_animation_loop())
    processing_task = asyncio.create_task(
        processor.process_events(poller.poll_events(), led_controller)
    )

    # Wait for the shutdown event to be set
    await shutdown_event.wait()

    # Shutdown event received, cancel and await tasks
    logger.debug("Shutdown event received, cancelling tasks.")
    animation_task.cancel()
    processing_task.cancel()

    # Wait for tasks to finish
    logger.info("Stopping StripAlerts.")
    await asyncio.gather(animation_task, processing_task, return_exceptions=True)

    # Stop the LED animation and perform any necessary cleanup
    await led_controller.stop_animation()
    logger.debug("Cleanup complete, exiting.")

    await LogAligner("app.log", delete_original=True).align_log_entries()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit, asyncio.CancelledError):
        pass
