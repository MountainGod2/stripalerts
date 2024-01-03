"""This module contains the EventProcessor class."""

import logging

from constants import COLOR_ALERT_TOKENS
from event_types import EventType
from led_controller import AlertColors


class EventProcessor:
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
        """
        Process tip events.

        Args:
            event (dict): Tip event.
            led_controller (LEDController): LED controller instance.
        """
        tip = event["object"]["tip"]
        tokens = tip.get("tokens", 0)
        message = self.clean_message(tip.get("message", ""))
        color = AlertColors.from_string(message)
        if tokens == COLOR_ALERT_TOKENS and color:
            await led_controller.activate_color_alert(color)
        else:
            await led_controller.activate_normal_alert()

        # If log level is DEBUG, log tip details
        if self.logger.isEnabledFor(logging.DEBUG):
            self.log_tip_details(tip, event["object"]["user"])

    def clean_message(self, message):
        """
        Clean the message by removing the "-- Select One --" option.

        Args:
            message (str): Message to clean.

        Returns:
            str: Cleaned message.
        """
        return message.replace("-- Select One -- | ", "").replace("-- Select One --", "")

    def log_tip_details(self, tip, user):
        """
        Log tip details.

        Args:
            tip (dict): Tip details.
            user (dict): User details.
        """
        tokens = tip.get("tokens", 0)
        message = tip.get("message", "")
        username = user.get("username", "Unknown")
        self.logger.debug(f"Tip received from {username}: {tokens} tokens. Message: '{message}'")
