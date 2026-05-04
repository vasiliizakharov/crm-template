"""SQLAlchemy models for CRM template."""
from datetime import datetime
from sqlalchemy import (Column, Integer, String, Text, DateTime, ForeignKey,
                        Boolean, Numeric, Enum, func)
from sqlalchemy.orm import declarative_base, relationship
import enum

Base = declarative_base()

class UserRole(str, enum.Enum):
    admin = "admin"
    manager = "manager"
    worker = "worker"

class OrderStatus(str, enum.Enum):
    new = "new"
    in_progress = "in_progress"
    done = "done"
    cancelled = "cancelled"
    archived = "archived"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(200), unique=True, nullable=False, index=True)
    password_hash = Column(String(200), nullable=False)
    full_name = Column(String(200), default="")
    role = Column(Enum(UserRole), default=UserRole.worker)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    phone = Column(String(50), default="")
    email = Column(String(200), default="")
    notes = Column(Text, default="")
    tags = Column(String(500), default="")
    created_at = Column(DateTime, default=func.now())
    orders = relationship("Order", back_populates="customer")

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    sku = Column(String(50), unique=True)
    name = Column(String(300), nullable=False)
    price = Column(Numeric(12, 2), default=0)
    stock_qty = Column(Integer, default=0)
    description = Column(Text, default="")

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    status = Column(Enum(OrderStatus), default=OrderStatus.new)
    title = Column(String(300), nullable=False)
    description = Column(Text, default="")
    total = Column(Numeric(12, 2), default=0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    assigned_to = Column(Integer, ForeignKey("users.id"))
    customer = relationship("Customer", back_populates="orders")
    transactions = relationship("Transaction", back_populates="order")

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    type = Column(String(20))  # income | expense
    amount = Column(Numeric(12, 2), nullable=False)
    description = Column(String(500), default="")
    created_at = Column(DateTime, default=func.now())
    order = relationship("Order", back_populates="transactions")
