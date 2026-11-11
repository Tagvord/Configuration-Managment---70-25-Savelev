# Вариант 18. Визуализатор графа зависимостей пакетов Alpine Linux

Строит граф зависимостей пакета Alpine (apk) и рисует его в SVG. Индекс `APKINDEX.tar.gz`
скачивается и разбирается вручную, без менеджера пакетов и сторонних библиотек.

Нужны Python 3.11+ и Graphviz (команда `dot`).

Из корня репозитория в Windows можно запустить `.\run.bat examples\cycle.toml`.
Скрипт принимает пути к конфигам относительно папки `practice 2`.

При запуске напрямую из папки `practice 2`:

```sh
python main.py config.toml           # граф на языке Graphviz + картинка SVG
python main.py config.toml --order   # порядок загрузки зависимостей
```

Настройки (`config.toml`): `package`, `repository`, `test_mode`, `version`, `output_file`, `filter`.
Тестовые графы и примеры ошибок конфигурации лежат в `examples/`, картинки — в `images/`.
