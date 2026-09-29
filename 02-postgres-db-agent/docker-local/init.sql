-- Sample database schema for Bedrock Agent demo
CREATE TABLE IF NOT EXISTS employees (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    department VARCHAR(50),
    salary DECIMAL(10, 2),
    hire_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    budget DECIMAL(12, 2),
    start_date DATE,
    end_date DATE,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample data
INSERT INTO employees (name, email, department, salary, hire_date) VALUES
    ('John Doe', 'john.doe@example.com', 'Engineering', 85000.00, '2022-01-15'),
    ('Jane Smith', 'jane.smith@example.com', 'Marketing', 75000.00, '2022-03-20'),
    ('Bob Johnson', 'bob.johnson@example.com', 'Engineering', 95000.00, '2021-11-10'),
    ('Alice Williams', 'alice.williams@example.com', 'Sales', 80000.00, '2023-02-01'),
    ('Charlie Brown', 'charlie.brown@example.com', 'HR', 70000.00, '2022-06-15');

INSERT INTO projects (name, description, budget, start_date, end_date, status) VALUES
    ('Website Redesign', 'Complete overhaul of company website', 50000.00, '2024-01-01', '2024-06-30', 'active'),
    ('Mobile App', 'New mobile application for customers', 150000.00, '2024-03-01', '2024-12-31', 'active'),
    ('Data Migration', 'Migrate legacy systems to cloud', 75000.00, '2023-09-01', '2024-02-28', 'completed'),
    ('AI Integration', 'Integrate AI features into products', 200000.00, '2024-06-01', '2025-06-30', 'active');
