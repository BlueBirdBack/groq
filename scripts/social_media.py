import argparse
import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

# Constants
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
BASE_URL = "https://api.groq.com/openai/v1"
MODEL = "llama3-70b-8192"
TEMPERATURE = 0.38
PLATFORMS = [
    "Bluesky",
    "Facebook",
    "Instagram",
    "LinkedIn",
    "Mastodon",
    "Pinterest",
    "Reddit",
    "Threads",
]

# Initialize Groq client
client = OpenAI(api_key=GROQ_API_KEY, base_url=BASE_URL)


def get_completion(system_prompt, prompt):
    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            model=MODEL,
            temperature=TEMPERATURE,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error: {e}")
        return None


def load_prompt_from_file(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        print(f"Prompt file {file_path} not found.")
        return ""
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return ""


def construct_system_prompt(script_name):
    file_path = f"prompts/{script_name.lower()}.md"
    return load_prompt_from_file(file_path)


def main():
    parser = argparse.ArgumentParser(
        description="Process a markdown file with Groq's Llama 3 model."
    )
    parser.add_argument("md_path", help="Path to the markdown file")
    args = parser.parse_args()

    md_content = load_prompt_from_file(args.md_path)
    if not md_content:
        print(f"Could not read the markdown file: {args.md_path}")
        return

    for platform in PLATFORMS:
        script_name = f"{platform.lower()}_expert"
        print(f"{platform} {'-' * 60}\n")
        system_prompt = construct_system_prompt(script_name)
        if not system_prompt:
            print(f"Could not load system prompt for {platform}")
            continue

        user_prompt = (
            f"Craft a captivating {platform} post that drives engagement "
            f'(likes, comments, shares) based on the following text: """{md_content}"""'
        )
        response = get_completion(system_prompt, user_prompt)
        if response:
            print(response)
        else:
            print(f"Failed to get response for {platform}")
        print()


if __name__ == "__main__":
    main()
