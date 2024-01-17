import logging
import os
import asyncio
from dotenv import dotenv_values, load_dotenv
from nicegui import app, ui
from main import StripAlertsApp

# Load environment variables from .env file
load_dotenv()

# Define theme styles
THEMES = {
    "light": {
        "background-color": "#f5f5f5",
        "color": "#333333",
        "button-background": "#ff6b81",
        "button-color": "#ffffff",
        "card-background": "#ffffff",
        "card-color": "#333333",
        "box-shadow": "0px 4px 8px rgba(0, 0, 0, 0.2)",
        "accent-color": "#ff4f63",  # Define an accent color
    },
    "dark": {
        "background-color": "#333333",
        "color": "#ffffff",
        "button-background": "#ff6b81",
        "button-color": "#ffffff",
        "card-background": "#444444",
        "card-color": "#ffffff",
        "box-shadow": "0px 4px 8px rgba(255, 255, 255, 0.2)",
        "accent-color": "#ff4f63",  # Define an accent color
    },
}
current_theme = "light"

# Common styling constants
COMMON_STYLE = """
    font-family: 'Arial', sans-serif;
    max-width: 350px;
    margin: 0 auto;
    border-radius: 8px;
    transition: background-color 0.3s ease, transform 0.2s ease;
"""

BUTTON_STYLE = """
    background-color: #ff6b81;
    color: #ffffff;
    border: none;
    padding: 10px 20px;
    border-radius: 25px;
    transition: background-color 0.3s ease, transform 0.2s ease;
"""

CENTER_STYLE = "display: flex; justify-content: center; align-items: center;"
LABEL_STYLE = "margin: 0 auto; text-align: center; margin-top: 20px; font-size: 24px; color: #ff6b81;"
HEADER_IMAGE_STYLE = "width: 200px; height: auto; margin: 0 auto;"
HEADER_IMAGE_PATH = "./static/header.png"


def show_notification(message, type="info"):
    """
    Show a notification to the user.

    Args:
        message (str): The message to display in the notification.
        type (str): The type of notification ('info', 'success', 'warning', 'error').
    """
    ui.notify(message, type=type)


def get_env_var(var_name, default=""):
    """
    Get environment variable with a fallback value if not found.

    Args:
        var_name (str): The name of the environment variable to retrieve.
        default (str): The default value to return if the variable is not found.

    Returns:
        str: The value of the environment variable or the default value if not found.
    """
    return os.getenv(var_name, default)


def set_env_var(var_name, value):
    """
    Write an environment variable to the .env file and update the environment.

    Args:
        var_name (str): The name of the environment variable to set.
        value (str): The value to set for the environment variable.
    """
    env_vars = dotenv_values(".env")
    env_vars[var_name] = value
    with open(".env", "w") as env_file:
        for key, val in env_vars.items():
            env_file.write(f"{key}={val}\n")
    os.environ[var_name] = value
    # print(f"Set {var_name} to {value}") # Uncomment for debugging


class SettingsValidator:
    def __init__(self):
        self.settings_validated = False

    def validate_settings(self, storage):
        """
        Validate the settings for the StripAlerts app.
        """
        self.settings_validated = True
        storage.update(settings_validated=True)


class ControlFunctions:
    def __init__(self):
        self.app_instance = None

    async def start_service_logic(self, storage):
        """
        Start the StripAlerts service logic in a separate thread if not already running.

        Args:
            storage (dict): The storage dictionary for NiceGUI.

        Note:
            This method checks if the app is already running before starting it.
        """
        if not app.storage.user.get("app_running"):
            storage.update(app_running=True)
            self.app_instance = StripAlertsApp()
            self.app_instance.start_service_logic(self.app_instance, storage)
            show_notification("StripAlerts started", type="positive")
            await self.app_instance.shutdown_event.wait()
        else:
            logging.info("App is already running.")

    def stop_service_logic(self, storage):
        """
        Stop the StripAlerts service logic if it is running.

        Args:
            storage (dict): The storage dictionary for NiceGUI.
        """
        if self.app_instance:
            asyncio.create_task(self.app_instance.stop_service())
            show_notification("StripAlerts stopped", type="negative")
            storage.update(app_running=False)


def create_input(label, var_name, default=""):
    """
    Create an input element with a label and bind it to an environment variable.

    Args:
        label (str): The label for the input element.
        var_name (str): The name of the environment variable to bind.
        default (str): The default value for the input element.

    Returns:
        nicegui.ui.Input: The created input element.
    """
    return ui.input(
        label,
        value=get_env_var(var_name, default),
        on_change=lambda e: set_env_var(var_name, e.value),
    ).classes("w-full q-mb-md")


def create_number(label, var_name, default=0):
    """
    Create a number input element with a label and bind it to an environment variable.

    Args:
        label (str): The label for the number input element.
        var_name (str): The name of the environment variable to bind.
        default (int): The default value for the number input element.

    Returns:
        nicegui.ui.Number: The created number input element.
    """
    return ui.number(
        label,
        value=int(get_env_var(var_name, str(default))),
        on_change=lambda e: set_env_var(var_name, str(int(e.value))),
    ).classes("w-full q-mb-md")


def create_slider(label, var_name, default=0.1):
    """
    Create a slider element with a label and bind it to an environment variable.

    Args:
        label (str): The label for the slider element.
        var_name (str): The name of the environment variable to bind.
        default (float): The default value for the slider element.

    Returns:
        tuple: A tuple containing the label and slider elements.
    """
    slider_label = ui.label(label)
    slider = ui.slider(
        value=float(get_env_var(var_name, str(default))),
        min=0.1,
        max=1,
        step=0.01,
        on_change=lambda e: set_env_var(var_name, str(e.value)),
    ).classes("w-full q-mb-md")
    return slider_label, slider


def setup_configuration_stepper(storage):
    """
    Set up a configuration stepper with steps for API, LED, and Alerts configuration.

    Args:
        storage (dict): The storage dictionary for NiceGUI.
    """
    with ui.stepper().props("vertical").classes("w-full q-pa-md").style(
        COMMON_STYLE
    ) as stepper:
        storage.update(setup_complete=False)
        storage.update(app_running=False)
        stepper.bind_visibility_from(storage, "setup_complete", value=False)

        with ui.step("Configure API Credentials"):
            create_input("API Username", "USERNAME")
            create_input("API Token", "TOKEN")
            with ui.stepper_navigation().classes("center-container"):
                ui.button("Next", on_click=stepper.next).props("color=primary")

        with ui.step("Configure LED Strip"):
            create_input("LED Pin", "LED_PIN")
            create_number("LED Count", "LED_COUNT", 5)
            create_slider("LED Brightness", "LED_BRIGHTNESS", 0.1)
            with ui.stepper_navigation().classes("center-container"):
                ui.button("Back", on_click=stepper.previous).props("flat")
                ui.button("Next", on_click=stepper.next).props("color=primary")

        with ui.step("Configure Alert Settings"):
            create_number("Tokens for Color Alert", "TOKENS_FOR_COLOR_ALERT", 35)
            create_number("Alert duration (seconds)", "ALERT_DURATION", 3)
            create_number("User Color Duration (seconds)", "COLOR_DURATION", 600)
            with ui.stepper_navigation().classes("center-container"):
                ui.button("Back", on_click=stepper.previous).props("flat")
                ui.button(
                    "Next",
                    on_click=stepper.next,  # Add validation logic
                )
        with ui.step("Start StripAlerts"):
            ui.label("Settings validated.")
            with ui.stepper_navigation().classes("center-container"):
                ui.button(
                    "Complete Setup",
                    on_click=lambda: [
                        storage.update(setup_complete=True),
                        show_notification(
                            "Setup completed successfully!", type="positive"
                        ),
                    ],
                )


def setup_control_card(storage):
    """
    Set up a control card with buttons to start and stop the StripAlerts service.

    Args:
        storage (dict): The storage dictionary for NiceGUI.
    """
    with ui.card().bind_visibility_from(storage, "setup_complete").classes(
        "w-full q-pa-md"
    ).style(COMMON_STYLE).style(CENTER_STYLE):
        control_functions = ControlFunctions()
        username = str(get_env_var("USERNAME"))
        ui.label(f"Welcome, {username}!").style(LABEL_STYLE)

        # Stack the buttons vertically
        ui.button(
            "Start StripAlerts",
            on_click=lambda: control_functions.start_service_logic(storage),
        ).style(f"{BUTTON_STYLE} margin-bottom: 10px;")  # Added margin-bottom
        ui.button(
            "Stop StripAlerts",
            on_click=lambda: control_functions.stop_service_logic(storage),
        ).style(f"{BUTTON_STYLE} margin-bottom: 10px;").bind_visibility_from(
            storage, "app_running"
        )


def setup_log_display(storage):
    """
    Set up a log display card to show the latest log message.

    Args:
        storage (dict): The storage dictionary for NiceGUI.
    """
    with ui.card().bind_visibility_from(storage, "setup_complete").classes(
        "w-full q-pa-md"
    ).style(COMMON_STYLE):
        log_content = ui.label("").classes(
            "log-display q-mb-md font-bold margin-top: 40px;"
        )

        def update():
            asyncio.create_task(update_log_content(log_content))

        ui.timer(interval=5, callback=update, active=True)


async def update_log_content(log_label):
    """
    Update the log content with the latest log message.

    Args:
        log_label (nicegui.ui.Label): The label element to update.
    """
    try:
        with open("app.log", "r") as log_file:
            log_lines = log_file.readlines()

        info_messages = [
            line.split(" - INFO - ")[-1].strip()
            for line in log_lines
            if " - INFO - " in line
        ]

        latest_message = info_messages[-1] if info_messages else "Waiting for startup..."

        log_label.set_text(latest_message)

    except FileNotFoundError:
        log_label.set_text("Log file not found.")


def apply_theme():
    """Apply the current theme to the UI elements."""
    theme = THEMES[current_theme]
    ui.query("body").style(
        f"background-color: {theme['background-color']}; color: {theme['color']};"
    )
    ui.query(".card").style(
        f"background-color: {theme['card-background']}; color: {theme['card-color']}; box-shadow: {theme['box-shadow']};"
    )
    ui.query(".button").style(
        f"background-color: {theme['button-background']}; color: {theme['button-color']};"
    )


def toggle_dark_mode():
    """Toggle between light and dark mode."""
    global current_theme
    current_theme = "dark" if current_theme == "light" else "light"
    apply_theme()


@ui.page("/")
def index():
    storage = app.storage.user
    apply_theme()  # Apply the current theme

    with ui.element().classes("flex flex-column items-center justify-center").style(
        "margin-top: 50px; margin: 0 auto; margin-bottom: 0px;"
    ):
        ui.image(source="./static/header.png").style(
            "width: 200px; height: auto; margin: 0 auto;"
        )  # Header image path consolidated here

    with ui.card().classes("w-full q-pa-md").style(
        "max-width: 500px; margin: 0 auto; background-color: #ffffff; color: #333333; border-radius: 8px;"
    ):
        ui.colors(
            primary="#ff6b81",
            secondary="#ffffff",
            accent=THEMES[current_theme]["accent-color"],
        )  # Use the accent color
        ui.query("body").style(COMMON_STYLE)

        setup_configuration_stepper(storage)
        setup_control_card(storage)
        setup_log_display(storage)

    with ui.row().classes("w-full q-mb-md"):
        ui.switch("Toggle Dark Mode", on_change=lambda e: toggle_dark_mode()).style(
            "display: flex; justify-content: center; align-items: center;"
        )


# Run the NiceGUI app
ui.run(
    title="StripAlerts",
    port=8080,
    reload=False,
    storage_secret="stripalerts",
    show_welcome_message=False,
)
