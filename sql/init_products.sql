CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    url TEXT,
    price INTEGER NOT NULL CHECK (price >= 0),
    acne_symptom VARCHAR(20) NOT NULL,
    category VARCHAR(50) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_products_search
    ON products (acne_symptom, category, price);

-- 商品データの追加例
-- 実際の商品名・URL・価格に置き換えて使用してください。
--
-- INSERT INTO products (product_name, url, price, acne_symptom, category)
-- VALUES
--   ('商品A', 'https://example.com/a', 980, '赤', '化粧水'),
--   ('商品B', 'https://example.com/b', 1480, '赤', '化粧水'),
--   ('商品C', 'https://example.com/c', 1800, '白', '化粧水');
