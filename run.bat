@echo off
setlocal
pushd "%~dp0practice 2" || exit /b 1

set "python_exe=python"
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    set "python_exe=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
)
if exist "%ProgramFiles%\Graphviz\bin\dot.exe" (
    set "PATH=%ProgramFiles%\Graphviz\bin;%PATH%"
)

"%python_exe%" -X utf8 main.py %*
set "exit_code=%errorlevel%"
popd
exit /b %exit_code%
