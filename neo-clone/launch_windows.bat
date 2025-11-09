@echo off
REM launch_windows.bat - simple launcher for neo-clone (Windows)
SETLOCAL
python -c "import sys; print('Python', sys.version)"
IF %ERRORLEVEL% NEQ 0 (
  echo Python is not found in PATH. Please install Python 3.9+ and add to PATH.
  exit /b 1
)
REM Pass all args to main.py
python "%~dp0\main.py" %*
ENDLOCAL
