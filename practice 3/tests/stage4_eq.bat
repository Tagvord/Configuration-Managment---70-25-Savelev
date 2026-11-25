@echo off
cd /d "%~dp0.."
py -X utf8 assembler.py examples\eq.csv out\eq.bin
py -X utf8 interpreter.py out\eq.bin out\eq.json 1000:1016
