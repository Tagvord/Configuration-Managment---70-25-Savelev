@echo off
rem Тест приоритета: --vfs из командной строки перекрывает vfs из config.ini
cd ..
py main.py --config config.ini --vfs vfs/other.xml
