const express = require('express');
const { pool } = require('./db');
require('dotenv').config();

const app = express();
app.use(express.urlencoded({ extended: false }));

// cents per month
const pricePerMonth = { basic: 599, standard: 999, premium: 1499 };

function safe(s) {
  return String(s).replace(/[&<>"'`/=]/g, ch =>
    ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;','`':'&#96;','=':'&#61;','/':'&#47;'}[ch])
  );
}

function layout(body, note = '') {
  return `<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>student's VPN Management Console</title>
<style>
  body { font-family: system-ui, Arial, sans-serif; margin: 24px; }
  h1 { margin: 0 0 12px; }
  .note { color:#555; margin: 8px 0 16px; }
  .grid { display:grid; gap:20px; grid-template-columns: repeat(auto-fit, minmax(360px, 1fr)); }
  section { border:1px solid #ddd; border-radius:10px; padding:16px; }
  form { display:grid; gap:8px; margin-bottom:12px; }
  input, select, button { padding:8px 10px; border:1px solid #ccc; border-radius:8px; }
  button { cursor:pointer; }
  table { border-collapse:collapse; width:100%; }
  th, td { border-bottom:1px solid #eee; padding:8px; text-align:left; }
  small { color:#666; }
</style>
</head>
<body>
  <h1>student's VPN Management Console</h1>
  ${note ? `<div class="note">${note}</div>` : ''}
  ${body}
</body>
</html>`;
}

function renderHome(customers, orders) {
  const cRows = customers.map(c => `
    <tr>
      <td>${c.id}</td>
      <td>${safe(c.name)}</td>
      <td>${safe(c.email)}</td>
      <td>${safe(c.password)}</td>
      <td>${new Date(c.created_at).toLocaleString()}</td>
    </tr>
  `).join('');

  const oRows = orders.map(o => `
    <tr>
      <td>${o.id}</td>
      <td>${safe(o.customer_name)} (#${o.customer_id})</td>
      <td>${o.plan}</td>
      <td>$${(o.price_cents / 100).toFixed(2)}</td>
      <td>${new Date(o.expires_at).toLocaleString()}</td>
      <td>${new Date(o.created_at).toLocaleString()}</td>
    </tr>
  `).join('');

  const body = `
  <div class="grid">
    <section>
      <h2>Create Customer</h2>
      <form method="POST" action="/customers">
        <input name="name" placeholder="Full name" required>
        <input name="email" placeholder="Email address" type="email" required>
        <input name="password" placeholder="Password" required>
        <button type="submit">Add Customer</button>
      </form>
      <table>
        <thead><tr><th>#</th><th>Name</th><th>Email</th><th>Password</th><th>Created</th></tr></thead>
        <tbody>${cRows}</tbody>
      </table>
    </section>

    <section>
      <h2>Orders</h2>
      <form method="POST" action="/orders">
        <input name="customer_id" placeholder="Customer ID" type="number" required>
        <select name="plan" required>
          <option value="basic">basic</option>
          <option value="standard">standard</option>
          <option value="premium">premium</option>
        </select>
        <input name="months" placeholder="Months" type="number" min="1" value="1">
        <button type="submit">Create Order</button>
      </form>
      <table>
        <thead><tr><th>#</th><th>Customer</th><th>Plan</th><th>Price</th><th>Expires</th><th>Created</th></tr></thead>
        <tbody>${oRows}</tbody>
      </table>
      <small>Pricing (per month): basic $5.99, standard $9.99, premium $14.99.</small>
    </section>
  </div>`;
  return layout(body);
}

app.get('/', async (_req, res) => {
  try {
    const [c, o] = await Promise.all([
      pool.query('SELECT id, name, email, password, created_at FROM customers ORDER BY id'),
      pool.query(`
        SELECT o.id, o.plan, o.price_cents, o.expires_at, o.created_at,
               c.id AS customer_id, c.name AS customer_name
        FROM orders o
        JOIN customers c ON c.id = o.customer_id
        ORDER BY o.id
      `)
    ]);
    res.send(renderHome(c.rows, o.rows));
  } catch (e) {
    console.error('GET /', e);
    res.status(500).send(layout('<p>Unexpected error.</p>'));
  }
});

app.post('/customers', async (req, res) => {
  const { name, email, password } = req.body || {};
  if (!name || !email || !password) return res.status(400).send(layout('<p>Please fill all fields.</p>'));
  try {
    await pool.query('INSERT INTO customers (name, email, password) VALUES ($1, $2, $3)', [name, email, password]);
    res.redirect('/');
  } catch (e) {
    if (e.code === '23505') return res.status(409).send(layout('<p>Email already exists.</p>'));
    console.error('POST /customers', e);
    res.status(500).send(layout('<p>Failed to create customer.</p>'));
  }
});

app.post('/orders', async (req, res) => {
  const { customer_id, plan, months } = req.body || {};
  if (!customer_id || !plan) return res.status(400).send(layout('<p>customer_id and plan are required.</p>'));
  if (!pricePerMonth[plan]) return res.status(400).send(layout('<p>Invalid plan.</p>'));

  const m = Math.max(1, Math.min(36, Number(months || 1)));
  const price = pricePerMonth[plan] * m;
  const expires = new Date();
  expires.setMonth(expires.getMonth() + m);

  try {
    await pool.query(
      'INSERT INTO orders (customer_id, plan, expires_at, price_cents) VALUES ($1, $2, $3, $4)',
      [Number(customer_id), plan, expires.toISOString(), price]
    );
    res.redirect('/');
  } catch (e) {
    if (e.code === '23503') return res.status(400).send(layout('<p>customer_id does not exist.</p>'));
    console.error('POST /orders', e);
    res.status(500).send(layout('<p>Failed to create order.</p>'));
  }
});

const port = Number(process.env.PORT || 3000);
app.listen(port, () => console.log(`http://localhost:${port}`));
