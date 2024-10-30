import tkinter as tk
from tkinter import messagebox, simpledialog
import os
import time
import sched
import threading
import speech_recognition as sr
import pyttsx3

# Initialize speech recognizer and text-to-speech engine
recognizer = sr.Recognizer()
engine = pyttsx3.init()

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
    scheduler.enter(delay_seconds, 1, show_reminder, argument=(task,))
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
    try:
        task_index = task_listbox.curselection()[0]
        task = task_listbox.get(task_index)
        undo_stack.append(('delete', task))
        task_listbox.delete(task_index)
        save_tasks()
        voice_feedback(f"Task '{task}' has been deleted.")
    except:
        messagebox.showwarning("Delete Error", "Please select a task to delete.")

# Function to mark a task as completed
def mark_task_completed():
    try:
        task_index = task_listbox.curselection()[0]
        task = task_listbox.get(task_index)
        task_listbox.delete(task_index)
        task_listbox.insert(tk.END, f"{task} (Completed)")
        undo_stack.append(('complete', task))
        voice_feedback(f"Task '{task}' marked as completed.")
        save_tasks()
    except:
        messagebox.showwarning("Complete Error", "Please select a task to mark as completed.")

# Function to edit a task
def edit_task():
    try:
        task_index = task_listbox.curselection()[0]
        task = task_listbox.get(task_index)
        new_task = simpledialog.askstring("Edit Task", f"Edit the task:", initialvalue=task)
        if new_task:
            undo_stack.append(('edit', task, new_task))
            task_listbox.delete(task_index)
            task_listbox.insert(task_index, new_task)
            save_tasks()
            voice_feedback(f"Task has been edited to: {new_task}.")
    except:
        messagebox.showwarning("Edit Error", "Please select a task to edit.")

# Function to undo last operation
def undo():
    if undo_stack:
        action, *data = undo_stack.pop()
        if action == 'add':
            task_listbox.delete(tk.END)
        elif action == 'delete':
            task_listbox.insert(tk.END, data[0])
        elif action == 'complete':
            task_listbox.delete(tk.END)
            task_listbox.insert(tk.END, data[0])
        elif action == 'edit':
            old_task, new_task = data
            index = task_listbox.get(0, tk.END).index(new_task)
            task_listbox.delete(index)
            task_listbox.insert(index, old_task)
        redo_stack.append((action, *data))
        save_tasks()
        voice_feedback("Undo operation performed.")

# Function to redo last undone operation
def redo():
    if redo_stack:
        action, *data = redo_stack.pop()
        if action == 'add':
            task_listbox.insert(tk.END, data[0])
        elif action == 'delete':
            task_listbox.delete(tk.END)
        elif action == 'complete':
            task_listbox.insert(tk.END, f"{data[0]} (Completed)")
        elif action == 'edit':
            task_listbox.delete(task_listbox.get(0, tk.END).index(data[0]))
            task_listbox.insert(tk.END, data[1])
        save_tasks()
        voice_feedback("Redo operation performed.")

# Function to archive completed tasks
def archive_tasks():
    with open(ARCHIVE_FILE, "a") as file:
        for i in range(task_listbox.size()):
            task = task_listbox.get(i)
            if "(Completed)" in task:
                file.write(task + "\n")
                task_listbox.delete(i)
    save_tasks()
    voice_feedback("Archived completed tasks.")

# Function to save tasks to a file
def save_tasks():
    with open(TASKS_FILE, "w") as file:
        tasks = task_listbox.get(0, tk.END)
        for task in tasks:
            file.write(task + "\n")

# Function to load tasks from a file
def load_tasks():
    if os.path.exists(TASKS_FILE):
        with open(TASKS_FILE, "r") as file:
            for task in file.readlines():
                task_listbox.insert(tk.END, task.strip())

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

# Function to add task via voice
def add_task_by_voice():
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source)
            task = recognizer.recognize_google(audio)
            task_entry.delete(0, tk.END)
            task_entry.insert(tk.END, task)
            priority = recognize_priority()
            if priority not in ["High", "Medium", "Low"]:
                priority = "Medium"
            add_task(task_input=task, priority=priority)
    except sr.UnknownValueError:
        messagebox.showwarning("Voice Error", "Could not understand the task.")
    except sr.RequestError:
        messagebox.showwarning("Voice Error", "Issue with the speech recognition service.")

# Create the main application window
root = tk.Tk()
root.title("To-Do List MD AAMIR")
root.geometry("500x650")
root.config(bg=theme['bg'])

# Container frame for centering alignment
container_frame = tk.Frame(root, bg=theme['bg'])
container_frame.pack(expand=True)

# Task entry field
task_entry = tk.Entry(container_frame, width=40)
task_entry.pack(pady=10)

# Task listbox to display tasks
task_listbox = tk.Listbox(container_frame, width=40, height=15, selectmode=tk.SINGLE)
task_listbox.pack(pady=10)

# Button definitions and arrangements
button_widgets = []
buttons = {
    "Add Task": add_task,
    "Delete Task": delete_task,
    "Mark Completed": mark_task_completed,
    "Edit Task": edit_task,
    "Add Task by Voice": add_task_by_voice,
    "Toggle Theme": toggle_theme,
    "Archive Completed Tasks": archive_tasks,
    "Undo": undo,
    "Redo": redo
}

for label, command in buttons.items():
    button = tk.Button(container_frame, text=label, command=command, bg=theme['button_bg'], fg=theme['fg'])
    button.pack(pady=5, fill='x')
    button.bind("<Enter>", on_enter)
    button.bind("<Leave>", on_leave)
    button_widgets.append(button)

# Load tasks and apply the current theme
load_tasks()
apply_theme()

# Start the main loop
root.mainloop()
