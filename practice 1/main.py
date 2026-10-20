import tkinter as tk
import shlex

def print_line(string):
    text.config(state='normal')
    text.insert("end", string + '\n')
    text.config(state="disabled")
    text.see("end")

def on_enter(event):
    """Обработка ввода в entry"""
    line = entry.get()
    entry.delete(0, "end")
    print_line("$ " + line)

if __name__ == '__main__':
    root = tk.Tk()
    root.title('VFS: default') # ЗАГЛУШКА, ПОМЕНЯТЬ
    root.geometry("800x400")
    
    scrollbar = tk.Scrollbar(root)
    text = tk.Text(root, state="disabled", yscrollcommand=scrollbar.set)

    entry = tk.Entry(root)
    entry.focus()
    entry.bind("<Return>", on_enter)
    entry.pack(side="bottom", fill="x")

    scrollbar.config(command=text.yview)
    scrollbar.pack(side='right', fill='y')
    text.pack(side="top", fill="both", expand=True)
    
    
    root.mainloop()