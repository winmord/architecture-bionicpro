CREATE TABLE IF NOT EXISTS clientccs (
                                       id SERIAL PRIMARY KEY,
                                       email VARCHAR(255) NOT NULL,
                                       full_name VARCHAR(255),
                                       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS telemetry (
                                         id SERIAL PRIMARY KEY,
                                         client_id INTEGER REFERENCES clients(id),
                                         session_date DATE NOT NULL,
                                         gestures_count INTEGER DEFAULT 0,
                                         avg_confidence FLOAT DEFAULT 0,
                                         avg_battery FLOAT DEFAULT 0,
                                         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_telemetry_client_date ON telemetry(client_id, session_date);

INSERT INTO clients (email, full_name) VALUES
                                           ('ivan@bionicpro.ru', 'Иванов Иван'),
                                           ('petr@bionicpro.ru', 'Петров Петр'),
                                           ('maria@bionicpro.ru', 'Сидорова Мария'),
                                           ('alex@bionicpro.ru', 'Алексеев Алексей'),
                                           ('olga@bionicpro.ru', 'Ольгина Ольга');

INSERT INTO telemetry (client_id, session_date, gestures_count, avg_confidence, avg_battery)
SELECT
    client_id,
    CURRENT_DATE - (random() * 30)::int,
    (random() * 200)::int,
    random() * 100,
    random() * 100
FROM (
         SELECT id as client_id FROM clients
     ) clients
         CROSS JOIN generate_series(1, 10);  -- по 10 записей на клиента