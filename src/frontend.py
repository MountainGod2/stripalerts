from nicegui import ui, app
from strip_alerts import StripAlertsApp
import logging
import json
from log_formatter import LogAligner
import asyncio

button_style = "border: none; border-radius: 20px; cursor: pointer; margin: auto; margin-top: 20px; font-size: 16px;"


def setup_logging():
    """Setup logging configuration from JSON file."""
    with open("logging_config.json", "r", encoding="utf-8") as config_file:
        config = json.load(config_file)
        logging.config.dictConfig(config)


setup_logging()


class StripAlertsController:
    def __init__(self):
        self.app = None
        self.is_running = False

    async def start_strip_alerts(self):
        """Starts the service."""
        if not self.app:
            self.app = StripAlertsApp()
            self.is_running = True
            ui.notify("Service started", type="positive")
            await self.app.start_service()
            ui.notify("Service stopped", type="negative")

    async def stop_strip_alerts(self):
        """Stops the service."""
        if self.app:
            await self.app.stop_service()
            self.is_running = False
            self.app = None

    @ui.refreshable
    def is_running(self):
        """Check if the service is running."""
        return self.is_running


def control_elements():
    """Create control elements."""
    controller = StripAlertsController()

    with ui.row().style(
        "margin: auto; margin-top: 20px; justify-content: center; align-items: center;"
    ):
        ui.button(
            text="Stop Service",
            on_click=controller.stop_strip_alerts,
            color="secondary",
        ).style(
            add=button_style, replace="font-size: 20px; border-radius: 40px;"
        ).bind_visibility_from(
            target_object=controller,
            target_name="is_running",
            backward=lambda x: x,
        )

        ui.button(
            text="Start Service",
            on_click=controller.start_strip_alerts,
            color="primary",
        ).style(
            add=button_style, replace="font-size: 20px; border-radius: 40px;"
        ).bind_visibility_from(
            target_object=controller,
            target_name="is_running",
            backward=lambda x: not x,
        )


@ui.page("/settings")
async def settings_page():
    ui.label("Pass")


@ui.page("/")
async def index():
    """Run the GUI."""

    ui.colors(primary="#0c6a93")
    ui.colors(secondary="#f47321")
    ui.query("body").style("background-color: #17202a;")

    with ui.header(elevated=True).style("background-color: #0c6a93;").classes(
        "items-center justify-between"
    ):
        ui.image(source="./static/header.png").style("width: 200px; height: auto;")
        with ui.row().classes("items-center justify-end"):
            ui.button(
                icon="power_settings_new",
                on_click=app.shutdown,
                color="secondary",
            )
            with ui.expansion(icon="menu"):
                ui.link("Settings", "/settings")

    with ui.element().style(
        "max-width: 1280px; min-width: 600px; margin: auto; padding-top: 20px; background-color: transparent"
    ):
        control_elements()


async def align_logs():
    """Retrieve log contents."""
    try:
        await LogAligner(delete_original=True).align_log_entries()
    except FileNotFoundError:
        logging.error("Log file not found.")


try:
    ui.run(
        title="StripAlerts",
        reload=False,
        favicon="./static/favicon.ico",
    )
except KeyboardInterrupt:
    pass
finally:
    asyncio.run(align_logs())
