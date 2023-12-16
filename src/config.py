"""
Application Manager

This module manages configuration and logging for the application.
"""
# src/setup.py
import base64
import configparser
import logging
from urllib.parse import quote
from constants import API_TIMEOUT, LOG_FILENAME, LOG_LEVEL


class Config:
    """
    Application Manager

    Manages configuration and logging for the application.
    """

    def __init__(
        self,
        credentials_file="credentials.ini",
        log_filename=LOG_FILENAME,
        log_level=LOG_LEVEL,
    ):
        self.credentials_file = credentials_file
        self.log_filename = log_filename
        self.log_level = log_level
        self.config = self.read_configuration()
        self.logger = self.configure_logging()

    def read_configuration(self):
        """Read and process configuration from the config file."""
        config = configparser.ConfigParser()

        # Ensure the configuration file exists and can be read
        try:
            config.read(self.credentials_file)
            if not config.sections():
                raise FileNotFoundError(
                    f"Configuration file '{self.credentials_file}' not found or is empty."
                )

            # Decode and URL-encode the credentials
            user_name = self.decode_and_encode(config.get("Credentials", "user_name"))
            api_token = self.decode_and_encode(config.get("Credentials", "api_token"))

            # Construct the URL
            base_url = "https://events.testbed.cb.dev/events"
            initial_url = f"{base_url}/{user_name}/{api_token}/?timeout={API_TIMEOUT}"

            return {
                "user_name": user_name,
                "api_token": api_token,
                "initial_url": initial_url,
            }

        except (configparser.Error, FileNotFoundError) as error:
            raise ValueError(f"Error reading configuration: {error}") from error

    def decode_and_encode(self, encoded_value):
        """
        Decode from base64 and then URL-encode the value.
        """
        try:
            decoded_value = base64.b64decode(encoded_value).decode("utf-8")
            return quote(decoded_value)
        except UnicodeDecodeError as error:
            raise ValueError(f"Error decoding and encoding value: {error}") from error

    def configure_logging(self):
        """
        Configure logging for the application.
        """
        logging.basicConfig(
            filename=self.log_filename,
            format="%(asctime)s - %(levelname)s - %(message)s",
            level=self.log_level,
        )
        return logging.getLogger(__name__)
