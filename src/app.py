#!/usr/bin/env python3

"""
Sample Flask application with PostgreSQL integration
Demonstrates CI/CD pipeline capabilities with database integration
"""

# IMPORT STATEMENTS
import os           # Operating system interface for environment variables
import sys          # System-specific parameters and functions
from flask import Flask, jsonify, request  # Web framework and utilities
import psycopg2                            # PostgreSQL database adapter
from psycopg2.extras import RealDictCursor # Returns query results as dictionaries
import logging                             # Logging functionality

# LOGGING CONFIGURATION
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Set up logging to INFO level for application monitoring and debugging

# FLASK APPLICATION INITIALIZATION
app = Flask(__name__)

# DATABASE CONFIGURATION
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://testuser:testpass@localhost:5432/testdb')
# Gets database connection string from environment variable
# Falls back to default local database if not set
# Format: postgresql://username:password@host:port/database

# GLOBAL APPLICATION STATE
DATABASE_AVAILABLE = False
# Tracks whether database connection is working
# Used to provide graceful degradation when database is unavailable

# DATABASE CONNECTION MANAGEMENT
def get_db_connection():
    """
    Get database connection with error handling
    Returns a PostgreSQL connection object with dictionary cursor
    """
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        # RealDictCursor returns rows as dictionaries instead of tuples
        # Makes it easier to work with query results
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise  # Re-raise exception to be handled by caller

# DATABASE INITIALIZATION AND SCHEMA SETUP
def init_db():
    """
    Initialize database schema and set global availability flag
    Creates the users table if it doesn't exist
    """
    global DATABASE_AVAILABLE
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # CREATE TABLE IF NOT EXISTS: Only creates table if it doesn't already exist
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,              -- Auto-incrementing primary key
                    name VARCHAR(100) NOT NULL,         -- Required user name
                    email VARCHAR(100) UNIQUE NOT NULL, -- Required unique email
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- Automatic timestamp
                )
            """)
        conn.commit()  # Commit the transaction
        conn.close()   # Close the connection
        DATABASE_AVAILABLE = True
        logger.info("Database initialized successfully")
    except Exception as e:
        DATABASE_AVAILABLE = False
        logger.warning(f"Database initialization failed: {e}")
        logger.warning("App will run without database functionality")
        # Graceful degradation: App continues without database instead of crashing

# ROUTE DEFINITIONS (URL ENDPOINTS)

@app.route('/')
def index():
    """
    Homepage with navigation links and pipeline information
    Returns HTML page showing application status and available endpoints
    """
    db_status = "Connected" if DATABASE_AVAILABLE else "Not Available (Demo Mode)"
    
    # Return HTML page with dynamic database status
    return f'''
    <html>
        <head>
            <title>CircleCI Demo App</title>
            <style>
                /* CSS styling for professional appearance */
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
            
            <!-- Dynamic database status indicator -->
            <div class="db-status">
                <strong>Database Status:</strong> {db_status}
            </div>
            
            <!-- Available API endpoints -->
            <div class="status">
                <h3>Available Endpoints:</h3>
                <p><a href="/health">Health Check</a> - Application and database status</p>
                <p><a href="/users">View Users</a> - List all users (JSON)</p>
                <p><strong>POST /users</strong> - Create new user (requires JSON: {{"name": "...", "email": "..."}})</p>
            </div>
            
            <!-- Pipeline features demonstration -->
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
    """
    Health check endpoint for monitoring and load balancers
    Returns JSON with application and database status
    """
    if not DATABASE_AVAILABLE:
        # Return healthy status even without database
        return jsonify({
            "status": "healthy", 
            "database": "not_available",
            "mode": "demo_without_database"
        }), 200
    
    try:
        # Test actual database connection
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute('SELECT 1')  # Simple query to test connection
        conn.close()
        return jsonify({"status": "healthy", "database": "connected"}), 200
    except Exception as e:
        # Return healthy app status but database error
        return jsonify({"status": "healthy", "database": "error", "error": str(e)}), 200

@app.route('/users', methods=['GET'])
def get_users():
    """
    Get all users from database
    Returns JSON list of users or demo data if database unavailable
    """
    if not DATABASE_AVAILABLE:
        # Return demo data when database is not available
        return jsonify({
            "users": [],
            "message": "Database not available - running in demo mode",
            "demo_users": [
                {"id": 1, "name": "Demo User 1", "email": "demo1@example.com"},
                {"id": 2, "name": "Demo User 2", "email": "demo2@example.com"}
            ]
        }), 200
    
    try:
        # Query real database for user data
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM users ORDER BY created_at DESC')
            users = cur.fetchall()  # Get all results as list of dictionaries
        conn.close()
        return jsonify({"users": users}), 200
    except Exception as e:
        logger.error(f"Failed to get users: {e}")
        return jsonify({"error": str(e)}), 500  # Internal server error

@app.route('/users', methods=['POST'])
def create_user():
    """
    Create a new user in the database
    Expects JSON: {"name": "...", "email": "..."}
    Returns success message or error
    """
    if not DATABASE_AVAILABLE:
        # Inform client that database operations are disabled
        return jsonify({
            "message": "Database not available - user creation disabled in demo mode",
            "demo_mode": True
        }), 200
    
    # Parse JSON data from request body
    data = request.get_json()
    
    # Validate required fields
    if not data or 'name' not in data or 'email' not in data:
        return jsonify({"error": "Name and email are required"}), 400  # Bad request
    
    try:
        # Insert new user into database
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                'INSERT INTO users (name, email) VALUES (%s, %s) RETURNING id',
                (data['name'], data['email'])  # Use parameterized query to prevent SQL injection
            )
            user_id = cur.fetchone()['id']  # Get the ID of newly created user
        conn.commit()  # Commit the transaction
        conn.close()
        
        return jsonify({"id": user_id, "message": "User created successfully"}), 201  # Created
    except psycopg2.IntegrityError:
        # Handle unique constraint violation (duplicate email)
        return jsonify({"error": "Email already exists"}), 409  # Conflict
    except Exception as e:
        logger.error(f"Failed to create user: {e}")
        return jsonify({"error": str(e)}), 500  # Internal server error

# APPLICATION ENTRY POINT
if __name__ == '__main__':
    # Handle command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == 'migrate':
        # Migration mode: just initialize database and exit
        init_db()
        print("Database migration completed")
    else:
        # Normal application startup
        try:
            init_db()  # Try to initialize database
        except Exception as e:
            logger.warning(f"Starting without database: {e}")
        
        # Get port from environment (required for Heroku deployment)
        port = int(os.environ.get('PORT', 8000))
        # Start Flask development server
        app.run(host='0.0.0.0', port=port, debug=False)
        # host='0.0.0.0': Accept connections from any IP (required for containers)
        # debug=False: Disable debug mode for production safety