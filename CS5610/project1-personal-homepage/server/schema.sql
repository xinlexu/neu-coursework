CREATE TABLE IF NOT EXISTS links (
  id SERIAL PRIMARY KEY,
  title TEXT NOT NULL,
  url TEXT NOT NULL,
  category TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS links_url_unique ON links(url);

CREATE TABLE IF NOT EXISTS guestbook (
  id SERIAL PRIMARY KEY,
  nickname TEXT NOT NULL,
  message TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT message_maxlen CHECK (char_length(message) <= 140)
);

INSERT INTO links (title, url, category) VALUES
  ('Week 2 – Assignment', 'https://example.com/cs5610/week2-assignment', 'CS5610'),
  ('Week 3 – Assignment', 'https://example.com/cs5610/week3-assignment', 'CS5610'),
  ('Week 4 – Assignment', 'https://example.com/cs5610/week4-assignment', 'CS5610'),
  ('Week 5 – Assignment', 'https://example.com/cs5610/week5-assignment', 'CS5610'),
  ('Project 1', 'https://example.com/cs5610/project1-personal-homepage', 'CS5610')
ON CONFLICT DO NOTHING;
