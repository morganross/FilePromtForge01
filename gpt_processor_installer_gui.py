import tkinter as tk
from tkinter import messagebox, filedialog
import subprocess
import logging
import os
from datetime import datetime

# Default values
default_install_dir = "C:\\upp\\jimmy"
default_prompt_file = "default_prompt.txt"
default_executable_path = "C:\\upp\\ui branch\\FilePromtForge01\\gpt_processor_main.py"

# Create a directory named after the current time
current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
log_dir = f"logs_{current_time}"
os.makedirs(log_dir, exist_ok=True)

# Set up logging
log_file = os.path.join(log_dir, 'installer_gui.log')
logging.basicConfig(filename=log_file, level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def run_installer(install_dir, prompt_file, executable_path):
    logging.debug(f"Starting run_installer with install_dir={install_dir}, prompt_file={prompt_file}, executable_path={executable_path}")
    try:
        command = [
            'python', 'gpt_processor_installer.py',
            '--install_dir', install_dir,
            '--main_executable', executable_path
        ]
        logging.debug(f"Running command: {command}")
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        logging.debug(f"Command output: {result.stdout}")
        logging.debug(f"Command error (if any): {result.stderr}")
        messagebox.showinfo("Success", "Installation completed successfully.")
    except subprocess.CalledProcessError as e:
        error_message = f"Installation failed: {e}"
        logging.error(error_message)
        logging.debug(f"Command output: {e.stdout}")
        logging.debug(f"Command error: {e.stderr}")
        messagebox.showerror("Error", error_message)

def select_install_dir(entry):
    logging.debug("Opening directory selection dialog for install directory")
    path = filedialog.askdirectory(initialdir=default_install_dir)
    logging.debug(f"Selected install directory: {path}")
    if path:
        entry.delete(0, tk.END)
        entry.insert(0, path)

def select_prompt_file(entry):
    logging.debug("Opening file selection dialog for prompt file")
    path = filedialog.askopenfilename(initialdir=".", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
    logging.debug(f"Selected prompt file: {path}")
    if path:
        entry.delete(0, tk.END)
        entry.insert(0, path)

def select_executable_path(entry):
    logging.debug("Opening file selection dialog for executable path")
    path = filedialog.askopenfilename(initialdir=".", filetypes=[("Executable files", "*.exe"), ("All files", "*.*")])
    logging.debug(f"Selected executable path: {path}")
    if path:
        entry.delete(0, tk.END)
        entry.insert(0, path)

def create_gui():
    logging.debug("Creating main GUI window")
    root = tk.Tk()
    root.title("GPT Processor Installer")

    # Install directory
    logging.debug("Adding install directory input field")
    tk.Label(root, text="Install Directory:").pack(pady=5)
    install_dir_entry = tk.Entry(root, width=50)
    install_dir_entry.pack(pady=5)
    install_dir_entry.insert(0, default_install_dir)
    tk.Button(root, text="Browse...", command=lambda: select_install_dir(install_dir_entry)).pack(pady=5)

    # Prompt file
    logging.debug("Adding prompt file input field")
    tk.Label(root, text="Prompt File:").pack(pady=5)
    prompt_file_entry = tk.Entry(root, width=50)
    prompt_file_entry.pack(pady=5)
    prompt_file_entry.insert(0, default_prompt_file)
    tk.Button(root, text="Browse...", command=lambda: select_prompt_file(prompt_file_entry)).pack(pady=5)

    # Executable path
    logging.debug("Adding executable path input field")
    tk.Label(root, text="Executable Path:").pack(pady=5)
    executable_path_entry = tk.Entry(root, width=50)
    executable_path_entry.pack(pady=5)
    executable_path_entry.insert(0, default_executable_path)
    tk.Button(root, text="Browse...", command=lambda: select_executable_path(executable_path_entry)).pack(pady=5)

    # Install button
    logging.debug("Adding install button")
    install_button = tk.Button(root, text="Install", command=lambda: run_installer(install_dir_entry.get(), prompt_file_entry.get(), executable_path_entry.get()))
    install_button.pack(pady=20)

    logging.debug("Starting main GUI loop")
    root.mainloop()

if __name__ == "__main__":
    logging.debug("Starting the installer GUI script")
    create_gui()