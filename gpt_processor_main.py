#!/usr/bin/env python3
"""
GPT Processor Main Application

Features:
- Combine multiple prompt files into a single system prompt.
- Process multiple input files concurrently.
- Save AI-generated responses to output directory.
- Comprehensive logging to console and optional log file.
"""

import os
import argparse
import logging
import sys
import time
import subprocess
from concurrent.futures import ThreadPoolExecutor
from tkinter import messagebox

# Attempt to import required packages and handle missing dependencies
try:
    import openai
    import yaml
    from dotenv import load_dotenv
except ImportError as e:
    missing_package = str(e).split("'")[1]
    print(f"Error: Missing required package '{missing_package}'.")
    print("Please install all dependencies using:")
    print("    pip install openai PyYAML python-dotenv")
    sys.exit(1)

# Setting up the logger
def setup_logger(log_level=logging.INFO, log_file=None):
    logger = logging.getLogger('gpt_processor')
    logger.setLevel(log_level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(log_level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler
    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setLevel(log_level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger

# Ensure directory exists
def ensure_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

# Configuration class
class Config:
    def __init__(self, config_file=None, base_dir=None):
        load_dotenv()  # Load environment variables from .env if present
        default_config = {
            'prompts_dir': os.path.join(base_dir, 'prompts'),
            'input_dir': os.path.join(base_dir, 'input'),
            'output_dir': os.path.join(base_dir, 'output'),
            'openai': {
                'api_key': os.getenv('OPENAI_API_KEY'),
                'model': 'gpt-4',
                'temperature': 0.7,
                'max_tokens': 1500
            }
        }
        if config_file:
            if not os.path.isfile(config_file):
                raise FileNotFoundError(f"Configuration file '{config_file}' not found.")
            with open(config_file, 'r') as file:
                user_config = yaml.safe_load(file)
            # Merge user_config into default_config
            self.prompts_dir = os.path.join(base_dir, user_config.get('prompts_dir', 'prompts'))
            self.input_dir = os.path.join(base_dir, user_config.get('input_dir', 'input'))
            self.output_dir = os.path.join(base_dir, user_config.get('output_dir', 'output'))
            self.openai = self.OpenAI(user_config.get('openai', {}))
        else:
            self.prompts_dir = default_config['prompts_dir']
            self.input_dir = default_config['input_dir']
            self.output_dir = default_config['output_dir']
            self.openai = self.OpenAI(default_config['openai'])

    class OpenAI:
        def __init__(self, config):
            self.api_key = config.get('api_key')
            if not self.api_key:
                raise ValueError("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable or provide it in the config file.")
            self.model = config.get('model', 'gpt-4')
            self.temperature = config.get('temperature', 0.7)
            self.max_tokens = config.get('max_tokens', 1500)

# PromptManager class
class PromptManager:
    def __init__(self, prompts_dir):
        self.prompts_dir = prompts_dir

    def load_prompts(self, prompt_files):
        prompts = []
        for prompt_file in prompt_files:
            with open(os.path.join(self.prompts_dir, prompt_file), 'r', encoding='utf-8') as file:
                prompts.append(file.read())
        return "\n".join(prompts)

    def load_prompts_from_dirs(self, prompt_dirs):
        prompts = []
        for prompt_dir in prompt_dirs:
            for prompt_file in os.listdir(prompt_dir):
                with open(os.path.join(prompt_dir, prompt_file), 'r', encoding='utf-8') as file:
                    prompts.append(file.read())
        return "\n".join(prompts)

# FileHandler class
class FileHandler:
    def __init__(self, input_dir, output_dir):
        self.input_dir = input_dir
        self.output_dir = output_dir

    def list_input_files(self):
        return [f for f in os.listdir(self.input_dir) if os.path.isfile(os.path.join(self.input_dir, f))]

    def read_file(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()

    def write_file(self, file_path, content):
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)

# APIClient class
class APIClient:
    def __init__(self, api_key, model, temperature, max_tokens, max_retries=3, backoff_factor=2):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

    def send_prompt(self, system_prompt, user_prompt, logger):
        openai.api_key = self.api_key
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        for attempt in range(1, self.max_retries + 1):
            try:
                response = openai.ChatCompletion.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )
                return response.choices[0].message['content'].strip()
            except openai.error.RateLimitError as e:
                logger.error(f"Rate limit exceeded on attempt {attempt}: {e}")
            except openai.error.OpenAIError as e:
                logger.error(f"OpenAI API error on attempt {attempt}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt}: {e}")
            if attempt < self.max_retries:
                sleep_time = self.backoff_factor ** attempt
                logger.info(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
            else:
                logger.error("Max retries reached. Failed to get a response from OpenAI API.")
                raise

# Function to create default prompt file if not exists
def create_default_prompt(prompts_dir):
    default_prompt_path = os.path.join(prompts_dir, 'standard_prompt.txt')
    if not os.path.isfile(default_prompt_path):
        default_prompt = (
            "You are ChatGPT, a large language model trained by OpenAI. "
            "Provide clear and concise answers to the user's queries."
        )
        with open(default_prompt_path, 'w', encoding='utf-8') as file:
            file.write(default_prompt)

# Main processing function
def process_file(input_file, file_handler, api_client, system_prompt, logger):
    user_prompt = file_handler.read_file(input_file)
    response = api_client.send_prompt(system_prompt, user_prompt, logger)
    output_file = os.path.join(file_handler.output_dir, f"response_{os.path.basename(input_file)}")
    file_handler.write_file(output_file, response)

# CLI main function
def main():
    parser = argparse.ArgumentParser(description='GPT Processor Main Application')
    parser.add_argument('--config', type=str, help='Path to configuration file.')
    parser.add_argument('--log_file', type=str, help='Path to log file.')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging.')
    parser.add_argument('--prompt', type=str, nargs='+', help='List of prompt files.')
    parser.add_argument('--prompt_dirs', type=str, nargs='+', help='List of directories containing prompt files.')
    parser.add_argument('--input_dir', type=str, help='Directory for input files.')
    parser.add_argument('--output_dir', type=str, help='Directory for output files.')
    parser.add_argument('--model', type=str, help='OpenAI model to use.')
    parser.add_argument('--temperature', type=float, help='Temperature setting for the OpenAI model.')
    parser.add_argument('--max_tokens', type=int, help='Maximum number of tokens for the OpenAI model.')
    args = parser.parse_args()

    # Set log level based on verbosity
    log_level = logging.DEBUG if args.verbose else logging.INFO

    # Setup logger
    logger = setup_logger(log_level=log_level, log_file=args.log_file)

    # Load configuration
    try:
        config = Config(args.config, base_dir=os.path.dirname(os.path.abspath(__file__)))
    except Exception as e:
        logger.error(e)
        sys.exit(1)

    # Override config with CLI arguments if provided
    prompt_files = args.prompt if args.prompt else []
    prompt_dirs = args.prompt_dirs if args.prompt_dirs else []
    if not prompt_files and not prompt_dirs:
        prompt_files = ['standard_prompt.txt']
    input_dir = args.input_dir if args.input_dir else config.input_dir
    output_dir = args.output_dir if args.output_dir else config.output_dir
    model = args.model if args.model else config.openai.model
    temperature = args.temperature if args.temperature else config.openai.temperature
    max_tokens = args.max_tokens if args.max_tokens else config.openai.max_tokens

    # Ensure necessary directories exist
    ensure_directory(input_dir)
    ensure_directory(output_dir)

    # Load and combine prompts
    prompt_manager = PromptManager(config.prompts_dir)
    system_prompt = ""
    if prompt_files:
        system_prompt += prompt_manager.load_prompts(prompt_files)
    if prompt_dirs:
        system_prompt += prompt_manager.load_prompts_from_dirs(prompt_dirs)

    # Initialize file handler and API client
    file_handler = FileHandler(input_dir, output_dir)
    api_client = APIClient(config.openai.api_key, model, temperature, max_tokens)

    # List input files
    input_files = file_handler.list_input_files()
    if not input_files:
        logger.info("No input files found. Exiting.")
        sys.exit(0)

    # Process files concurrently
    with ThreadPoolExecutor(max_workers=min(5, len(input_files))) as executor:
        for input_file in input_files:
            executor.submit(process_file, os.path.join(input_dir, input_file), file_handler, api_client, system_prompt, logger)

if __name__ == "__main__":
    main()
