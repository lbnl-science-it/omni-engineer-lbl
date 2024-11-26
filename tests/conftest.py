import asyncio
import pytest
import os

from unittest.mock import MagicMock, AsyncMock
from types import SimpleNamespace
#from openai import OpenAI


class MockStreamResponse:
    """Mock response object for OpenAI API streaming."""
    
    def __init__(self):
        """Initialize with default mock response structure."""
        self.choices = [
            SimpleNamespace(
                delta=SimpleNamespace(content="Mock response"),
                finish_reason=None
            )
        ]



class MockFileSystem:
    """Helper class for file system operations"""
    def __init__(self):
        self.files = {
            "test.py": "print('hello')",
            "test.txt": "Hello World",
            "empty.txt": ""
        }

    def read_file(self, filepath):
         """Mock file reading"""
         if filepath in self.files:
            return self.files[filepath]
         return f"❌ Error: File not found: {filepath}"

    def write_file(self, filepath, content):
        self.files[filepath] = content
        return True

@pytest.fixture
def mock_file_system():
    """Provide mock file system instance"""
    fs = MockFileSystem()
    return {
        'files': fs.files,
        'read': fs.read_file,
        'write': fs.write_file
    }

@pytest.fixture
def mock_session():
    """Create mock session with proper async support"""
    session = MagicMock()
    session.prompt_async = AsyncMock()
    session.prompt_async.return_value = "test input"
    return session

@pytest.fixture
def test_chat_history():
    """Provide standard test chat history"""
    return [
        {"role": "system", "content": "System prompt"},
        {"role": "user", "content": "Test message"}
    ]



class MockImageProcessor:
    """Helper class for image processing"""
    @staticmethod
    def encode(image_path):
        return "base64_encoded_string"

    @staticmethod
    def validate(url):
        """Mock URL Validation"""
        return url.startswith('http')

class MockSearchEngine:
    """Mock search engine operations."""
    
    @staticmethod
    async def search():
        """Mock search operation."""
        return [
            {"title": "Test Result 1", "body": "Test content 1"},
            {"title": "Test Result 2", "body": "Test content 2"}
        ]


@pytest.fixture
def mock_openai_client():
    """Create a properly structured mock OpenAI client."""
    mock_client = MagicMock()
    mock_client.chat = MagicMock()
    mock_client.chat.completions = MagicMock()
    mock_client.chat.completions.create = AsyncMock(
        return_value=[MockStreamResponse()]
    )
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
def mock_search_results():
    """Provide mock search results."""
    engine = MockSearchEngine()
    return engine.search


@pytest.fixture
async def event_loop():
    """Provide event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
