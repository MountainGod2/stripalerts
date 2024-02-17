"""Event handler module."""

import logging
from typing import Generator

from pydantic import BaseModel, ValidationError

from alert_colors_enum import AlertColor
from app_config import TOKENS_FOR_COLOR_ALERT
from led_controller import LEDController


class User(BaseModel):
    """Model representing a user."""

    username: str = "Unknown"


class Tip(BaseModel):
    """Model representing a tip."""

    tokens: int = 0
    message: str = ""


class TipEvent(BaseModel):
    """Model representing a tip event."""

    user: User
    tip: Tip


class EventHandler:
    """
    Class to process events.

    Attributes:
        logger (logging.Logger): Logger instance.
    """

    def __init__(self):
        """Initialize EventHandler."""
        self.logger = logging.getLogger(self.__class__.__name__)

    async def process_events(self, events_gen: Generator, led_controller: LEDController):
        """
        Process events.

        Args:
            events_gen (generator): Generator for events.
            led_controller (LEDController): LED controller instance.
        """
        async for events in events_gen:
            for event in events:
                await self._process_event(event, led_controller)

    async def _process_event(self, event: dict, led_controller: LEDController):
        """
        Process a single event.

        Args:
            event (dict): Event data.
            led_controller (LEDController): LED controller instance.
        """
        try:
            method = event.get("method")
            self.logger.debug(f"Received event: {method}")
            if method == "tip":
                await self._process_tip(event, led_controller)
        except KeyError as e:
            self.logger.error(f"Key error in event data: {e}")

    async def _process_tip(self, event: dict, led_controller: LEDController):
        """
        Process a tip event.

        Args:
            event (dict): Tip event data.
            led_controller (LEDController): LED controller instance.
        """
        try:
            self.logger.info("Tip received.")
            tip_data = event.get("object", {})
            tip_event = TipEvent(**tip_data)
            username = tip_event.user.username
            tokens = tip_event.tip.tokens
            message = self._clean_message(tip_event.tip.message)
            color = AlertColor.from_string(message)

            self.logger.debug(
                f"Tip from {username}: {tokens} tokens. Message: '{message}'"
            )

            if tokens >= TOKENS_FOR_COLOR_ALERT and color:
                await led_controller.trigger_color_alert(color)
            else:
                await led_controller.trigger_normal_alert()

        except ValidationError as e:
            self._handle_validation_error(e)
        except Exception as e:
            self.logger.error(f"Error processing tip event: {e}")

    def _clean_message(self, message: str) -> str:
        """
        Clean the message by removing unwanted text.

        Args:
            message (str): Message to clean.

        Returns:
            str: Cleaned message.
        """
        return (
            message.replace("-- Select One -- | ", "")
            .replace("-- Select One --", "")
            .replace(" | ", "")
        )

    def _handle_validation_error(self, error: ValidationError):
        """
        Handle validation errors.

        Args:
            error (ValidationError): Validation error.
        """
        self.logger.error("Validation error occurred:")
        for error in error.errors():
            field, message = error["loc"][0], error["msg"]
            self.logger.error(f"Error in field '{field}': {message}")
