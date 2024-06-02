"""
This module is all about running AI-driven tasks. It's packed with features to chat with AI models served by Groq, log conversation history, and save the results.

Usage:
    python run_script.py <script_name>

The <script_name> part decides what kind of script runs, and that sets the stage for how the AI conversation goes down.
"""

import os
import sys
import time
from datetime import datetime
import json
import concurrent.futures
from typing import Dict, List, Optional
from dotenv import load_dotenv
from groq import Groq


# Constants for model names
# MODELS = ["llama3-70b-8192", "llama3-8b-8192", "mixtral-8x7b-32768"]
MODELS = ["llama3-70b-8192", "llama3-8b-8192"]

# conversation_history = {}


class BaseScript:
    """Base class for all scripts."""

    def __init__(self):
        load_dotenv()
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        if not self.groq_api_key:
            raise ValueError("The GROQ_API_KEY environment variable is not set.")
        self.client = Groq(api_key=self.groq_api_key)
        self.conversation_history: Dict[str, List[Dict[str, str]]] = {}

    def get_completion(
        self, prompt: str, model: str, system_prompt: str = None
    ) -> Optional[str]:
        """Get a response for the given prompt and model."""
        # global self.conversation_history
        start_time = time.time()
        try:
            # Create a separate conversation history for each model
            if model not in self.conversation_history:
                self.conversation_history[model] = []

            messages = self.conversation_history[model] + [
                {"role": "user", "content": prompt}
            ]
            if system_prompt:
                messages.insert(0, {"role": "system", "content": system_prompt})
            response = self.client.chat.completions.create(
                messages=messages,
                model=model,
            )
            end_time = time.time()
            print(f"{model}: {end_time - start_time:.2f} seconds")

            response_content = response.choices[0].message.content
            self.conversation_history[model].append({"role": "user", "content": prompt})
            self.conversation_history[model].append(
                {"role": "assistant", "content": response_content}
            )
            return response_content
        except Exception as e:
            print(f"Error fetching completion for model {model}: {e}")
            return None

    def get_completions(
        self, prompt: str, models: List[str], system_prompt: str = None
    ) -> Dict[str, str]:
        # start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(
                    self.get_completion, prompt, model, system_prompt
                ): model
                for model in models
            }
            results = {
                futures[future]: future.result()
                for future in concurrent.futures.as_completed(futures)
            }
        # end_time = time.time()
        # print(f"Time taken to fetch completions: {end_time - start_time:.2f} seconds")
        return results

    def load_prompt_from_file(self, file_path: str) -> str:
        """Loads a prompt from a file and returns its contents as a string."""
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                return file.read()
        except FileNotFoundError:
            print(f"Prompt file {file_path} not found.")
            return None

    def construct_system_prompt(self, script_name: str) -> str:
        """Constructs a system prompt from a file based on the given script name."""
        file_path = f"prompts/{script_name.lower()}.md"
        return self.load_prompt_from_file(file_path)

    def gather_input(self) -> str:
        """Gather user input until 'Q' is entered."""
        print("Enter your prompt (type 'Q' to finish):")
        lines = []
        while True:
            line = input()
            if line.strip().upper() == "Q":
                break
            lines.append(line)
        return "\n".join(lines)

    def save_history(self, script_name: str):
        """Save the chat history in the cloud directory."""
        history_dir = os.path.join(os.getcwd(), "history")
        now = datetime.now().strftime("%y%m%d_%H%M%S")
        filename = f"{script_name}_{now}.json"
        filepath = os.path.join(history_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.conversation_history, f, ensure_ascii=False, indent=4)
        print(f"Saved history to {filepath}")

        filename = f"{script_name}_{now}.md"
        filepath = os.path.join(history_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            for model, history in self.conversation_history.items():
                f.write(f"# {model}\n")
                for message in history:
                    # f.write(f"## Turn: {i + 1}\n")
                    f.write(f"### {message['role']}:\n{message['content']}\n\n")
                f.write("\n\n")
        print(f"Saved history to {filepath}")

    def main(self, script_name: str):
        """Main method to run the script."""
        while True:
            user_input = self.gather_input()
            start_time = time.time()
            if len(user_input.strip()) == 0:
                self.save_history(script_name)
                self.conversation_history = {}  # Clear conversation history
                break
            # prompt = self.construct_prompt(script_name, user_input)
            system_prompt = self.construct_system_prompt(script_name)
            prompt = user_input
            results = self.get_completions(prompt, MODELS, system_prompt)

            for model, result in results.items():
                print("-" * 60)
                print(f"Turn: {len(self.conversation_history[model]) // 2}")
                # pprint(self.conversation_history[model])
                print(f"Model: {model}\n\n{result}\n")

            end_time = time.time()
            print(f"Total time taken: {end_time - start_time:.2f} seconds")

    @staticmethod
    def validate_arguments():
        """Validate the command-line arguments."""
        if len(sys.argv) < 2:
            print("Usage: python run_script.py <script_name>")
            sys.exit(1)
        return sys.argv[1]


if __name__ == "__main__":
    prompt_name = BaseScript.validate_arguments()
    base_script = BaseScript()
    base_script.main(prompt_name)
