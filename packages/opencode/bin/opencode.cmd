@echo off
setlocal enabledelayedexpansion

rem Get the directory of this script
set "script_dir=%~dp0"
set "script_dir=%script_dir:~0,-1%"

rem Get the root directory (two levels up from bin)
for %%i in ("%script_dir%") do set "parent_dir=%%~dpi"
for %%i in ("%parent_dir%") do set "root_dir=%%~dpi"
set "root_dir=%root_dir:~0,-1%"

rem Path to the TUI binary
set "tui_binary=%root_dir%\packages\tui\opencode.exe"

rem Check if TUI binary exists, if not try to build it
if not exist "%tui_binary%" (
    echo Building TUI binary...
    pushd "%root_dir%\packages\tui"
    go build -o opencode.exe ./cmd/opencode
    if errorlevel 1 (
        echo Failed to build TUI
        exit /b 1
    )
    popd
)

rem Run the TUI binary with all arguments
"%tui_binary%" %*