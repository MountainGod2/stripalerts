# frontend.py
from nicegui import ui
from strip_alerts import StripAlertsApp


class StripAlertsController:
    def __init__(self):
        self.app = None
        self.is_running = False

    async def start_alerts_service(self):
        """Starts the service."""
        if not self.app:
            self.app = StripAlertsApp()
            self.is_running = True
            await self.app.start_service()

    async def stop_alerts_service(self):
        """Stops the service."""
        if self.app:
            await self.app.stop_service()
            self.is_running = False
            self.app = None

    @ui.refreshable
    def is_running(self):
        """Check if the service is running."""
        return self.is_running


ui.colors(primary="#0c6a93")
ui.colors(secondary="#f47321")
controller = StripAlertsController()
button_style = "padding: 10px 20px; border: none; border-radius: 20px; cursor: pointer;"


def control_elements():
    """Create control elements."""
    with ui.row().style("margin: auto;"):
        start_button = (
            ui.button(
                text="Start Service",
                on_click=controller.start_alerts_service,
                color="primary",
            )
            .style(button_style)
            .bind_visibility_from(
                target_object=controller,
                target_name="is_running",
                backward=lambda x: not x,
            )
        )
        stop_button = (
            ui.button(text="Stop Service", on_click=controller.stop_alerts_service)
            .style(button_style)
            .bind_visibility_from(
                target_object=controller,
                target_name="is_running",
                backward=lambda x: x,
            )
        )


@ui.page("/")
async def index():
    """Run the GUI."""
    with ui.element().style(
        add="max-width: 600px; margin: auto; padding-top: 20px;"
    ) as root_element:
        with ui.row():
            title = ui.label("StripAlerts").style(
                "font-size: 24px; font-weight: bold; margin:auto; margin-bottom: 20px;"
            )
        control_elements()


ui.run(reload=False)
