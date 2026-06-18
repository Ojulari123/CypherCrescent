from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, Boolean, Numeric, Date, TIMESTAMP, func, DECIMAL, Enum, text, CheckConstraint, UniqueConstraint, Index, Time
from sqlalchemy.orm import sessionmaker, relationship, backref, declarative_base
from sqlalchemy import JSON
from Config.config import settings
from dotenv import load_dotenv
load_dotenv()

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    pool_recycle=300
)
Local_Session = sessionmaker(bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    display_name = Column(String(100), nullable=True)
    email_verified = Column(Boolean, default=False, nullable=False)
    two_factor_enabled = Column(Boolean, nullable=False, server_default="false", default=False)
    profile_photo_url = Column(String(500), nullable=True)
    token_version = Column(Integer, nullable=False, server_default="0", default=0)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    holdings = relationship("Holding", back_populates="user", cascade="all, delete-orphan")
    watchlist = relationship("Watchlist", back_populates="user", cascade="all, delete-orphan")

class Holding(Base):
    __tablename__ = "holdings"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    coin_slug = Column(String(100), nullable=False)
    quantity = Column(Numeric(38, 18), nullable=False)
    buy_price = Column(Numeric(24, 12), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="holdings")

    __table_args__ = (
        UniqueConstraint("user_id", "coin_slug", name="uq_holdings_user_coin"),
    )

class Watchlist(Base):
    __tablename__ = "watchlist"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    coin_slug = Column(String(100), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="watchlist")

    __table_args__ = (
        UniqueConstraint("user_id", "coin_slug", name="uq_watchlist_user_coin"),
    )

def get_db():
    db = Local_Session()
    try:
        yield db
    finally:
        db.close()