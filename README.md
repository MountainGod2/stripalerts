# StripAlerts - LED Alerts for Chaturbate Events

![example](https://github.com/MountainGod2/stripalerts/assets/88257202/bedc83a7-e428-4026-9d2c-249b31c61371)

Enhance your Chaturbate streaming experience with StripAlerts! This Python script integrates with the Chaturbate Events API to process tip events, controlling an LED strip to display visual alerts.

## Key Features

- **Event Polling:** Real-time polling of the Chaturbate Events API for the latest tip events.
- **Dynamic Tip Processing:** Responds to tipping events with customizable LED animations.
- **Advanced LED Control:** Manages LED strips for a variety of animations and colors.
- **Color-Specific Alerts:** Set up alerts that react to specific user messages with designated colors.
- **User-Friendly Customization:** Easy-to-configure settings for alert types, duration, LED brightness, and more.

## Getting Started

### Prerequisites

- Python 3.x: [Download Python](https://www.python.org/downloads/)
- Libraries: `aiohttp`, `adafruit_led_animation`, `dotenv` , etc. (See `requirements.txt`)

### Installation

1. **Clone the Repository:** 
   ```bash
   git clone https://github.com/MountainGod2/stripalerts.git
   ```
2. **Install Dependencies:**
   Navigate to the cloned directory and run:
   ```bash
   pip install -r requirements.txt
   ```

### Configuration

- Create a `.env` file in the root directory with the following variables:
   ```
   USERNAME=YourChaturbateAPIUsername
   TOKEN=YourChaturbateAPIToken
   BASE_URL=https://events.testbed.cb.dev/events/
   LED_PIN=D18
   LED_COUNT=100
   LED_BRIGHTNESS=0.1
   COLOR_ALERT_TOKENS=35
   COLOR_DURATION=600
   ALERT_DURATION=3
   ```

### Customizing LED Settings

Modify the settings in the `.env` file to match your connected LED strip and user preferences.

### Usage

1. Run the script:
   ```bash
   python main.py
   ```
2. Observe the LED strip responding to Chaturbate events.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Chaturbate Events API](https://chaturbate.com/) for providing the event data.
- [Adafruit](https://www.adafruit.com/) for the fantastic LED animation library.
- [ChatGPT](https://chat.openai.com/) for creating 90% of this program (README.md included), and for letting me pretend I know Python.
