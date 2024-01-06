#!/usr/bin/env python3
import asyncio
import os.path
import platform
import shlex
import sys

from nicegui import ui


async def run_command(command: str) -> None:
    """Run a command in the background and display the output in the pre-created dialog."""
    dialog.open()
    result.content = ""
    command = command.replace(
        "python3", sys.executable
    )  # NOTE replace with machine-independent Python path (#1240)
    process = await asyncio.create_subprocess_exec(
        *shlex.split(command, posix="win" not in sys.platform.lower()),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        cwd=os.path.dirname(os.path.abspath(__file__)),
    )
    # NOTE we need to read the output in chunks, otherwise the process will block
    output = ""
    while True:
        if process.stdout is not None:
            new = await process.stdout.read(4096)
            if not new:
                break
            output += new.decode()
            # NOTE the content of the markdown element is replaced every time we have new output
            result.content = f"```\n{output}\n```"


with ui.dialog() as dialog, ui.card():
    result = ui.markdown()

ui.button("Run StripAlerts", on_click=lambda: run_command("sudo python3 src/main.py"))

# NOTE: On Windows reload must be disabled to make asyncio.create_subprocess_exec work (see https://github.com/zauberzeug/nicegui/issues/486)
ui.run(reload=platform.system() != "Windows")
