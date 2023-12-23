"""
Mock API server for the application.

This module simulates the API server for the application.
"""
import argparse
import threading
import time

from flask import Flask, jsonify, request

app = Flask(__name__)

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Mock API Server")
parser.add_argument("--response-code", type=int, default=200, help="Response code to return")
args = parser.parse_args()


class EventManager:
    """
    Event manager class.
    """

    def __init__(self):
        self.latest_event = None

    def create_event_id(self, has_event):
        """
        Create an event ID.
        """
        epoch_time = int(time.time())
        return f"{epoch_time}-0" if has_event else str(epoch_time)

    def generate_event(self):
        """
        Generate an event.
        """
        event_id = self.create_event_id(True)
        self.latest_event = {
            "method": "tip",
            "object": {
                "broadcaster": "user_name",
                "tip": {"isAnon": False, "message": "red", "tokens": 35},
                "user": {
                    "colorGroup": "l",
                    "fcAutoRenew": False,
                    "gender": "m",
                    "hasDarkmode": False,
                    "hasTokens": True,
                    "inFanclub": False,
                    "inPrivateShow": False,
                    "isBroadcasting": True,
                    "isFollower": False,
                    "isMod": False,
                    "isOwner": False,
                    "isSilenced": False,
                    "isSpying": False,
                    "language": "en",
                    "recentTips": "tons",
                    "subgender": "",
                    "username": "myFavoriteTipper",
                },
            },
            "id": event_id,
        }

    def get_next_url(self, base_url, username, token):
        """
        Get the next URL.
        """
        last_id = self.create_event_id(False)
        return f"{base_url}events/{username}/{token}/?i={last_id}&timeout=10"

    def get_latest_event(self):
        """
        Get the latest event.
        """
        event = self.latest_event
        self.latest_event = None  # Clear the event after getting it
        return event


event_manager = EventManager()


@app.route("/events/<username>/<token>/")
def events(username, token):
    """
    Handle the events endpoint.
    """
    timeout = request.args.get("timeout", default=10, type=int)
    timeout = max(0, min(timeout, 90))  # Enforce the 0-90 seconds range
    start_time = time.time()

    if args.response_code == 521:
        return jsonify({"message": "Service Unavailable"}), 521

    if args.response_code == 500:
        return jsonify({"message": "Internal Server Error"}), 500

    while time.time() - start_time < timeout:
        event = event_manager.get_latest_event()
        if event:
            return (
                jsonify(
                    {
                        "events": [event],
                        "nextUrl": event_manager.get_next_url(request.host_url, username, token),
                    }
                ),
                args.response_code,
            )
        time.sleep(1)

    return (
        jsonify(
            {
                "events": [],
                "nextUrl": event_manager.get_next_url(request.host_url, username, token),
            }
        ),
        args.response_code,
    )


def simulate_event_creation():
    """
    Simulate event creation.
    """
    while True:
        event_manager.generate_event()
        time.sleep(10)


threading.Thread(target=simulate_event_creation, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
