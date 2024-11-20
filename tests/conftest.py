import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from openai import OpenAI
import os

class MockFileSystem:
    """Helper class for file system operations"""
    def __init__(self):
        self.files = {
            "test.py": "print('hello')",
            "test.txt": "Hello World",
        }

    def read_file(self, filepath):
        return self.files.get(filepath, "")

    def write_file(self, filepath, content):
        self.files[filepath] = content
        return True

class MockImageProcessor:
    """Helper class for image processing"""
    @staticmethod
    def encode(image_path):
        return "base64_encoded_string"

    @staticmethod
    def validate(url):
        return True if url.startswith("http") else False

async def mock_search_results(query):
    """Mock function for search results"""
    return [
        {"title": "Test Result 1", "body": "Test content 1"},
        {"title": "Test Result 2", "body": "Test content 2"}
    ]

def create_mock_stream():
    """Create a mock stream response"""
    mock_stream = MagicMock()
    mock_stream.choices = [MagicMock(delta=MagicMock(content="Test response"))]
    return mock_stream

@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing"""
    mock_client = MagicMock(spec=OpenAI)
    mock_client.chat.completions.create.return_value = [create_mock_stream()]
    return mock_client

@pytest.fixture
def mock_file_system():
    """Mock file system operations"""
    fs = MockFileSystem()
    return {
        "read": fs.read_file,
        "write": fs.write_file,
        "files": fs.files
    }

@pytest.fixture
def mock_session():
    """Mock PromptSession for testing user input"""
    mock = MagicMock()
    mock.prompt_async = AsyncMock(return_value="test input")
    return mock

@pytest.fixture
def test_chat_history():
    """Provide a clean chat history for tests"""
    return [
        {"role": "system", "content": "System prompt"},
        {"role": "user", "content": "Test message"}
    ]

@pytest.fixture
def mock_image_processing():
    """Mock image processing functions"""
    processor = MockImageProcessor()
    return {
        "encode": processor.encode,
        "validate": processor.validate
    }

@pytest.fixture(autouse=True)
def mock_environment():
    """Set up test environment variables"""
    os.environ["CBORG_API_KEY"] = "test_key"
    yield
    del os.environ["CBORG_API_KEY"]

@pytest.fixture
def mock_search():
    """Mock DuckDuckGo search results"""
    return mock_search_results

@pytest.fixture
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop()
    yield loop