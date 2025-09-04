#!/usr/bin/env python3
"""
Sample Flask application with PostgreSQL integration
"""

import os
import sys
from flask import Flask, jsonify, request
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Database configuration
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://testuser:testpass@localhost:5432/testdb')

def get_db_connection():
    """Get database connection"""
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise

def init_db():
    """Initialize database schema"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        conn.commit()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    finally:
        conn.close()

@app.route('/')
def index():
    """Homepage with navigation links"""
    return '''
    <html>
        <head>
            <title>CircleCI Demo App</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                h1 { color: #333; }
                a { color: #007cba; text-decoration: none; margin-right: 20px; }
                a:hover { text-decoration: underline; }
                .status { background: #f0f0f0; padding: 20px; border-radius: 5px; margin-top: 20px; }
            </style>
        </head>
        <body>
            <h1>CircleCI Demo Application</h1>
            <p>Welcome to the CircleCI reference pipeline demonstration!</p>
            
            <div class="status">
                <h3>Available Endpoints:</h3>
                <p><a href="/health">Health Check</a> - Application and database status</p>
                <p><a href="/users">View Users</a> - List all users (JSON)</p>
                <p><strong>POST /users</strong> - Create new user (requires JSON: {"name": "...", "email": "..."})</p>
            </div>
            
            <div class="status">
                <h3>Pipeline Features Demonstrated:</h3>
                <ul>
                    <li>Custom Docker image built in CircleCI</li>
                    <li>PostgreSQL database integration with sidecar container</li>
                    <li>Automated testing with result collection</li>
                    <li>Conditional deployment (main branch only)</li>
                    <li>Artifact publishing to Heroku PaaS</li>
                </ul>
            </div>
        </body>
    </html>
    '''

@app.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute('SELECT 1')
        conn.close()
        return jsonify({"status": "healthy", "database": "connected"}), 200
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

@app.route('/users', methods=['GET'])
def get_users():
    """Get all users"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM users ORDER BY created_at DESC')
            users = cur.fetchall()
        conn.close()
        return jsonify({"users": users}), 200
    except Exception as e:
        logger.error(f"Failed to get users: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/users', methods=['POST'])
def create_user():
    """Create a new user"""
    data = request.get_json()
    
    if not data or 'name' not in data or 'email' not in data:
        return jsonify({"error": "Name and email are required"}), 400
    
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                'INSERT INTO users (name, email) VALUES (%s, %s) RETURNING id',
                (data['name'], data['email'])
            )
            user_id = cur.fetchone()['id']
        conn.commit()
        conn.close()
        
        return jsonify({"id": user_id, "message": "User created successfully"}), 201
    except psycopg2.IntegrityError:
        return jsonify({"error": "Email already exists"}), 409
    except Exception as e:
        logger.error(f"Failed to create user: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'migrate':
        init_db()
        print("Database migration completed")
    else:
        init_db()
        port = int(os.environ.get('PORT', 8000))
        app.run(host='0.0.0.0', port=port, debug=False)