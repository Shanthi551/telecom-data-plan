-- ---------------------------
-- Database: telecom
-- ---------------------------

-- Drop tables if they exist
DROP TABLE IF EXISTS purchases;
DROP TABLE IF EXISTS plans;
DROP TABLE IF EXISTS users;

-- ---------------------------
-- Table: users
-- ---------------------------
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    firstname TEXT NOT NULL,
    lastname TEXT NOT NULL,
    fullname TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    mobile TEXT,
    password TEXT NOT NULL,
    role TEXT DEFAULT 'Customer'
);

-- Insert an Admin user (default)
INSERT INTO users (firstname, lastname, fullname, email, mobile, password, role)
VALUES ('Admin', 'User', 'Admin User', 'admin@example.com', '9999999999', 'admin123', 'Admin');

-- ---------------------------
-- Table: plans
-- ---------------------------
CREATE TABLE plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    price REAL NOT NULL,
    validity_days INTEGER NOT NULL,
    data_limit TEXT
);

-- Insert some default plans
INSERT INTO plans (name, price, validity_days, data_limit) VALUES
('Basic Plan', 199.0, 30, '2GB/day'),
('Standard Plan', 399.0, 30, '5GB/day'),
('Premium Plan', 599.0, 30, '10GB/day');

-- ---------------------------
-- Table: purchases
-- ---------------------------
CREATE TABLE purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    plan_id INTEGER NOT NULL,
    purchase_date TEXT,
    expiry_date TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(plan_id) REFERENCES plans(id)
);

-- Optional: Insert sample purchase
INSERT INTO purchases (user_id, plan_id, purchase_date, expiry_date)
VALUES (1, 1, '2025-09-05', '2025-10-05');
