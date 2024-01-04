"""
This module demonstrates an example usage of the Chaturbate Events API to process tips
and control LED animations based on the events.
"""

import asyncio
import json
import logging
import logging.config
import os

import neopixel
from dotenv import load_dotenv

from constants import API_TIMEOUT, LED_BRIGHTNESS, LED_COUNT, LED_PIN
from event_poller import EventPoller
from event_processor import EventProcessor
from led_controller import LEDController
from log_formatter import LogFormatter


# Configure logging
def setup_logging():
    """Sets up logging based on the configuration file and .env log level."""
    with open("logging_config.json", "r", encoding="utf-8") as config_file:
        config = json.load(config_file)

    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    config["loggers"][""]["level"] = log_level

    logging.config.dictConfig(config)


# Validate environment variables
def validate_env_vars():
    """Validates that all required environment variables are set."""
    required_vars = ["USERNAME", "TOKEN"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"Missing environment variables: {', '.join(missing_vars)}")


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
        self.api_username = os.getenv("USERNAME", "")
        self.api_token = os.getenv("TOKEN", "")
        self.base_url = os.getenv("BASE_URL", "https://eventsapi.chaturbate.com/events/")
        self.request_timeout = int(os.getenv("TIMEOUT", "30"))
        self.led_strip = self.setup_led_strip()
        self.logger = logging.getLogger(self.__class__.__name__)

    def setup_led_strip(self):
        """
        Setup the NeoPixel LED strip.

        Returns:
            neopixel.NeoPixel: NeoPixel LED strip.
        """
        try:
            return neopixel.NeoPixel(
                LED_PIN, LED_COUNT, brightness=LED_BRIGHTNESS, auto_write=False  # type: ignore
            )
        except RuntimeError as error:
            self.logger.error(f"Error initializing LED strip: {error}")
            raise

    def get_base_url(self):
        """
        Get the base URL for the Chaturbate Events API.

        Returns:
            str: Base URL for the Chaturbate Events API.
        """
        return f"{self.base_url}{self.api_username}/{self.api_token}/?timeout={API_TIMEOUT}"


async def main():
    """Main function."""

    # Load environment variables and validate
    load_dotenv()
    validate_env_vars()

    # Setup logging
    setup_logging()

    logger = logging.getLogger("StripAlerts")
    logger.debug("Setting up application.")

    # Create instances of the main classes
    config = AppConfig()
    led_controller = LEDController(config.led_strip)
    poller = EventPoller(config.get_base_url(), config.request_timeout)
    processor = EventProcessor()

    # Create tasks for the animation loop and event processing
    animation_task = asyncio.create_task(led_controller.run_animation_loop())
    processing_task = asyncio.create_task(
        processor.process_events(poller.fetch_events(), led_controller)
    )
    log_formatter = LogFormatter(delete_original=True)
    logger.debug("Application setup complete.")

    # Run the application
    try:
        logger.info("Starting application.")
        await asyncio.gather(animation_task, processing_task)
    except KeyboardInterrupt:
        logger.warning("Keyboard interrupt received. Stopping application.")
    finally:
        animation_task.cancel()
        processing_task.cancel()
        await asyncio.gather(animation_task, processing_task, return_exceptions=True)
        await led_controller.stop_animation()
        logger.info("Application stopped.")
        await log_formatter.align_logs()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
