"""
Constants and configuration parameters for the application.

This module contains constants and configuration parameters for the
application. It also contains an enum of colors that can be used to
represent colors in the application.
"""
# src/config.py
from enum import Enum

import board

# LED strip parameters
NUM_PIXELS = 4  # Number of pixels in the LED strip
PIXEL_PIN = board.D18  # Pin for the LED strip
PIXEL_BRIGHTNESS = 0.1  # Brightness of the pixels (0.0 to 1.0)

# Logging parameters
LOG_FILENAME = "stripalerts.log"  # Name of the log file
LOG_LEVEL = "INFO"  # Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

# LED animation parameters
ANIMATION_LOOP_SPEED = 0.001  # Speed of the animation loop in seconds
RAINBOW_SPEED = 0.01  # Speed of the rainbow animation in seconds
RAINBOW_PERIOD = 60  # Period of the rainbow animation in seconds
SPARKLE_SPEED = 0.02  # Speed of the sparkle animation in seconds
SPARKLE_PERIOD = 1  # Period of the sparkle animation in seconds
SPARKLE_NUM_SPARKLES = 50  # Number of sparkles in the sparkle animation
PULSE_PERIOD = 1  # Period of the pulse animation in seconds
PULSE_SPEED = 0.01  # Speed of the pulse animation in seconds

# LED alert parameters
COLOR_TIP_AMOUNT = 35  # Amount of tokens to tip for a color change
ALERT_DURATION = 2.5  # Duration of the alert animation in seconds
COLOR_TIMEOUT = 600  # Duration of the color change timeout in seconds
BACKGROUND_ANIMATION = "rainbow"  # Animation to play in the background
ALERT_ANIMATION = "sparkle"  # Animation to play during an alert

# API parameters
API_REQUEST_TIMEOUT = 20  # Timeout for API requests in seconds

# HTTP request parameters
HTTP_REQUEST_TIMEOUT = 30  # Timeout for HTTP requests in seconds
HTTP_RETRY_DELAY = 5  # Delay between HTTP request retries in seconds
HTTP_MAX_RETRIES = 10  # Maximum number of HTTP request retries


class ColorList(Enum):
    """Enum of colors

    Each color is represented as a tuple of three integers, corresponding to
    the red, green, and blue values of the color. For example, the color
    "red" is represented as (255, 0, 0)."""

    RED = (255, 0, 0)
    ORANGE = (255, 165, 0)
    YELLOW = (255, 255, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    INDIGO = (75, 0, 130)
    VIOLET = (148, 0, 211)
    BLACK = (0, 0, 0)
