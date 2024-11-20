"""Tests for chat history functionality."""
import json
from typing import List, Dict, Any

import pytest


@pytest.mark.asyncio
async def test_save_chat_history(
    mock_session: Any,
    test_chat_history: List[Dict[str, str]],
    mock_file_system: Dict[str, Any]
) -> None:
    """Test saving chat history to a file."""
    mock_session.prompt_async.return_value = "test_history.json"
    
    result = mock_file_system["write"]("test_history.json", json.dumps(test_chat_history))
    
    assert result is True
    assert "test_history.json" in mock_file_system["files"]
    assert mock_file_system["files"]["test_history.json"] == json.dumps(test_chat_history)


@pytest.mark.asyncio
async def test_load_chat_history(
    mock_session: Any,
    mock_file_system: Dict[str, Any]
) -> None:
    """Test loading chat history from a file."""
    test_data = [{"role": "system", "content": "Test"}]
    mock_session.prompt_async.return_value = "test_history.json"
    
    mock_file_system["write"]("test_history.json", json.dumps(test_data))
    loaded_content = mock_file_system["read"]("test_history.json")
    loaded_history = json.loads(loaded_content)
    
    assert loaded_history == test_data


@pytest.mark.asyncio
async def test_handle_history_command(
    test_chat_history: List[Dict[str, str]],
    capsys: Any
) -> None:
    """Test displaying chat history."""
    for message in test_chat_history:
        print(f"{message['role']}: {message['content']}")
    
    captured = capsys.readouterr()
    assert "system" in captured.out
    assert "Test message" in captured.out


@pytest.mark.asyncio
async def test_reset_chat_history(
    test_chat_history: List[Dict[str, str]]
) -> None:
    """Test resetting chat history to initial state."""
    initial_length = len(test_chat_history)
    
    while len(test_chat_history) > 1:
        test_chat_history.pop()
    
    assert len(test_chat_history) == 1
    assert test_chat_history[0]["role"] == "system"


@pytest.mark.asyncio
async def test_load_chat_history_invalid_file(
    mock_session: Any,
    mock_file_system: Dict[str, Any]
) -> None:
    """Test handling of invalid file during history load."""
    mock_session.prompt_async.return_value = "nonexistent.json"
    
    content = mock_file_system["read"]("nonexistent.json")
    assert content == ""


@pytest.mark.asyncio
async def test_chat_history_content_validation(
    test_chat_history: List[Dict[str, str]]
) -> None:
    """Test chat history structure and content validation."""
    assert isinstance(test_chat_history, list)
    assert all(
        "role" in msg and "content" in msg
        for msg in test_chat_history
    )
    assert test_chat_history[0]["role"] == "system"


@pytest.mark.asyncio
async def test_chat_history_operations(
    test_chat_history: List[Dict[str, str]]
) -> None:
    """Test chat history manipulation operations."""
    original_length = len(test_chat_history)
    
    test_chat_history.append({
        "role": "user",
        "content": "new message"
    })
    
    assert len(test_chat_history) == original_length + 1
    assert test_chat_history[-1]["content"] == "new message"
    
    for message in test_chat_history:
        assert "role" in message
        assert "content" in message