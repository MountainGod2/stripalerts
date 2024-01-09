"""Alert colors enum."""
from enum import Enum


class AlertColor(Enum):
    """
    Enum for alert colors.

    Attributes:
        RED (tuple): RGB value for red.
        ORANGE (tuple): RGB value for orange.
        YELLOW (tuple): RGB value for yellow.
        GREEN (tuple): RGB value for green.
        BLUE (tuple): RGB value for blue.
        INDIGO (tuple): RGB value for indigo.
        VIOLET (tuple): RGB value for violet.
        BLACK (tuple): RGB value for black.
    """

    # def __iter__(self):
    #     return iter(AlertColors.__members__)

    RED = (255, 0, 0)
    ORANGE = (255, 165, 0)
    YELLOW = (255, 255, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    INDIGO = (75, 0, 130)
    VIOLET = (148, 0, 211)
    BLACK = (0, 0, 0)

    @staticmethod
    def from_string(color_str):
        """
        Get the AlertColor enum value from a string.

        Args:
            color_str (str): Color name.

        Returns:
            AlertColor: AlertColor enum value.
        """
        return AlertColor.__members__.get(color_str.upper(), None)
