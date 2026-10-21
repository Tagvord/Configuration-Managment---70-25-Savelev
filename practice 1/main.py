import tkinter as tk
import shlex
import argparse
import configparser
import os

def ls_cmd(args):
    print_line("ls " + str(args))

def cd_cmd(args):
    print_line("cd " + str(args))

def conf_dump_cmd(args):
    print_params(params)

def exit_cmd(args):
    root.destroy()

commands = {'ls': ls_cmd, 
            'cd': cd_cmd, 
            # 'clear': clear_cmd, 
            'conf-dump': conf_dump_cmd,
            'exit': exit_cmd}

def execute(line):
    """Исполнение команды"""
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
    """Вывод строки в текстовое поле"""
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

def run_script(path):
    """Запускает построчно команды из указанного файла"""
    try:
        with open(path, encoding="UTF-8") as f:
            ln = f.read().splitlines()
    except OSError as e:
        print_line(f"script error: {e}")
        return
    for line in ln:
        try:
            if not root.winfo_exists():
                return
        except tk.TclError:
            return
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        print_line("$ " + line)
        execute(line)
    

def print_params(params):
    """Вывод полученных параметров из командной строки в поле текста"""
    for key, value in params.items():
        print_line(f'{key}={value}')

def parce_CMD_args():
    """Получение аргументов переданных в командной строке при вызове"""
    parcer = argparse.ArgumentParser()
    parcer.add_argument('--vfs')
    parcer.add_argument('--scripts')
    parcer.add_argument('--config')
    return parcer.parse_args()

params = {
    'vfs':None,
    'scripts':None,
    'config': None
}

if __name__ == '__main__':
    cli = parce_CMD_args()
    
    cfg = configparser.ConfigParser()
    if cli.config:
        cfg.read(cli.config)
    file_vfs = cfg.get('emulator', 'vfs', fallback=None)
    file_script = cfg.get('emulator', 'scripts', fallback=None)

    params.update({'vfs': cli.vfs or file_vfs,
                   'scripts': cli.scripts or file_script,
                   'config': cli.config})

    root = tk.Tk()
    root.title(f'VFS: {params["vfs"] if params['vfs'] != None else 'default'}')
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
    print_line('Доступные команды: ls, cd, conf-dump, exit')

    print_params(params)
        
    if params['config'] != None:
        if os.path.exists(params['config']):
            print_line('config error: file not found')
    if params['scripts']:
        run_script(params['scripts'])
    
    root.mainloop()