"""
Test suite for the Flask application
"""

import pytest
import json
import os
from unittest.mock import patch, MagicMock
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, init_db

@pytest.fixture
def client():
    """Test client fixture"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def mock_db():
    """Mock database fixture"""
    with patch('app.get_db_connection') as mock_conn:
        mock_cursor = MagicMock()
        mock_conn.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        yield mock_cursor

def test_health_check_success(client, mock_db):
    """Test successful health check"""
    mock_db.execute.return_value = None
    
    response = client.get('/health')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['status'] == 'healthy'
    assert data['database'] == 'connected'

def test_health_check_failure(client):
    """Test health check with database failure"""
    with patch('app.get_db_connection', side_effect=Exception('DB Error')):
        response = client.get('/health')
        assert response.status_code == 500
        
        data = json.loads(response.data)
        assert data['status'] == 'unhealthy'

def test_get_users_empty(client, mock_db):
    """Test getting users when none exist"""
    mock_db.fetchall.return_value = []
    
    response = client.get('/users')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['users'] == []

def test_get_users_with_data(client, mock_db):
    """Test getting users with existing data"""
    mock_users = [
        {'id': 1, 'name': 'John Doe', 'email': 'john@example.com'},
        {'id': 2, 'name': 'Jane Smith', 'email': 'jane@example.com'}
    ]
    mock_db.fetchall.return_value = mock_users
    
    response = client.get('/users')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert len(data['users']) == 2
    assert data['users'] == mock_users

def test_create_user_success(client, mock_db):
    """Test successful user creation"""
    mock_db.fetchone.return_value = {'id': 1}
    
    user_data = {
        'name': 'Test User',
        'email': 'test@example.com'
    }
    
    response = client.post('/users', 
                          data=json.dumps(user_data),
                          content_type='application/json')
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['id'] == 1
    assert 'created successfully' in data['message']

def test_create_user_missing_data(client):
    """Test user creation with missing data"""
    user_data = {'name': 'Test User'}  # Missing email
    
    response = client.post('/users',
                          data=json.dumps(user_data),
                          content_type='application/json')
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'required' in data['error']

def test_create_user_duplicate_email(client, mock_db):
    """Test user creation with duplicate email"""
    import psycopg2
    mock_db.execute.side_effect = psycopg2.IntegrityError('Duplicate email')
    
    user_data = {
        'name': 'Test User',
        'email': 'existing@example.com'
    }
    
    response = client.post('/users',
                          data=json.dumps(user_data),
                          content_type='application/json')
    
    assert response.status_code == 409
    data = json.loads(response.data)
    assert 'already exists' in data['error']
