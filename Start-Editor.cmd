@echo off
setlocal
cd /d "%~dp0"
set "UV_EXE=%USERPROFILE%\.local\bin\uv.exe"
if not exist "%UV_EXE%" set "UV_EXE=uv"
set "PYTHON_EXE=3.12"
for /d %%D in ("%APPDATA%\uv\python\cpython-3.12*") do if exist "%%~fD\python.exe" set "PYTHON_EXE=%%~fD\python.exe"
if exist "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" set "PYTHON_EXE=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
"%UV_EXE%" run --python "%PYTHON_EXE%" scripts/launch.py editor
exit /b %errorlevel%
