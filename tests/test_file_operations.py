"""Test file operations functionality."""
import main
import pytest
from unittest.mock import patch, mock_open
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
import sys
sys.path.append(str(project_root))
from main import read_file_content, write_file_content, is_text_file


@pytest.mark.parametrize("filename,expected_content", [
    ("test.py", "print('hello')"),
    ("test.txt", "Hello World")
])
def test_read_file_content_success(mock_file_system, filename, expected_content):
    """Test successful file reading."""
    with patch('builtins.open', mock_open(read_data=mock_file_system['files'][filename])):
        content = read_file_content(filename)
        assert content == expected_content 


@pytest.mark.parametrize("error,expected_message", [
    (FileNotFoundError(), "Error: File not found"),
    (PermissionError(), "Error reading")
    ])
def test_read_file_content_errors(error, expected_message):
    """Test file reading error conditions"""
    # Test non-existent file
    with patch('builtins.open', mock_open()) as mock_file:
        mock_file.side_effect = error
        result = read_file_content("test.txt")
        assert expected_message in result
    # Test permission error
    with patch('builtins.open', mock_open()) as mock_file:
        mock_file.side_effect = PermissionError()
        result = read_file_content("protected.txt")
        assert "Error reading" in result


def test_write_file_content_success(mock_write, mock_file_system):
    """Test successful file writing."""
    test_cases = [
        ("new_file.txt", "New content"),
        ("test.py", "Updated content")
    ]
    for filename, content in test_cases:
        success = write_file_content(filename, content)
        assert success is True
        #Verify that content has written to the mock file system
        assert mock_file_system['files'][filename] == content

def test_write_file_content_errors():
    """Test file writing error conditions"""
    # Test permission error
    with patch('builtins.open', mock_open()) as mock_file:
        mock_file.side_effect = PermissionError()
        success = write_file_content("protected.txt", "content")
        assert success is False
    
    # Test directory doesn't exist
    with patch('builtins.open', mock_open()) as mock_file:
        mock_file.side_effect = FileNotFoundError()
        success = write_file_content("nonexistent/file.txt", "content")
        assert success is False

def test_is_text_file():
    """Test text file validation"""
    # Create mock file contents
    text_content = b"Hello, this is text content\n"
    binary_content = b"\x00\x01\x02\x03"
    
    # Test text file
    with patch('builtins.open', mock_open(read_data=text_content)):
        assert is_text_file("text.txt") is True
    
    # Test binary file
    with patch('builtins.open', mock_open(read_data=binary_content)):
        assert is_text_file("binary.bin") is False

def test_file_operations_edge_cases(mock_write, special_chars):
    """Test edge cases in file operations."""
    # Test empty file
    with patch('main.open', mock_open(read_data="")):
        content = read_file_content("empty.txt")
        assert content == ""
    
    # Test very large content
    large_content = "x" * 1000000
    success = write_file_content("large.txt", large_content)
    assert success is True
    mock_write().write.assert_called_with(large_content)
    
    # Test special characters
    success = write_file_content("special.txt", special_chars)
    assert success is True
    mock_write().write.assert_called_with(special_chars)


def test_file_operations_integration(mock_write, mock_file_system):
    """Test file operations working together."""
    test_content = "Test content"
    updated_content = "Updated content"
    test_filename = "test_integration.txt"
    
    # Test write operation
    success = write_file_content(test_filename, test_content)
    assert success is True
    mock_write().write.assert_called_with(test_content)
    
    # Update mock_file_system to reflect written content
    mock_file_system['files'][test_filename] = test_content
    
    # Test read operation
    with patch('builtins.open', mock_open(read_data=test_content)):
        read_content = read_file_content(test_filename)
        assert read_content == test_content
    
    # Test update operation
    success = write_file_content(test_filename, updated_content)
    assert success is True
    mock_write().write.assert_called_with(updated_content)
    
    # Update mock_file_system and verify final state
    mock_file_system['files'][test_filename] = updated_content
    with patch('builtins.open', mock_open(read_data=updated_content)):
        final_content = read_file_content(test_filename)
        assert final_content == updated_content
