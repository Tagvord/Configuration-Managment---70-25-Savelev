import os
import sys
import tomllib
from pathlib import Path

PARAMS = {
    "package": str,
    "repository": str,
    "test_mode": bool,
    "version": str,
    "output_file": str,
    "filter": str,
}

def error(message):
    raise SystemExit(f"Ошибка: {message}")

def load_config(path):
    try:
        with open(path, 'rb') as f:
            cfg = tomllib.load(f)
    except OSError as exc:
        error(f'не удалось открыть файл конфигурации: {exc}')
    except (tomllib.TOMLDecodeError, UnicodeDecodeError):
        error('неверный формат TOML')

    for name in cfg:
        if name not in PARAMS:
            error(f'неизвестный параметр {name}')
    for name, typ in PARAMS.items():
        if name not in cfg:
            error(f'отсутствует параметр "{name}"')
        if type(cfg[name]) is not typ:
            error(f'неверный тип у параметра "{name}"')
    package = cfg["package"]
    if not package:
        error("имя пакета не задано")
    if cfg["test_mode"]:
        if not (package.isascii() and package.isalpha() and package.isupper()):
            error('в тестовом режиме пакета неверный ввод')
        if not os.path.isfile(cfg["repository"]):
            error('файл тестового репозитория не найден')
    elif not cfg["repository"].startswith(("http://", "https://")):
        error("репозиторий должен начинаться с http:// или с https://")
    if not cfg["version"]:
        error("версия не задана")
    if not cfg["output_file"].endswith(".svg"):
        error("имя файла изображения должно оканчиваться на .svg")
    out_dir = os.path.dirname(cfg["output_file"])
    if out_dir and not os.path.isdir(out_dir):
        error("указанный каталог не существует")
    if cfg["filter"] and cfg["filter"] in package:
        error("подстрока фильтра входит в имя пакета")
    return cfg


cfg = load_config(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).with_name("config.toml"))
for key, val in cfg.items():
    print(f"{key} = {val}")
