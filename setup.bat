cls
@echo off
echo [Setup] Beginning setup
cd "%~dp0"
if not exist ".venv" (
	echo [Setup] Creating virtual environment
	python -m venv .venv
)
call ./.venv/scripts/activate
pip install --upgrade pip
pip install -r requirements.txt
call deactivate
echo [Setup] Setup complete
pause
exit
