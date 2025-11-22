-- ===============================
--  CRIAÇÃO DO BANCO INICIAL
-- ===============================

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS rooms (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    room_id INTEGER NOT NULL REFERENCES rooms(id),
    sender_id INTEGER NOT NULL REFERENCES users(id),
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS files (
    id VARCHAR(36) PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    content_type VARCHAR(100),
    size_bytes INTEGER NOT NULL,
    checksum VARCHAR(64),
    storage_key VARCHAR(255) NOT NULL,
    uploader_id INTEGER NOT NULL REFERENCES users(id),
    room_id INTEGER NOT NULL REFERENCES rooms(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ===============================
--  DADOS INICIAIS
-- ===============================

INSERT INTO users (username)
VALUES ('user1'), ('user2'), ('user3')
ON CONFLICT DO NOTHING;

INSERT INTO rooms (name)
VALUES ('Sala Principal')
ON CONFLICT DO NOTHING;
