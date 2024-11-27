"""Test suite for model management functionality."""

import pytest
import pathlib 
# Add project root to path
import sys
project_root = pathlib.Path(__file__).parent
sys.path.append(str(project_root))
import main

from unittest.mock import  patch

def test_show_current_model(capsys):
    """Test that show_current_model displays correct model."""
    main.DEFAULT_MODEL = "test/model:v1"
    main.show_current_model()
    captured = capsys.readouterr()
    assert "Current model: test/model:v1" in captured.out


@pytest.mark.asyncio
async def test_change_model(mock_session):
    """Test model change functionality with mock session."""
    main.DEFAULT_MODEL = "old/model:v1"
    with patch('main.session', mock_session):
        mock_session.prompt_async.return_value = "new/model:v2"
        await main.change_model()
        assert main.DEFAULT_MODEL == "new/model:v2"
        mock_session.prompt_async.assert_called_once()


@pytest.mark.asyncio
async def test_change_model_error(mock_session):
    """Test model change error handling."""
    main.DEFAULT_MODEL = "old/model:v1"
    with patch('main.session', mock_session):
        mock_session.prompt_async.side_effect = EOFError
        await main.change_model()
        assert main.DEFAULT_MODEL == "old/model:v1"


@pytest.mark.asyncio
async def test_model_persistence_in_chat(mock_openai_client, test_chat_history):
    """Test that model persists throughout chat session."""
    original_client = main.client
    try:
        main.DEFAULT_MODEL = "test/model:v1"
        main.client = mock_openai_client
        await main.get_streaming_response(test_chat_history, main.DEFAULT_MODEL)
        
        mock_openai_client.chat.completions.create.assert_called_once_with(
            model="test/model:v1",
            messages=test_chat_history,
            stream=True
        )
    finally:
        main.client = original_client


@pytest.mark.asyncio
async def test_model_validation(mock_openai_client, test_chat_history):
    """Test that empty model name raises exception."""
    original_client = main.client
    try:
        main.DEFAULT_MODEL = ""
        main.client = mock_openai_client
        with pytest.raises(ValueError, match="Model name cannot be empty"):
            await main.get_streaming_response(test_chat_history, main.DEFAULT_MODEL)
    finally:
        main.client = original_client


@pytest.mark.asyncio
async def test_stream_response_handling(mock_openai_client, test_chat_history):
    """Test handling of streaming responses."""
    original_client = main.client
    try:
        main.client = mock_openai_client
        response = await main.get_streaming_response(test_chat_history, "test/model:v1")
        assert response is not None
        mock_openai_client.chat.completions.create.assert_called_once()
    finally:
        main.client = original_client


@pytest.mark.asyncio
async def test_model_error_handling(mock_openai_client, test_chat_history):
    """Test handling of OpenAI API errors."""
    original_client = main.client
    try:
        main.client = mock_openai_client
        mock_openai_client.chat.completions.create.side_effect = Exception("Model error")
        response = await main.get_streaming_response(test_chat_history, main.DEFAULT_MODEL)
        assert response is None
    finally:
        main.client = original_client


def test_default_model_initialization():
    """Test that DEFAULT_MODEL is properly initialized."""
    assert hasattr(main, 'DEFAULT_MODEL')
    assert isinstance(main.DEFAULT_MODEL, str)
    assert len(main.DEFAULT_MODEL) > 0


def test_editor_model_consistency():
    """Test that EDITOR_MODEL is properly defined."""