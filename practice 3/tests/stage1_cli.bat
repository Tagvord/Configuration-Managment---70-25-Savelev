@echo off
rem Этап 1: поля A и B для тестов из спецификации
cd /d "%~dp0.."
py -X utf8 assembler.py examples\spec.csv out\spec.bin --test
