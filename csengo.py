import tkinter as tk, asyncio, logging
import modules.state as state
from tkinter import Tk, messagebox
from tkinter.ttk import Separator
from sys import executable, argv, platform
from datetime import datetime
from os import path, chdir, mkdir, environ
from pathlib import Path
from github import Github, Repository, GitRelease
from ctypes import windll
from ctypes.wintypes import BOOL
from modules.settings import Settings
from modules.tray import setup_tray
from modules.clock import updateCycle, setClickThrough, fontSize, transparencyCheck
logger = logging.getLogger(__name__)
logging.getLogger("PIL").setLevel(logging.WARNING)
logging.getLogger("pystray").setLevel(logging.WARNING)

# region Setting PATH
if path.splitext(argv[0])[1].lower() != ".exe":
	current_dir = path.dirname(path.abspath(__file__))
else:
	current_dir = path.dirname(path.abspath(executable))
chdir(current_dir)
# endregion
# region update handler
class Version:
	"""Uses the principle of 'semantic versioning' (https://semver.org)"""
	major:int
	minor:int = 0
	patch:int = 0
	# 0 - Release
	# 1 - Pre-release
	# 2 - Beta
	# 3 - Alpha
	subversion:int 
	__subver_map = {
		"release": 0,
		"pre-release": 1,
		"beta": 2,
		"alpha": 3
	}
	__inv_subver_map = {v: k for k, v in __subver_map.items()}
	def __init__(self, ver:str):
		self.subversion = 0
		tmp = ver.split(".")
		if len(tmp) > 0:
			self.major = int(tmp[0])
		if len(tmp) > 1:
			self.minor = int(tmp[1])
		if len(tmp) > 2 and "-" in tmp[2]: 
			tmp2 = tmp[2].split("-")
			self.patch = int(tmp2[0])
			self.subversion = self.__subver_map.get(tmp2[1], 0)
		elif len(tmp) > 2:
			self.patch = int(tmp[2])
	def __str__(self):
		return f"{self.major}.{self.minor}.{self.patch}{f"-{self.__inv_subver_map[self.subversion]}" if self.subversion != 0 else ""}"
	def __gt__(self, version:"Version"):
		return (self.major, self.minor, self.patch, -self.subversion) > \
		       (version.major, version.minor, version.patch, -version.subversion)
	def __lt__(self, version:"Version"):
		return (self.major, self.minor, self.patch, -self.subversion) < \
		       (version.major, version.minor, version.patch, -version.subversion)
	def __eq__(self, version:"Version"):
		return (self.major, self.minor, self.patch, self.subversion) == \
		       (version.major, version.minor, version.patch, version.subversion)
VERSION:"Version" = Version("3.0.0")
def checkUpdate():
	logger.info("Checking for updates...")
	repo:Repository = Github().get_repo("Maho-Yoshino/csengetes-visszaszamlalo")
	latest_release:GitRelease = repo.get_releases()[0]
	tag = latest_release.tag_name.lstrip("v")
	latest_version = Version(tag)
	logger.info(f"Latest version online: {latest_version}")
	logger.info(f"Current version: {VERSION}")
	if latest_version > VERSION:
		logger.warning("Update available!")
		return {
			"update_available": True,
			"current": str(VERSION),
			"latest": str(latest_version),
			"url": latest_release.html_url,
			"notes": latest_release.body,
		}
	else:
		logger.info("You're running the newest version.")
		return {
			"update_available": False,
			"current": str(VERSION),
			"latest": str(latest_version),
		}

# endregion
state.settings = Settings()
async def startup(root:Tk):
	state.root.configure(background="black")
	state.root.attributes("-topmost", True)
	state.root.title(state.windowHandle)
	state.root.resizable(False, False)
	state.root.overrideredirect(True)
	state.root.wm_attributes("-alpha", state.settings.alpha["default"])
	state.root.grid(3, 5, root.winfo_screenwidth()//4, root.winfo_screenheight()//8)
	state.root.config(padx=15, pady=15, border=1, borderwidth=1)
	init_data = {
		"text":"Initializing...",
		"bg":"black",
		"fg":"white"
	}
	mainLabel = tk.Label(state.root, init_data, font=fontSize(20))
	mainLabel.grid(row=0, column=0, sticky="nsew", columnspan=3)
	mainLabel.grid_rowconfigure(0, weight=1)
	timeLabel = tk.Label(state.root, init_data, font=fontSize(30), anchor="center")
	timeLabel.grid_rowconfigure(1, weight=1)
	separator = Separator(state.root, orient="horizontal")
	separator.grid_rowconfigure(2, weight=1)
	class1Label = tk.Label(state.root, init_data, font=fontSize(10), padx=5, anchor="center", justify="center", wraplength=128)
	class1Label.grid_rowconfigure(3, weight=1)
	class2Label = tk.Label(state.root, init_data, font=fontSize(10), padx=5, anchor="center", justify="center")
	loc2Label = tk.Label(state.root, init_data, font=fontSize(10), padx=5, anchor="center", justify="center")
	loc1Label = tk.Label(state.root, init_data, font=fontSize(10), padx=5, anchor="center", justify="center")
	teacher1Label = tk.Label(state.root, init_data, font=fontSize(10), padx=5, anchor="center", justify="center")
	teacher2Label = tk.Label(state.root, init_data, font=fontSize(10), padx=5, anchor="center", justify="center")
	auxLabel = tk.Label(state.root, init_data, font=fontSize(10), padx=5, anchor="center", justify="center")
	vertSeparator = Separator(state.root, orient="vertical")
	asyncio.create_task(setClickThrough())
	state.transparencyTask = asyncio.create_task(transparencyCheck(state.root))
	del init_data
	await setup_tray(state.root)
	state.root.columnconfigure(0, weight=1)
	state.root.columnconfigure(1, weight=0)
	state.root.columnconfigure(2, weight=1)
	state.updateCycleTask = asyncio.create_task(updateCycle(mainLabel, timeLabel, class1Label, class2Label, loc1Label, loc2Label, state.root, vertSeparator, separator, auxLabel, teacher1Label, teacher2Label))
	state.root.protocol("WM_DELETE_WINDOW", state.root.withdraw)
	logger.info("Startup complete")
MAX_LOGS:int=5
def findInstance(name:str) -> bool:
	"""Check if another instance of the application is running, and returns `True` if there is, otherwise `False`"""
	k32 = windll.kernel32
	mutex = k32.CreateMutexW(None, BOOL(True), name)
	if k32.GetLastError() == 183:
		return True
	return False
def main(dummyDate:datetime|None = None):
	if (platform != "win32"):
		logger.critical(f"User is not using windows (platform: {platform})")
		messagebox.showerror("User not using windows", "This program can only run on windows due to technical limitation", icon="error")
		return
	if (findInstance(state.windowHandle)):
		logger.critical("Another instance is already running.\nClosing application.")
		messagebox.showerror("Another instance detected", "This program can only run once on a single computer at the same time due to technical limitations\nClosing application.", icon="error")
		return
	if state.settings.ignoreUpdates == False:
		checkUpdate()
	if dummyDate is not None:
		state.dummyDate = dummyDate
		del dummyDate
	def cleanup_old_logs(logFolder: str = "logs", prefix: str = "timer_"):
		"""Delete old log files, keeping only the last MAX_LOGS."""
		folder = Path(logFolder)
		# get all files that start with prefix and end with .log
		logFiles = sorted(folder.glob(f"{prefix}*.log"), key=lambda f: f.stat().st_mtime, reverse=True)
		# keep only the first MAX_LOGS, delete the rest
		for oldFile in logFiles[MAX_LOGS:]:
			oldFile.unlink()
	filename = f"logs/timer_{datetime.now().date().isoformat().replace('-', '_')}.log"
	if (not path.isdir("logs")): mkdir("logs")
	logFormat = "%(asctime)s::%(levelname)-8s:%(message)s"
	logging.basicConfig(filename=filename, encoding='utf-8', level=state.settings.logLevel, format=logFormat, datefmt="%Y-%m-%dT%H:%M:%S")
	cleanup_old_logs()
	logger.info(f"Application Starting up (v{VERSION})")
	state.root = Tk()
	state.runtime = asyncio.new_event_loop()
	asyncio.set_event_loop(state.runtime)
	state.runtime.create_task(startup(state.root))
	state.runtime.run_forever()
	state.runtime.close()

if __name__ == "__main__":
	if environ.get('TERM_PROGRAM') == 'vscode':
		#main()
		#main(datetime(year=2025, month=11, day=13, hour=14, minute=5, second=30)) # Stuck
		#main(datetime(year=2025, month=11, day=12, hour=12, minute=25, second=30)) # Flashing class
		main()
	else:
		main()