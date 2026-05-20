import express from 'express';
import path from 'path';
import { fileURLToPath } from 'url';
import dotenv from 'dotenv';
import pg from 'pg';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
dotenv.config({ path: path.join(__dirname, '.env') });

const { Pool } = pg;
const app = express();
const root = path.resolve(__dirname, '..');
const pool = new Pool();
const PORT = Number(process.env.PORT) || 3000;

app.use(express.json());
app.use('/assets', express.static(path.join(root, 'assets')));
app.use('/styles', express.static(path.join(root, 'styles')));
app.use('/scripts', express.static(path.join(root, 'scripts')));
app.use(express.static(path.join(root, 'public')));

app.get('/api/links', async (_req, res) => {
  try {
    const { rows } = await pool.query(
      'SELECT id, title, url, category FROM links ORDER BY category, id;'
    );
    res.json(rows);
  } catch {
    res.status(500).json({ error: 'db_error' });
  }
});

app.get('/api/guestbook', async (req, res) => {
  const limit = Math.min(Math.max(parseInt(req.query.limit || '50', 10), 1), 200);
  try {
    const { rows } = await pool.query(
      'SELECT id, nickname, message, created_at FROM guestbook ORDER BY created_at DESC LIMIT $1;',
      [limit]
    );
    res.json(rows);
  } catch {
    res.status(500).json({ error: 'db_error' });
  }
});

app.post('/api/guestbook', async (req, res) => {
  try {
    const nickname = String(req.body?.nickname || '').trim();
    const message = String(req.body?.message || '').trim();
    if (!nickname || !message) return res.status(400).json({ error: 'invalid_input' });
    if (message.length > 140) return res.status(400).json({ error: 'too_long' });

    const { rows } = await pool.query(
      'INSERT INTO guestbook (nickname, message) VALUES ($1, $2) RETURNING id, nickname, message, created_at;',
      [nickname, message]
    );
    res.status(201).json(rows[0]);
  } catch {
    res.status(500).json({ error: 'db_error' });
  }
});

app.get('/healthz', (_req, res) => res.json({ ok: true }));

app.listen(PORT, () => {
  console.log(`Project1 running at http://localhost:${PORT}`);
});
