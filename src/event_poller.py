"""EventPoller class."""

import asyncio
import logging

import aiohttp
import backoff

from constants import INITIAL_RETRY_DELAY, MAX_RETRY_DELAY, RETRY_FACTOR


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

    @backoff.on_exception(backoff.expo, aiohttp.ClientError, max_tries=5)
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
                        # If response status is any 5xx error
                        elif response.status >= 500:
                            self.logger.error(f"Server error: Status {response.status}")
                            await self.handle_error(server_error=True)
                        else:
                            self.logger.error(f"Error fetching events: Status {response.status}")
                            await self.handle_error()

                except aiohttp.ClientError as error:
                    self.logger.error(f"Client error: {error}")
                    await self.handle_error()

    async def handle_error(self, server_error=False):
        """Handle errors by waiting and increasing the retry delay."""
        if server_error:
            self.retry_delay = INITIAL_RETRY_DELAY
        else:
            self.retry_delay = min(self.retry_delay * RETRY_FACTOR, MAX_RETRY_DELAY)
        self.logger.info(f"Waiting {self.retry_delay} seconds before retrying...")
        await asyncio.sleep(self.retry_delay)
