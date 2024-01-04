"""Web UI for the Chaturbate Events API LED Alert."""

import requests
from nicegui import app, ui

ui.dark_mode(True)


token_url = ""
color_alert_tokens = 35
color_duration = 600
alert_duration = 3
led_pin = "D18"
led_count = 100
led_brightness = 0.1


def validate_token_url():
    """Validate the token URL."""
    # if not token_url.startswith("https://eventsapi.chaturbate.com/events/"):
    if not token_url.startswith("https://events.testbed.cb.dev/events/"):
        ui.notify(
            "Invalid token URL format."
            " Token URL should be in the format: https://eventsapi.chaturbate.com/events/:username/:token/",
            type="negative",
        )
        return
    if not requests.get(token_url).ok:
        ui.notify(
            "Token URL not reachable."
            " Ensure you have copied the full URL and that the token is valid",
            type="negative",
        )
        return
    ui.notify("Valid token URL", type="positive")
    stepper.next()


with ui.stepper().props("vertical").classes("w-300") as stepper:
    with ui.step("API Credentials"):
        ui.label("To use the Events API, you need to create an API token.")
        ui.label("You can create a token here:")
        ui.link(
            "https://chaturbate.com/statsapi/authtoken/",
            "https://chaturbate.com/statsapi/authtoken/",
            new_tab=True,
        )
        ui.label("Make sure to select Events API scope").tailwind.font_weight("extrabold")
        ui.label("Copy the token URL and paste it below.")
        ui.input(
            "Token URL",
            placeholder="https://eventsapi.chaturbate.com/events/:username/:token/",
            # validation={
            #     "Invalid URL": lambda url: url.startswith(
            #         "https://eventsapi.chaturbate.com/events/"
            #     ),
            #     "URL not reachable": lambda url: requests.get(url).ok,
            # },
        ).bind_value(globals(), "token_url")
        with ui.stepper_navigation():
            # Perform validation on click
            ui.button("Next", on_click=validate_token_url)
    with ui.step("Alert Settings"):
        ui.label("Set your desired alert settings below:")
        ui.number(
            label="Color change price",
            value=35,
            min=1,
            precision=0,
            step=5,
            suffix="tokens",
        ).bind_value(globals(), "color_alert_tokens")
        ui.number(
            label="Color duration",
            value=600,
            min=1,
            precision=0,
            step=60,
            suffix="seconds",
        ).bind_value(globals(), "color_duration")
        ui.number(
            label="Alert duration",
            value=3,
            min=1,
            precision=0,
            step=1,
            suffix="seconds",
        ).bind_value(globals(), "alert_duration")

        with ui.stepper_navigation():
            ui.button("Next", on_click=stepper.next)
            ui.button("Back", on_click=stepper.previous).props("flat")
    with ui.step("LED Settings"):
        ui.label("Set your LED settings below:")
        ui.input("LED Pin", placeholder="GPIO pin number, ex: D18").bind_value(globals(), "led_pin")
        ui.number(label="LED Count", value=100, min=1, precision=0, step=1).bind_value(
            globals(), "led_count"
        )
        ui.number(
            label="LED Brightness", value=0.1, min=0.1, max=1.0, precision=1, step=0.1
        ).bind_value(globals(), "led_brightness")
        with ui.stepper_navigation():
            ui.button("Done", on_click=lambda: ui.notify("Yay!", type="positive"))
            ui.button("Back", on_click=stepper.previous).props("flat")

ui.run()
