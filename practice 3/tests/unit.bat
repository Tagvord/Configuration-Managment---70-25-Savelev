@echo off
rem Автоматические проверки
cd /d "%~dp0.."
py -X utf8 -m unittest discover -s tests -v
