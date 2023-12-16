"""
Application Manager

This module manages configuration and logging for the application.
"""
# src/setup.py
import base64
import configparser
import logging

from config import API_TIMEOUT, LOG_FILENAME, LOG_LEVEL


class AppManager:
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
        """Read configuration from the config file."""
        config = configparser.ConfigParser()
        config.read(self.credentials_file)

        try:
            # Decode base64-encoded credentials
            encoded_user_name = config.get("Credentials", "user_name")
            encoded_api_token = config.get("Credentials", "api_token")

            user_name = base64.b64decode(encoded_user_name).decode("utf-8")
            api_token = base64.b64decode(encoded_api_token).decode("utf-8")

            # Format the URL
            initial_url = f"https://events.testbed.cb.dev/events/{user_name}/{api_token}/?timeout={API_TIMEOUT}"

            return {
                "user_name": user_name,
                "api_token": api_token,
                "initial_url": initial_url,
            }

        except configparser.Error as error:
            raise ValueError(f"Error reading configuration: {error}") from error

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
