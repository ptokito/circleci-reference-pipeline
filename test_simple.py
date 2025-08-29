"""
Simple test to verify our setup works
"""

import pytest
import sys
import os

def test_python_works():
    """Test that Python and pytest work"""
    assert True

def test_can_import_json():
    """Test basic imports work"""
    import json
    data = {"test": "value"}
    assert json.dumps(data) == '{"test": "value"}'

def test_mock_works():
    """Test that mocking works"""
    from unittest.mock import MagicMock
    mock = MagicMock()
    mock.return_value = 42
    assert mock() == 42
