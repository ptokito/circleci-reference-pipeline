"""
Test suite for the Flask application
This file contains automated tests that validate the REST API endpoints
work correctly under various scenarios including success and failure cases.
"""

import pytest
import json
import sys
import os
from unittest.mock import patch, MagicMock

# IMPORT PATH SETUP
# Add the 'src' directory to Python's module search path so we can import our Flask app
# This is necessary because the test file is in the project root, but the app is in src/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
import app

# TEST FIXTURES
# Fixtures are reusable components that set up test environments

@pytest.fixture
def client():
    """
    Test client fixture - Creates a Flask test client for making HTTP requests
    This allows us to test API endpoints without running a real web server
    """
    app.app.config['TESTING'] = True  # Enable Flask testing mode
    with app.app.test_client() as client:
        yield client  # Provide the test client to test functions

@pytest.fixture
def mock_db():
    """
    Mock database fixture - Replaces real database connections with fake ones
    This prevents tests from needing a real PostgreSQL database
    and makes tests faster and more predictable
    """
    # Replace the real database connection function with a mock
    with patch('app.get_db_connection') as mock_conn:
        mock_cursor = MagicMock()  # Create a fake database cursor
        # Set up the mock to behave like a real database connection
        mock_conn.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        yield mock_cursor  # Provide the mock cursor to test functions

# TEST FUNCTIONS
# Each function tests a specific scenario of the API

def test_health_check_success(client, mock_db):
    """
    Test the /health endpoint when everything is working correctly
    Verifies the API returns a 200 status and correct JSON response
    """
    # Configure the mock database to simulate successful connection
    mock_db.execute.return_value = None
    
    # Make an HTTP GET request to the health endpoint
    response = client.get('/health')
    assert response.status_code == 200  # Verify successful HTTP status
    
    # Parse the JSON response and verify its contents
    data = json.loads(response.data)
    assert data['status'] == 'healthy'
    assert data['database'] == 'connected'

def test_health_check_failure(client):
    """
    Test the /health endpoint when database connection fails
    Verifies the API handles errors gracefully and returns appropriate status
    """
    # Mock the database connection to raise an exception (simulating failure)
    with patch('app.get_db_connection', side_effect=Exception('DB Error')):
        response = client.get('/health')
        assert response.status_code == 500  # Verify error HTTP status
        
        # Verify the error response contains expected information
        data = json.loads(response.data)
        assert data['status'] == 'unhealthy'

def test_get_users_empty(client, mock_db):
    """
    Test the /users GET endpoint when no users exist in the database
    Verifies the API returns an empty list correctly
    """
    # Configure mock database to return no users
    mock_db.fetchall.return_value = []
    
    # Make request and verify response
    response = client.get('/users')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['users'] == []  # Verify empty user list

def test_create_user_success(client, mock_db):
    """
    Test the /users POST endpoint for successful user creation
    Verifies the API can create new users and return proper confirmation
    """
    # Configure mock database to simulate successful user creation
    mock_db.fetchone.return_value = {'id': 1}  # Mock returning new user ID
    
    # Prepare test data for user creation
    user_data = {
        'name': 'Test User',
        'email': 'test@example.com'
    }
    
    # Make POST request with JSON data
    response = client.post('/users', 
                          data=json.dumps(user_data),  # Convert to JSON string
                          content_type='application/json')  # Set proper content type
    
    # Verify successful creation response
    assert response.status_code == 201  # 201 = Created
    data = json.loads(response.data)
    assert data['id'] == 1  # Verify returned user ID
    assert 'created successfully' in data['message']  # Verify success message

def test_create_user_missing_data(client):
    """
    Test the /users POST endpoint with incomplete data
    Verifies the API properly validates input and rejects invalid requests
    """
    # Send incomplete user data (missing required email field)
    user_data = {'name': 'Test User'}  # Missing email
    
    response = client.post('/users',
                          data=json.dumps(user_data),
                          content_type='application/json')
    
    # Verify the API rejects the invalid request
    assert response.status_code == 400  # 400 = Bad Request
    data = json.loads(response.data)
    assert 'required' in data['error']  # Verify error message mentions required fields