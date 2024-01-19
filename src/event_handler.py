from pydantic import BaseModel, ValidationError
import logging
from alert_colors_enum import AlertColor
from constants import AlertConfig


# Define Pydantic models for structured data
class User(BaseModel):
    username: str = "Unknown"


class Tip(BaseModel):
    tokens: int = 0
    message: str = ""


class TipEvent(BaseModel):
    user: User
    tip: Tip


class EventHandler:
    """
    Class to process events.

    Attributes:
        logger (logging.Logger): Logger instance.
    """

    def __init__(self):
        self.alert_config = AlertConfig()
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
                try:
                    event_method = event["method"]
                    self.logger.debug(f"Received event: {event_method}")
                    if event_method == "tip":
                        await self.process_tip(event, led_controller)
                except KeyError as e:
                    self.logger.error(f"Key error in event data: {e}")

    async def process_tip(self, event_dict, led_controller):
        try:
            self.logger.info("Tip received.")
            # Assuming the relevant data is nested under 'object' key in event_dict
            tip_data = event_dict.get("object", {})
            tip_event = TipEvent(**tip_data)
            username = tip_event.user.username
            tokens = tip_event.tip.tokens
            message = self.clean_message(tip_event.tip.message)
            color = AlertColor.from_string(message)

            self.logger.debug(
                f"Tip from {username}: {tokens} tokens. Message: '{message}'"
            )

            if tokens >= self.alert_config.tokens_for_color_alert and color:
                await led_controller.trigger_color_alert(color)
            else:
                await led_controller.trigger_normal_alert()

        except ValidationError as e:
            self.logger.error(f"Validation error: {e}")
            for error in e.errors():
                self.logger.error(f"Error in field '{error['loc'][0]}': {error['msg']}")
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
