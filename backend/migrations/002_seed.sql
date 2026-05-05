-- Seed: branches, categories, settings
BEGIN;

INSERT INTO branches (code, name, address, phone) VALUES
    ('main',     'Центральный',         '',            ''),
    ('doc-labs', 'Doc Labs',            '',            ''),
    ('ddoc93',   'ДОК-93 (Краснодар)',  '',            ''),
    ('giga',     'Giga-Chip',           '',            '')
ON CONFLICT (code) DO NOTHING;

INSERT INTO categories (name, sort_order) VALUES
    ('Запчасти', 10),
    ('Услуги',   20),
    ('Аксессуары', 30)
ON CONFLICT DO NOTHING;

INSERT INTO cash_accounts (branch_id, name)
SELECT b.id, 'Касса'
FROM branches b
ON CONFLICT (branch_id, name) DO NOTHING;

INSERT INTO settings (key, value) VALUES
    ('order_number_prefix', '"СЦ-"'),
    ('default_warranty_days', '90'),
    ('default_currency', '"RUB"')
ON CONFLICT (key) DO NOTHING;

COMMIT;
