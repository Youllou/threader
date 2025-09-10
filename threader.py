from slack_bolt import App
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv
import os

from sqlalchemy import Column, Integer, String, Boolean, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class ShameConfig(Base):
    __tablename__ = "shame_config"

    id = Column(Integer, primary_key=True)
    dest_channel = Column(String, default="wall-of-shame")
    trigger_emoji = Column(String, default="shame")
    message_template = Column(
        String,
        default=":rotating_light: SHAME! :rotating_light:\n<PERMALINK|this message>"
    )
    admin_only = Column(Boolean, default=False)


load_dotenv()
# Initialize app with bot token and signing secret
app = App(
    token=os.getenv("TOKEN"),
    signing_secret=os.getenv("SIGNING_SECRET")
)

engine = create_engine("sqlite:///shame.db")  # or postgres://...
Session = sessionmaker(bind=engine)
session = Session()

Base.metadata.create_all(engine)


def get_config():
    config = session.query(ShameConfig).first()
    if not config:
        config = ShameConfig()
        session.add(config)
        session.commit()
    return config


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
    user = event["user"]
    if config.admin_only:
        user_info = client.users_info(user=user)["user"]
        if not (user_info.get("is_admin") or user_info.get("is_owner")):
            return  # ignore reaction
    try:
        reaction = event["reaction"]
        if reaction != config.trigger_emoji:
            return

        channel = event["item"]["channel"]
        ts = event["item"]["ts"]
        
        permalink = client.chat_getPermalink(channel=channel, message_ts=ts)["permalink"]

        message_text = config.message_template.replace("<PERMALINK>", permalink)

        client.chat_postMessage(channel=config.dest_channel, text=message_text)

    except SlackApiError as e:
        print(f"Error: {e.response['error']}")

@app.command("/shameconfig")
def handle_config(ack, respond, command):
    ack()
    user_id = command["user_id"]
    user_info = app.client.users_info(user=user_id)["user"]

    if not (user_info.get("is_admin") or user_info.get("is_owner")):
        return

    args = command["text"].split(" ", 1)
    if not args or len(args) < 2:
        respond("Usage: /shameconfig <option> <value>")
        return
    
    option, value = args
    config = get_config()

    if option == "channel":
        config.dest_channel = value.lstrip("#")
    elif option == "emoji":
        config.trigger_emoji = value
    elif option == "template":
        config.message_template = value
    elif option == "admin_only":
        config.admin_only = value.lower() in ["true", "1", "yes"]

    session.commit()
    respond(f"✅ Updated {option} to {value}")



if __name__ == "__main__":
    auto_join_public_channels(app.client)
    app.start(port=3001)
    