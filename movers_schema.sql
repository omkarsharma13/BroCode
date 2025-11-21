-- Add mover capability to drivers
ALTER TABLE drivers
  ADD COLUMN IF NOT EXISTS is_mover boolean DEFAULT false,
  ADD COLUMN IF NOT EXISTS vehicle_type varchar(50);

-- Moves table for packers & movers jobs
CREATE TABLE IF NOT EXISTS moves (
    move_id        SERIAL PRIMARY KEY,
    user_id        INTEGER NOT NULL REFERENCES users(user_id),
    driver_id      INTEGER REFERENCES drivers(driver_id),
    pickup_address TEXT NOT NULL,
    drop_address   TEXT NOT NULL,
    item_list      TEXT,
    vehicle_type   VARCHAR(50),
    helpers_needed INTEGER DEFAULT 1,
    packing_required boolean DEFAULT false,
    insurance_opted boolean DEFAULT false,
    package_type   VARCHAR(20) DEFAULT 'basic', -- basic / premium / white_glove
    photos         JSONB,
    inventory      JSONB,
    quote_breakdown JSONB,
    estimated_cost NUMERIC(10,2),
    status         VARCHAR(20) DEFAULT 'requested', -- requested/assigned/ongoing/completed/cancelled
    requested_at   TIMESTAMP DEFAULT NOW(),
    completed_at   TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_moves_status ON moves(status);

-- Optional feedback table
CREATE TABLE IF NOT EXISTS move_feedback (
    feedback_id SERIAL PRIMARY KEY,
    move_id INTEGER REFERENCES moves(move_id),
    rating INTEGER CHECK (rating BETWEEN 1 AND 5),
    tags TEXT,
    comment TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

