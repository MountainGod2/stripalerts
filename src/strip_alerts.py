import asyncio
import json
import logging
import logging.config
import signal

import board
import neopixel

from api_config import APIConfig
from app_config import API_TIMEOUT, LED_BRIGHTNESS, LED_COUNT, LED_PIN
from event_handler import EventHandler
from event_poller import EventPoller
from led_controller import LEDController
from log_formatter import LogAligner


def setup_logging():
    """Setup logging configuration from JSON file."""
    with open("logging_config.json", "r", encoding="utf-8") as config_file:
        config = json.load(config_file)
        logging.config.dictConfig(config)


class AppConfig:
    """
    Application configuration.
    """

    def __init__(self):
        self.api_config = APIConfig()
        self.logger = logging.getLogger(self.__class__.__name__)

    def initialize_led_strip(self):
        """Initialize the NeoPixel LED strip."""
        try:
            return neopixel.NeoPixel(
                pin=getattr(board, LED_PIN),
                n=LED_COUNT,
                auto_write=False,
                bpp=3,
                brightness=LED_BRIGHTNESS,
                pixel_order="RGB",
            )
        except Exception as error:
            self.logger.exception(error)
            raise

    def get_base_url(self):
        """Get the base URL for the API."""
        return f"{self.api_config.base_url}{self.api_config.username}/{self.api_config.token}/?timeout={API_TIMEOUT}"


class StripAlertsApp:
    def __init__(self):
        self.shutdown_event = asyncio.Event()
        self.animation_task = None
        self.processing_task = None
        self.app_config = None
        self.led_strip = None
        self.led_controller = None
        self.poller = None
        self.processor = None
        self.logger = logging.getLogger(self.__class__.__name__)

    async def start_service(self):
        """Starts the main application."""
        self.logger.info("StripAlerts started.")
        self.shutdown_event.clear()
        try:
            self.initialize_services()
            await self.run_tasks()
        except Exception as e:
            self.logger.error(f"Error starting service: {e}")
            await self.stop_service()

    def initialize_services(self):
        """Initialize services."""
        self.app_config = AppConfig()
        self.led_strip = self.app_config.initialize_led_strip()
        self.led_controller = LEDController(self.led_strip)
        self.poller = EventPoller(
            self.app_config.get_base_url(), self.app_config.api_config.request_timeout
        )
        self.processor = EventHandler()

        # Register signal handlers
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, self.signal_handler)

    def signal_handler(self, sig, frame):
        """Signal handler."""
        if self.is_running() and not self.shutdown_event.is_set():
            self.logger.debug(f"Signal {sig} received, initiating shutdown.")
            asyncio.create_task(self.stop_service())

    async def run_tasks(self):
        """Run tasks."""
        if self.led_controller:
            self.animation_task = asyncio.create_task(
                self.led_controller.run_animation_loop()
            )
        if self.poller and self.processor:
            self.processing_task = asyncio.create_task(
                self.processor.process_events(
                    self.poller.poll_events(), self.led_controller
                )
            )

        await self.shutdown_event.wait()

    async def stop_service(self):
        """Stops the main application."""
        if self.shutdown_event:
            self.shutdown_event.set()

        await self.cancel_task(self.animation_task)
        await self.cancel_task(self.processing_task)

        try:
            if self.led_controller:
                await self.led_controller.stop_animation()
        except Exception as e:
            self.logger.error(f"Error stopping animation: {e}")

        self.logger.info("StripAlerts stopped.")

    async def cancel_task(self, task):
        """Cancel task if not None."""
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    def is_running(self):
        """Check if the application is currently running."""
        return not self.shutdown_event.is_set()

    @staticmethod
    async def run_standalone():
        """Run standalone."""
        setup_logging()
        app = StripAlertsApp()
        await app.start_service()


async def align_logs():
    """Retrieve log contents."""
    try:
        await LogAligner(delete_original=True).align_log_entries()
    except FileNotFoundError:
        logging.error("Log file not found.")


def main():
    """Main function to start the StripAlerts application."""
    try:
        asyncio.run(StripAlertsApp.run_standalone())
    except (KeyboardInterrupt, SystemExit, asyncio.CancelledError):
        pass
    finally:
        asyncio.get_event_loop().close()

        align_logs()


if __name__ == "__main__":
    main()
