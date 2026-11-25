@echo off
cd /d "%~dp0.."
py -X utf8 assembler.py examples\copy.csv out\copy.bin
py -X utf8 interpreter.py out\copy.bin out\copy.json 1000:1017
