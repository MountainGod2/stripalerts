
# Chaturbate Events API and LED Controller

This Python script utilizes the Chaturbate Events API to process tip events and controls an LED strip to provide visual alerts. When certain conditions are met, such as receiving a specific number of tokens, the LED strip displays different animations or colors.

## Features

- **Event Polling:** Continuously polls the Chaturbate Events API for new events.
- **Tip Processing:** Detects tip events and activates LED animations based on the number of tokens.
- **LED Control:** Manages an LED strip to display various animations and colors.
- **Color Alerts:** Supports color-specific alerts based on user messages.
- **Customizable Settings:** Includes settings for alert duration, LED brightness, and more.

## Requirements

- Python 3.x
- `aiohttp` for asynchronous HTTP requests
- `neopixel` and `board` for LED control
- `adafruit_led_animation` for LED animations
- `dotenv` for environment variable management

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/your-repo-name.git
   ```

2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Create a `.env` file in the root directory and specify the following variables:
- `TIMEOUT`: Request timeout for the API.
- `USERNAME`: Your Chaturbate API username.
- `TOKEN`: Your Chaturbate API token.

## Usage

Run the script using:
```bash
python main.py
```

## LED Settings

Modify the `LED_COUNT`, `LED_PIN`, and `LED_BRIGHTNESS` variables in `main.py` to match your LED strip's specifications.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Chaturbate Events API for providing the event data.
- Adafruit for the LED animation library.
