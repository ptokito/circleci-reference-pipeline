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

# Global flag to track database availability
DATABASE_AVAILABLE = False

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
    global DATABASE_AVAILABLE
    try:
        conn = get_db_connection()
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
        conn.close()
        DATABASE_AVAILABLE = True
        logger.info("Database initialized successfully")
    except Exception as e:
        DATABASE_AVAILABLE = False
        logger.warning(f"Database initialization failed: {e}")
        logger.warning("App will run without database functionality")

@app.route('/')
def index():
    """Homepage with navigation links"""
    db_status = "Connected" if DATABASE_AVAILABLE else "Not Available (Demo Mode)"
    
    return f'''
    <html>
        <head>
            <title>CircleCI Demo App</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                h1 {{ color: #333; }}
                a {{ color: #007cba; text-decoration: none; margin-right: 20px; }}
                a:hover {{ text-decoration: underline; }}
                .status {{ background: #f0f0f0; padding: 20px; border-radius: 5px; margin-top: 20px; }}
                .db-status {{ background: {'#d4edda' if DATABASE_AVAILABLE else '#f8d7da'}; 
                            color: {'#155724' if DATABASE_AVAILABLE else '#721c24'}; 
                            padding: 10px; border-radius: 5px; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <h1>CircleCI Demo Application</h1>
            <p>Welcome to the CircleCI reference pipeline demonstration!</p>
            
            <div class="db-status">
                <strong>Database Status:</strong> {db_status}
            </div>
            
            <div class="status">
                <h3>Available Endpoints:</h3>
                <p><a href="/health">Health Check</a> - Application and database status</p>
                <p><a href="/users">View Users</a> - List all users (JSON)</p>
                <p><strong>POST /users</strong> - Create new user (requires JSON: {{"name": "...", "email": "..."}})</p>
            </div>
            
            <div class="status">
                <h3>Pipeline Features Demonstrated:</h3>
                <ul>
                    <li>Custom Docker image built in CircleCI</li>
                    <li>PostgreSQL database integration with sidecar container</li>
                    <li>Automated testing with result collection</li>
                    <li>Conditional deployment (main branch only)</li>
                    <li>Artifact publishing to Heroku PaaS</li>
                    <li>Graceful handling of deployment environments</li>
                </ul>
            </div>
        </body>
    </html>
    '''

@app.route('/health')
def health_check():
    """Health check endpoint"""
    if not DATABASE_AVAILABLE:
        return jsonify({
            "status": "healthy", 
            "database": "not_available",
            "mode": "demo_without_database"
        }), 200
    
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute('SELECT 1')
        conn.close()
        return jsonify({"status": "healthy", "database": "connected"}), 200
    except Exception as e:
        return jsonify({"status": "healthy", "database": "error", "error": str(e)}), 200

@app.route('/users', methods=['GET'])
def get_users():
    """Get all users"""
    if not DATABASE_AVAILABLE:
        return jsonify({
            "users": [],
            "message": "Database not available - running in demo mode",
            "demo_users": [
                {"id": 1, "name": "Demo User 1", "email": "demo1@example.com"},
                {"id": 2, "name": "Demo User 2", "email": "demo2@example.com"}
            ]
        }), 200
    
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
    if not DATABASE_AVAILABLE:
        return jsonify({
            "message": "Database not available - user creation disabled in demo mode",
            "demo_mode": True
        }), 200
    
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
        # Try to initialize database, but don't fail if it's not available
        try:
            init_db()
        except Exception as e:
            logger.warning(f"Starting without database: {e}")
        
        port = int(os.environ.get('PORT', 8000))
        app.run(host='0.0.0.0', port=port, debug=False)