INSERT INTO customers (name, email, password) VALUES
  ('Alice Chen', 'alice@example.com', 'alice123'),
  ('Bob Lee',    'bob@example.com',   'bob123'),
  ('Student',   'student@example.com',  'student123');

-- map 1→Alice, 2→Bob, 3→Student
-- basic 5.99/mo, standard 9.99/mo, premium 14.99/mo
INSERT INTO orders (customer_id, plan, expires_at, price_cents) VALUES
  (1, 'basic',    NOW() + INTERVAL '30 days',   599),
  (2, 'standard', NOW() + INTERVAL '90 days',  2997),
  (3, 'premium',  NOW() + INTERVAL '365 days', 17988);
