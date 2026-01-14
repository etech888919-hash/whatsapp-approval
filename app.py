from flask import Flask, request, jsonify
import requests
import time

app = Flask(__name__)

TEXTMEBOT_API_KEY = "ZLynFyRSaXps"

# simple in-memory dedup store (OK for now)
processed_events = {}
DEDUP_WINDOW_SECONDS = 30


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    print("Incoming:", data)

    event_type = data.get("type")

    # 👉 HANDLE BUTTON EVENTS ONLY
    if event_type == "button":
        button_id = data.get("buttonId")
        sender = data.get("from")
        lid = data.get("from_lid")

        # build a unique event key
        event_key = f"{lid}:{button_id}"

        now = time.time()

        # 🔒 DEDUPLICATION
        if event_key in processed_events:
            if now - processed_events[event_key] < DEDUP_WINDOW_SECONDS:
                print("Duplicate button event ignored:", event_key)
                return jsonify({"status": "duplicate_ignored"})

        # mark as processed
        processed_events[event_key] = now

        if button_id == "APPROVE":
            print("APPROVE received, calling API...")
            requests.get(
                "https://kems.in/secure.php",
                params={"q": "APPROVE_TOKEN"},
                timeout=30
            )
            send_reply(sender, "✅ Approved successfully")
            return jsonify({"status": "approved"})

        elif button_id == "REJECT":
            print("REJECT received, calling API...")
            requests.get(
                "https://kems.in/secure.php",
                params={"q": "REJECT_TOKEN"},
                timeout=30
            )
            send_reply(sender, "❌ Rejected successfully")
            return jsonify({"status": "rejected"})

    return jsonify({"status": "ignored"})


def send_reply(phone, text):
    requests.get(
        "https://api.textmebot.com/send.php",
        params={
            "recipient": phone,
            "apikey": TEXTMEBOT_API_KEY,
            "text": text,
            "json": "yes"
        }
    )


if __name__ == "__main__":
    app.run(port=5000)
