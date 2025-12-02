@echo off
cd /d "%~dp0"
if not exist ".venv" (
	echo .venv does not exist. Please run setup.bat first.
	exit
)
call .\.venv\Scripts\activate
python .\csengo.py
deactivate
exit