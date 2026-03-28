-- FlexiFees Database Schema
-- Run this in PostgreSQL to create all tables

-- Drop existing tables (if any)
DROP TABLE IF EXISTS payment_transactions CASCADE;
DROP TABLE IF EXISTS invoice_items CASCADE;
DROP TABLE IF EXISTS invoices CASCADE;
DROP TABLE IF EXISTS students CASCADE;
DROP TABLE IF EXISTS guardians CASCADE;
DROP TABLE IF EXISTS schools CASCADE;

-- Schools Table
CREATE TABLE schools (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    address TEXT,
    phone VARCHAR(20),
    email VARCHAR(100),
    mpesa_shortcode VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Guardians/Parents Table
CREATE TABLE guardians (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(20) NOT NULL,
    id_number VARCHAR(50),
    relationship VARCHAR(50),
    school_id INTEGER REFERENCES schools(id),
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Students Table
CREATE TABLE students (
    id SERIAL PRIMARY KEY,
    admission_number VARCHAR(50) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE,
    gender VARCHAR(10),
    class_name VARCHAR(50) NOT NULL,
    stream VARCHAR(20),
    guardian_id INTEGER REFERENCES guardians(id),
    school_id INTEGER REFERENCES schools(id),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Invoices Table
CREATE TABLE invoices (
    id SERIAL PRIMARY KEY,
    invoice_number VARCHAR(50) UNIQUE NOT NULL,
    student_id INTEGER REFERENCES students(id),
    guardian_id INTEGER REFERENCES guardians(id),
    school_id INTEGER REFERENCES schools(id),
    term VARCHAR(20),
    year INTEGER,
    total_amount DECIMAL(12, 2) NOT NULL,
    paid_amount DECIMAL(12, 2) DEFAULT 0,
    balance DECIMAL(12, 2) NOT NULL,
    due_date DATE,
    status VARCHAR(20) DEFAULT 'pending',
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Invoice Items Table
CREATE TABLE invoice_items (
    id SERIAL PRIMARY KEY,
    invoice_id INTEGER REFERENCES invoices(id) ON DELETE CASCADE,
    description VARCHAR(255) NOT NULL,
    quantity INTEGER DEFAULT 1,
    unit_price DECIMAL(12, 2) NOT NULL,
    total_price DECIMAL(12, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Payments Table (Main payment records)
CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    transaction_id VARCHAR(50) UNIQUE NOT NULL,
    checkout_request_id VARCHAR(100),
    merchant_request_id VARCHAR(100),
    invoice_id INTEGER REFERENCES invoices(id),
    student_id INTEGER REFERENCES students(id),
    guardian_id INTEGER REFERENCES guardians(id),
    school_id INTEGER REFERENCES schools(id),
    amount DECIMAL(12, 2) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    account_reference VARCHAR(100),
    transaction_description VARCHAR(255),
    status VARCHAR(20) DEFAULT 'pending',
    mpesa_receipt_number VARCHAR(50),
    result_code VARCHAR(10),
    result_desc VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Payment Transactions Table (for audit trail)
CREATE TABLE payment_transactions (
    id SERIAL PRIMARY KEY,
    payment_id INTEGER REFERENCES payments(id),
    action VARCHAR(50) NOT NULL,
    status_from VARCHAR(20),
    status_to VARCHAR(20),
    amount DECIMAL(12, 2),
    details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX idx_guardians_school ON guardians(school_id);
CREATE INDEX idx_students_admission ON students(admission_number);
CREATE INDEX idx_students_guardian ON students(guardian_id);
CREATE INDEX idx_students_school ON students(school_id);
CREATE INDEX idx_invoices_student ON invoices(student_id);
CREATE INDEX idx_invoices_number ON invoices(invoice_number);
CREATE INDEX idx_invoices_status ON invoices(status);
CREATE INDEX idx_payments_transaction ON payments(transaction_id);
CREATE INDEX idx_payments_checkout ON payments(checkout_request_id);
CREATE INDEX idx_payments_invoice ON payments(invoice_id);
CREATE INDEX idx_payments_status ON payments(status);
CREATE INDEX idx_payments_phone ON payments(phone);
CREATE INDEX idx_payment_transactions_payment ON payment_transactions(payment_id);

-- Insert sample data

-- Sample School
INSERT INTO schools (name, code, address, phone, email, mpesa_shortcode) VALUES
('Greenfield Academy', 'GFA', '123 Education Lane, Nairobi', '+254700123456', 'info@greenfield.edu', '174379');

-- Sample Guardians
INSERT INTO guardians (first_name, last_name, email, phone, id_number, relationship, school_id) VALUES
('John', 'Kamau', 'john.kamau@email.com', '254712345678', '12345678', 'Father', 1),
('Jane', 'Kamau', 'jane.kamau@email.com', '254723456789', '23456789', 'Mother', 1),
('Peter', 'Ochieng', 'peter.ochieng@email.com', '254734567890', '34567890', 'Father', 1);

-- Sample Students
INSERT INTO students (admission_number, first_name, last_name, date_of_birth, gender, class_name, stream, guardian_id, school_id) VALUES
('GFA001', 'Alice', 'Kamau', '2010-03-15', 'Female', 'Grade 4', 'A', 1, 1),
('GFA002', 'Brian', 'Kamau', '2008-07-22', 'Male', 'Grade 6', 'A', 1, 1),
('GFA003', 'Catherine', 'Ochieng', '2009-11-08', 'Female', 'Grade 5', 'B', 3, 1);

-- Sample Invoices
INSERT INTO invoices (invoice_number, student_id, guardian_id, school_id, term, year, total_amount, paid_amount, balance, due_date, status, description) VALUES
('INV-2026-001', 1, 1, 1, 'Term 1', 2026, 45000.00, 0, 45000.00, '2026-02-28', 'pending', 'Grade 4 Term 1 Fees'),
('INV-2026-002', 2, 1, 1, 'Term 1', 2026, 52000.00, 0, 52000.00, '2026-02-28', 'pending', 'Grade 6 Term 1 Fees'),
('INV-2026-003', 3, 3, 1, 'Term 1', 2026, 48000.00, 0, 48000.00, '2026-02-28', 'pending', 'Grade 5 Term 1 Fees');

-- Sample Invoice Items
INSERT INTO invoice_items (invoice_id, description, quantity, unit_price, total_price) VALUES
(1, 'Tuition Fee', 1, 35000.00, 35000.00),
(1, 'Boarding Fee', 1, 8000.00, 8000.00),
(1, 'Activity Fee', 1, 2000.00, 2000.00),
(2, 'Tuition Fee', 1, 40000.00, 40000.00),
(2, 'Boarding Fee', 1, 10000.00, 10000.00),
(2, 'Activity Fee', 1, 2000.00, 2000.00),
(3, 'Tuition Fee', 1, 38000.00, 38000.00),
(3, 'Boarding Fee', 1, 8000.00, 8000.00),
(3, 'Activity Fee', 1, 2000.00, 2000.00);

-- Verify data
SELECT 'Schools:' as table_name, count(*) as count FROM schools
UNION ALL SELECT 'Guardians:', count(*) FROM guardians
UNION ALL SELECT 'Students:', count(*) FROM students
UNION ALL SELECT 'Invoices:', count(*) FROM invoices
UNION ALL SELECT 'Invoice Items:', count(*) FROM invoice_items;
