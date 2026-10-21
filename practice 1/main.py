import tkinter as tk
import shlex
import argparse
import configparser
import os
import base64
import binascii
import xml.etree.ElementTree as ET

vfs_root = {'type': 'dir', 'children': {}}
vfs_name = 'default'
cwd = []   

def load_node(el):
    if el.tag == 'file':
        data = el.text or ''
        if el.get('encoding') == 'base64':
            data = base64.b64decode(data)
        return {'type': 'file', 'data': data}
    return {'type': 'dir', 'children': {c.get('name'): load_node(c) for c in el}}


def load_vfs(path):
    """Возвращает имя и корень"""
    root_el = ET.parse(path).getroot()
    return root_el.get('name', 'vfs'), load_node(root_el)

def resolve(path):
    """Превращает путь в список имён от корня"""
    parts = [] if path.startswith('/') else list(cwd)
    for p in path.split('/'):
        if p in ('', '.'):
            continue
        if p == '..':
            if parts:
                parts.pop()
        else:
            parts.append(p)
    return parts

def get_node(parts):
    """Узел по списку имён или None"""
    node = vfs_root
    for p in parts:
        if node['type'] != 'dir' or p not in node['children']:
            return None
        node = node['children'][p]
    return node

def prompt():
    return '/' + '/'.join(cwd) + ' $ '

def ls_cmd(args):
    path = args[0] if args else '.'
    node = get_node(resolve(path))
    if node is None:
        print_line(f"ls: {path}: No such file or directory")
    elif node['type'] == 'dir':
        for name in node['children']:
            print_line(name)
    else:
        print_line(path)

def cd_cmd(args):
    global cwd
    path = args[0] if args else '/'
    parts = resolve(path)
    node = get_node(parts)
    if node is None:
        print_line(f"cd: {path}: No such file or directory")
    elif node['type'] != 'dir':
        print_line(f"cd: {path}: Not a directory")
    else:
        cwd = parts

def pwd_cmd(args):
    print_line('/' + '/'.join(cwd))

def conf_dump_cmd(args):
    print_params(params)

def exit_cmd(args):
    root.destroy()

commands = {'ls': ls_cmd, 
            'cd': cd_cmd,
            'pwd': pwd_cmd,
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
    print_line(prompt() + line)
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
        print_line(prompt() + line)
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
    root.title('VFS: default')
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
    print_line('Доступные команды: ls, cd, pwd, conf-dump, exit')

    print_params(params)

    if params['config'] and not os.path.exists(params['config']):
        print_line('config error: file not found')
    if params['vfs']:
        try:
            vfs_name, vfs_root = load_vfs(params['vfs'])
            root.title(f'VFS: {vfs_name}')
        except (OSError, ET.ParseError, binascii.Error) as e:
            print_line(f'vfs error: {e}')
    if params['scripts']:
        run_script(params['scripts'])
    
    root.mainloop()