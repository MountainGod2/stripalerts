"""
Config Module

This module manages configuration and logging for the application.
"""
import base64
import configparser
import logging
import os
from typing import Dict, Union
from urllib.parse import quote

from dotenv import load_dotenv

from constants import API_RESPONSE_TIMEOUT, LOG_FILENAME, LOG_LEVEL


class AppConfig:
    """
    Config class

    Manages configuration and logging for the application.
    """

    def __init__(
        self, log_filename: str = LOG_FILENAME, log_level: Union[int, str] = LOG_LEVEL
    ) -> None:
        load_dotenv()  # This loads the .env file at the initialization of AppConfig
        self.log_filename = log_filename
        self.log_level = log_level
        self.config = self.read_configuration()
        self.logger = self.configure_logging()

    def read_configuration(self) -> Dict[str, str]:
        """Read and process configuration from the .env file."""
        try:
            user_name = self.decode_and_encode(os.getenv("USER_NAME", ""))
            api_token = self.decode_and_encode(os.getenv("API_TOKEN", ""))

            base_url = os.getenv("BASE_URL", "")
            # base_url = "https://events.testbed.cb.dev/events"

            initial_url = f"{base_url}/{user_name}/{api_token}/?timeout={API_RESPONSE_TIMEOUT}"

            return {
                "user_name": user_name,
                "api_token": api_token,
                "initial_url": initial_url,
            }

        except (configparser.Error, FileNotFoundError) as error:
            log_message = f"Error reading configuration: {error}"
            self.logger.error(log_message)
            raise ValueError(log_message) from error

    def decode_and_encode(self, encoded_value: str) -> str:
        """
        Decode from base64 and then URL-encode the value.
        """
        try:
            decoded_value = base64.b64decode(encoded_value).decode("utf-8")
            return quote(decoded_value)

        except UnicodeDecodeError as error:
            log_message = f"Error decoding and encoding value: {error}"
            self.logger.error(log_message)
            raise ValueError(log_message) from error

    def configure_logging(self) -> logging.Logger:
        """
        Configure logging for the application.
        """
        # Convert log_level to its integer value if it's provided as a string
        numeric_level = logging.getLevelName(self.log_level)
        if not isinstance(numeric_level, int):
            log_message = f"Invalid log level: {self.log_level}"
            self.logger.error(log_message)
            raise ValueError(log_message)

        logging.basicConfig(
            filename=self.log_filename,
            format="%(asctime)s - %(levelname)s - %(message)s",
            level=numeric_level,
        )
        return logging.getLogger(__name__)
