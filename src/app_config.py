import json

# Load constants from config.json
with open("config.json", "r") as config_file:
    config = json.load(config_file)

# LED parameters
LED_PIN = config.get("LED_PIN", "D18")
LED_COUNT = config.get("LED_COUNT", 50)
LED_BRIGHTNESS = config.get("LED_BRIGHTNESS", 0.2)

# Alert parameters
TOKENS_FOR_COLOR_ALERT = config.get("TOKENS_FOR_COLOR_ALERT", 35)
ALERT_DURATION = config.get("ALERT_DURATION", 3)
COLOR_DURATION = config.get("COLOR_DURATION", 600)

# Animation parameters
ANIMATION_SPEED = 0.01

# Rainbow animation parameters
RAINBOW_PERIOD = config.get("RAINBOW_PERIOD", 60)
RAINBOW_SPEED = 0.01

# Sparkle alert parameters
SPARKLE_PERIOD = config.get("SPARKLE_PERIOD", 60)
SPARKLE_SPEED = 0.1
SPARKLE_NUM_SPARKLES = config.get("SPARKLE_NUM_SPARKLES", 5)
SPARKLE_BASE_BRIGHTNESS = config.get("SPARKLE_BASE_BRIGHTNESS", 0.5)

# Pulse alert parameters
PULSE_PERIOD = config.get("PULSE_PERIOD", ALERT_DURATION * 0.66)
PULSE_PERIOD = 1 if PULSE_PERIOD < 1 else PULSE_PERIOD
PULSE_SPEED = 0.01

# Other parameters
MAX_RETRY_DELAY = 60
RETRY_FACTOR = 2
INITIAL_RETRY_DELAY = 5
SECONDS_PER_MIN = 60
API_TIMEOUT = 2
