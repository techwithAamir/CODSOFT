import tkinter as tk
from tkinter import messagebox
import math
import os

class EnhancedCalculator:
    def __init__(self, master):
        self.master = master
        self.master.title("Enhanced Calculator")
        self.master.geometry("400x600")
        self.master.configure(bg="#2E2E2E")

        self.result_var = tk.StringVar()
        self.memory = 0
        self.history = []
        self.dark_mode = True

        # Check for and load history from file
        self.history_file = "calculator_history.txt"
        self.load_history()

        # Configure rows and columns for responsiveness
        for i in range(8):
            self.master.grid_rowconfigure(i, weight=1)
        for i in range(4):
            self.master.grid_columnconfigure(i, weight=1)

        # Display field for calculation results
        self.display = tk.Entry(master, textvariable=self.result_var, font=("Arial", 24), bd=10, insertwidth=2,
                                width=14, borderwidth=4, bg="#FFFFFF", justify='right')
        self.display.grid(row=0, column=0, columnspan=4, sticky="nsew", pady=(10, 10), padx=(10, 10))

        # Memory display label
        self.memory_label = tk.Label(master, text="Memory: 0", font=("Arial", 12), bg="#2E2E2E", fg="white", anchor="e")
        self.memory_label.grid(row=1, column=0, columnspan=4, sticky="nsew", padx=10)

        # Button color definitions
        button_colors = {
            'C': '#FF6347', 'CE': '#FF6347', '=': '#32CD32', '√': '#FFD700', '^': '#6A5ACD',
            '%': '#FF4500', '1/x': '#FF7F50', 'sin': '#8B008B', 'cos': '#20B2AA',
            'tan': '#FF1493', 'ln': '#66CDAA', 'log': '#FF8C00', 'M+': '#7CFC00',
            'M-': '#DB7093', 'MR': '#AFEEEE', 'MC': '#DA70D6', '+': '#FFA07A', 
            '-': '#FFA07A', '*': '#FFA07A', '/': '#FFA07A', '(': '#D3D3D3', ')': '#D3D3D3'
        }

        # Define buttons layout for optimal arrangement
        buttons = [
            'C', 'CE', 'M+', 'M-',
            'MR', 'MC', '√', '^',
            'sin', 'cos', 'tan', '%',
            'ln', 'log', '1/x', '(', ')',
            '7', '8', '9', '/',
            '4', '5', '6', '+',
            '1', '2', '3', '-',
            '0', '.', '=', '*'
        ]

        # Place buttons with styling and tooltip hints
        row_val, col_val = 2, 0
        for button in buttons:
            color = button_colors.get(button, '#D3D3D3')
            btn = tk.Button(master, text=button, font=("Arial", 16), bg=color, fg="white", activebackground="#A9A9A9",
                            command=lambda b=button: self.on_button_click(b))
            btn.grid(row=row_val, column=col_val, sticky="nsew", padx=5, pady=5)
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg="#A9A9A9"))
            btn.bind("<Leave>", lambda e, b=btn, c=color: b.config(bg=c))
            self.create_tooltip(btn, f"Button '{button}'")

            col_val += 1
            if col_val > 3:
                col_val = 0
                row_val += 1

        # Add a history and toggle button at the bottom row for modes
        self.history_button = tk.Button(master, text="History", font=("Arial", 12), command=self.show_history)
        self.history_button.grid(row=row_val + 1, column=0, columnspan=2, sticky="nsew", padx=10, pady=(0, 10))

        self.mode_toggle_button = tk.Button(master, text="Toggle Mode", font=("Arial", 12), command=self.toggle_mode)
        self.mode_toggle_button.grid(row=row_val + 1, column=2, columnspan=2, sticky="nsew", padx=10, pady=(0, 10))

        # Bind keyboard input
        master.bind("<Key>", self.on_key_press)
        master.bind("<Control-c>", lambda e: self.copy_to_clipboard())
        master.bind("<Control-v>", lambda e: self.paste_from_clipboard())

    def update_memory_label(self):
        self.memory_label.config(text=f"Memory: {self.memory}")

    def on_button_click(self, char):
        if char == 'C':
            self.result_var.set("")
        elif char == 'CE':
            self.result_var.set(self.result_var.get()[:-1])  # Clear last entry
        elif char == '=':
            self.calculate_result()
        elif char == '√':
            self.calculate_square_root()
        elif char == '^':
            self.result_var.set(self.result_var.get() + '**')
        elif char == '%':
            self.calculate_percentage()
        elif char == '1/x':
            self.calculate_reciprocal()
        elif char in ['sin', 'cos', 'tan', 'ln', 'log']:
            self.calculate_trig_or_log(char)
        elif char == 'M+':
            self.add_to_memory()
        elif char == 'M-':
            self.subtract_from_memory()
        elif char == 'MR':
            self.result_var.set(self.memory)
        elif char == 'MC':
            self.memory = 0
            self.update_memory_label()
        else:
            self.result_var.set(self.result_var.get() + char)

    def calculate_result(self):
        try:
            expression = self.result_var.get()
            if expression:
                result = round(eval(expression), 4)  # Format result to 4 decimal places
                self.history.append(f"{expression} = {result}")
                self.save_history()
                self.result_var.set(result)
        except Exception:
            messagebox.showerror("Error", "Invalid Input")
            self.result_var.set("Error")

    def calculate_square_root(self):
        try:
            value = float(self.result_var.get())
            self.result_var.set(round(math.sqrt(value), 4))  # 4 decimal places
        except ValueError:
            messagebox.showerror("Error", "Invalid Input")
            self.result_var.set("Error")

    def calculate_percentage(self):
        try:
            value = float(self.result_var.get())
            self.result_var.set(round(value / 100, 4))  # 4 decimal places
        except ValueError:
            messagebox.showerror("Error", "Invalid Input")
            self.result_var.set("Error")

    def calculate_reciprocal(self):
        try:
            value = float(self.result_var.get())
            if value == 0:
                raise ValueError("Cannot divide by zero")
            self.result_var.set(round(1 / value, 4))  # 4 decimal places
        except ValueError:
            messagebox.showerror("Error", "Invalid Input")
            self.result_var.set("Error")

    def calculate_trig_or_log(self, char):
        try:
            value = float(self.result_var.get())
            result = {
                'sin': math.sin(math.radians(value)),
                'cos': math.cos(math.radians(value)),
                'tan': math.tan(math.radians(value)),
                'ln': math.log(value),
                'log': math.log10(value)
            }.get(char)
            self.result_var.set(round(result, 4))  # 4 decimal places
        except ValueError:
            messagebox.showerror("Error", "Invalid Input")
            self.result_var.set("Error")

    def add_to_memory(self):
        try:
            self.memory += float(self.result_var.get())
            self.update_memory_label()
        except ValueError:
            messagebox.showerror("Error", "Invalid Input")

    def subtract_from_memory(self):
        try:
            self.memory -= float(self.result_var.get())
            self.update_memory_label()
        except ValueError:
            messagebox.showerror("Error", "Invalid Input")

    def on_key_press(self, event):
        char = event.char
        if char.isdigit() or char in '+-*/.()':
            self.result_var.set(self.result_var.get() + char)
        elif char == '\r':  # Enter key
            self.calculate_result()
        elif char == '\b':  # Backspace key
            self.result_var.set(self.result_var.get()[:-1])
        elif event.keysym == 'Escape':
            self.result_var.set("")

    def show_history(self):
        if self.history:
            messagebox.showinfo("History", "\n".join(self.history))
        else:
            messagebox.showinfo("History", "No history available.")

    def toggle_mode(self):
        self.dark_mode = not self.dark_mode
        bg_color, fg_color = ("#2E2E2E", "white") if self.dark_mode else ("#FFFFFF", "black")
        self.master.configure(bg=bg_color)
        self.display.configure(bg=bg_color, fg=fg_color)

    def create_tooltip(self, widget, text):
        tooltip = tk.Toplevel(widget)
        tooltip.withdraw()
        tooltip.overrideredirect(True)
        label = tk.Label(tooltip, text=text, font=("Arial", 8), bg="yellow", relief="solid", bd=1)
        label.pack()
        
        def show_tooltip(event):
            tooltip.geometry(f"+{event.x_root + 10}+{event.y_root + 10}")
            tooltip.deiconify()

        def hide_tooltip(event):
            tooltip.withdraw()

        widget.bind("<Enter>", show_tooltip)
        widget.bind("<Leave>", hide_tooltip)

    def copy_to_clipboard(self):
        self.master.clipboard_clear()
        self.master.clipboard_append(self.result_var.get())

    def paste_from_clipboard(self):
        try:
            paste_val = self.master.clipboard_get()
            self.result_var.set(self.result_var.get() + paste_val)
        except tk.TclError:
            messagebox.showerror("Error", "No text in clipboard")

    def save_history(self):
        with open(self.history_file, 'w') as f:
            f.write("\n".join(self.history))

    def load_history(self):
        if os.path.exists(self.history_file):
            with open(self.history_file, 'r') as f:
                self.history = f.read().splitlines()

# Run the calculator
root = tk.Tk()
app = EnhancedCalculator(root)
root.mainloop()
