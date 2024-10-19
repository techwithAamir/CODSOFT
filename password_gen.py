import secrets
import string
import difflib
import tkinter as tk
from tkinter import messagebox, ttk
from turtle import mode
from cryptography.fernet import Fernet
import hashlib
import os
import time

# Global variables
password_history = []
password_expiry_time = 30 * 24 * 60 * 60  # Password expiry in seconds (30 days)
dark_mode = True
master_password_hash = ""
encryption_key = None
master_password_salt = None

# Load the encryption key once
def load_key():
    global encryption_key
    if not os.path.exists("encryption_key.key"):
        generate_key()
    if encryption_key is None:
        encryption_key = open("encryption_key.key", "rb").read()
    return encryption_key

# Generate encryption key if it doesn't exist
def generate_key():
    key = Fernet.generate_key()
    with open("encryption_key.key", "wb") as key_file:
        key_file.write(key)

# Encrypt the password before saving
def encrypt_password(password, key):
    f = Fernet(key)
    return f.encrypt(password.encode())

# Decrypt the password when loading from file
def decrypt_password(encrypted_password, key):
    f = Fernet(key)
    try:
        return f.decrypt(encrypted_password).decode()
    except Exception as e:
        messagebox.showerror("Decryption Error", f"Failed to decrypt the password: {str(e)}")
        return None

# Hash the master password with salt
def hash_password(password):
    salt = os.urandom(16)
    return hashlib.sha256(salt + password.encode()).hexdigest(), salt

# Function to generate password
def generate_password(length, use_lowercase=True, use_uppercase=True, use_digits=True, use_special=True):
    character_set = ""
    required_chars = []

    if use_lowercase:
        character_set += string.ascii_lowercase
        required_chars.append(secrets.choice(string.ascii_lowercase))
    if use_uppercase:
        character_set += string.ascii_uppercase
        required_chars.append(secrets.choice(string.ascii_uppercase))
    if use_digits:
        character_set += string.digits
        required_chars.append(secrets.choice(string.digits))
    if use_special:
        character_set += "!@#$%^&*()?|[]~`"
        required_chars.append(secrets.choice("!@#$%^&*()?|[]~`"))

    if not character_set:
        messagebox.showerror("Error", "You must select at least one character type!")
        return None
    if length < len(required_chars):
        messagebox.showerror("Error", f"Please enter a valid password length (at least {len(required_chars)}).")
        return None

    password = required_chars + [secrets.choice(character_set) for _ in range(length - len(required_chars))]
    secrets.SystemRandom().shuffle(password)

    return ''.join(password)

# Enhanced password strength evaluation
def password_strength(password):
    score = 0
    if len(password) >= 8: score += 1
    if any(c.islower() for c in password): score += 1
    if any(c.isupper() for c in password): score += 1
    if any(c.isdigit() for c in password): score += 1
    if any(c in "!@#$%^&*()?|[]~`" for c in password): score += 1
    if len(password) >= 12: score += 1
    if len(password) >= 16: score += 1
    if len(set(password)) == len(password): score += 1  # No repeating characters

    strength = {
        1: "Very Weak",
        2: "Weak",
        3: "Moderate",
        4: "Strong",
        5: "Very Strong",
        6: "Excellent",
        7: "Top-tier"
    }
    return strength.get(score, "Invalid")

# Check similarity to previous passwords
def is_similar_to_previous(password, history, threshold=0.8):
    for old_password in history:
        ratio = difflib.SequenceMatcher(None, password, old_password).ratio()
        if ratio > threshold:
            return True
    return False

# Save the encrypted password to a .txt file
def save_password_to_file(password, filename="passwords.txt"):
    key = load_key()
    encrypted_password = encrypt_password(password, key)
    with open(filename, 'a') as file:
        file.write(f"{encrypted_password.decode()}:{int(time.time())}\n")  # Save with timestamp for expiry tracking
    print(f"Password saved to {filename} (encrypted).")

# Load and decrypt passwords from the .txt file
def load_passwords_from_file():
    key = load_key()
    decrypted_passwords = []
    if os.path.exists("passwords.txt"):
        with open("passwords.txt", 'r') as file:
            lines = file.readlines()
            for line in lines:
                encrypted_password, timestamp = line.strip().split(":")
                if time.time() - float(timestamp) > password_expiry_time:
                    messagebox.showwarning("Password Expired", "A password has expired and should be updated.")
                    continue
                decrypted_pwd = decrypt_password(encrypted_password.encode(), key)
                if decrypted_pwd:
                    decrypted_passwords.append(decrypted_pwd)
    return decrypted_passwords

# Set master password dynamically and store its hash and salt
def set_master_password():
    global master_password_hash, master_password_salt
    entered_password = master_password_entry.get()
    if len(entered_password) < 8:
        messagebox.showerror("Error", "Master password must be at least 8 characters long!")
        return
    master_password_hash, master_password_salt = hash_password(entered_password)  # Store both hash and salt
    messagebox.showinfo("Success", "Master password set successfully!")
    master_password_entry.delete(0, tk.END)  # Clear master password entry

# Master password validation using the stored salt
def validate_master_password():
    global master_password_hash, master_password_salt
    entered_password = master_password_entry.get()
    if not master_password_salt:
        messagebox.showerror("Error", "Master password not set!")
        return
    # Use the stored salt to hash the entered password
    entered_hash = hashlib.sha256(master_password_salt + entered_password.encode()).hexdigest()
    if entered_hash == master_password_hash:
        show_decrypt_window()
    else:
        messagebox.showerror("Error", "Incorrect Master Password!")


# Password Decryption Window
def show_decrypt_window():
    decrypted_passwords = load_passwords_from_file()
    if not decrypted_passwords:
        messagebox.showinfo("No Passwords", "No passwords saved yet.")
        return

    decrypt_window = tk.Toplevel(root)
    decrypt_window.title("Decrypted Passwords")
    decrypt_window.geometry("300x200")

    scrollbar = tk.Scrollbar(decrypt_window)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    text = tk.Text(decrypt_window, wrap=tk.WORD, yscrollcommand=scrollbar.set)
    for pwd in decrypted_passwords:
        text.insert(tk.END, f"{pwd}\n")
    text.pack(expand=True, fill=tk.BOTH)

    scrollbar.config(command=text.yview)

# Password Generation GUI
def generate_password_gui():
    try:
        passlen = int(password_length.get())
        if passlen < 8 or passlen > 128:
            messagebox.showerror("Error", "Password length should be between 8 and 128 characters!")
            return
    except ValueError:
        messagebox.showerror("Error", "Please enter a valid number for password length!")
        return

    use_lower = lowercase_var.get()
    use_upper = uppercase_var.get()
    use_digits = digits_var.get()
    use_special = special_var.get()

    password = generate_password(passlen, use_lower, use_upper, use_digits, use_special)
    if password:
        password_output.delete(0, tk.END)
        password_output.insert(0, password)
        strength = password_strength(password)
        strength_label.config(text=f"Password Strength: {strength}")
        
        if is_similar_to_previous(password, password_history):
            messagebox.showwarning("Password Similarity", "This password is too similar to a previous one.")
        else:
            password_history.append(password)
            if save_var.get():
                save_password_to_file(password)

# Copy password to clipboard
def copy_to_clipboard():
    root.clipboard_clear()
    root.clipboard_append(password_output.get())
    root.update()  # Ensure clipboard update

# Toggle between dark and light modes
def toggle_theme():
    global dark_mode
    if dark_mode:
        # Light mode settings
        root.configure(bg="#ffffff")
        frame.configure(bg="#ffffff")
        for widget in frame.winfo_children():
            if isinstance(widget, (tk.Label, tk.Button, tk.Checkbutton)):
                widget.configure(bg="#ffffff", fg="#000000")
            if isinstance(widget, tk.Entry):
                widget.configure(bg="#FFFFFF", fg="#000000")
            if isinstance(widget, tk.Checkbutton):  # Set checkbox background in light mode
                widget.configure(bg="#FFFFFF", selectcolor="#FFFFFF")  # Change the select color to white
            if isinstance(widget, tk.Button):
                widget.configure(bg="#4CAF50", activebackground="#87C28A", activeforeground="#000000")
        dark_mode = False
    else:
        # Dark mode settings
        root.configure(bg="#282828")
        frame.configure(bg="#282828")
        for widget in frame.winfo_children():
            if isinstance(widget, (tk.Label, tk.Button, tk.Checkbutton)):
                widget.configure(bg="#282828", fg="#ffffff")
            if isinstance(widget, tk.Entry):
                widget.configure(bg="#333333", fg="#ffffff")
            if isinstance(widget, tk.Checkbutton):  # Set checkbox background in dark mode
                widget.configure(bg="#282828", selectcolor="#282828")  # Maintain dark mode background
            if isinstance(widget, tk.Button):
                widget.configure(bg="#FF5722", activebackground="#FF8A65", activeforeground="#FFFFFF")
        dark_mode = True

# Create the main window
root = tk.Tk()
root.title("Secure Password Generator")
root.geometry("500x600")
root.configure(bg="#282828")  # Set the background color (dark mode by default)

# Frame to hold all the widgets
frame = tk.Frame(root, bg="#282828")
frame.pack(expand=True)

# Labels and input fields
label = tk.Label(frame, text="Password Length:", bg="#282828", fg="#ffffff")
label.grid(row=0, column=0, padx=10, pady=10)

password_length = tk.Entry(frame)
password_length.grid(row=0, column=1, padx=10, pady=10)

lowercase_var = tk.BooleanVar(value=True)
uppercase_var = tk.BooleanVar(value=True)
digits_var = tk.BooleanVar(value=True)
special_var = tk.BooleanVar(value=True)
save_var = tk.BooleanVar(value=True)

lowercase_checkbox = tk.Checkbutton(frame, text="Include lowercase", variable=lowercase_var, bg="#282828", fg="#ffffff", selectcolor="#282828")
lowercase_checkbox.grid(row=1, column=0, columnspan=2)

uppercase_checkbox = tk.Checkbutton(frame, text="Include uppercase", variable=uppercase_var, bg="#282828", fg="#ffffff", selectcolor="#282828")
uppercase_checkbox.grid(row=2, column=0, columnspan=2)

digits_checkbox = tk.Checkbutton(frame, text="Include digits", variable=digits_var, bg="#282828", fg="#ffffff", selectcolor="#282828")
digits_checkbox.grid(row=3, column=0, columnspan=2)

special_checkbox = tk.Checkbutton(frame, text="Include special chars", variable=special_var, bg="#282828", fg="#ffffff", selectcolor="#282828")
special_checkbox.grid(row=4, column=0, columnspan=2)

save_checkbox = tk.Checkbutton(frame, text="Save password", variable=save_var, bg="#282828", fg="#ffffff", selectcolor="#282828")
save_checkbox.grid(row=5, column=0, columnspan=2)

# Change the layout of the checkboxes for better alignment
lowercase_checkbox.grid(row=1, column=0, sticky='w', padx=10, pady=5)
uppercase_checkbox.grid(row=2, column=0, sticky='w', padx=10, pady=5)
digits_checkbox.grid(row=3, column=0, sticky='w', padx=10, pady=5)
special_checkbox.grid(row=4, column=0, sticky='w', padx=10, pady=5)
save_checkbox.grid(row=5, column=0, sticky='w', padx=10, pady=5)

# Output field for generated password
password_output = tk.Entry(frame, width=30)
password_output.grid(row=6, column=0, columnspan=2, padx=10, pady=10)

# Strength label
strength_label = tk.Label(frame, text="Password Strength:", bg="#282828", fg="#ffffff")
strength_label.grid(row=7, column=0, columnspan=2, padx=10, pady=10)

# Generate password button
generate_button = tk.Button(frame, text="Generate Password", command=generate_password_gui, bg="#FF5722", fg="#ffffff", activebackground="#FF8A65")
generate_button.grid(row=8, column=0, columnspan=2, padx=10, pady=10)

# Copy to clipboard button
copy_button = tk.Button(frame, text="Copy", command=copy_to_clipboard, bg="#4CAF50", fg="#ffffff", activebackground="#87C28A")
copy_button.grid(row=9, column=0, columnspan=2, padx=10, pady=10)

# Master password section
master_password_label = tk.Label(frame, text="Set Master Password:", bg="#282828", fg="#ffffff")
master_password_label.grid(row=10, column=0, padx=10, pady=10)

master_password_entry = tk.Entry(frame, show="*")
master_password_entry.grid(row=10, column=1, padx=10, pady=10)

# Set master password button
set_password_button = tk.Button(frame, text="Set Password", command=set_master_password, bg="#FF5722", fg="#ffffff", activebackground="#FF8A65")
set_password_button.grid(row=11, column=0, padx=10, pady=10)

# Validate master password button
validate_password_button = tk.Button(frame, text="Decrypt Password", command=validate_master_password, bg="#4CAF50", fg="#ffffff", activebackground="#87C28A")
validate_password_button.grid(row=11, column=1, padx=10, pady=10)

# Toggle theme button
toggle_theme_button = tk.Button(frame, text="Toggle Theme", command=toggle_theme, bg="#4CAF50", fg="#ffffff", activebackground="#87C28A")
toggle_theme_button.grid(row=12, column=0, columnspan=2, padx=10, pady=10)

# Start the application
root.mainloop()

