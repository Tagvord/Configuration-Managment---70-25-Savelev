"""Запуск: python main.py [config.toml] [--order] из папки practice 2."""

import gzip
import io
import os
import re
import subprocess
import sys
import tarfile
import tomllib
import urllib.request
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
    """Завершает программу с сообщением об ошибке."""
    raise SystemExit(f"Ошибка: {message}")


def validate_fields(cfg):
    """Проверяет состав и типы полей конфигурации."""
    for name in cfg:
        if name not in PARAMS:
            error(f'неизвестный параметр {name}')
    for name, typ in PARAMS.items():
        if name not in cfg:
            error(f'отсутствует параметр "{name}"')
        if type(cfg[name]) is not typ:
            error(f'неверный тип у параметра "{name}"')


def validate_repository(cfg):
    """Проверяет имя корневого пакета и источник зависимостей."""
    package = cfg["package"]
    if not package:
        error("имя пакета не задано")
    if cfg["test_mode"]:
        if not re.fullmatch(r"[A-Z]+", package):
            error('в тестовом режиме пакета неверный ввод')
        if not os.path.isfile(cfg["repository"]):
            error('файл тестового репозитория не найден')
    elif not cfg["repository"].startswith(("http://", "https://")):
        error("репозиторий должен начинаться с http:// или с https://")


def validate_graph_options(cfg):
    """Проверяет версию, путь изображения и фильтр корневого пакета."""
    if not cfg["version"]:
        error("версия не задана")
    if not cfg["output_file"].endswith(".svg"):
        error("имя файла изображения должно оканчиваться на .svg")
    out_dir = os.path.dirname(cfg["output_file"])
    if out_dir and not os.path.isdir(out_dir):
        error("указанный каталог не существует")
    if cfg["filter"] and cfg["filter"] in cfg["package"]:
        error("подстрока фильтра входит в имя пакета")


def load_config(path):
    """Читает TOML и проверяет настройки перед построением графа."""
    try:
        with open(path, "rb") as file:
            cfg = tomllib.load(file)
    except OSError as exc:
        error(f"не удалось открыть файл конфигурации: {exc}")
    except (tomllib.TOMLDecodeError, UnicodeDecodeError):
        error("неверный формат TOML")

    validate_fields(cfg)
    validate_repository(cfg)
    validate_graph_options(cfg)
    return cfg


def download_index(url):
    """Читает APKINDEX из склеенных gzip-потоков с подписью и индексом."""
    url = url.rstrip("/") + "/APKINDEX.tar.gz"
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            data = response.read()
        contents = io.BytesIO(gzip.decompress(data))
        with tarfile.open(fileobj=contents, ignore_zeros=True) as archive:
            index_file = archive.extractfile("APKINDEX")
            if index_file is None:
                error(f"{url} не похож на индекс репозитория Alpine")
            with index_file:
                return index_file.read().decode("utf-8")
    except OSError as exc:
        error(f"не удалось получить {url}: {exc}")
    except (tarfile.TarError, KeyError, EOFError, UnicodeDecodeError):
        error(f"{url} не похож на индекс репозитория Alpine")


def parse_index(text):
    """Возвращает версии с зависимостями и поставщиков виртуальных пакетов."""
    versions, providers = {}, {}
    for block in text.split("\n\n"):
        fields = {}
        for line in block.splitlines():
            if line[1:2] == ":":
                fields[line[0]] = line[2:]
        if "P" not in fields:
            continue
        package_versions = versions.setdefault(fields["P"], {})
        package_versions[fields["V"]] = fields.get("D", "").split()
        for item in fields.get("p", "").split():
            providers.setdefault(item.split("=", 1)[0], fields["P"])
    return versions, providers


def apk_dependencies(repo, name, version):
    """Возвращает прямые зависимости, пропуская записи о конфликтах."""
    versions, providers = repo
    if name not in versions:
        return []
    if version == "latest":
        version = next(iter(versions[name]))
    result = []
    for token in versions[name][version]:
        if token.startswith("!"):
            continue
        dep = re.split(r"[<>=~]", token, maxsplit=1)[0]
        dep = dep if dep in versions else providers.get(dep)
        if dep is None:
            print(
                f"Предупреждение: зависимость {token} "
                f"пакета {name} не найдена",
                file=sys.stderr,
            )
        elif dep != name and dep not in result:
            result.append(dep)
    return result


def load_test_repo(path):
    """Чтение тестового графа 'A: B C'."""
    graph = {}
    try:
        with open(path, encoding="utf-8") as file:
            for number, line in enumerate(file, 1):
                line = line.split("#", 1)[0].strip()
                if not line:
                    continue
                if ":" not in line:
                    error(
                        f"{path}, строка {number}: "
                        "ожидается 'ИМЯ: ЗАВИСИМОСТИ'"
                    )
                name, deps = line.split(":", 1)
                names = [name.strip(), *deps.split()]
                for package in names:
                    if not re.fullmatch(r"[A-Z]+", package):
                        error(
                            f"{path}, строка {number}: "
                            f"имя '{package}' — не большие латинские буквы"
                        )
                graph[names[0]] = names[1:]
    except (OSError, UnicodeDecodeError) as exc:
        error(f"не удалось прочитать тестовый репозиторий {path}: {exc}")
    return graph


def get_dependencies_function(cfg):
    """Возвращает функцию зависимостей пакета."""
    package, version = cfg["package"], cfg["version"]
    if cfg["test_mode"]:
        test_graph = load_test_repo(cfg["repository"])
        if package not in test_graph:
            error(f"пакет {package} не найден в тестовом репозитории")
        return lambda name: test_graph.get(name, [])

    repo = parse_index(download_index(cfg["repository"]))
    versions = repo[0]
    if package not in versions:
        error(f"пакет {package} не найден в репозитории")
    if version != "latest" and version not in versions[package]:
        available = ", ".join(versions[package])
        error(f"версии {version} нет, доступны: {available}")

    def get_apk_dependencies(name):
        """Применяет выбранную версию к корневому пакету."""
        selected = version if name == package else "latest"
        return apk_dependencies(repo, name, selected)

    return get_apk_dependencies


def bfs(level, graph, get_dependencies, skip):
    """Граф в ширину."""
    if not level:
        return
    next_level = []
    queued = set(level)
    for name in level:
        deps = [
            dep for dep in get_dependencies(name) if not (skip and skip in dep)
        ]
        graph[name] = deps
        for dep in deps:
            if dep not in graph and dep not in queued:
                next_level.append(dep)
                queued.add(dep)
    bfs(next_level, graph, get_dependencies, skip)


def dfs(graph, root):
    """Обход в глубину"""
    order, state, cycle_edges = [], {}, []

    def visit(name):
        """Помечает обратные рёбра и добавляет пакет после его зависимостей."""
        state[name] = "в обработке"
        for dep in graph[name]:
            if state.get(dep) == "в обработке":
                cycle_edges.append((name, dep))
            elif dep not in state:
                visit(dep)
        state[name] = "готов"
        order.append(name)

    visit(root)
    return order, cycle_edges


def to_dot(graph, root, cycle_edges):
    """Преобразует граф зависимостей в формат Graphviz DOT."""
    lines = [
        "digraph dependencies {",
        " node [shape=box];",
        f' "{root}" [style=filled, fillcolor=lightblue];',
    ]
    cycle_edges = set(cycle_edges)
    for name, deps in graph.items():
        if not deps:
            lines.append(f' "{name}";')
        for dep in deps:
            color = " [color=red]" if (name, dep) in cycle_edges else ""
            lines.append(f' "{name}" -> "{dep}"{color};')
    lines.append("}")
    return "\n".join(lines)


def save_svg(dot_text, path):
    """Сохраняет граф в SVG с помощью команды dot."""
    try:
        subprocess.run(
            ["dot", "-Tsvg", "-o", path],
            input=dot_text,
            text=True,
            check=True,
        )
    except FileNotFoundError:
        error("не установлен Graphviz (нужна команда dot)")
    except subprocess.CalledProcessError:
        error("Graphviz не смог построить изображение")


def main():
    """Строит граф и выводит порядок загрузки либо сохраняет SVG."""
    args = sys.argv[1:]
    show_order = "--order" in args
    if show_order:
        args.remove("--order")
    project_dir = Path(__file__).resolve().parent.parent / "practice 2"
    config_path = args[0] if args else project_dir / "config.toml"
    cfg = load_config(config_path)
    root = cfg["package"]
    graph = {}
    bfs([root], graph, get_dependencies_function(cfg), cfg["filter"])
    order, cycle_edges = dfs(graph, root)
    if show_order:
        print(f"Порядок загрузки зависимостей {root}:")
        for number, name in enumerate(order, 1):
            print(f" {number}. {name}")
        for name, dep in cycle_edges:
            print(f"Цикл: связь {name} -> {dep} пропущена")
        return

    for name, dep in cycle_edges:
        print(f"Цикл: {name} -> {dep}", file=sys.stderr)
    dot_text = to_dot(graph, root, cycle_edges)
    print(dot_text)
    save_svg(dot_text, cfg["output_file"])
    print(f"Изображение сохранено в {cfg['output_file']}", file=sys.stderr)


if __name__ == "__main__":
    main()
