"""
Main entry point for the application.
"""
import asyncio
import json
import logging
import logging.config
import os
import signal
import sys

import board
import neopixel

from constants import API_TIMEOUT, LEDConfig, APIConfig
from event_handler import EventHandler
from event_poller import EventPoller
from led_controller import LEDController
from log_formatter import LogAligner


def setup_logging():
    """Setup logging configuration from JSON file."""
    with open("logging_config.json", "r", encoding="utf-8") as config_file:
        config = json.load(config_file)
        logging.config.dictConfig(config)


class ValidateRequiredVariables:
    """Validates required vairables are set."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def validate_env_vars(self):
        """Validate that all required environment variables are set."""
        required_vars = ["USERNAME", "TOKEN"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            logging.error("Missing environment variables: %s", missing_vars)
            raise ValueError(f"Missing environment variables: {', '.join(missing_vars)}")


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
        self.pixel_pin = getattr(board, self.led_config.pin)
        self.logger = logging.getLogger(self.__class__.__name__)

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
        self.app_config = AppConfig()
        self.led_strip = None
        self.led_controller = None
        self.poller = None
        self.processor = EventHandler()

    def initialize_services(self):
        """Initialize services that should start only on demand."""
        self.led_strip = self.app_config.initialize_led_strip()
        self.led_controller = LEDController(self.led_strip)
        self.poller = EventPoller(
            self.app_config.get_base_url(), self.app_config.api_config.request_timeout
        )

        # Register the signal handler for interrupt and termination signals
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, self.signal_handler)

    # Define a signal handler that sets the shutdown event
    def signal_handler(self, sig, frame):
        logging.debug(f"Signal {sig} received, initiating shutdown.")
        asyncio.create_task(self.stop_service())

    def start_service_logic(self, app_instance, storage):
        """Start the main logic of the StripAlertsApp."""
        if not app_instance.led_controller:  # Check if services are already initialized
            app_instance.initialize_services()
        asyncio.create_task(app_instance.start_service())
        storage.update(app_running=True)

    async def start_service(self):
        """Starts the main application."""
        logging.info("StripAlerts started.")
        validate_envs = ValidateRequiredVariables()
        # Load environment variables and validate required variables are set
        validate_envs.validate_env_vars()

        # Create and start tasks for LED animation and event processing
        if self.led_controller:
            self.animation_task = asyncio.create_task(self.led_controller.run_animation_loop())
        if self.poller:
            self.processing_task = asyncio.create_task(
                self.processor.process_events(self.poller.poll_events(), self.led_controller)
            )

        await self.shutdown_event.wait()

    def is_running(self):
        """Check if the application is currently running."""
        return not self.shutdown_event.is_set()

    async def get_logs(self):
        """Retrieve log contents."""
        try:
            with open("app.log", "r"):
                await LogAligner().align_log_entries()
        except FileNotFoundError:
            return "Log file not found."

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

        try:
            if self.led_controller:
                await self.led_controller.stop_animation()
        except Exception:
            pass

        await self.get_logs()
        logging.info("StripAlerts stopped.")

    @staticmethod
    async def run_standalone():
        app = StripAlertsApp()
        dummy_storage = {}  # Create a dummy storage object
        app.start_service_logic(app, dummy_storage)  # Start services using the unified method
        await app.shutdown_event.wait()  # Wait for the shutdown event to be set


setup_logging()
if __name__ == "__main__":
    # Option to run the web UI
    if "--web-ui" in sys.argv:
        from webui import index as run_web_ui

        run_web_ui()
    else:
        # Existing CLI-based execution code
        try:
            asyncio.run(StripAlertsApp.run_standalone())
        except (KeyboardInterrupt, SystemExit, asyncio.CancelledError):
            pass
