import pytest
# Add project root to path
import sys

from unittest.mock import MagicMock, AsyncMock
from pathlib import Path
project_root = Path(__file__).parent
sys.path.append(str(project_root))
import main


def test_show_current_model(capsys):
    main.DEFAULT_MODEL = "test/model:v1"
    main.show_current_model()
    captured = capsys.readouterr()
    assert "Current model: test/model:v1" in captured.out

@pytest.mark.asyncio
async def test_change_model(mock_session):
    main.DEFAULT_MODEL = "old/model:v1"
    mock_session.prompt_async.return_value = "new/model:v2"
    await main.change_model()
    assert main.DEFAULT_MODEL == "new/model:v2"

@pytest.mark.asyncio
async def test_model_persistence_in_chat(mock_openai_client, test_chat_history):
    main.DEFAULT_MODEL = "test/model:v1"
    main.client = mock_openai_client
    response = await main.get_streaming_response(test_chat_history, main.DEFAULT_MODEL)
    mock_openai_client.chat.completions.create.assert_called_once_with(
        model="test/model:v1",
        messages=test_chat_history,
        stream=True
    )

@pytest.mark.asyncio
async def test_model_validation(mock_openai_client, test_chat_history):
    main.DEFAULT_MODEL = ""
    main.client = mock_openai_client
    with pytest.raises(Exception):
        await main.get_streaming_response(test_chat_history, main.DEFAULT_MODEL)

@pytest.mark.asyncio
async def test_model_error_handling(mock_openai_client, test_chat_history):
    mock_openai_client.chat.completions.create.side_effect = Exception("Model error")
    main.client = mock_openai_client
    response = await main.get_streaming_response(test_chat_history, main.DEFAULT_MODEL)
    assert response is None

def test_default_model_initialization():
    assert hasattr(main, 'DEFAULT_MODEL')
    assert isinstance(main.DEFAULT_MODEL, str)
    assert len(main.DEFAULT_MODEL) > 0

def test_editor_model_consistency():
    assert hasattr(main, 'EDITOR_MODEL')
    assert isinstance(main.EDITOR_MODEL, str)