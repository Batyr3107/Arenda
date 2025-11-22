from sqlalchemy import Column, Integer, String, BigInteger, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


class TelegramUser(Base):
    """Telegram user linked to system user"""
    __tablename__ = "telegram_users"

    id = Column(Integer, primary_key=True, index=True)

    # Telegram info
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    language_code = Column(String, default="ru")

    # Link to system user
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    # Bot state for conversation
    is_active = Column(Boolean, default=True)
    is_notifications_enabled = Column(Boolean, default=True)
    last_interaction = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship
    user = relationship("User", backref="telegram_accounts")

    def __repr__(self):
        return f"<TelegramUser {self.telegram_id} - {self.username}>"


class TelegramMessage(Base):
    """Log of telegram bot messages"""
    __tablename__ = "telegram_messages"

    id = Column(Integer, primary_key=True, index=True)

    telegram_user_id = Column(Integer, ForeignKey("telegram_users.id"), nullable=False, index=True)
    message_type = Column(String, nullable=False)  # incoming, outgoing, command
    message_text = Column(Text, nullable=True)
    command = Column(String, nullable=True, index=True)

    # Response info
    is_successful = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    telegram_user = relationship("TelegramUser", backref="messages")

    def __repr__(self):
        return f"<TelegramMessage {self.id} - {self.command}>"
