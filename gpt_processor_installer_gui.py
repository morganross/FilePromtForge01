import tkinter as tk
from tkinter import messagebox, filedialog
import subprocess
import logging

# Default values
default_install_dir = "C:\\upp\\jimmy"
default_prompt_file = "default_prompt.txt"
default_executable_path = "C:\\upp\\ui branch\\FilePromtForge01\\gpt_processor_main.py"

# Set up logging
logging.basicConfig(filename='installer_gui.log', level=logging.ERROR, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def run_installer(install_dir, prompt_file, executable_path):
    try:
        subprocess.run(['python', 'gpt_processor_installer.py', '--install-dir', install_dir, '--prompt-file', prompt_file, '--main_executable', executable_path], check=True)
        messagebox.showinfo("Success", "Installation completed successfully.")
    except subprocess.CalledProcessError as e:
        error_message = f"Installation failed: {e}"
        logging.error(error_message)
        messagebox.showerror("Error", error_message)

def select_install_dir(entry):
    path = filedialog.askdirectory(initialdir=default_install_dir)
    if path:
        entry.delete(0, tk.END)
        entry.insert(0, path)

def select_prompt_file(entry):
    path = filedialog.askopenfilename(initialdir=".", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
    if path:
        entry.delete(0, tk.END)
        entry.insert(0, path)

def select_executable_path(entry):
    path = filedialog.askopenfilename(initialdir=".", filetypes=[("Executable files", "*.exe"), ("All files", "*.*")])
    if path:
        entry.delete(0, tk.END)
        entry.insert(0, path)

def create_gui():
    root = tk.Tk()
    root.title("GPT Processor Installer")

    # Install directory
    tk.Label(root, text="Install Directory:").pack(pady=5)
    install_dir_entry = tk.Entry(root, width=50)
    install_dir_entry.pack(pady=5)
    install_dir_entry.insert(0, default_install_dir)
    tk.Button(root, text="Browse...", command=lambda: select_install_dir(install_dir_entry)).pack(pady=5)

    # Prompt file
    tk.Label(root, text="Prompt File:").pack(pady=5)
    prompt_file_entry = tk.Entry(root, width=50)
    prompt_file_entry.pack(pady=5)
    prompt_file_entry.insert(0, default_prompt_file)
    tk.Button(root, text="Browse...", command=lambda: select_prompt_file(prompt_file_entry)).pack(pady=5)

    # Executable path
    tk.Label(root, text="Executable Path:").pack(pady=5)
    executable_path_entry = tk.Entry(root, width=50)
    executable_path_entry.pack(pady=5)
    executable_path_entry.insert(0, default_executable_path)
    tk.Button(root, text="Browse...", command=lambda: select_executable_path(executable_path_entry)).pack(pady=5)

    # Install button
    install_button = tk.Button(root, text="Install", command=lambda: run_installer(install_dir_entry.get(), prompt_file_entry.get(), executable_path_entry.get()))
    install_button.pack(pady=20)

    root.mainloop()

if __name__ == "__main__":
    create_gui()