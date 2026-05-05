-- Service CRM Template — initial schema
-- PostgreSQL 16+
-- Author: Service CRM
-- All money — numeric(14,2) RUB. All timestamps — timestamptz UTC.

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS citext;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- ============================================================
-- Roles & users
-- ============================================================
CREATE TYPE user_role AS ENUM ('admin', 'manager', 'warehouse', 'master', 'accountant');

CREATE TABLE branches (
    id              SERIAL PRIMARY KEY,
    code            varchar(32) NOT NULL UNIQUE,
    name            varchar(128) NOT NULL,
    address         text,
    phone           varchar(32),
    is_active       boolean NOT NULL DEFAULT TRUE,
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE users (
    id              SERIAL PRIMARY KEY,
    branch_id       integer REFERENCES branches(id) ON DELETE SET NULL,
    email           citext NOT NULL UNIQUE,
    full_name       varchar(128) NOT NULL,
    phone           varchar(32),
    password_hash   varchar(255) NOT NULL,
    role            user_role NOT NULL,
    is_active       boolean NOT NULL DEFAULT TRUE,
    last_login_at   timestamptz,
    created_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_users_role ON users(role) WHERE is_active = TRUE;
CREATE INDEX idx_users_branch ON users(branch_id);

-- ============================================================
-- Customers
-- ============================================================
CREATE TYPE customer_kind AS ENUM ('individual', 'legal');

CREATE TABLE customers (
    id              SERIAL PRIMARY KEY,
    branch_id       integer REFERENCES branches(id) ON DELETE SET NULL,
    kind            customer_kind NOT NULL DEFAULT 'individual',
    full_name       varchar(255) NOT NULL,
    phone           varchar(32),
    extra_phone     varchar(32),
    email           citext,
    inn             varchar(12),
    address         text,
    notes           text,
    discount_pct    numeric(5,2) NOT NULL DEFAULT 0,
    blacklist       boolean NOT NULL DEFAULT FALSE,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_customers_phone ON customers(phone);
CREATE INDEX idx_customers_name_trgm ON customers USING gin (full_name gin_trgm_ops);

-- ============================================================
-- Devices (что принёс клиент в сервис)
-- ============================================================
CREATE TABLE devices (
    id              SERIAL PRIMARY KEY,
    customer_id     integer NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    device_type     varchar(64) NOT NULL,            -- "телефон", "ноутбук", "холодильник"
    brand           varchar(64),
    model           varchar(128),
    serial          varchar(128),
    imei            varchar(32),
    notes           text,
    created_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_devices_customer ON devices(customer_id);
CREATE INDEX idx_devices_serial ON devices(serial);

-- ============================================================
-- Catalog: categories, products, services
-- ============================================================
CREATE TYPE product_kind AS ENUM ('part', 'service');

CREATE TABLE categories (
    id              SERIAL PRIMARY KEY,
    parent_id       integer REFERENCES categories(id) ON DELETE SET NULL,
    name            varchar(128) NOT NULL,
    sort_order      integer NOT NULL DEFAULT 0
);

CREATE TABLE products (
    id              SERIAL PRIMARY KEY,
    category_id     integer REFERENCES categories(id) ON DELETE SET NULL,
    kind            product_kind NOT NULL DEFAULT 'part',
    sku             varchar(64) UNIQUE,
    name            varchar(255) NOT NULL,
    description     text,
    unit            varchar(16) NOT NULL DEFAULT 'шт',
    cost            numeric(14,2) NOT NULL DEFAULT 0 CHECK (cost >= 0),
    price           numeric(14,2) NOT NULL DEFAULT 0 CHECK (price >= 0),
    is_active       boolean NOT NULL DEFAULT TRUE,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_products_kind ON products(kind);
CREATE INDEX idx_products_active ON products(is_active);

-- ============================================================
-- Stock — current inventory + immutable movement log
-- ============================================================
CREATE TABLE stock (
    product_id      integer PRIMARY KEY REFERENCES products(id) ON DELETE CASCADE,
    quantity        numeric(14,3) NOT NULL DEFAULT 0,
    reserved        numeric(14,3) NOT NULL DEFAULT 0,
    updated_at      timestamptz NOT NULL DEFAULT now(),
    CHECK (quantity >= 0),
    CHECK (reserved >= 0)
);

CREATE TYPE movement_type AS ENUM ('in', 'out', 'adjust', 'reserve', 'unreserve', 'writeoff');

CREATE TABLE stock_movements (
    id              BIGSERIAL PRIMARY KEY,
    product_id      integer NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    user_id         integer NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    order_id        integer,                          -- FK added after orders table
    type            movement_type NOT NULL,
    quantity        numeric(14,3) NOT NULL,
    cost            numeric(14,2) NOT NULL DEFAULT 0,
    note            text,
    created_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_stockmov_product ON stock_movements(product_id);
CREATE INDEX idx_stockmov_order   ON stock_movements(order_id);
CREATE INDEX idx_stockmov_created ON stock_movements(created_at DESC);

-- ============================================================
-- Orders (заказ-наряд)
-- ============================================================
CREATE TYPE order_status AS ENUM (
    'new',           -- принят
    'diagnosing',    -- на диагностике
    'awaiting',      -- ожидание запчастей / согласования
    'in_repair',     -- в работе
    'ready',         -- готов
    'issued',        -- выдан
    'cancelled',
    'warranty'
);

CREATE TYPE payment_status AS ENUM ('unpaid', 'partial', 'paid', 'refunded');

CREATE TABLE orders (
    id              SERIAL PRIMARY KEY,
    branch_id       integer REFERENCES branches(id) ON DELETE SET NULL,
    number          varchar(24) NOT NULL UNIQUE,
    customer_id     integer NOT NULL REFERENCES customers(id) ON DELETE RESTRICT,
    device_id       integer REFERENCES devices(id) ON DELETE SET NULL,
    manager_id      integer REFERENCES users(id) ON DELETE SET NULL,
    master_id       integer REFERENCES users(id) ON DELETE SET NULL,
    status          order_status NOT NULL DEFAULT 'new',
    payment_status  payment_status NOT NULL DEFAULT 'unpaid',
    declared_problem text,                            -- со слов клиента
    diagnosis       text,                             -- что обнаружено
    work_done       text,                             -- что сделано
    accessories     text,                             -- комплект (зарядка, чехол)
    appearance      text,                             -- внешний вид при приёме
    estimated_cost  numeric(14,2) NOT NULL DEFAULT 0,
    total_amount    numeric(14,2) NOT NULL DEFAULT 0,
    paid_amount     numeric(14,2) NOT NULL DEFAULT 0,
    discount_amount numeric(14,2) NOT NULL DEFAULT 0,
    deadline_at     timestamptz,
    issued_at       timestamptz,
    warranty_until  date,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now(),
    created_by      integer REFERENCES users(id) ON DELETE SET NULL
);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_orders_master ON orders(master_id);
CREATE INDEX idx_orders_created ON orders(created_at DESC);

ALTER TABLE stock_movements
    ADD CONSTRAINT fk_stockmov_order FOREIGN KEY (order_id)
    REFERENCES orders(id) ON DELETE SET NULL;

-- Order items: parts (with stock binding) and services (master share %)
CREATE TYPE item_kind AS ENUM ('part', 'service');

CREATE TABLE order_items (
    id              SERIAL PRIMARY KEY,
    order_id        integer NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id      integer REFERENCES products(id) ON DELETE RESTRICT,
    kind            item_kind NOT NULL,
    name            varchar(255) NOT NULL,             -- snapshot
    quantity        numeric(14,3) NOT NULL DEFAULT 1 CHECK (quantity > 0),
    unit_cost       numeric(14,2) NOT NULL DEFAULT 0,  -- закупка / себестоимость
    unit_price      numeric(14,2) NOT NULL DEFAULT 0,  -- цена клиента
    discount_pct    numeric(5,2)  NOT NULL DEFAULT 0,
    master_share_pct numeric(5,2) NOT NULL DEFAULT 0,  -- % мастеру с этой позиции
    created_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_orderitems_order ON order_items(order_id);

-- Order history (audit)
CREATE TABLE order_history (
    id              BIGSERIAL PRIMARY KEY,
    order_id        integer NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    user_id         integer REFERENCES users(id) ON DELETE SET NULL,
    action          varchar(64) NOT NULL,              -- 'create','status_change','edit','payment',...
    before_state    jsonb,
    after_state     jsonb,
    note            text,
    created_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_orderhist_order ON order_history(order_id, created_at DESC);

-- ============================================================
-- Finance: transactions strictly bound to orders (or null=общие)
-- ============================================================
CREATE TYPE tx_type AS ENUM ('income', 'expense');
CREATE TYPE tx_method AS ENUM ('cash', 'card', 'transfer', 'sbp', 'other');

CREATE TABLE cash_accounts (
    id              SERIAL PRIMARY KEY,
    branch_id       integer REFERENCES branches(id) ON DELETE SET NULL,
    name            varchar(64) NOT NULL,
    is_active       boolean NOT NULL DEFAULT TRUE,
    UNIQUE (branch_id, name)
);

CREATE TABLE transactions (
    id              BIGSERIAL PRIMARY KEY,
    order_id        integer REFERENCES orders(id) ON DELETE SET NULL,  -- NULL = операционный расход (аренда и т.п.)
    cash_account_id integer REFERENCES cash_accounts(id) ON DELETE SET NULL,
    user_id         integer NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    type            tx_type NOT NULL,
    method          tx_method NOT NULL DEFAULT 'cash',
    amount          numeric(14,2) NOT NULL CHECK (amount > 0),
    category        varchar(64),                       -- 'order_payment','salary','rent','utilities','part_purchase'
    description     text,
    created_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_tx_order ON transactions(order_id);
CREATE INDEX idx_tx_type_created ON transactions(type, created_at DESC);

-- ============================================================
-- Salaries — параметры расчёта и факты
-- ============================================================
CREATE TABLE salary_rules (
    id              SERIAL PRIMARY KEY,
    user_id         integer NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    base_salary     numeric(14,2) NOT NULL DEFAULT 0,    -- оклад / период
    work_share_pct  numeric(5,2)  NOT NULL DEFAULT 0,    -- % от стоимости работ
    parts_share_pct numeric(5,2)  NOT NULL DEFAULT 0,    -- % от наценки на запчасти
    revenue_share_pct numeric(5,2) NOT NULL DEFAULT 0,   -- % от общей выручки (для менеджера)
    valid_from      date NOT NULL DEFAULT CURRENT_DATE,
    valid_to        date,
    created_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_salaryrules_user ON salary_rules(user_id);

CREATE TABLE salary_records (
    id              BIGSERIAL PRIMARY KEY,
    user_id         integer NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    period_start    date NOT NULL,
    period_end      date NOT NULL,
    base_amount     numeric(14,2) NOT NULL DEFAULT 0,
    works_amount    numeric(14,2) NOT NULL DEFAULT 0,
    parts_amount    numeric(14,2) NOT NULL DEFAULT 0,
    revenue_amount  numeric(14,2) NOT NULL DEFAULT 0,
    bonus_amount    numeric(14,2) NOT NULL DEFAULT 0,
    deduction_amount numeric(14,2) NOT NULL DEFAULT 0,
    total_amount    numeric(14,2) NOT NULL DEFAULT 0,
    paid            boolean NOT NULL DEFAULT FALSE,
    paid_at         timestamptz,
    breakdown       jsonb,
    created_at      timestamptz NOT NULL DEFAULT now(),
    UNIQUE (user_id, period_start, period_end)
);

-- ============================================================
-- Application settings (singleton-row K/V)
-- ============================================================
CREATE TABLE settings (
    key             varchar(64) PRIMARY KEY,
    value           jsonb NOT NULL,
    updated_at      timestamptz NOT NULL DEFAULT now()
);

-- ============================================================
-- Triggers: updated_at
-- ============================================================
CREATE OR REPLACE FUNCTION trg_set_updated_at() RETURNS trigger AS $$
BEGIN NEW.updated_at = now(); RETURN NEW; END $$ LANGUAGE plpgsql;

CREATE TRIGGER trg_customers_updated BEFORE UPDATE ON customers
    FOR EACH ROW EXECUTE FUNCTION trg_set_updated_at();
CREATE TRIGGER trg_products_updated BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION trg_set_updated_at();
CREATE TRIGGER trg_orders_updated BEFORE UPDATE ON orders
    FOR EACH ROW EXECUTE FUNCTION trg_set_updated_at();

-- ============================================================
-- Helper view: stock with product info
-- ============================================================
CREATE OR REPLACE VIEW v_stock AS
SELECT
    p.id           AS product_id,
    p.sku,
    p.name,
    p.unit,
    p.cost,
    p.price,
    COALESCE(s.quantity, 0)  AS quantity,
    COALESCE(s.reserved, 0)  AS reserved,
    COALESCE(s.quantity, 0) - COALESCE(s.reserved, 0) AS available
FROM products p
LEFT JOIN stock s ON s.product_id = p.id
WHERE p.is_active = TRUE AND p.kind = 'part';

COMMIT;
