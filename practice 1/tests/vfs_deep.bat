@echo off
rem VFS с 3+ уровнями вложенности, тест всех команд
cd ..
py main.py --vfs vfs/deep.xml --scripts script/test_all.txt
