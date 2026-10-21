@echo off
rem Ошибки загрузки: битый XML, несуществующий файл VFS
cd ..
py main.py --vfs vfs/broken.xml
py main.py --vfs vfs/nothing.xml
