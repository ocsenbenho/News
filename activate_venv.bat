@echo off
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo Failed to activate virtual environment.
    echo Please make sure you're in the correct directory and the environment is set up properly.
) else (
    echo Virtual environment activated successfully.
)
pause