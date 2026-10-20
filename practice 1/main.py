import tkinter as tk
import shlex

def ls_cmd(args):
    print_line("ls " + str(args))

def cd_cmd(args):
    print_line("cd " + str(args))

def exit_cmd(args):
    root.destroy()


commands = {'ls': ls_cmd, 
            'cd': cd_cmd, 
            # 'clear': clear_cmd, 
            'exit': exit_cmd}

def execute(line):
    try:
        parts = shlex.split(line)
    except ValueError as e:
        print_line(f"parsing error: {e}")
        return
    if not parts:
        return
    name, args = parts[0], parts[1:]
    if name not in commands:
        print_line(f'{name}: command not found')
        return
    commands[name](args)

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
    execute(line)


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