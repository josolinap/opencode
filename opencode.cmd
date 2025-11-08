@echo off
setlocal enabledelayedexpansion

rem Check if TUI binary exists in the expected location
set "tui_binary=%~dp0packages\tui\opencode.exe"
if not exist "!tui_binary!" (
    echo Building TUI binary...
    pushd "%~dp0packages\tui"
    go build -o opencode.exe ./cmd/opencode
    if errorlevel 1 (
        echo Failed to build TUI
        exit /b 1
    )
    popd
)

rem Run the TUI binary
start /b /wait "" "!tui_binary!" %*