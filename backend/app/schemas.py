from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, ConfigDict, EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class LoginIn(BaseModel):
    email: EmailStr
    password: str


# ---- User ----
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    phone: Optional[str] = None
    role: Literal['admin', 'manager', 'warehouse', 'master', 'accountant']
    branch_id: Optional[int] = None
    is_active: bool = True


class UserCreate(UserBase):
    password: str = Field(min_length=6)


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[Literal['admin', 'manager', 'warehouse', 'master', 'accountant']] = None
    branch_id: Optional[int] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(default=None, min_length=6)


class UserOut(UserBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ---- Branch ----
class BranchOut(BaseModel):
    id: int
    code: str
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool
    model_config = ConfigDict(from_attributes=True)


class BranchCreate(BaseModel):
    code: str
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None


# ---- Customer ----
class CustomerBase(BaseModel):
    kind: Literal['individual', 'legal'] = 'individual'
    full_name: str
    phone: Optional[str] = None
    extra_phone: Optional[str] = None
    email: Optional[str] = None
    inn: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    discount_pct: Decimal = Decimal('0')
    blacklist: bool = False
    branch_id: Optional[int] = None


class CustomerCreate(CustomerBase): ...
class CustomerUpdate(CustomerBase): ...

class CustomerOut(CustomerBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ---- Device ----
class DeviceBase(BaseModel):
    customer_id: int
    device_type: str
    brand: Optional[str] = None
    model: Optional[str] = None
    serial: Optional[str] = None
    imei: Optional[str] = None
    notes: Optional[str] = None


class DeviceCreate(DeviceBase): ...

class DeviceOut(DeviceBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ---- Product ----
class ProductBase(BaseModel):
    kind: Literal['part', 'service'] = 'part'
    sku: Optional[str] = None
    name: str
    description: Optional[str] = None
    unit: str = 'шт'
    cost: Decimal = Decimal('0')
    price: Decimal = Decimal('0')
    category_id: Optional[int] = None
    is_active: bool = True


class ProductCreate(ProductBase): ...
class ProductUpdate(ProductBase): ...

class ProductOut(ProductBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ---- Stock ----
class StockOut(BaseModel):
    product_id: int
    sku: Optional[str] = None
    name: str
    unit: str
    cost: Decimal
    price: Decimal
    quantity: Decimal
    reserved: Decimal
    available: Decimal
    model_config = ConfigDict(from_attributes=True)


class StockMovementIn(BaseModel):
    product_id: int
    quantity: Decimal = Field(gt=0)
    type: Literal['in', 'out', 'adjust', 'writeoff'] = 'in'
    cost: Decimal = Decimal('0')
    note: Optional[str] = None


class StockMovementOut(BaseModel):
    id: int
    product_id: int
    user_id: int
    order_id: Optional[int] = None
    type: str
    quantity: Decimal
    cost: Decimal
    note: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ---- Order items ----
class OrderItemIn(BaseModel):
    product_id: Optional[int] = None
    kind: Literal['part', 'service']
    name: str
    quantity: Decimal = Decimal('1')
    unit_cost: Decimal = Decimal('0')
    unit_price: Decimal = Decimal('0')
    discount_pct: Decimal = Decimal('0')
    master_share_pct: Decimal = Decimal('0')


class OrderItemOut(OrderItemIn):
    id: int
    order_id: int
    model_config = ConfigDict(from_attributes=True)


# ---- Order ----
class OrderCreate(BaseModel):
    customer_id: int
    device_id: Optional[int] = None
    manager_id: Optional[int] = None
    master_id: Optional[int] = None
    branch_id: Optional[int] = None
    declared_problem: Optional[str] = None
    accessories: Optional[str] = None
    appearance: Optional[str] = None
    estimated_cost: Decimal = Decimal('0')
    deadline_at: Optional[datetime] = None
    items: List[OrderItemIn] = []


class OrderUpdate(BaseModel):
    master_id: Optional[int] = None
    manager_id: Optional[int] = None
    declared_problem: Optional[str] = None
    diagnosis: Optional[str] = None
    work_done: Optional[str] = None
    accessories: Optional[str] = None
    appearance: Optional[str] = None
    estimated_cost: Optional[Decimal] = None
    discount_amount: Optional[Decimal] = None
    deadline_at: Optional[datetime] = None
    warranty_until: Optional[date] = None


class OrderStatusIn(BaseModel):
    status: Literal['new', 'diagnosing', 'awaiting', 'in_repair', 'ready', 'issued', 'cancelled', 'warranty']
    note: Optional[str] = None


class CustomerMini(BaseModel):
    id: int
    full_name: str
    phone: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class UserMini(BaseModel):
    id: int
    full_name: str
    role: str
    model_config = ConfigDict(from_attributes=True)


class DeviceMini(BaseModel):
    id: int
    device_type: str
    brand: Optional[str] = None
    model: Optional[str] = None
    serial: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class OrderOut(BaseModel):
    id: int
    number: str
    branch_id: Optional[int] = None
    customer: CustomerMini
    device: Optional[DeviceMini] = None
    manager: Optional[UserMini] = None
    master: Optional[UserMini] = None
    status: str
    payment_status: str
    declared_problem: Optional[str] = None
    diagnosis: Optional[str] = None
    work_done: Optional[str] = None
    accessories: Optional[str] = None
    appearance: Optional[str] = None
    estimated_cost: Decimal
    total_amount: Decimal
    paid_amount: Decimal
    discount_amount: Decimal
    deadline_at: Optional[datetime] = None
    issued_at: Optional[datetime] = None
    warranty_until: Optional[date] = None
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemOut] = []
    model_config = ConfigDict(from_attributes=True)


class OrderHistoryOut(BaseModel):
    id: int
    order_id: int
    user_id: Optional[int] = None
    action: str
    before_state: Optional[dict] = None
    after_state: Optional[dict] = None
    note: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ---- Finance ----
class TransactionIn(BaseModel):
    order_id: Optional[int] = None
    cash_account_id: Optional[int] = None
    type: Literal['income', 'expense']
    method: Literal['cash', 'card', 'transfer', 'sbp', 'other'] = 'cash'
    amount: Decimal = Field(gt=0)
    category: Optional[str] = None
    description: Optional[str] = None


class TransactionOut(TransactionIn):
    id: int
    user_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ---- Salary ----
class SalaryRuleIn(BaseModel):
    user_id: int
    base_salary: Decimal = Decimal('0')
    work_share_pct: Decimal = Decimal('0')
    parts_share_pct: Decimal = Decimal('0')
    revenue_share_pct: Decimal = Decimal('0')
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None


class SalaryRuleOut(SalaryRuleIn):
    id: int
    model_config = ConfigDict(from_attributes=True)


class SalaryCalcIn(BaseModel):
    user_id: int
    period_start: date
    period_end: date
    bonus_amount: Decimal = Decimal('0')
    deduction_amount: Decimal = Decimal('0')
    save: bool = False


class SalaryRecordOut(BaseModel):
    id: int
    user_id: int
    period_start: date
    period_end: date
    base_amount: Decimal
    works_amount: Decimal
    parts_amount: Decimal
    revenue_amount: Decimal
    bonus_amount: Decimal
    deduction_amount: Decimal
    total_amount: Decimal
    paid: bool
    paid_at: Optional[datetime] = None
    breakdown: Optional[dict] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ---- Reports ----
class ReportSummary(BaseModel):
    period_start: date
    period_end: date
    orders_total: int
    orders_by_status: dict
    revenue: Decimal
    expense: Decimal
    profit: Decimal
    avg_check: Decimal


# Forward refs
Token.model_rebuild()
