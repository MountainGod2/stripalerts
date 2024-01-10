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


class StripAlertsApp:
    def __init__(self):
        self.shutdown_event = asyncio.Event()
        self.animation_task = None
        self.processing_task = None

        # Initialize configurations
        self.app_config = AppConfig()
        self.led_strip = self.app_config.initialize_led_strip()
        self.led_controller = LEDController(self.led_strip)
        self.poller = EventPoller(
            self.app_config.get_base_url(), self.app_config.api_config.request_timeout
        )
        self.processor = EventHandler()

        # Register the signal handler for interrupt and termination signals
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, self.signal_handler)

    # Define a signal handler that sets the shutdown event
    def signal_handler(self, sig, frame):
        logging.debug(f"Signal {sig} received, initiating shutdown.")
        asyncio.create_task(self.stop_service())

    async def start_service(self):
        """Starts the main application."""
        setup_logging()
        load_dotenv()
        logging.info("StripAlerts started.")

        # Load environment variables and validate required variables are set
        validate_env_vars()

        # Create and start tasks for LED animation and event processing
        self.animation_task = asyncio.create_task(self.led_controller.run_animation_loop())
        self.processing_task = asyncio.create_task(
            self.processor.process_events(self.poller.poll_events(), self.led_controller)
        )

        await self.shutdown_event.wait()

    async def stop_service(self):
        """Stops the main application."""
        if self.shutdown_event:
            self.shutdown_event.set()

        if self.animation_task:
            self.animation_task.cancel()
            try:
                await self.animation_task
            except asyncio.CancelledError:
                pass

        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass

        await self.led_controller.stop_animation()
        logging.info("StripAlerts stopped.")
        await LogAligner(delete_original=True).align_log_entries()

    # Optional: If you want to support standalone execution of the script
    @staticmethod
    async def run_standalone():
        app = StripAlertsApp()
        await app.start_service()


if __name__ == "__main__":
    try:
        asyncio.run(StripAlertsApp.run_standalone())
    except (KeyboardInterrupt, SystemExit, asyncio.CancelledError):
        pass
