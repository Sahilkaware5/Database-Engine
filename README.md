# 🗄️ Database Engine

A complete database engine built with Python backend and TypeScript frontend.

## Features

- **Custom Storage Engine**: Page-based data storage with B-tree indexing
- **SQL Parser**: Support for SELECT, INSERT, CREATE TABLE, CREATE INDEX
- **REST API**: Flask-based API server with CORS support
- **Modern UI**: React frontend with shadcn/ui components
- **Real-time Stats**: Database statistics and performance insights

## Quick Start

### 1. Install Python Dependencies

\`\`\`bash
pip install flask flask-cors
\`\`\`

### 2. Start the Database Server

\`\`\`bash
python scripts/start_server.py
\`\`\`

The server will start on `http://localhost:5000` with sample data.

### 3. Start the Frontend

\`\`\`bash
npm run dev
\`\`\`

Open `http://localhost:3000` in your browser.

## API Endpoints

- `GET /api/health` - Health check
- `GET /api/tables` - List all tables
- `POST /api/sql` - Execute SQL query
- `GET /api/database/stats` - Database statistics
- `POST /api/tables` - Create new table
- `DELETE /api/tables/{name}` - Drop table

## Sample SQL Queries

\`\`\`sql
-- Select all users
SELECT * FROM users;

-- Filter by age
SELECT name, email FROM users WHERE age > 25;

-- Insert new user
INSERT INTO users (id, name, email, age) VALUES (6, 'New User', 'new@example.com', 30);

-- Create new table
CREATE TABLE orders (
  id INT,
  user_id INT,
  product VARCHAR(100),
  total FLOAT
);

-- Create index
CREATE INDEX idx_user_email ON users (email);
\`\`\`

## Architecture

- **Storage Engine**: Custom page-based storage with metadata persistence
- **SQL Parser**: Tokenizer and parser for SQL statement processing
- **API Layer**: Flask REST API with CORS support
- **Frontend**: Next.js with TypeScript and shadcn/ui components

## Troubleshooting

If you see connection errors:

1. Ensure Python server is running: `python scripts/start_server.py`
2. Check that port 5000 is not in use
3. Verify Flask and flask-cors are installed
4. Check browser console for detailed error messages

The frontend includes a connection test that will help diagnose issues.
