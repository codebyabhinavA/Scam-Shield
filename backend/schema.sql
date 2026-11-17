CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  email TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE checks (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  message_text TEXT NOT NULL,
  risk_level TEXT NOT NULL CHECK (risk_level IN ('low', 'medium', 'high')),
  summary TEXT,
  next_steps TEXT,
  feedback TEXT CHECK (feedback IN ('scam', 'legit')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_checks_user_created ON checks (user_id, created_at DESC);

CREATE TABLE red_flags (
  id SERIAL PRIMARY KEY,
  check_id INTEGER NOT NULL REFERENCES checks(id) ON DELETE CASCADE,
  type TEXT NOT NULL,
  explanation TEXT NOT NULL
);
CREATE TABLE ai_usage (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_ai_usage_user_created ON ai_usage (user_id, created_at DESC);