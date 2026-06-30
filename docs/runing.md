# Run and Build Commands

Run these commands from the project root:

```powershell
cd D:\Lyhour_python\Win_UI
```

Do not `cd app` before running the app. The app uses package imports like `app.core...`, so it must be started from the project root.

## Activate Virtual Environment

PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Command Prompt:

```bat
.\.venv\Scripts\activate.bat
```

## Install Requirements

```powershell
python -m pip install -r requirements.txt
```

## Run App

```powershell
python -m app.main
```

Without activating the virtual environment:

```powershell
.\.venv\Scripts\python.exe -m app.main
```

## Check Before Build

```powershell
python scripts\check_before_build.py
```

Without activating the virtual environment:

```powershell
.\.venv\Scripts\python.exe scripts\check_before_build.py
```

## Build EXE

```powershell
python scripts\build_exe.py
```

Without activating the virtual environment:

```powershell
.\.venv\Scripts\python.exe scripts\build_exe.py
```

The exe output will be created in:

```text
dist\KIEC Engineering Consulting\KIEC Engineering Consulting.exe
```
