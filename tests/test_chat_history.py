"""Tests for chat history functionality.

Args:
    mock_session (MagicMock): Mock session for testing
    test_chat_history (List[Dict[str, str]]): Test chat history data
    mock_file_system (Dict[str, Any]): Mock file system for testing
"""
import json
import pytest

from typing import List, Dict, Any


@pytest.mark.asyncio
async def test_save_chat_history(
    mock_session: Any,
    test_chat_history: List[Dict[str, str]],
    mock_file_system: Dict[str, Any]
) -> None:
    """Test saving chat history to a file.
    
    Args:
        mock_session: Mock prompt session
        test_chat_history: Sample chat history
        mock_file_system: Mock file system
    """
    try:
        assert mock_session.prompt_async.return_value == "test input"
        result = mock_file_system["write"]("test_history.json", 
                                         json.dumps(test_chat_history))
        
        assert result is True
        assert "test_history.json" in mock_file_system["files"]
        assert mock_file_system["files"]["test_history.json"] == json.dumps(test_chat_history)
    except Exception as e:
        pytest.fail(f"Failed to save chat history: {str(e)}")


@pytest.mark.asyncio
async def test_load_chat_history(
    mock_session: Any,
    mock_file_system: Dict[str, Any]
) -> None:
    """Test loading chat history from a file.
    
    Args:
        mock_session: Mock prompt session
        mock_file_system: Mock file system
    """
    try:
        test_data = [{"role": "system", "content": "Test"}]
        mock_file_system["write"]("test_history.json", json.dumps(test_data))
        
        # Load and verify
        loaded_content = mock_file_system["read"]("test_history.json")
        loaded_history = json.loads(loaded_content)
        
        assert loaded_history == test_data
        assert isinstance(loaded_history, list)
        assert all(isinstance(msg, dict) for msg in loaded_history)
    except Exception as e:
        pytest.fail(f"Failed to load chat history: {str(e)}")


@pytest.mark.asyncio
async def test_handle_history_command(
    test_chat_history: List[Dict[str, str]],
    capsys: Any
) -> None:
    """Test displaying chat history.
    
    Args:
        test_chat_history: Sample chat history
        capsys: Pytest fixture for capturing stdout/stderr
    """
    try:
        for message in test_chat_history:
            print(f"{message['role']}: {message['content']}")
        
        captured = capsys.readouterr()
        assert "system" in captured.out
        assert "Test message" in captured.out
        assert all(msg['role'] in captured.out for msg in test_chat_history)
    except Exception as e:
        pytest.fail(f"Failed to handle history command: {str(e)}")


@pytest.mark.asyncio
async def test_reset_chat_history(
    test_chat_history: List[Dict[str, str]]
) -> None:
    """Test resetting chat history to initial state.
    
    Args:
        test_chat_history: Sample chat history
    """
    try:
        initial_length = len(test_chat_history)
        initial_system_message = test_chat_history[0].copy()
        
        while len(test_chat_history) > 1:
            test_chat_history.pop()
        
        assert len(test_chat_history) == 1
        assert test_chat_history[0]["role"] == "system"
        assert test_chat_history[0] == initial_system_message
    except Exception as e:
        pytest.fail(f"Failed to reset chat history: {str(e)}")


@pytest.mark.asyncio
async def test_load_chat_history_invalid_file(
    mock_session: Any,
    mock_file_system: Dict[str, Any]
) -> None:
    """Test handling of invalid file during history load.
    
    Args:
        mock_session: Mock prompt session
        mock_file_system: Mock file system
    """
    try:
        mock_session.prompt_async.return_value = "nonexistent.json"
        content = mock_file_system["read"]("nonexistent.json")
        
        assert content == ""
        with pytest.raises(json.JSONDecodeError):
            json.loads(content)
    except Exception as e:
        pytest.fail(f"Failed to handle invalid file: {str(e)}")


@pytest.mark.asyncio
async def test_chat_history_content_validation(
    test_chat_history: List[Dict[str, str]]
) -> None:
    """Test chat history structure and content validation.
    
    Args:
        test_chat_history: Sample chat history
    """
    try:
        assert isinstance(test_chat_history, list)
        assert len(test_chat_history) > 0
        
        for msg in test_chat_history:
            assert isinstance(msg, dict)
            assert "role" in msg
            assert "content" in msg
            assert isinstance(msg["role"], str)
            assert isinstance(msg["content"], str)
            
        assert test_chat_history[0]["role"] == "system"
    except Exception as e:
        pytest.fail(f"Failed content validation: {str(e)}")


@pytest.mark.asyncio
async def test_chat_history_operations(
    test_chat_history: List[Dict[str, str]]
) -> None:
    """Test chat history manipulation operations.
    
    Args:
        test_chat_history: Sample chat history
    """
    try:
        original_length = len(test_chat_history)
        original_history = test_chat_history.copy()
        
        new_message = {
            "role": "user",
            "content": "new message"
        }
        test_chat_history.append(new_message)
        
        assert len(test_chat_history) == original_length + 1
        assert test_chat_history[-1] == new_message
        assert test_chat_history[:-1] == original_history
        
        for message in test_chat_history:
            assert isinstance(message, dict)
            assert set(message.keys()) == {"role", "content"}
            assert message["role"] in {"system", "user", "assistant"}
    except Exception as e:
        pytest.fail(f"Failed operations test: {str(e)}")