"""
This module contains the web UI for the StripAlerts setup.

The web UI is built using the NiceGUI library.
"""
import asyncio
import platform
import shlex
import socket

import board
import requests
from nicegui import app, ui

BUFFER_SIZE = 4096  # Buffer size for reading process output in bytes


def get_ip() -> str:
    """
    Returns the IP address of the device.

    Returns:
        str: IP address of the device.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.settimeout(0)
            s.connect(("10.254.254.254", 1))  # This IP is unreachable, but packets are not sent
            return s.getsockname()[0]
    except socket.error:
        return "127.0.0.1"


class CommandRunner:
    """
    Class to run commands asynchronously.

    Attributes:
        result (ui.markdown): Markdown component to display the process output.
        process (asyncio.subprocess.Process): Process instance.
    """

    def __init__(self):
        self.result = ui.markdown()
        self.process = None

    async def start_main_script(self):
        """Starts the main script asynchronously."""
        if self.process is None or self.process.returncode is not None:
            self.process = await self.create_subprocess("sudo python3 src/main.py")
            asyncio.create_task(self.read_process_output(self.process))

    async def stop_main_script(self):
        """Stops the main script asynchronously."""
        if self.process and self.process.returncode is None:
            self.process.terminate()
            await self.process.wait()

    async def create_subprocess(self, command: str):
        """Creates a subprocess asynchronously."""
        return await asyncio.create_subprocess_exec(
            *shlex.split(command),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )

    async def read_process_output(self, process):
        """Reads the process output asynchronously."""
        while data := await process.stdout.read(BUFFER_SIZE):
            self.result.content += data.decode()


class Validator:
    """
    Class to validate the setup settings.

    Attributes:
        storage (dict): Storage instance.
    """

    def __init__(self, storage):
        self.storage = storage

    def set_storage_item(self, key: str, value: bool) -> None:
        """
        Sets a storage item.

        Args:
            key (str): Key of the item to set.
            value (bool): Value to set.
        """
        self.storage[key] = value

    def validate_api_settings(self, formatter) -> None:
        """
        Validates the API settings.

        Args:
            formatter (Formatter): Formatter instance.
        """
        url = self.storage.get("token_url")
        if url:
            try:
                response = requests.get(url, timeout=5)
                self.set_storage_item("api_settings_validated", response.status_code == 200)
                if response.status_code == 200:
                    formatter.extract_credentials()
            except requests.RequestException:
                self.set_storage_item("api_settings_validated", False)
        else:
            self.set_storage_item("api_settings_validated", False)

    def validate_led_settings(self) -> None:
        """Validates the LED settings."""
        pin, count = self.storage.get("led_pin"), self.storage.get("led_count")
        is_pin_valid = pin in board.__dict__
        is_count_valid = count.isdigit() if count else False
        self.set_storage_item("led_settings_validated", is_pin_valid and is_count_valid)

    def validate_alert_settings(self) -> None:
        """Validates the alert settings."""
        color_alert_tokens, color_duration, alert_duration = (
            self.storage.get("color_alert_tokens"),
            self.storage.get("color_duration"),
            self.storage.get("alert_duration"),
        )
        is_tokens_valid = color_alert_tokens.isdigit() if color_alert_tokens else False
        is_color_duration_valid = color_duration.isdigit() if color_duration else False
        is_alert_duration_valid = alert_duration.isdigit() if alert_duration else False
        self.set_storage_item(
            "alert_settings_validated",
            is_tokens_valid and is_color_duration_valid and is_alert_duration_valid,
        )

    def verify_settings(self, stepper, setting_key: str, success_message: str) -> None:
        """
        Verifies the settings.

        Args:
            stepper (ui.stepper): Stepper instance.
            setting_key (str): Key of the setting to verify.
            success_message (str): Success message to display.
        """
        if self.storage.get(setting_key):
            stepper.next()
            ui.notify(success_message, type="positive")

    def verify_setup_is_complete(self, stepper, formatter) -> None:
        """
        Verifies that the setup is complete.

        Args:
            stepper (ui.stepper): Stepper instance.
            formatter (Formatter): Formatter instance.
        """
        if self.storage.get("api_settings_validated") and self.storage.get(
            "led_settings_validated"
        ):
            ui.notify("Setup complete!", type="positive")
            self.set_storage_item("setup_complete", True)
            stepper.value = "Set API credentials"
            formatter.write_credentials_to_env()
        else:
            self.set_storage_item("setup_complete", False)


class Formatter:
    """
    Class to format the setup settings.

    Attributes:
        storage (dict): Storage instance.
    """

    def __init__(self, storage):
        self.storage = storage

    def extract_credentials(self):
        """Extracts the credentials from the token URL."""
        url = self.storage.get("token_url")
        parts = url.split("/")
        username, token = parts[4], parts[5]
        base_url = url.replace(f"{username}/{token}/", "")

        for key, value in {
            "username": username,
            "token": token,
            "base_url": base_url,
        }.items():
            self.storage[key] = value

    def write_credentials_to_env(self):
        """Writes the credentials to the .env file."""
        env_file_path = ".env"
        with open(env_file_path, "w", encoding="utf-8") as env_file:
            for key in [
                "username",
                "token",
                "base_url",
                "led_pin",
                "led_count",
                "led_brightness",
                "color_alert_tokens",
                "color_duration",
                "alert_duration",
            ]:
                value = str(self.storage.get(key))
                env_file.write(f"{key.upper()}={value}\n")


def initialize_storage(storage):
    """
    Initializes the storage.

    Args:
        storage (dict): Storage instance.
    """
    default_values = {
        "setup_complete": False,
        "api_settings_validated": False,
        "led_settings_validated": True,
        "alert_settings_validated": True,
    }

    for key, value in default_values.items():
        if key not in storage:
            storage[key] = value


@ui.page("/")
def index():
    """Creates the web UI."""
    storage = app.storage.user
    initialize_storage(storage)

    validator = Validator(storage)
    formatter = Formatter(storage)

    create_setup_stepper(storage, validator, formatter)
    create_control_card(storage)


def create_setup_stepper(storage, validator, formatter):
    """Creates the stepper."""
    with ui.stepper().props("vertical").style(
        "max-width: 600px; margin: 0 auto;"
    ).bind_visibility_from(
        storage, "setup_complete", backward=lambda complete: not complete
    ) as stepper:
        create_api_credentials_step(stepper, storage, validator, formatter)
        create_led_setup_step(stepper, storage, validator)
        create_alert_settings_step(stepper, storage, validator)
        create_finalize_setup_step(stepper, validator, formatter)
    return stepper


def create_api_credentials_step(stepper, storage, validator, formatter):
    """Creates the API credentials step."""
    with ui.step("Set API credentials"):
        ui.input(
            "Token URL",
            placeholder="https://events.testbed.cb.dev/events/username/token/",
            on_change=lambda: validator.validate_api_settings(formatter),
            validation={
                "Invalid URL": lambda value: value.startswith(
                    "https://events.testbed.cb.dev/events/"
                )
            },
        ).bind_value_to(storage, "token_url")

        ui.button(
            "Next",
            on_click=lambda: validator.verify_settings(
                stepper, "api_settings_validated", "API settings validated!"
            ),
        ).bind_enabled_from(storage, "api_settings_validated")


def create_led_setup_step(stepper, storage, validator):
    """Creates the LED setup step."""
    with ui.step("Setup LED strip"):
        ui.input(
            "LED Pin",
            placeholder="D18",
            value="D18",
            on_change=validator.validate_led_settings,
        ).bind_value_to(storage, "led_pin")
        ui.input(
            "LED Count",
            placeholder="30",
            value="100",
            on_change=validator.validate_led_settings,
        ).bind_value_to(storage, "led_count")

        slider = ui.slider(min=0.1, max=1.0, value=0.1, step=0.1).bind_value_to(
            storage, "led_brightness"
        )
        ui.label().bind_text_from(slider, "value")

        ui.button(
            "Next",
            on_click=lambda: validator.verify_settings(
                stepper, "led_settings_validated", "LED settings validated!"
            ),
        ).bind_enabled_from(storage, "led_settings_validated")
        ui.button("Back", on_click=stepper.previous()).props("flat")


def create_alert_settings_step(stepper, storage, validator):
    """Creates the alert settings step."""
    with ui.step("Set up alert settings"):
        ui.input(
            "Color Alert Tokens",
            placeholder="35",
            value="35",
            on_change=validator.validate_alert_settings,
        ).bind_value_to(storage, "color_alert_tokens")
        ui.input(
            "Color Duration",
            placeholder="600",
            value="600",
            on_change=validator.validate_alert_settings,
        ).bind_value_to(storage, "color_duration")
        ui.input(
            "Alert Duration",
            placeholder="3",
            value="3",
            on_change=validator.validate_alert_settings,
        ).bind_value_to(storage, "alert_duration")

        ui.button(
            "Next",
            on_click=lambda: validator.verify_settings(
                stepper, "alert_settings_validated", "Alert settings validated!"
            ),
        ).bind_enabled_from(storage, "alert_settings_validated")
        ui.button("Back", on_click=stepper.previous()).props("flat")


def create_finalize_setup_step(stepper, validator, formatter):
    """Creates the finalize setup step."""
    with ui.step("Finalize setup"):
        ui.button(
            "Finish",
            on_click=lambda: validator.verify_setup_is_complete(stepper, formatter),
        )
        ui.button("Back", on_click=stepper.previous()).props("flat")


def create_control_card(storage):
    """Creates the control card."""
    with ui.card().bind_visibility_from(storage, "setup_complete").props("vertical").style(
        "max-width: 600px; margin: 0 auto;"
    ):
        ui.label().bind_text_from(
            storage, "username", backward=lambda username: f"Welcome, {username}!"
        ).style("margin: 0 auto;").tailwind.font_weight("bold")
        runner = CommandRunner()
        ui.button("Start StripAlerts", on_click=runner.start_main_script)
        ui.button("Stop StripAlerts", on_click=runner.stop_main_script)
        ui.button(
            "Return to setup",
            on_click=lambda: storage.set("setup_complete", False),
        ).style("margin: 0 auto;").props("flat")


# Run the app with necessary configurations
ui.run(
    host=get_ip(),
    port=8080,
    reload=platform.system() != "Windows",
    storage_secret="stripalerts",
)
