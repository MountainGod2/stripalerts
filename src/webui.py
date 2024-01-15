from nicegui import app, ui
import os
import asyncio
from dotenv import dotenv_values, load_dotenv  # Import load_dotenv

# Importing classes from your application
from stripalerts_app import StripAlertsApp

# Load environment variables from .env file
load_dotenv()


def get_env_var(var_name, default=""):
    """Get environment variable with fallback."""
    return os.getenv(var_name, default)


def set_env_var(var_name, value):
    """Write environment variable to .env file."""
    # Load current .env file into a dictionary
    env_vars = dotenv_values(".env")
    # Update the dictionary with the new value
    env_vars[var_name] = value
    # Write the updated dictionary back to the .env file
    with open(".env", "w") as env_file:
        for key, val in env_vars.items():
            env_file.write(f"{key}={val}\n")

    # Optionally, update the environment variable in the current session
    os.environ[var_name] = value
    print(f"Set {var_name} to {value}")


def setup_configuration_stepper(storage):
    """Create a stepper for setting up configuration."""
    with ui.stepper().props("vertical").classes("w-full q-pa-md").style(
        "max-width: 350px; margin: 0 auto; background-color: #202c39;"
    ) as stepper:
        storage.update(setup_complete=False)
        storage.update(app_running=False)
        storage.update(show_stepper=True)
        stepper.bind_visibility_from(storage, "show_stepper")
        # API configuration step
        with ui.step("API Configuration"):
            ui.input(
                "API Username",
                value=get_env_var("USERNAME"),
                on_change=lambda e: set_env_var("USERNAME", e.value),
            ).classes("w-full q-mb-md")
            ui.input(
                "API Token",
                value=get_env_var("TOKEN"),
                on_change=lambda e: set_env_var("TOKEN", e.value),
            ).classes("w-full q-mb-md")
            with ui.stepper_navigation().classes("center-container"):
                ui.button("Next", on_click=stepper.next).props("color=primary")

        # LED configuration step
        with ui.step("LED Configuration"):
            # LED pin input
            ui.input(
                "LED Pin",
                value=get_env_var("LED_PIN"),
                on_change=lambda e: set_env_var("LED_PIN", e.value),
            ).classes("w-full q-mb-md")

            # LED count input
            ui.number(
                "LED Count",
                value=int(get_env_var("LED_COUNT", "5")),
                on_change=lambda e: set_env_var("LED_COUNT", str(int(e.value))),
            ).classes("w-full q-mb-md")

            # Label for the slider
            ui.label("LED Brightness")

            # Slider element
            ui.slider(
                value=float(get_env_var("LED_BRIGHTNESS", "0.1")),
                min=0.1,
                max=1,
                step=0.01,
                on_change=lambda e: set_env_var("LED_BRIGHTNESS", str(e.value)),
            ).classes("w-full q-mb-md")

            # Navigation buttons (centered)
            with ui.stepper_navigation().classes("center-container"):
                ui.button("Back", on_click=stepper.previous).props("flat")
                ui.button("Next", on_click=stepper.next).props("color=primary")

        # Alerts configuration step
        with ui.step("Alerts Configuration"):
            # Tokens for color alert input
            ui.number(
                "Tokens for Color Alert",
                value=int(get_env_var("TOKENS_FOR_COLOR_ALERT", "35")),
                on_change=lambda e: set_env_var("LED_COUNT", str(int(e.value))),
            ).classes("w-full q-mb-md")

            # Alert duration input
            ui.number(
                "Alert duration (seconds)",
                value=int(get_env_var("ALERT_DURATION", "3")),
                on_change=lambda e: set_env_var("ALERT_DURATION", str(int(e.value))),
            ).classes("w-full q-mb-md")

            # Color duration input
            ui.number(
                "User Color Duration (seconds)",
                value=int(get_env_var("COLOR_DURATION", "600")),
                on_change=lambda e: set_env_var("COLOR_DURATION", str(int(e.value))),
            ).classes("w-full q-mb-md")

            # Navigation buttons (centered)
            with ui.stepper_navigation().classes("center-container"):
                ui.button("Back", on_click=stepper.previous).props("flat")
                ui.button("Next", on_click=stepper.next).props("color=primary")

        # Setup stepper complete
        with ui.step("Setup Complete"):
            # Welcome message centered
            username = str(get_env_var("USERNAME"))
            ui.label().bind_text_from(
                target_object=username,
                backward=lambda username: f"Welcome, {username}!",
            ).style("margin: 0 auto; text-align: center;").classes("font-bold")

            # Complete setup button centered
            with ui.stepper_navigation().style("margin: 0 auto;"):
                ui.button(
                    "Complete Setup",
                    on_click=lambda: [
                        storage.update(setup_complete=True),
                        storage.update(show_stepper=False),
                    ],
                ).props("color=primary")


# Helper functions for starting and stopping the service
def start_service_logic(app_instance, storage):
    asyncio.create_task(app_instance.start_service())
    storage.update(app_running=True)


def stop_service_logic(app_instance, storage):
    asyncio.create_task(app_instance.stop_service())
    storage.update(app_running=False)


def setup_control_card(storage):
    """Create a control card for starting and stopping the application."""
    with ui.card().bind_visibility_from(storage, "setup_complete").classes("w-full q-pa-md").style(
        "max-width: 350px; margin: 0 auto; background-color: #202c39; color: white;"
    ):
        app_instance = StripAlertsApp()
        ui.button(
            "Start StripAlerts", on_click=lambda: start_service_logic(app_instance, storage)
        ).style("margin: 0 auto;").props("color=primary")
        ui.button(
            "Stop StripAlerts", on_click=lambda: stop_service_logic(app_instance, storage)
        ).style("margin: 0 auto;").bind_visibility_from(storage, "app_running").props("flat")


def setup_log_display(storage):
    """Display real-time logs."""
    with ui.card().bind_visibility_from(storage, "app_running").classes("w-full q-pa-md").style(
        "max-width: 350px; margin: 0 auto; background-color: #202c39; color: white;"
    ):
        log_content = ui.label("").classes("log-display q-mb-md font-bold")

        def update():
            asyncio.create_task(update_log_content(log_content))

        # Set up a timer to call the update function periodically
        ui.timer(interval=5, callback=update, active=True)


async def update_log_content(log_label):
    """Update log content to display only the latest 'INFO' level message."""
    try:
        with open("app.log", "r") as log_file:
            # Read all lines from the log file
            log_lines = log_file.readlines()

        # Filter lines that contain 'INFO' and extract the message part
        info_messages = [
            line.split(" - INFO - ")[-1].strip() for line in log_lines if " - INFO - " in line
        ]

        # Get the latest message, if any
        latest_message = info_messages[-1] if info_messages else "Waiting for startup..."

        # Update the text of the log_label UI element with the latest message
        log_label.set_text(latest_message)

    except FileNotFoundError:
        log_label.set_text("Log file not found.")

@ui.page("/")
def index():
    """Run the web UI."""
    storage = app.storage.user
    ui.colors(primary="#68b5f0", secondary="#202c39", accent="#f47321")
    ui.query("body").style(
        "background-color: #121212; color: #FFFFFF;"
    )  # Dark background with light text

    # Setting up the UI elements
    with ui.card().classes("w-full q-pa-md").style(
        "max-width: 400px; margin: 0 auto; background-color: #202c39; color: white; min-height: 680px;"
    ):
        # Container for centering the image
        with ui.element().classes("flex flex-column items-center justify-center").style("margin-top: 50px; margin: 0 auto; margin-bottom: 0px;"):
            ui.image(
                source="https://github.com/MountainGod2/stripalerts/assets/88257202/92fe191c-ad63-4181-93e3-98ba5e2e9eb0"
            ).style(
                "width: 200px; height: auto; margin: 0 auto;"
            )
        setup_configuration_stepper(storage)
        setup_control_card(storage)
        setup_log_display(storage)

# Run the NiceGUI server
ui.run(title="StripAlerts", port=8080, reload=False, storage_secret="stripalerts", dark=True)
