@echo off
rem Ошибки в тексте программы на ассемблере
cd /d "%~dp0.."
for %%f in (examples\errors\*.csv) do (
    echo %%f
    py -X utf8 assembler.py %%f out\error.bin
)
