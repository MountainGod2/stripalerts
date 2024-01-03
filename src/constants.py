"""Constants for the alert light program."""
import board

# LED parameters
LED_COUNT = 100  # Number of NeoPixels
LED_PIN = board.D18  # GPIO pin connected to the pixels (18 is PCM)
LED_BRIGHTNESS = 0.1  # Float from 0.0 (min) to 1.0 (max)

# Alert parameters
COLOR_ALERT_TOKENS = 35  # Number of tokens to trigger color changing alert
ALERT_LENGTH = 3  # Length of alert in minutes
COLOR_ACTIVE_TIME = 600  # Time in seconds to keep color active after alert

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
PULSE_PERIOD = int(ALERT_LENGTH * 2 / 3)  # Time in seconds to complete a pulse cycle
PULSE_PERIOD = 1 if PULSE_PERIOD < 1 else PULSE_PERIOD  # Minimum pulse period is 1 second
PULSE_SPEED = 0.01  # Speed of pulse animation

# Other parameters
MAX_RETRY_DELAY = 60  # Maximum delay between retries in seconds
RETRY_FACTOR = 2  # Factor by which to increase retry delay
INITIAL_RETRY_DELAY = 5  # Initial delay between retries in seconds
TIMEOUT_BUFFER_FACTOR = 2  # Factor by which to reduce api timeout from request timeout
SECONDS_PER_MIN = 60  # Number of seconds in a minute
