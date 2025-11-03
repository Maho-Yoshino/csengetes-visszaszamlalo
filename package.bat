cls
@echo off
echo [Packager] Starting Packager
cd "%~dp0"
if not exist "builds" (
	mkdir builds
)
call ./.venv/scripts/activate
pyinstaller --noconfirm --onefile --windowed --icon "%~dp0icon.ico" --name "Csengetés Visszaszámláló" --clean "%~dp0csengo.py"
call deactivate
echo Package Made (it can be found in "build")
pause
exit