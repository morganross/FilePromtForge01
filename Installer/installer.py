import os
import argparse
import logging
import sys
import time
from concurrent.futures import ThreadPoolExecutor

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

# Determine the base directory
def get_base_directory():
    if getattr(sys, 'frozen', False):
        # If the application is run as a bundle (PyInstaller)
        base_dir = sys._MEIPASS
    else:
        # If the application is run as a script
        base_dir = os.path.dirname(os.path.abspath(__file__))
    return base_dir

# Ensure directory exists
def ensure_directory(directory):
    os.makedirs(directory, exist_ok=True)

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
        self.cache = {}

    def load_prompts(self, prompt_files, separator="\n\n"):
        combined_prompt = ""
        for prompt_file in prompt_files:
            if prompt_file in self.cache:
                combined_prompt += self.cache[prompt_file] + separator
                continue
            full_path = os.path.join(self.prompts_dir, prompt_file)
            if not os.path.isfile(full_path):
                raise FileNotFoundError(f"Prompt file '{prompt_file}' not found in '{self.prompts_dir}'.")
            with open(full_path, 'r', encoding='utf-8') as file:
                prompt = file.read()
                self.cache[prompt_file] = prompt
                combined_prompt += prompt + separator
        return combined_prompt.strip()

# FileHandler class
class FileHandler:
    def __init__(self, input_dir, output_dir):
        self.input_dir = input_dir
        self.output_dir = output_dir

    def list_input_files(self):
        return [
            os.path.join(self.input_dir, f)
            for f in os.listdir(self.input_dir)
            if os.path.isfile(os.path.join(self.input_dir, f))
        ]

    def read_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='latin-1') as file:
                return file.read()
        except Exception as e:
            raise IOError(f"Error reading file '{file_path}': {e}")

    def write_output(self, input_file, content):
        output_file = os.path.join(self.output_dir, os.path.basename(input_file))
        try:
            with open(output_file, 'w', encoding='utf-8') as file:
                file.write(content)
            return output_file
        except Exception as e:
            raise IOError(f"Error writing to file '{output_file}': {e}")

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
    try:
        user_prompt = file_handler.read_file(input_file)
        response = api_client.send_prompt(system_prompt, user_prompt, logger)
        output_filename = file_handler.write_output(input_file, response)
        logger.info(f"Processed '{input_file}' and saved to '{output_filename}'.")
    except Exception as e:
        logger.error(f"Error processing '{input_file}': {e}")

# CLI main function
def main():
    parser = argparse.ArgumentParser(description='ChatGPT Prompt Processor')
    parser.add_argument('--prompt', type=str, nargs='+', help='Specify one or more prompt files to use.')
    parser.add_argument('--input_dir', type=str, help='Specify input directory.')
    parser.add_argument('--output_dir', type=str, help='Specify output directory.')
    parser.add_argument('--model', type=str, help='Specify the OpenAI model to use.')
    parser.add_argument('--temperature', type=float, help='Set the temperature for the API.')
    parser.add_argument('--max_tokens', type=int, help='Set the maximum tokens for the API.')
    parser.add_argument('--config', type=str, help='Path to configuration file.')
    parser.add_argument('--log_file', type=str, help='Path to the log file.')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging.')
    args = parser.parse_args()

    # Determine base directory
    base_dir = get_base_directory()

    # Set log level based on verbosity
    log_level = logging.DEBUG if args.verbose else logging.INFO

    # Setup logger
    logger = setup_logger(log_level=log_level, log_file=args.log_file)

    # Load configuration
    try:
        config = Config(args.config, base_dir=base_dir)
    except Exception as e:
        logger.error(e)
        sys.exit(1)

    # Override config with CLI arguments if provided
    prompt_files = args.prompt if args.prompt else ['standard_prompt.txt']
    input_dir = args.input_dir if args.input_dir else config.input_dir
    output_dir = args.output_dir if args.output_dir else config.output_dir
    model = args.model if args.model else config.openai.model
    temperature = args.temperature if args.temperature else config.openai.temperature
    max_tokens = args.max_tokens if args.max_tokens else config.openai.max_tokens

    # Ensure directories exist
    ensure_directory(output_dir)
    ensure_directory(input_dir)
    ensure_directory(config.prompts_dir)

    # Create default prompt if not exists
    create_default_prompt(config.prompts_dir)

    # Initialize components
    prompt_manager = PromptManager(config.prompts_dir)
    file_handler = FileHandler(input_dir, output_dir)
    try:
        api_client = APIClient(config.openai.api_key, model, temperature, max_tokens)
    except Exception as e:
        logger.error(e)
        sys.exit(1)

    # Load and combine prompts
    try:
        system_prompt = prompt_manager.load_prompts(prompt_files)
    except Exception as e:
        logger.error(e)
        sys.exit(1)

    # Process input files
    input_files = file_handler.list_input_files()
    if not input_files:
        logger.info(f"No input files found in '{input_dir}'.")
        sys.exit(0)

    # Use ThreadPoolExecutor for concurrent processing
    max_workers = min(5, len(input_files))  # Limit number of threads
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for input_file in input_files:
            executor.submit(process_file, input_file, file_handler, api_client, system_prompt, logger)

if __name__ == '__main__':
    main()
