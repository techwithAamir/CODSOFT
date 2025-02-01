import tkinter as tk
from tkinter import messagebox, simpledialog
import os
import time
import sched
import threading
import speech_recognition as sr
import pyttsx3
from tkinter import PhotoImage
from PIL import Image, ImageTk 
from datetime import datetime, timedelta
import re 
import spacy
# Initialize speech recognizer and text-to-speech engine
recognizer = sr.Recognizer()
engine = pyttsx3.init()
# Load spaCy's English NLP model
nlp = spacy.load("en_core_web_sm")

# Scheduler for reminders
scheduler = sched.scheduler(time.time, time.sleep)
undo_stack = []
redo_stack = []



TASKS_FILE = "tasks.txt"
ARCHIVE_FILE = "archive.txt"

# Vibrant color themes for dark and light modes
dark_mode = {
    "bg": "#1e1f26", "fg": "#FFFFFF", "button_bg": "#4b4f77", "entry_bg": "#282c34",
    "list_bg": "#3d405b", "highlight": "#ff007f", "button_hover": "#ff77aa"
}
light_mode = {
    "bg": "#f5f7fa", "fg": "#000000", "button_bg": "#6a98f0", "entry_bg": "#d0e1ff",
    "list_bg": "#d3e0dc", "highlight": "#ff8b4c", "button_hover": "#ffa982"
}
theme = light_mode  # Start with light mode

# Function to apply hover effect to buttons
def on_enter(e):
    e.widget['background'] = theme['button_hover']

def on_leave(e):
    e.widget['background'] = theme['button_bg']

# Function to read a task aloud
def read_task(task):
    engine.say(task)
    engine.runAndWait()

# Function to provide voice feedback for button actions
def voice_feedback(text):
    engine.say(text)
    engine.runAndWait()

# Function to schedule a reminder
def set_reminder(task, delay_seconds):
    scheduler.enter(delay_seconds, 1, lambda: root.after(0, show_reminder, task))
    threading.Thread(target=scheduler.run).start()

# Function to show the reminder
def show_reminder(task):
    messagebox.showinfo("Reminder", f"Reminder for task: {task}")

# Function to toggle between dark and light modes
def toggle_theme():
    global theme
    theme = dark_mode if theme == light_mode else light_mode
    apply_theme()
    voice_feedback("Theme has been toggled.")

# Function to apply the current theme to the UI
def apply_theme():
    root.config(bg=theme['bg'])
    container_frame.config(bg=theme['bg'])
    task_entry.config(bg=theme['entry_bg'], fg=theme['fg'])
    task_listbox.config(bg=theme['list_bg'], fg=theme['fg'], selectbackground=theme['highlight'])
    
    for button in button_widgets:
        button.config(bg=theme['button_bg'], fg=theme['fg'], activebackground=theme['highlight'])
def parse_task_nlp(task_text):
    doc = nlp(task_text)
    priority, due_date = None, None

    # Detect keywords for priority
    if re.search(r"\burgent\b|\bimportant\b|\bhigh\b", task_text, re.IGNORECASE):
        priority = "High"
    elif re.search(r"\bmedium\b", task_text, re.IGNORECASE):
        priority = "Medium"
    elif re.search(r"\blow\b", task_text, re.IGNORECASE):
        priority = "Low"
    else:
        priority = "Normal"  # Default priority

    # Extract due date if any date is mentioned in the text
    for ent in doc.ents:
        if ent.label_ == "DATE":
            try:
                due_date = datetime.strptime(ent.text, "%Y-%m-%d")
            except ValueError:
                # Handle common relative dates like "tomorrow" or "next week"
                if "tomorrow" in ent.text.lower():
                    due_date = datetime.now() + timedelta(days=1)
                elif "next week" in ent.text.lower():
                    due_date = datetime.now() + timedelta(weeks=1)
                elif "today" in ent.text.lower():
                    due_date = datetime.now()
            break

    return priority, due_date

# Function to add a task
def add_task(event=None, task_input=None, priority=None):
    task = task_input if task_input else task_entry.get()
    if task != "":
        if not priority:
            priority = simpledialog.askstring("Priority", "Enter task priority: High, Medium, Low")
        reminder_time = simpledialog.askinteger("Set Reminder", "Set a reminder in how many seconds? (Leave blank for none)")
        if priority:
            task = f"{task} [{priority}]"
        task_listbox.insert(tk.END, task)
        undo_stack.append(('add', task))
        task_entry.delete(0, tk.END)
        if reminder_time:
            set_reminder(task, reminder_time)
        save_tasks()
        voice_feedback(f"Task '{task}' has been added.")
    else:
        messagebox.showwarning("Input Error", "Please enter a task.")

# Function to delete a task
def delete_task():
    selected_task_index = task_listbox.curselection()
    if selected_task_index:
        task = task_listbox.get(selected_task_index)
        undo_stack.append(('delete', task, selected_task_index[0]))
        task_listbox.delete(selected_task_index)
        save_tasks()
        voice_feedback(f"Task '{task}' has been deleted.")
    else:
        messagebox.showwarning("Selection Error", "Please select a task to delete.")

        # Example function to delete a selected task (adjust as needed)
def delete_task_via_command():
    if task_listbox.size() > 0:
        selected_task = task_listbox.get(0)  # Select the first task for demonstration
        task_listbox.delete(0)
        save_tasks()
        voice_feedback(f"Task '{selected_task}' deleted.")
    else:
        voice_feedback("No tasks to delete.")

# Function to mark a task as completed
def mark_task_complete():
    selected_task_index = task_listbox.curselection()
    if selected_task_index:
        task = task_listbox.get(selected_task_index)
        task_listbox.delete(selected_task_index)
        task_listbox.insert(selected_task_index, f"{task} - Completed")
        undo_stack.append(('complete', task, selected_task_index[0]))
        save_tasks()
        voice_feedback(f"Task '{task}' has been marked as completed.")
    else:
        messagebox.showwarning("Selection Error", "Please select a task to mark as complete.")

# Function to edit a task
def edit_task():
    selected_task_index = task_listbox.curselection()
    if selected_task_index:
        old_task = task_listbox.get(selected_task_index)
        new_task = simpledialog.askstring("Edit Task", "Modify the selected task:", initialvalue=old_task)
        if new_task:
            priority = determine_priority(new_task)
            due_date = parse_due_date(new_task)
            if due_date:
                new_task += f" (Due: {due_date.strftime('%Y-%m-%d')})"
            task_listbox.delete(selected_task_index)
            task_listbox.insert(selected_task_index, f"{new_task} [{priority}]")
            undo_stack.append(('edit', old_task, new_task, selected_task_index[0]))
            save_tasks()
            voice_feedback(f"Task has been updated to '{new_task}' with {priority} priority.")
    else:
        messagebox.showwarning("Selection Error", "Please select a task to edit.")

def undo():
    if undo_stack:
        action = undo_stack.pop()
        if action[0] == 'add':
            task_listbox.delete(tk.END)
            redo_stack.append(action)
            voice_feedback("Last task addition has been undone.")
        elif action[0] == 'delete':
            task_listbox.insert(action[2], action[1])
            redo_stack.append(action)
            voice_feedback("Last task deletion has been undone.")
        elif action[0] == 'edit':
            task_listbox.delete(action[3])
            task_listbox.insert(action[3], action[1])
            redo_stack.append(action)
            voice_feedback("Last task edit has been undone.")
        elif action[0] == 'complete':
            task_listbox.delete(action[2])
            task_listbox.insert(action[2], action[1])
            redo_stack.append(action)
            voice_feedback("Last task completion has been undone.")
        elif action[0] == 'archive':
            task_listbox.insert(action[2], action[1])
            redo_stack.append(action)
            voice_feedback("Last task archival has been undone.")
        save_tasks()

def redo():
    if redo_stack:
        action = redo_stack.pop()
        if action[0] == 'add':
            add_task(task_input=action[1])
            voice_feedback("Last undone task addition has been redone.")
        elif action[0] == 'delete':
            task_listbox.delete(action[2])
            save_tasks()
            voice_feedback("Last undone task deletion has been redone.")
        elif action[0] == 'edit':
            task_listbox.delete(action[3])
            task_listbox.insert(action[3], action[2])
            save_tasks()
            voice_feedback("Last undone task edit has been redone.")
        elif action[0] == 'complete':
            mark_task_complete()
            voice_feedback("Last undone task completion has been redone.")
        elif action[0] == 'archive':
            archive_task()
            voice_feedback("Last undone task archival has been redone.")
        save_tasks()

# Function to archive completed tasks
def archive_task():
    selected_task_index = task_listbox.curselection()
    if selected_task_index:
        task = task_listbox.get(selected_task_index)
        task_listbox.delete(selected_task_index)
        with open(ARCHIVE_FILE, "a") as archive_file:
            archive_file.write(task + "\n")
        undo_stack.append(('archive', task, selected_task_index[0]))
        save_tasks()
        voice_feedback(f"Task '{task}' has been archived.")
    else:
        messagebox.showwarning("Selection Error", "Please select a task to archive.")


# Function to save tasks to a file with error handling
def save_tasks():
    try:
        with open(TASKS_FILE, "w") as file:
            tasks = task_listbox.get(0, tk.END)
            for task in tasks:
                file.write(task + "\n")
    except Exception as e:
        messagebox.showerror("Save Error", f"Error saving tasks: {e}")

# Function to load tasks from a file with error handling
def load_tasks():
    if os.path.exists(TASKS_FILE):
        try:
            with open(TASKS_FILE, "r") as file:
                for task in file.readlines():
                    task_listbox.insert(tk.END, task.strip())
        except Exception as e:
            messagebox.showerror("Load Error", f"Error loading tasks: {e}")

# Function to capture priority via voice
def recognize_priority():
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source)
            priority = recognizer.recognize_google(audio)
            return priority.capitalize()
    except sr.UnknownValueError:
        return None
    except sr.RequestError:
        return None


def listen_for_task():
    try:
        with sr.Microphone() as source:
            audio = recognizer.listen(source)
            task = recognizer.recognize_google(audio)
            priority = determine_priority(task)
            add_task(task_input=task, priority=priority)
    except sr.UnknownValueError:
        voice_feedback("I couldn't understand the task.")
    except sr.RequestError:
        voice_feedback("Voice recognition service is unavailable.")

# Function to add task via voice with enhanced parsing
def add_task_by_voice():
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source)
            task = recognizer.recognize_google(audio)
            task_entry.delete(0, tk.END)
            task_entry.insert(tk.END, task)
            priority = determine_priority(task)
            add_task(task_input=task, priority=priority)
    except sr.UnknownValueError:
        messagebox.showwarning("Voice Error", "Could not understand the task.")
    except sr.RequestError:
        messagebox.showwarning("Voice Error", "Issue with the speech recognition service.")
        
def determine_priority(task):
    if re.search(r"\burgent\b|\bimportant\b|\bASAP\b", task, re.IGNORECASE):
        return "High"
    elif re.search(r"\btomorrow\b|\bsoon\b|\bnext week\b", task, re.IGNORECASE):
        return "Medium"
    elif re.search(r"\blow\b|\bwhenever\b", task, re.IGNORECASE):
        return "Low"
    return "Normal"  # Default priority if none specified
# Natural language processing for dates in task descriptions
def parse_due_date(task):
    if "tomorrow" in task:
        return datetime.now() + timedelta(days=1)
    # Additional NLP parsing can be added here
    return None

# Function to apply hover effect to buttons with animation
def on_enter(e):
    e.widget['background'] = theme['button_hover']
    e.widget['font'] = ('Arial', 12, 'bold')

def on_leave(e):
    e.widget['background'] = theme['button_bg']
    e.widget['font'] = ('Arial', 10, 'normal')

# Dark and light mode toggle functionality
def toggle_theme():
    global theme
    theme = dark_mode if theme == light_mode else light_mode
    apply_theme()
    voice_feedback("Theme has been toggled.")

# Apply theme to the interface
def apply_theme():
    root.config(bg=theme['bg'])
    container_frame.config(bg=theme['bg'])
    task_entry.config(bg=theme['entry_bg'], fg=theme['fg'])
    task_listbox.config(bg=theme['list_bg'], fg=theme['fg'], selectbackground=theme['highlight'])
    
    for button in button_widgets:
        button.config(bg=theme['button_bg'], fg=theme['fg'], activebackground=theme['highlight'])


# Create the main application window
root = tk.Tk()
root.title("To-Do List MD AAMIR")
root.geometry("500x800")
root.config(bg=theme['bg'])

# Container frame for centering alignment
container_frame = tk.Frame(root, bg=theme['bg'])
container_frame.pack(expand=True)

# Task entry field
task_entry = tk.Entry(container_frame, width=40)
task_entry.pack(pady=10)

# Task listbox to display tasks
task_listbox = tk.Listbox(container_frame, width=50, height=20, selectmode=tk.SINGLE)
task_listbox.pack(pady=5)

# Define icon size
icon_size = (24, 24)

button_widgets = []
# Load icons (Make sure to place your icon files in the same directory or provide correct paths)
add_icon = PhotoImage(file="add_icon.png")  # Replace with your icon file paths
delete_icon = PhotoImage(file="delete_icon.png")
complete_icon = PhotoImage(file="complete_icon.png")
edit_icon = PhotoImage(file="edit_icon.png")
voice_icon = PhotoImage(file="voice_icon.png")
theme_icon = PhotoImage(file="theme_icon.png")
archive_icon = PhotoImage(file="archive_icon.png")
undo_icon = PhotoImage(file="undo_icon.png")
redo_icon = PhotoImage(file="redo_icon.png")

# Updated button configurations with PIL for icons  
buttons = {
    "Add Task":{"command": add_task, "icon": ImageTk.PhotoImage(Image.open("add_icon.png").resize(icon_size))},
    "Delete Task":{"command": delete_task, "icon": ImageTk.PhotoImage(Image.open("delete_icon.png").resize(icon_size))},
    "Mark Completed":{"command": mark_task_complete, "icon": ImageTk.PhotoImage(Image.open("complete_icon.png").resize(icon_size))},
    "Edit Task":{"command": edit_task, "icon": ImageTk.PhotoImage(Image.open("edit_icon.png").resize(icon_size))},
    "Add Task by Voice":{"command": add_task_by_voice, "icon": ImageTk.PhotoImage(Image.open("voice_icon.png").resize(icon_size))},
    "Toggle Theme":{"command": toggle_theme, "icon": ImageTk.PhotoImage(Image.open("theme_icon.png").resize(icon_size))},
    "Archive Completed Tasks":{"command": archive_task, "icon": ImageTk.PhotoImage(Image.open("archive_icon.png").resize(icon_size))},
    "Undo":{"command": undo, "icon": ImageTk.PhotoImage(Image.open("undo_icon.png").resize(icon_size))},
    "Redo":{"command": redo, "icon": ImageTk.PhotoImage(Image.open("redo_icon.png").resize(icon_size))}
}
# Create buttons with icons
for label, props in buttons.items():
    button = tk.Button(container_frame, text=label, command=props['command'], image=props['icon'], compound="left")
    button.pack(pady=5, fill='x')
    button.bind("<Enter>", on_enter)
    button.bind("<Leave>", on_leave)
    button_widgets.append(button)

# Apply theme settings to start
apply_theme()
load_tasks()
root.mainloop()
