"""Constants for the alert light program."""
import os
import dotenv

dotenv.load_dotenv()

# LED parameters
LED_PIN = str(os.getenv("LED_PIN", ""))
LED_COUNT = int(os.getenv("LED_COUNT", "5"))
LED_BRIGHTNESS = float(os.getenv("LED_BRIGHTNESS", "0.1"))


# Alert parameters
COLOR_ALERT_TOKENS = int(os.getenv("COLOR_ALERT_TOKENS", "35"))
ALERT_DURATION = int(os.getenv("ALERT_DURATION", "60"))
COLOR_DURATION = int(os.getenv("COLOR_DURATION", "600"))

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
PULSE_PERIOD = ALERT_DURATION * (2 // 3)  # Time in seconds to complete a pulse cycle
PULSE_PERIOD = (
    1 if PULSE_PERIOD < 1 else PULSE_PERIOD
)  # Minimum pulse period is 1 second
PULSE_SPEED = 0.01  # Speed of pulse animation

# Other parameters
MAX_RETRY_DELAY = 60  # Maximum delay between retries in seconds
RETRY_FACTOR = 2  # Factor by which to increase retry delay
INITIAL_RETRY_DELAY = 5  # Initial delay between retries in seconds
SECONDS_PER_MIN = 60  # Number of seconds in a minute
API_TIMEOUT = 2  # Timeout for API requests in seconds
