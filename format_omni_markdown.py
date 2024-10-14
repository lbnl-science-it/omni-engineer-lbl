import os
import sys
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()



# Initialize the OpenAI client
openai_api_key = os.getenv("CYCLOGPT_API_KEY")
if not openai_api_key:
    raise ValueError("CYCLOGPT_API_KEY not found in environment variables")
# Local clients/VPN users can also use https://api-local.cborg.lbl.gov
base_url = "https://api.cborg.lbl.gov"

client = OpenAI(api_key=openai_api_key, base_url=base_url)


def process_markdown(input_file, output_file, output_dir=None):
    print(f"Processing {input_file}...")
    
    # Read the input file
    with open(input_file, 'r') as file:
        content = file.read()
    print(f"File content length: {len(content)}")

    # Prepare the prompt for the LLM
    prompt = f"""
    Please format the following conversation transcript to be more human-readable. 
    Follow these guidelines:
    1. Use headers to separate different parts of the conversation
    2. Apply formatting to distinguish between the human and assistant and system prompt
    3. Use code blocks for file paths and code snippets
    4. Organize information into numbered lists for easier reading
    5. Highlight important commands or file names

    Here's the conversation transcript:

    {content}

    Please provide the formatted version of this conversation.
    """

    # Send the content to the LLM API
    # Note that this uses gemini-pro because it has the longest context window. Other models may not have enough context window to handle long markdown files. 
    try:
        response = client.chat.completions.create(
            model='google/gemini-pro',
            messages=[
                {"role": "system", "content": "You are an AI assistant tasked with formatting conversation transcripts."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400000,
            stream=True
        )
        
        formatted_content = ""
        for chunk in response:
            if chunk.choices[0].delta.content is not None:
                formatted_content += chunk.choices[0].delta.content
                print(".", end="", flush=True)  # Progress indicator
        print()  # New line after progress indicator
    except Exception as e:
        print(f"Error calling the API: {str(e)}")
        return

    print(f"Received formatted content. Length: {len(formatted_content)}")

    # Write the formatted content to the output file
    if output_dir:
        output_file =Path(output_dir,output_file)

    with open(output_file, 'w') as file:
        file.write(formatted_content)
    print(f"Formatted content written to {output_file}")

if __name__ == "__main__":
    try:
        if len(sys.argv) != 3:
            raise ValueError("Incorrect number of arguments")
        
        input_file = sys.argv[1]
        output_file = sys.argv[2]
        
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Input file not found: {input_file}")
         
        home_path = Path.home()
        process_markdown(input_file, output_file)
        print("Processing complete.")
    except Exception as e:
            raise FileNotFoundError(f"Input file not found: {input_file}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")