"""
This module demonstrates an example usage of the Chaturbate Events API to process tips
and control LED animations based on the events.
"""
import asyncio
import json
import logging
import logging.config
import os
import signal

import board
import neopixel
from dotenv import load_dotenv

from constants import API_TIMEOUT
from event_poller import EventPoller
from event_processor import EventProcessor
from led_controller import LEDController
from log_formatter import LogFormatter


# Configure logging
def setup_logging():
    """
    Setup logging configuration from JSON file.
    """
    with open("logging_config.json", "r", encoding="utf-8") as config_file:
        config = json.load(config_file)
        logging.config.dictConfig(config)


def validate_env_vars():
    required_vars = ["USERNAME", "TOKEN"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logging.error("Missing environment variables: %s", missing_vars)
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
        self.base_url = os.getenv(
            "BASE_URL", "https://eventsapi.chaturbate.com/events/"
        )
        self.request_timeout = int(os.getenv("TIMEOUT", "30"))
        self.led_pin = str(os.getenv("LED_PIN", ""))
        self.led_count = int(os.getenv("LED_COUNT", "5"))
        self.led_brightness = float(os.getenv("LED_BRIGHTNESS", "0.1"))
        self.led_strip = self.setup_led_strip()

        self.logger = logging.getLogger(self.__class__.__name__)

    def setup_led_strip(self):
        """
        Setup the NeoPixel LED strip.

        Returns:
            neopixel.NeoPixel: NeoPixel LED strip.
        """
        pixel_pin = getattr(board, self.led_pin)
        try:
            return neopixel.NeoPixel(
                pin=pixel_pin,
                n=self.led_count,
                auto_write=False,
                brightness=self.led_brightness,
            )
        except Exception as error:
            self.logger.exception(error)
            raise

    def get_base_url(self):
        """
        Get the base URL for the Chaturbate Events API.

        Returns:
            str: Base URL for the Chaturbate Events API.
        """
        return f"{self.base_url}{self.api_username}/{self.api_token}/?timeout={API_TIMEOUT}"


async def main():
    # Initialize logging
    setup_logging()
    logger = logging.getLogger("StripAlerts")
    logger.info("Starting StripAlerts.")
    logger.debug("Logging initialized, beginning setup.")

    # Load environment variables and validate required variables are set
    logger.debug("Loading environment variables and validating.")
    load_dotenv()
    validate_env_vars()

    # Create a shutdown event for signal handling
    shutdown_event = asyncio.Event()

    # Define a signal handler that sets the shutdown event
    def signal_handler(sig, frame):
        logger.debug(f"Signal {sig} received, initiating shutdown.")
        shutdown_event.set()

    # Register the signal handler for interrupt and termination signals
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, signal_handler)

    # Create the application configuration
    config = AppConfig()
    logger.debug("Application configuration created.")

    # Create the LED controller, event poller, and event processor
    led_controller = LEDController(config.led_strip)
    poller = EventPoller(config.get_base_url(), config.request_timeout)
    processor = EventProcessor()
    logger.debug("Application objects created, starting tasks.")

    # Create and start tasks for LED animation and event processing
    animation_task = asyncio.create_task(led_controller.run_animation_loop())
    processing_task = asyncio.create_task(
        processor.process_events(poller.fetch_events(), led_controller)
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

    await LogFormatter("app.log", delete_original=True).align_logs()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit, asyncio.CancelledError):
        pass
