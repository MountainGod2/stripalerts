"""
This is a simple example of how to use the Chaturbate Events API to process tips.
It will fetch events from the API and log any tips.
"""
import asyncio
import logging
import os

import aiohttp
from dotenv import load_dotenv


class AppSetup:
    """
    This class is used to load configuration from the .env file.
    """

    def __init__(self):
        load_dotenv()
        self.username = os.getenv("USERNAME")
        self.token = os.getenv("TOKEN")
        try:
            self.timeout = int(os.getenv("TIMEOUT", "10"))  # Default to "10" if not set
        except ValueError as exc:
            raise ValueError("TIMEOUT must be a valid integer.") from exc
        self.base_url = f"https://events.testbed.cb.dev/events/{self.username}/{self.token}/"

    def configure_logging(self):
        """
        Configure logging to write to a file.
        """
        logging.basicConfig(
            filename="app.log",
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            filemode="w",
        )

    def validate_configuration(self):
        """
        Validate the loaded configuration.

        Raises:
            ValueError: If any required configuration is missing or invalid.
        """
        required_configs = ["USERNAME", "TOKEN", "TIMEOUT"]
        missing_configs = [
            config for config in required_configs if getattr(self, config.lower()) is None
        ]

        if missing_configs:
            raise ValueError(f"Missing required configurations: {', '.join(missing_configs)}")
        try:
            timeout_value = int(self.timeout)
            if timeout_value <= 0:
                raise ValueError("TIMEOUT must be a positive integer.")
        except ValueError as exc:
            raise ValueError("TIMEOUT must be a valid integer.") from exc


class EventPoller:
    """
    This class is used to fetch events from the API.

    Args:
        base_url (str): The base URL to fetch events from.
        timeout (int): The timeout for the events API.
    """

    def __init__(self, base_url, timeout):
        self.base_url = base_url
        self.timeout = timeout
        self.session = aiohttp.ClientSession()

    async def fetch_events(self):
        """
        Fetch events from the API.

        Yields:
            list: A list of events.

        Raises:
            Exception: If an error occurs while fetching events.
        """
        url = self.base_url + f"?timeout={self.timeout}"
        try:
            while True:
                async with self.session.get(url) as response:
                    logging.debug("Fetching events from %s", url)
                    if response.status == 200:
                        data = await response.json()
                        url = data["nextUrl"]
                        yield data["events"]
                    else:
                        logging.error("Failed to fetch events: %s", response.status)
                        break
        except aiohttp.ClientError as client_error:
            logging.error("Error during event fetching: %s", client_error)
        finally:
            await self.close()

    async def close(self):
        """
        Close the session.
        """
        if self.session:
            await self.session.close()


class EventProcessor:
    """
    This class is used to process tips from the events.
    """

    def __init__(self):
        pass

    async def process_tips(self, events):
        """
        Process tips from the events.

        Args:
            events (list): A list of events.
        """

        for event in events:
            if event["method"] == "tip":
                tip_obj = event["object"]
                await self.log_tip_details(tip_obj)

    async def log_tip_details(self, tip_obj):
        """
        Log tip details to the console.

        Args:
            tip_obj (dict): A dictionary containing tip details.
        """

        broadcaster = tip_obj.get("broadcaster", "Unknown")
        tip_details = tip_obj.get("tip", {})
        user_details = tip_obj.get("user", {})
        tokens = tip_details.get("tokens", 0)
        message = tip_details.get("message", "")
        is_anon = tip_details.get("isAnon", False)

        # Remove the unwanted prefix if present
        prefix = "-- Select One -- | "
        if message.startswith(prefix):
            message = message[len(prefix) :]
        elif message == "-- Select One --":
            message = ""

        # Use the username if available, otherwise use Anonymous or Unknown
        username = user_details.get("username", "Anonymous" if is_anon else "Unknown")

        # Format the log message
        log_message = f"Tip received from {username} to {broadcaster}: {tokens} tokens."
        # Only log the message if it is not empty
        if message != "":
            log_message += f" Message: '{message}'"
        # Log the message to the file
        logging.info(log_message)


async def main():
    """
    The main entry point for the application.
    """
    setup = AppSetup()
    setup.configure_logging()

    poller = EventPoller(setup.base_url, setup.timeout)
    processor = EventProcessor()

    try:
        async for events in poller.fetch_events():
            await processor.process_tips(events)

    except asyncio.exceptions as async_exception:
        logging.error("Error in main: %s", async_exception)
        await poller.close()
    finally:
        await poller.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
