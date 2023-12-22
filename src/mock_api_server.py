from flask import Flask, jsonify, request
import time
import threading

app = Flask(__name__)

# Global variable to store the latest event
latest_event = None


def create_event_id(has_event):
    """
    Create an event ID based on the current epoch time.
    Append '-0' if there is an event.
    """
    epoch_time = int(time.time())
    return f"{epoch_time}-0" if has_event else str(epoch_time)


def generate_event():
    """
    Generate a new event.
    """
    global latest_event
    event_id = create_event_id(True)
    latest_event = {
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


def get_next_url(base_url, username, token):
    """
    Generate the nextUrl dynamically.
    """
    last_id = create_event_id(False)
    return f"{base_url}/events/{username}/{token}/?i={last_id}&timeout=10"


@app.route("/events/<username>/<token>/")
def events(username, token):
    """
    Endpoint to return events data with long polling.
    """
    global latest_event
    timeout = request.args.get("timeout", default=10, type=int)
    timeout = max(0, min(timeout, 90))  # Enforce the 0-90 seconds range
    start_time = time.time()
    while time.time() - start_time < timeout:
        if latest_event:  # If there is an event, return it
            event = latest_event
            latest_event = None  # Clear the event after sending
            return jsonify(
                {
                    "events": [event],
                    "nextUrl": get_next_url(request.host_url, username, token),
                }
            )
        time.sleep(1)  # Sleep to avoid busy waiting

    return jsonify(
        {"events": [], "nextUrl": get_next_url(request.host_url, username, token)}
    )


# Background thread to simulate event creation
def simulate_event_creation():
    while True:
        generate_event()
        time.sleep(10)  # Generate a new event every 10 seconds


threading.Thread(target=simulate_event_creation, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
