
# StripAlerts - LED Alerts for Chaturbate Events

![StripAlerts](https://github.com/MountainGod2/stripalerts/assets/88257202/6237796c-c9ec-4da8-8411-5bb8e18e95e8)

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
- Libraries: `aiohttp`, `neopixel`, `board`, `adafruit_led_animation`, `dotenv`. Installation instructions are provided in the installation section.

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

- Create a `.env` file in the root directory.
- Add the following variables:
   ```
   USERNAME=YourChaturbateAPIUsername
   TOKEN=YourChaturbateAPIToken
   ```

## Customizing LED Settings

Modify `LED_COUNT`, `LED_PIN` in `src/constants.py` to match your connected LED strip.


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
- [ChatGPT](https://chat.openai.com/) for creating 90% of this program (README.md included), and for letting me cosplay as a python programmer.
