@echo off
cd /d "%~dp0.."
py -X utf8 assembler.py examples\spec.csv out\spec.bin --test
