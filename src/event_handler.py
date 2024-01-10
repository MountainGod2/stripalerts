"""This module contains the EventProcessor class."""

import logging

from alert_colors_enum import AlertColor
from constants import TOKENS_FOR_COLOR_ALERT
from event_types import EventType


class EventHandler:
    """
    Class to process events.

    Attributes:
        logger (logging.Logger): Logger instance.
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    async def process_events(self, events_gen, led_controller):
        """
        Process events.

        Args:
            events_gen (generator): Generator for events.
            led_controller (LEDController): LED controller instance.
        """
        async for events in events_gen:
            for event in events:
                event_method = EventType(event["method"])
                self.logger.debug(f"Received event: {event_method}")
                if event_method == EventType.TIP:
                    await self.process_tip(event, led_controller)

    async def process_tip(self, event, led_controller):
        try:
            self.logger.info("Tip received.")
            tip = event["object"]["tip"]
            user = event["object"]["user"]
            username = user.get("username", "Unknown")
            tokens = tip.get("tokens", 0)
            message = self.clean_message(tip.get("message", ""))
            color = AlertColor.from_string(message)
            self.logger.debug(f"Tip from {username}: {tokens} tokens. Message: '{message}'")

            if tokens == TOKENS_FOR_COLOR_ALERT and color:
                await led_controller.trigger_color_alert(color)
            else:
                await led_controller.trigger_normal_alert()

        except Exception as e:
            self.logger.error(f"Error processing tip event: {e}")

    def clean_message(self, message):
        """
        Clean the message by removing the "-- Select One --" option.

        Args:
            message (str): Message to clean.

        Returns:
            str: Cleaned message.
        """
        return message.replace("-- Select One -- | ", "").replace("-- Select One --", "")
