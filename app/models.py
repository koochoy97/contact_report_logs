from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, BigInteger,
    String, Text, func,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Account(Base):
    __tablename__ = "elt_accounts"

    id = Column(Integer, primary_key=True)
    email = Column(String, nullable=False)
    password_encrypted = Column(String, nullable=False)
    cookies_json = Column(Text, nullable=True)
    label = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

    clients = relationship("Client", back_populates="account")


class Client(Base):
    __tablename__ = "elt_clients"

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("elt_accounts.id"))
    team_id = Column(Integer, nullable=False)
    display_name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

    account = relationship("Account", back_populates="clients")
    runs = relationship("Run", back_populates="client")


class Run(Base):
    __tablename__ = "elt_runs"

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("elt_clients.id"))
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    status = Column(String, default="pending")
    rows_extracted = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    duration_seconds = Column(Integer, nullable=True)

    client = relationship("Client", back_populates="runs")

    def mark_success(self, rows: int):
        self.status = "success"
        self.rows_extracted = rows
        self.finished_at = datetime.now()
        if self.started_at:
            self.duration_seconds = int((self.finished_at - self.started_at).total_seconds())

    def mark_error(self, message: str):
        self.status = "error"
        self.error_message = message
        self.finished_at = datetime.now()
        if self.started_at:
            self.duration_seconds = int((self.finished_at - self.started_at).total_seconds())
