import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from io import BytesIO
from PIL import Image
import base64
import requests
import sys

from pathlib import Path 
project_root = Path(__file__).parent
sys.path.append(str(project_root))
import main

@pytest.mark.asyncio
async def test_handle_search_command(mock_session, test_chat_history):
    mock_search_results = AsyncMock(return_value=[
        {"title": "Test Result", "body": "Test content"}
    ])
    with patch('main.aget_results', mock_search_results):
        mock_session.prompt_async.return_value = "test query"
        result_history = await main.handle_search_command(test_chat_history)
        
        mock_search_results.assert_called_once_with("test query")
        assert len(result_history) > len(test_chat_history)
        assert "Test Result" in result_history[-1]["content"]

@pytest.mark.asyncio
async def test_search_results_storage():
    mock_session = MagicMock()
    mock_session.prompt_async = AsyncMock(return_value="test query")
    mock_results = AsyncMock(return_value=[
        {"title": "Test", "body": "Content"}
    ])
    
    with patch('main.aget_results', mock_results), \
         patch('main.session', mock_session):
        initial_searches = len(main.stored_searches)
        await main.handle_search_command([])
        assert len(main.stored_searches) == initial_searches + 1
        mock_results.assert_called_once()

def test_validate_image_url():
    mock_response = MagicMock()
    mock_response.headers = {'Content-Type': 'image/jpeg'}
    mock_response.content = BytesIO(b'fake-image-data').getvalue()
    
    with patch('requests.get', return_value=mock_response):
        assert main.validate_image_url("https://example.com/image.jpg") is True
    
    with patch('requests.get', side_effect=requests.exceptions.RequestException):
        assert main.validate_image_url("invalid-url") is False

@pytest.mark.asyncio
async def test_handle_image_command(test_chat_history):
    mock_response = MagicMock()
    mock_response.headers = {'Content-Type': 'image/jpeg'}
    mock_response.content = BytesIO(b'fake-image-data').getvalue()
    
    with patch('requests.get', return_value=mock_response), \
         patch('PIL.Image.open') as mock_image:
        mock_image.return_value = MagicMock(format='JPEG')
        mock_image.return_value.__enter__ = MagicMock(return_value=mock_image.return_value)
        mock_image.return_value.__exit__ = MagicMock(return_value=None)
        
        test_urls = ["https://example.com/image.jpg"]
        result_history = await main.handle_image_command(test_urls, test_chat_history)
        assert len(result_history) > len(test_chat_history)
        assert "image_url" in result_history[-1]["content"][0]

@pytest.mark.asyncio
async def test_local_image_processing():
    fake_image_data = BytesIO()
    test_image = Image.new('RGB', (100, 100), color='red')
    test_image.save(fake_image_data, format='PNG')
    
    with patch('builtins.open', return_value=BytesIO(fake_image_data.getvalue())), \
         patch('PIL.Image.open') as mock_image:
        mock_image.return_value = MagicMock(format='PNG')
        mock_image.return_value.__enter__ = MagicMock(return_value=mock_image.return_value)
        mock_image.return_value.__exit__ = MagicMock(return_value=None)
        
        encoded = main.encode_image("test.png")
        assert encoded is not None
        assert isinstance(encoded, str)
        assert len(encoded) > 0

@pytest.mark.asyncio
async def test_invalid_image_handling(test_chat_history):
    mock_error = MagicMock(side_effect=requests.exceptions.RequestException)
    with patch('requests.get', mock_error):
        invalid_paths = ["https://example.com/nonexistent.jpg"]
        result_history = await main.handle_image_command(invalid_paths, test_chat_history)
        assert result_history == test_chat_history
        mock_error.assert_called_once()

@pytest.mark.asyncio
async def test_mixed_image_sources(test_chat_history):
    mock_response = MagicMock()
    mock_response.headers = {'Content-Type': 'image/jpeg'}
    mock_response.content = BytesIO(b'fake-remote-image').getvalue()
    
    local_image_data = BytesIO()
    Image.new('RGB', (100, 100), color='red').save(local_image_data, format='PNG')
    
    with patch('requests.get', return_value=mock_response), \
         patch('builtins.open', return_value=BytesIO(local_image_data.getvalue())), \
         patch('PIL.Image.open') as mock_image:
        mock_image.return_value = MagicMock(format='PNG')
        mock_image.return_value.__enter__ = MagicMock(return_value=mock_image.return_value)
        mock_image.return_value.__exit__ = MagicMock(return_value=None)
        
        mixed_sources = ["local_image.png", "https://example.com/image.jpg"]
        result_history = await main.handle_image_command(mixed_sources, test_chat_history)
        assert len(main.stored_images) > 0

@pytest.mark.asyncio
async def test_search_error_handling():
    mock_session = MagicMock()
    mock_session.prompt_async = AsyncMock(side_effect=Exception("Search error"))
    mock_search = AsyncMock(side_effect=Exception("Search failed"))
    
    with patch('main.session', mock_session), \
         patch('main.aget_results', mock_search):
        result = await main.handle_search_command([])
        assert result == []
        mock_search.assert_not_called()

def test_image_storage_management():
    mock_image_data = BytesIO()
    Image.new('RGB', (100, 100), color='blue').save(mock_image_data, format='PNG')
    
    initial_count = len(main.stored_images)
    main.stored_images["test_image"] = {
        "type": "image",
        "source": "url",
        "content": base64.b64encode(mock_image_data.getvalue()).decode('utf-8')
    }
    
    assert len(main.stored_images) == initial_count + 1
    assert "test_image" in main.stored_images