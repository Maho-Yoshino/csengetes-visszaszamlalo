cls
@echo off
if not exist ".venv" (
	echo Virtual environment doesn't exist, running setup
	call setup
)
cd %~dp0
echo [Packager] Starting Packager
%~dp0.venv\Scripts\python.exe -m PyInstaller -y -F -w --distpath "%~dp0" --workpath "%~dp0\output\work" -i "%~dp0\icon.ico" -n "csengo"  --clean "%~dp0\csengo.py"
if not exist "output" (
	echo An error happened while creating package.
)
if exist "output" (
	del output
	echo Package Made (it can be found in the root directory)
)
pause
exit