@echo off
cd /d "%~dp0.."
for %%n in (1 2 3) do (
    echo === vectors%%n.csv ===
    py -X utf8 assembler.py examples\vectors%%n.csv out\vectors%%n.bin
    py -X utf8 interpreter.py out\vectors%%n.bin out\vectors%%n.json 1000:1019
)
