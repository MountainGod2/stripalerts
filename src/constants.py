"""Constants for the alert light program."""
import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.getcwd(), ".env"))


@dataclass
class LEDConfig:
    pin: str = os.getenv("LED_PIN", "")
    count: int = int(os.getenv("LED_COUNT", "5"))
    brightness: float = float(os.getenv("LED_BRIGHTNESS", "0.1"))


@dataclass
class AlertConfig:
    tokens_for_color_alert: int = int(os.getenv("TOKENS_FOR_COLOR_ALERT", "35"))
    alert_duration: int = int(os.getenv("ALERT_DURATION", "3"))
    color_duration: int = int(os.getenv("COLOR_DURATION", "600"))


@dataclass
class APIConfig:
    username: str = os.getenv("USERNAME", "")
    token: str = os.getenv("TOKEN", "")
    base_url: str = os.getenv("BASE_URL", "https://eventsapi.chaturbate.com/events/")
    request_timeout: int = int(os.getenv("TIMEOUT", "30"))


# Animation parameters
ANIMATION_SPEED = 0.01  # Speed of animation loop

# Rainbow animation parameters (run when no alerts or colors are active)
RAINBOW_PERIOD = 60  # Time in seconds to complete a rainbow cycle
RAINBOW_SPEED = 0.01  # Speed of rainbow animation

# Sparkle alert parameters (used for normal alerts)
SPARKLE_PERIOD = 60  # Time in seconds to complete a sparkle cycle
SPARKLE_SPEED = 0.1  # Speed of sparkle animation
SPARKLE_NUM_SPARKLES = 5  # Number of sparkles in sparkle animation
SPARKLE_BASE_BRIGHTNESS = 0.5  # Base brightness of sparkle animation

# Pulse alert parameters (used for color alerts)
PULSE_PERIOD = AlertConfig().alert_duration * (
    2 // 3  # Always complete pulse cycle within 2/3 of alert duration
)  # Time in seconds to complete a pulse cycle
PULSE_PERIOD = 1 if PULSE_PERIOD < 1 else PULSE_PERIOD  # Minimum pulse period is 1 second
PULSE_SPEED = 0.01  # Speed of pulse animation

# Other parameters
MAX_RETRY_DELAY = 60  # Maximum delay between retries in seconds
RETRY_FACTOR = 2  # Factor by which to increase retry delay
INITIAL_RETRY_DELAY = 5  # Initial delay between retries in seconds
SECONDS_PER_MIN = 60  # Number of seconds in a minute
API_TIMEOUT = 2  # Timeout for API requests in seconds
