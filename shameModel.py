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
