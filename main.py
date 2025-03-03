import atexit
import os
from openai import OpenAI
import sys
from dotenv import load_dotenv
from colorama import init, Fore, Back, Style
import difflib
import asyncio
from duckduckgo_search import AsyncDDGS
import json
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import TerminalFormatter
from rich.console import Console
from rich.table import Table
import base64
from urllib.parse import urlparse
import requests
from PIL import Image
from io import BytesIO

import select

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import Window
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.application.current import get_app


is_diff_on = True

init(autoreset=True)
load_dotenv()
# Local clients/VPN users can also use https://api-local.cborg.lbl.gov
base_url = "https://api.cborg.lbl.gov"
client = OpenAI(
    base_url=base_url,
    api_key=os.getenv("CBORG_API_KEY"),
)

# Some model options available at LBL
DEFAULT_MODEL = "lbl/cborg-coder:latest"
EDITOR_MODEL = "lbl/cborg-coder:latest"
#DEFAULT_MODEL = "lbl/deepseek-r1:llama-70b
#DEFAULT_MODEL= "openai/gpt-4o" 
#DEFAULT_MODEL = "openai/gpt-4o-mini" 
#DEFAULT_MODEL = "openai/o1"
#DEFAULT_MODEL = "openai/o1-mini"
#DEFAULT_MODEL = "anthropic/claude-haiku"
#DEFAULT_MODEL = "anthropic/claude-sonnet"
#DEFAULT_MODEL = "anthropic/claude-opus"
#DEFAULT_MODEL = "google/gemini-pro"
#DEFAULT_MODEL = "google/gemini-flash"
#DEFAULT_MODEL = "aws/llama-3.1-405b"
#DEFAULT_MODEL = "aws/llama-3.1-70b"
#DEFAULT_MODEL = "aws/llama-3.1-8b"
#DEFAULT_MODEL = "aws/command-r-plus-v1"
#DEFAULT_MODEL = "aws/command-r-v1"
#EDITOR_MODEL = "lbl/deepseek-r1:llama-70b
#EDITOR_MODEL = "openai/gpt-4o-mini"
#EDITOR_MODEL = "openai/o1"
#EDITOR_MODEL = "openai/o1-mini"
#EDITOR_MODEL = "anthropic/claude-haiku"
#EDITOR_MODEL = "anthropic/claude-sonnet"
#EDITOR_MODEL = "anthropic/claude-opus"
#EDITOR_MODEL = "google/gemini-pro"
#EDITOR_MODEL = "google/gemini-flash"
#EDITOR_MODEL = "aws/llama-3.1-405b"
#EDITOR_MODEL = "aws/llama-3.1-70b"
#EDITOR_MODEL = "aws/llama-3.1-8b"
#EDITOR_MODEL = "aws/command-r-plus-v1"
#EDITOR_MODEL = "aws/command-r-v1"

SYSTEM_PROMPT = """You are an incredible developer assistant. You have the following traits:
- You write clean, efficient code
- You explain concepts with clarity
- You think through problems step-by-step
- You're passionate about helping developers improve

When given an /edit instruction:
- First After completing the code review, construct a plan for the change
- Then provide specific edit instructions
- Format your response as edit instructions
- Do NOT execute changes yourself"""

EDITOR_PROMPT = """You are a code-editing AI. Your mission:

ULTRA IMPORTANT:
- YOU NEVER!!! add the type of file at the beginning of the file like ```python etq.
- YOU NEVER!!! add ``` at the start or end of the file meaning you never add anything that is not the code at the start or end of the file.

- Execute line-by-line edit instructions safely
- If a line doesn't need to be changed, output the line as is.
- NEVER add or delete lines, unless explicitly instructed
- YOU ONLY OUTPUT THE CODE.
- NEVER!!! add the type of file at the beginning of the file like ```python etq.
- ULTRA IMPORTANT you NEVER!!! add ``` at the start or end of the file meaning you never add anything that is not the code at the start or end of the file.
- Never change imports or function definitions unless explicitly instructed
- If you spot potential issues in the instructions, fix them!"""

added_files = []
stored_searches = {}
file_templates = {
    "python": "def main():\n    pass\n\nif __name__ == \"__main__\":\n    main()",
    "html": "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n    <meta charset=\"UTF-8\">\n    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n    <title>Document</title>\n</head>\n<body>\n    \n</body>\n</html>",
    "javascript": "// Your JavaScript code here"
}
undo_history = {}
stored_images = {}
command_history = FileHistory('.aiconsole_history.txt')
commands = WordCompleter(['/add', '/edit', '/new', '/search', '/image', '/clear', '/reset', '/diff', '/history', '/save', '/load', '/undo', '/help', '/model', '/change_model', '/show', 'exit'], ignore_case=True)
session = PromptSession(history=command_history)
force_exit = False
interrupt_output = False

def encode_image(image_path):
    """Turn a local image into base64."""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except FileNotFoundError:
        return None
    except IOError:
        return None

def validate_image_url(url, timeout=10):
    try:
        response = requests.get(
            url,
            stream=True,
            timeout=timeout,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.28 Safari/537.36'}
        )
        response.raise_for_status()

        # Check Content-Type
        content_type = response.headers.get('Content-Type', '').lower()
        if content_type.startswith(('image/', 'application/octet-stream')):
            return True

        # Force load it as an image
        image = Image.open(BytesIO(response.content))
        image.verify()

        return True

    except requests.exceptions.RequestException as e:
        print_colored(f"Network error: {e}", Fore.RED)
        return False
    except Image.UnidentifiedImageError:
        print_colored(f"The URL doesn't point to a valid image.", Fore.RED)
        return False
    except Exception as e:
        print_colored(f"Unexpected error: {e}", Fore.RED)
        return False

def is_url(string):
    """Check if a string is a valid URL."""
    try:
        result = urlparse(string)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

async def handle_image_command(filepaths_or_urls, default_chat_history):
    """Add local images & URLs to memory and chat history"""
    if not filepaths_or_urls:
        print_colored("❌ No images or URLs provided.", Fore.RED)
        return default_chat_history

    processed_images = 0
    success_images = 0

    for idx, image_path in enumerate(filepaths_or_urls, 1):
        try:
            if is_url(image_path):  # URL-based
                if validate_image_url(image_path):
                    stored_images[f"image_{len(stored_images) + 1}"] = {
                        "type": "image",
                        "source": "url",
                        "content": image_path
                    }
                    default_chat_history.append({
                        "role": "user",
                        "content": [{"type": "image_url", "image_url": {"url": image_path}}]
                    })
                    print_colored(f"✅ URL-based image {idx} added successfully!", Fore.GREEN)
                    success_images += 1
                else:
                    print_colored(f"❌ {image_path} isn't a valid image URL. Skipping.", Fore.RED)

            else:  # Local filepath
                image_content = encode_image(image_path)
                if image_content:
                    try:
                        # Detect if it's actually an image
                        with Image.open(image_path) as img:
                            img_format = img.format.lower() if img.format else None
                            if img_format not in ['jpeg', 'jpg', 'png', 'webp', 'gif']:
                                raise ValueError(f"Unsupported image format: {img_format}")

                            data_uri = f"image/{img_format};base64,{image_content}"

                            stored_images[f"image_{len(stored_images) + 1}"] = {
                                "type": "image",
                                "source": "local",
                                "content": data_uri
                            }
                            default_chat_history.append({
                                "role": "user",
                                "content": [{
                                    "type": "image_url",
                                    "image_url": {"url": data_uri}
                                }]
                            })
                            print_colored(f"✅ Local image {idx} added successfully!", Fore.GREEN)
                            success_images += 1
                    except (IOError, ValueError) as e:
                        print_colored(f"❌ {image_path} isn't a valid image. Error: {e}. Skipping.", Fore.RED)
                else:
                    print_colored(f"❌ Failed loading: {image_path}", Fore.RED)

        except Exception as e:
            print_colored(f"❌ Unexpected error processing {image_path}: {e}. Skipping.", Fore.RED)

        processed_images += 1  # Always increment, even if we skip

    print_colored(f"🖼️ {processed_images} images processed. {success_images} added successfully. {len(stored_images)} total images in memory!", Fore.CYAN)

    return default_chat_history

async def aget_results(word):
    results = await AsyncDDGS(proxy=None).atext(word, max_results=100)
    return results

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_colored(text, color=Fore.WHITE, style=Style.NORMAL, end='\n'):
    print(f"{style}{color}{text}{Style.RESET_ALL}", end=end)

def get_streaming_response(messages, model):
    try:
        stream = client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
        )
        full_response = ""
        for chunk in stream:
            # Check for user input without blocking
            rlist, _, _ = select.select([sys.stdin], [], [], 0)
            if rlist:
                user_input = sys.stdin.readline().strip()
                if user_input.lower() == '/stop':
                    print_colored("\n\nResponse interrupted by user.", Fore.YELLOW)
                    return None

            if chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
                print_colored(content, end="")
                full_response += content

        return full_response.strip()
    except Exception as e:
        print_colored(f"Error in streaming response: {e}", Fore.RED)
        return None 

def read_file_content(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        return f