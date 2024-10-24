#!/usr/bin/env python3
"""
GPT Processor Installer

Features:
- Creates necessary directories (`prompts/`, `input/`, `output/`).
- Copies the main application executable to the installation directory.
- Creates default prompt files.
- Optionally adds the installation directory to the system PATH for easy access.
- Provides user-friendly logging and error handling.
"""

import os
import sys
import argparse
import logging
import shutil
import subprocess
from pathlib import Path

# Setting up the logger
def setup_logger(log_level=logging.INFO, log_file=None):
    logger = logging.getLogger('gpt_processor_installer')
    logger.setLevel(log_level)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

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

# Function to create directories
def create_directories(base_dir, dirs):
    for directory in dirs:
        path = os.path.join(base_dir, directory)
        os.makedirs(path, exist_ok=True)

# Function to create default prompt file
def create_default_prompt(prompts_dir, logger):
    default_prompt_path = os.path.join(prompts_dir, 'standard_prompt.txt')
    if not os.path.isfile(default_prompt_path):
        default_prompt = (
            "You are ChatGPT, a large language model trained by OpenAI. "
            "Provide clear and concise answers to the user's queries."
        )
        try:
            with open(default_prompt_path, 'w', encoding='utf-8') as file:
                file.write(default_prompt)
            logger.info(f"Created default prompt file at '{default_prompt_path}'.")
        except Exception as e:
            logger.error(f"Failed to create default prompt file: {e}")
            sys.exit(1)
    else:
        logger.info(f"Default prompt file already exists at '{default_prompt_path}'.")

# Function to copy the main executable
def copy_main_executable(source_path, dest_dir, logger):
    if not os.path.isfile(source_path):
        logger.error(f"Main executable '{source_path}' not found.")
        sys.exit(1)
    try:
        shutil.copy(source_path, dest_dir)
        logger.info(f"Copied main executable to '{dest_dir}'.")
    except Exception as e:
        logger.error(f"Failed to copy main executable: {e}")
        sys.exit(1)

# Function to add directory to system PATH (Windows)
def add_to_system_path_windows(directory, logger):
    try:
        # Get current PATH
        current_path = os.environ['PATH']
        if directory in current_path:
            logger.info(f"'{directory}' is already in the system PATH.")
            return
        # Add to PATH using setx
        subprocess.run(['setx', 'PATH', f'{current_path};{directory}'], check=True)
        logger.info(f"Added '{directory}' to the system PATH. You may need to restart your command prompt for changes to take effect.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to add '{directory}' to system PATH: {e}")
        sys.exit(1)

# Function to add directory to system PATH (Unix/Linux/Mac)
def add_to_system_path_unix(directory, shell, logger):
    try:
        # Determine shell profile file
        home = Path.home()
        if shell.lower() in ['bash', 'sh']:
            profile = home / '.bashrc'
        elif shell.lower() == 'zsh':
            profile = home / '.zshrc'
        else:
            profile = home / '.profile'
        # Add export PATH statement
        export_statement = f'\n# Added by GPT Processor Installer\nexport PATH="$PATH:{directory}"\n'
        with open(profile, 'a') as file:
            file.write(export_statement)
        logger.info(f"Added '{directory}' to PATH in '{profile}'. Please restart your terminal or run 'source {profile}' to apply changes.")
    except Exception as e:
        logger.error(f"Failed to add '{directory}' to system PATH: {e}")
        sys.exit(1)

# Detect operating system
def detect_os():
    if sys.platform.startswith('win'):
        return 'windows'
    elif sys.platform.startswith('darwin'):
        return 'mac'
    elif sys.platform.startswith('linux'):
        return 'linux'
    else:
        return 'unknown'

# Main installer function
def main():
    parser = argparse.ArgumentParser(description='GPT Processor Installer')
    parser.add_argument('--install_dir', type=str, default=None, help='Directory to install GPT Processor.')
    parser.add_argument('--main_executable', type=str, required=True, help='Path to the main executable to install.')
    parser.add_argument('--add_to_path', action='store_true', help='Add the installation directory to system PATH.')
    parser.add_argument('--log_file', type=str, help='Path to the log file.')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging.')
    args = parser.parse_args()

    # Set log level based on verbosity
    log_level = logging.DEBUG if args.verbose else logging.INFO

    # Setup logger
    logger = setup_logger(log_level=log_level, log_file=args.log_file)

    # Determine installation directory
    if args.install_dir:
        install_dir = os.path.abspath(args.install_dir)
    else:
        # Default installation directory based on OS
        os_type = detect_os()
        if os_type == 'windows':
            install_dir = os.path.join(os.environ.get('ProgramFiles', 'C:\\Program Files'), 'GPTProcessor')
        elif os_type in ['mac', 'linux']:
            install_dir = os.path.join(os.path.expanduser('~'), 'gpt_processor')
        else:
            logger.error("Unsupported operating system.")
            sys.exit(1)

    logger.info(f"Installation Directory: {install_dir}")

    # Create installation directories
    dirs_to_create = ['prompts', 'input', 'output']
    create_directories(install_dir, dirs_to_create)
    logger.info("Created necessary directories.")

    # Create default prompt file
    prompts_dir = os.path.join(install_dir, 'prompts')
    create_default_prompt(prompts_dir, logger)

    # Copy main executable
    main_executable_source = os.path.abspath(args.main_executable)
    main_executable_dest = os.path.join(install_dir, os.path.basename(args.main_executable))
    copy_main_executable(main_executable_source, install_dir, logger)

    # Add to system PATH if requested
    if args.add_to_path:
        os_type = detect_os()
        if os_type == 'windows':
            add_to_system_path_windows(install_dir, logger)
        elif os_type in ['mac', 'linux']:
            # Detect user's shell
            shell = os.environ.get('SHELL', 'bash').split('/')[-1]
            add_to_system_path_unix(install_dir, shell, logger)
        else:
            logger.warning("Could not determine shell to update PATH.")
    
    logger.info("GPT Processor installation completed successfully.")

if __name__ == '__main__':
    main()
