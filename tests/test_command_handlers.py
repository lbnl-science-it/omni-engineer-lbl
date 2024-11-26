import pytest
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))
from main import (
    handle_add_command,
    handle_edit_command,
    handle_new_command,
    handle_search_command,
    handle_image_command
)
from unittest.mock import patch, MagicMock, AsyncMock

@pytest.mark.asyncio
async def test_handle_add_command(mock_file_system, test_chat_history):
    """Test the add command with both existing and non-existing files."""
    with patch('main.read_file_content', mock_file_system['read']), \
         patch('main.os.path.isfile', return_value=True):
        initial_length = len(test_chat_history)
        result = await handle_add_command(test_chat_history, "test.py")
        assert len(result) == initial_length + 1
        assert "test.py" in result[-1]["content"]
        assert "print('hello')" in result[-1]["content"]

    # Test adding non-existent file
    with patch('main.os.path.isfile', return_value=False):
        with patch('main.os.path.isdir', return_value=False):
            original_length = len(test_chat_history)
            result = await handle_add_command(test_chat_history, "nonexistent.py")
            assert len(result) == original_length

@pytest.mark.asyncio
async def test_handle_edit_command(
    mock_file_system,
    mock_session,
    test_chat_history,
    mock_openai_client
):
    """Test the edit command with proper mocking of file system and OpenAI client."""
    with patch('main.read_file_content', mock_file_system['read']):
        with patch('main.write_file_content', mock_file_system['write']):
            with patch('main.client', mock_openai_client):
                with patch('main.session', mock_session):
                    editor_history = [{"role": "system", "content": "Editor prompt"}]
                    result_default, result_editor = await handle_edit_command(
                        test_chat_history,
                        editor_history,
                        ["test.py"]
                    )
                    assert len(result_default) > len(test_chat_history)
                    assert len(result_editor) > 1

@pytest.mark.asyncio
async def test_handle_new_command(mock_session, test_chat_history):
    """Test the new command for creating new files."""
    with patch('main.os.path.isfile', return_value=False):
        with patch('builtins.open', MagicMock()):
            with patch('main.session', mock_session):
                editor_history = [{"role": "system", "content": "Editor prompt"}]
                result_default, result_editor = await handle_new_command(
                    test_chat_history,
                    editor_history,
                    ["new_test.py"]
                )
                assert len(result_default) == len(test_chat_history)
                assert len(result_editor) == len(editor_history)

@pytest.mark.asyncio
async def test_handle_search_command(mock_session, test_chat_history):
    """Test the search command with mocked search results."""
    mock_search = AsyncMock(return_value=[
        {"title": "Test Result", "body": "Test content"}
    ])
    
    with patch('main.aget_results', mock_search), \
         patch('main.session', mock_session):
        initial_length = len(test_chat_history)
        result = await handle_search_command(test_chat_history)
        assert len(result) == initial_length + 1
        assert "Search results" in result[-1]["content"]

@pytest.mark.asyncio
async def test_handle_image_command(mock_image_processing, test_chat_history):
    """Test the image command with both local and URL-based images."""
    initial_length = len(test_chat_history)
    
    # Test local image
    with patch('main.encode_image', mock_image_processing['encode']), \
         patch('main.validate_image_url', mock_image_processing['validate']), \
         patch('main.os.path.exists', return_value=True):
        result = await handle_image_command(
            ["local_image.jpg"],
            test_chat_history
        )
        assert len(result) == initial_length + 1

@pytest.mark.asyncio
async def test_handle_image_command_errors(mock_image_processing, test_chat_history):
    """Test image command error handling."""
    with patch('main.encode_image', side_effect=Exception("Test error")), \
         patch('main.os.path.exists', return_value=True):
        result = await handle_image_command(
            ["bad_image.jpg"],
            test_chat_history
        )
        assert len(result) == len(test_chat_history)

@pytest.mark.asyncio
async def test_handle_commands_with_invalid_input(test_chat_history):
    """Test command handlers with invalid or empty inputs."""
    # Test add command with empty path
    result = await handle_add_command(test_chat_history)
    assert len(result) == len(test_chat_history)

    # Test edit command with empty path
    editor_history = [{"role": "system", "content": "Editor prompt"}]
    result_default, result_editor = await handle_edit_command(
        test_chat_history,
        editor_history,
        []
    )
    assert len(result_default) == len(test_chat_history)
    assert len(result_editor) == len(editor_history)