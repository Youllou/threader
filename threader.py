from slack_bolt import App
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv
import os

load_dotenv()
# Initialize app with bot token and signing secret
app = App(
    token=os.getenv("TOKEN"),
    signing_secret=os.getenv("SIGNING_SECRET")
)

TRIGGER_EMOJI = "thread"  # name of the emoji without colons
DEST_CHANNEL = "wall-of-shame"

def auto_join_public_channels(client):
    try:
        result = client.conversations_list(types="public_channel")
        for ch in result["channels"]:
            try:
                client.conversations_join(channel=ch["id"])
                print(f"Joined #{ch['name']}")
            except SlackApiError as e:
                if e.response["error"] == "method_not_supported_for_channel_type":
                    # e.g. it's a private channel or archived
                    continue
                print(f"Could not join #{ch['name']}: {e.response['error']}")
    except SlackApiError as e:
        print(f"Error fetching channels: {e.response['error']}")


@app.event("reaction_added")
def handle_reaction_added(event, client):
    try:
        reaction = event["reaction"]
        if reaction != TRIGGER_EMOJI:
            return

        channel = event["item"]["channel"]
        ts = event["item"]["ts"]
        
        history = client.conversations_history(channel=channel, latest=ts, inclusive=True, limit=1)
        if not history["messages"]:
            return

        original_message = history["messages"][0]
        text = original_message.get("text", "")
        
        user = original_message.get("user")
        channel_info = client.conversations_info(channel=channel)
        channel_name = channel_info["channel"]["name"]

        client.chat_postMessage(
            channel=DEST_CHANNEL,
            text=(
                f":rotating_light: SHAME! :rotating_light:\n"
                f"> {text}\n\n"
                f"_Originally posted by <@{user}> in #{channel_name}_"
            )
        )


    except SlackApiError as e:
        print(f"Error: {e.response['error']}")

if __name__ == "__main__":
    auto_join_public_channels(app.client)
    app.start(port=3001)
    