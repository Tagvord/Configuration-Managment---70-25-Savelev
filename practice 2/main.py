
import gzip
import io
import os
import re
import sys
import tarfile
import tomllib
import urllib.request

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


def download_index(url):
    """Скачивает APKINDEX.tar.gz и возвращает текст файла APKINDEX из архива."""
    url = url.rstrip("/") + "/APKINDEX.tar.gz"
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            data = response.read()
        # Архив содержит два склеенных gzip-потока: подпись и индекс.
        with tarfile.open(fileobj=io.BytesIO(gzip.decompress(data)), ignore_zeros=True) as archive:
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
    """Возвращает версии пакетов с зависимостями и поставщиков виртуальных пакетов."""
    versions, providers = {}, {}
    for block in text.split("\n\n"):
        fields = {}
        for line in block.splitlines():
            if line[1:2] == ":":
                fields[line[0]] = line[2:]
        if "P" not in fields:
            continue
        versions.setdefault(fields["P"], {})[fields["V"]] = fields.get("D", "").split()
        for item in fields.get("p", "").split():
            providers.setdefault(item.split("=", 1)[0], fields["P"])
    return versions, providers


def apk_dependencies(repo, name, version):
    """Возвращает имена пакетов, от которых пакет зависит напрямую."""
    versions, providers = repo
    if name not in versions:
        return []
    if version == "latest":
        version = next(iter(versions[name]))
    result = []
    for token in versions[name][version]:
        if token.startswith("!"):  # Конфликт пакетов.
            continue
        dep = re.split(r"[<>=~]", token, maxsplit=1)[0]
        dep = dep if dep in versions else providers.get(dep)
        if dep is None:
            print(f"Предупреждение: зависимость {token} пакета {name} не найдена",
                  file=sys.stderr)
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
                    error(f"{path}, строка {number}: ожидается 'ИМЯ: ЗАВИСИМОСТИ'")
                name, deps = line.split(":", 1)
                names = [name.strip(), *deps.split()]
                for package in names:
                    if not (package.isascii() and package.isalpha() and package.isupper()):
                        error(f"{path}, строка {number}: имя '{package}' — не большие латинские буквы")
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
        error(f"версии {version} нет, доступны: {', '.join(versions[package])}")
    return lambda name: apk_dependencies(repo, name, version if name == package else "latest")


def bfs(level, graph, get_dependencies, skip):
    """Граф в ширину."""
    if not level:
        return
    next_level = []
    queued = set(level)
    for name in level:
        deps = [dep for dep in get_dependencies(name) if not (skip and skip in dep)]
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


def main():
    args = sys.argv[1:]
    show_order = "--order" in args
    if show_order:
        args.remove("--order")
    config_path = args[0] if args else os.path.join(os.path.dirname(__file__), "config.toml")
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

    print(f"Граф зависимостей {root}:")
    for name, deps in graph.items():
        print(f" {name} -> {', '.join(deps) or '—'}")
    for name, dep in cycle_edges:
        print(f"Цикл: {name} -> {dep}")


if __name__ == "__main__":
    main()
