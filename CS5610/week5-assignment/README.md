# student's VPN Management Console

A demo site to manage VPN customers and their subscription orders.

## Run locally

```bash
npm install
cp .env.example .env
set -a; source .env; set +a
npm run db:reset
npm run dev   # open http://localhost:3000
```

On the home page, the left panel creates a customer (name, email, password).
The right panel creates an order for a given customer id with plan and months.
The server computes `expires_at` from months and sets `price_cents` from per-month rates (cents): basic 599, standard 999, premium 1499.

## SQL (DDL)

```sql
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE orders (
  id SERIAL PRIMARY KEY,
  customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
  plan TEXT NOT NULL CHECK (plan IN ('basic','standard','premium')),
  expires_at TIMESTAMPTZ NOT NULL,
  price_cents INTEGER NOT NULL CHECK (price_cents >= 0),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_orders_customer_id ON orders(customer_id);
```

## Seed data

```sql
INSERT INTO customers (name, email, password) VALUES
  ('Alice Chen', 'alice@example.com', 'alice123'),
  ('Bob Lee',    'bob@example.com',   'bob123'),
  ('Student',   'student@example.com',  'student123');

INSERT INTO orders (customer_id, plan, expires_at, price_cents) VALUES
  (1, 'basic',    NOW() + INTERVAL '30 days',   599),
  (2, 'standard', NOW() + INTERVAL '90 days',  2997),
  (3, 'premium',  NOW() + INTERVAL '365 days', 17988);
```

## Project layout
```
src/
  db.js
  server.js
sql/
  schema.sql
  seed.sql
.env.example
package.json
README.md
```
