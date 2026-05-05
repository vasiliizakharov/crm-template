from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import (
    BigInteger, Integer, String, Text, Boolean, ForeignKey, Numeric, Date, DateTime,
    Enum as SAEnum, func, JSON, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import JSONB, ENUM as PgEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base

# Enums (as native pg types — they exist already from migration)
UserRole       = PgEnum('admin', 'manager', 'warehouse', 'master', 'accountant', name='user_role', create_type=False)
CustomerKind   = PgEnum('individual', 'legal', name='customer_kind', create_type=False)
ProductKind    = PgEnum('part', 'service', name='product_kind', create_type=False)
MovementType   = PgEnum('in', 'out', 'adjust', 'reserve', 'unreserve', 'writeoff', name='movement_type', create_type=False)
OrderStatus    = PgEnum('new', 'diagnosing', 'awaiting', 'in_repair', 'ready', 'issued', 'cancelled', 'warranty', name='order_status', create_type=False)
PaymentStatus  = PgEnum('unpaid', 'partial', 'paid', 'refunded', name='payment_status', create_type=False)
ItemKind       = PgEnum('part', 'service', name='item_kind', create_type=False)
TxType         = PgEnum('income', 'expense', name='tx_type', create_type=False)
TxMethod       = PgEnum('cash', 'card', 'transfer', 'sbp', 'other', name='tx_method', create_type=False)


class Branch(Base):
    __tablename__ = "branches"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True)
    name: Mapped[str] = mapped_column(String(128))
    address: Mapped[Optional[str]] = mapped_column(Text)
    phone: Mapped[Optional[str]] = mapped_column(String(32))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    branch_id: Mapped[Optional[int]] = mapped_column(ForeignKey("branches.id"))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    full_name: Mapped[str] = mapped_column(String(128))
    phone: Mapped[Optional[str]] = mapped_column(String(32))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(UserRole)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    branch: Mapped[Optional["Branch"]] = relationship(lazy="joined")


class Customer(Base):
    __tablename__ = "customers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    branch_id: Mapped[Optional[int]] = mapped_column(ForeignKey("branches.id"))
    kind: Mapped[str] = mapped_column(CustomerKind, default='individual')
    full_name: Mapped[str] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(32))
    extra_phone: Mapped[Optional[str]] = mapped_column(String(32))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    inn: Mapped[Optional[str]] = mapped_column(String(12))
    address: Mapped[Optional[str]] = mapped_column(Text)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    discount_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    blacklist: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    devices: Mapped[List["Device"]] = relationship(back_populates="customer", cascade="all, delete-orphan")


class Device(Base):
    __tablename__ = "devices"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"))
    device_type: Mapped[str] = mapped_column(String(64))
    brand: Mapped[Optional[str]] = mapped_column(String(64))
    model: Mapped[Optional[str]] = mapped_column(String(128))
    serial: Mapped[Optional[str]] = mapped_column(String(128))
    imei: Mapped[Optional[str]] = mapped_column(String(32))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    customer: Mapped["Customer"] = relationship(back_populates="devices")


class Category(Base):
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categories.id"))
    name: Mapped[str] = mapped_column(String(128))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categories.id"))
    kind: Mapped[str] = mapped_column(ProductKind, default='part')
    sku: Mapped[Optional[str]] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    unit: Mapped[str] = mapped_column(String(16), default='шт')
    cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    price: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Stock(Base):
    __tablename__ = "stock"
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), primary_key=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), default=0)
    reserved: Mapped[Decimal] = mapped_column(Numeric(14, 3), default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    product: Mapped["Product"] = relationship(lazy="joined")


class StockMovement(Base):
    __tablename__ = "stock_movements"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    order_id: Mapped[Optional[int]] = mapped_column(ForeignKey("orders.id"))
    type: Mapped[str] = mapped_column(MovementType)
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3))
    cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    note: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    product: Mapped["Product"] = relationship(lazy="joined")
    user: Mapped["User"] = relationship(lazy="joined")


class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    branch_id: Mapped[Optional[int]] = mapped_column(ForeignKey("branches.id"))
    number: Mapped[str] = mapped_column(String(24), unique=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"))
    device_id: Mapped[Optional[int]] = mapped_column(ForeignKey("devices.id"))
    manager_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    master_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(OrderStatus, default='new')
    payment_status: Mapped[str] = mapped_column(PaymentStatus, default='unpaid')
    declared_problem: Mapped[Optional[str]] = mapped_column(Text)
    diagnosis: Mapped[Optional[str]] = mapped_column(Text)
    work_done: Mapped[Optional[str]] = mapped_column(Text)
    accessories: Mapped[Optional[str]] = mapped_column(Text)
    appearance: Mapped[Optional[str]] = mapped_column(Text)
    estimated_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    deadline_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    issued_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    warranty_until: Mapped[Optional[date]] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))

    customer: Mapped["Customer"] = relationship(lazy="joined", foreign_keys=[customer_id])
    device: Mapped[Optional["Device"]] = relationship(lazy="joined", foreign_keys=[device_id])
    manager: Mapped[Optional["User"]] = relationship(lazy="joined", foreign_keys=[manager_id])
    master: Mapped[Optional["User"]] = relationship(lazy="joined", foreign_keys=[master_id])
    items: Mapped[List["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan", lazy="selectin")


class OrderItem(Base):
    __tablename__ = "order_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"))
    product_id: Mapped[Optional[int]] = mapped_column(ForeignKey("products.id"))
    kind: Mapped[str] = mapped_column(ItemKind)
    name: Mapped[str] = mapped_column(String(255))
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), default=1)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    discount_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    master_share_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    order: Mapped["Order"] = relationship(back_populates="items")


class OrderHistory(Base):
    __tablename__ = "order_history"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"))
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(64))
    before_state: Mapped[Optional[dict]] = mapped_column(JSONB)
    after_state: Mapped[Optional[dict]] = mapped_column(JSONB)
    note: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[Optional["User"]] = relationship(lazy="joined")


class CashAccount(Base):
    __tablename__ = "cash_accounts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    branch_id: Mapped[Optional[int]] = mapped_column(ForeignKey("branches.id"))
    name: Mapped[str] = mapped_column(String(64))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Transaction(Base):
    __tablename__ = "transactions"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    order_id: Mapped[Optional[int]] = mapped_column(ForeignKey("orders.id"))
    cash_account_id: Mapped[Optional[int]] = mapped_column(ForeignKey("cash_accounts.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    type: Mapped[str] = mapped_column(TxType)
    method: Mapped[str] = mapped_column(TxMethod, default='cash')
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    category: Mapped[Optional[str]] = mapped_column(String(64))
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SalaryRule(Base):
    __tablename__ = "salary_rules"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    base_salary: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    work_share_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    parts_share_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    revenue_share_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    valid_from: Mapped[date] = mapped_column(Date, server_default=func.current_date())
    valid_to: Mapped[Optional[date]] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SalaryRecord(Base):
    __tablename__ = "salary_records"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    period_start: Mapped[date] = mapped_column(Date)
    period_end: Mapped[date] = mapped_column(Date)
    base_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    works_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    parts_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    revenue_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    bonus_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    deduction_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    paid: Mapped[bool] = mapped_column(Boolean, default=False)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    breakdown: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint("user_id", "period_start", "period_end"),)


class Setting(Base):
    __tablename__ = "settings"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[dict] = mapped_column(JSONB)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
