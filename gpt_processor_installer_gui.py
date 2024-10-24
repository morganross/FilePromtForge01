import tkinter as tk
from tkinter import messagebox
import subprocess

def run_installer():
    try:
        subprocess.run(['python', 'gpt_processor_installer.py'], check=True)
        messagebox.showinfo("Success", "Installation completed successfully.")
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Error", f"Installation failed: {e}")

def create_gui():
    root = tk.Tk()
    root.title("GPT Processor Installer")

    install_button = tk.Button(root, text="Install", command=run_installer)
    install_button.pack(pady=20)

    root.mainloop()

if __name__ == "__main__":
    create_gui()