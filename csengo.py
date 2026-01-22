import sys
sys.dont_write_bytecode = True # Prevent '__pycache__' creation
from asyncio import new_event_loop, set_event_loop, CancelledError, Task, create_task, sleep
from logging import getLogger, WARNING, DEBUG, INFO, Formatter
from logging.handlers import TimedRotatingFileHandler
from tkinter import Tk, messagebox, Label, Frame
from sys import executable, argv, platform
from datetime import datetime
from os import path, chdir, environ
from github import Github, Repository, GitRelease
from ctypes import windll
from ctypes.wintypes import BOOL
import modules.state as state
from modules.settings import Settings
from modules.tray import traySetup
from modules.clock import updateCycle, setClickThrough, fontSize, transparencyCheck
logger = getLogger()
getLogger("PIL").setLevel(WARNING)
getLogger("pystray").setLevel(WARNING)
getLogger("asyncio").setLevel(WARNING)

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
	repo:Repository.Repository = Github().get_repo("Maho-Yoshino/csengetes-visszaszamlalo")
	latest_release:GitRelease.GitRelease = repo.get_releases()[0]
	tag = latest_release.tag_name.lstrip("v")
	latest_version = Version(tag)
	logger.debug(f"Latest version online: {latest_version}")
	logger.debug(f"Current version: {VERSION}")
	if latest_version > VERSION:
		logger.warning(f"Update available ({VERSION} -> {latest_version})")
		loc = state.settings.localization
		response = messagebox.askyesnocancel(
			loc.messages.updatePrompt.title, 
			loc.format(
				loc.messages.updatePrompt.message, 
				current=VERSION, 
				latest=latest_version
			), 
			icon="warning", 
			default=messagebox.YES
		)
		if response:
			logger.info("User accepted automatic update")
			# TODO: Finish auto-updater
		elif response is None:
			logger.info("User asked to not be reminded again")
			state.settings.ignoreUpdates = True
		else:
			logger.info("User denied automatic update")
	else:
		logger.info("Running the latest version.")

# endregion
state.settings = Settings()
def exc_handler(task: Task):
	try:
		task.result()
	except CancelledError: return
	except Exception as e:
		logger.exception("Unhandled async task exception", exc_info=e)
		def showError(): # Needs a seperate def apparently due to threading
			messagebox.showerror(
				state.settings.localization.messages.error.title,
				state.settings.localization.messages.error.message,
				icon="error"
			)
			state.tray.quit()
		try:
			state.root.after(0, showError)
		except Exception:
			logger.exception("Failed to schedule Tk error dialog")
			state.tray.quit()
async def startup():
	state.root.iconbitmap(default="assets/icon.ico")
	state.root.configure(bg=f"#{state.settings.background:06x}", )
	state.root.attributes("-topmost", True)
	state.root.title(state.windowHandle)
	state.root.resizable(False, False)
	state.root.overrideredirect(True)
	state.root.wm_attributes("-alpha", state.settings.alpha["default"])
	state.root.grid(3, 5, state.root.winfo_screenwidth()//4, state.root.winfo_screenheight()//8)
	state.root.config(padx=15, pady=15, border=1, borderwidth=1)
	init_data = {
		"text":"",
		"bg":f"#{state.settings.background:06x}",
		"fg":f"#{state.settings.foreground:06x}"
	}
	mainLabel = Label(state.root, init_data, font=fontSize(20))
	mainLabel.grid(row=0, column=0, sticky="nsew", columnspan=3)
	mainLabel.grid_rowconfigure(0, weight=1)
	timeFrame = Frame(state.root, bg=init_data["bg"])
	timeFrame.grid(column=0, row=1, columnspan=4)
	timeFrame.grid_rowconfigure(0, weight=0)
	timeFrame.grid_rowconfigure(1, weight=1)
	timeLabel = Label(timeFrame, init_data, font=fontSize(30), anchor="center")
	timeLabel.grid(column=1)
	timeLabel.grid_columnconfigure(1, weight=1)
	separator = Frame(state.root, bg=init_data["fg"], height=1, width=state.root.winfo_width())
	separator.grid_rowconfigure(2, weight=1)
	class1Label = Label(state.root, init_data, font=fontSize(10), padx=5, anchor="center", justify="center", wraplength=128)
	class1Label.grid_rowconfigure(3, weight=1)
	class2Label = Label(state.root, init_data, font=fontSize(10), padx=5, anchor="center", justify="center")
	loc2Label = Label(state.root, init_data, font=fontSize(10), padx=5, anchor="center", justify="center")
	loc1Label = Label(state.root, init_data, font=fontSize(10), padx=5, anchor="center", justify="center")
	teacher1Label = Label(state.root, init_data, font=fontSize(10), padx=5, anchor="center", justify="center")
	teacher2Label = Label(state.root, init_data, font=fontSize(10), padx=5, anchor="center", justify="center")
	auxLabel = Label(state.root, init_data, font=fontSize(10), padx=5, anchor="center", justify="center")
	vertSeparator = Frame(state.root, bg=init_data["fg"], width=1, height=state.root.winfo_height())
	state.setClickThroughTask = create_task(setClickThrough())
	state.setClickThroughTask.add_done_callback(exc_handler)
	state.transparencyTask = create_task(transparencyCheck())
	state.transparencyTask.add_done_callback(exc_handler)
	del init_data
	state.root.columnconfigure(0, weight=1)
	state.root.columnconfigure(1, weight=0)
	state.root.columnconfigure(2, weight=1)
	state.updateCycleTask = create_task(updateCycle(mainLabel, timeLabel, class1Label, class2Label, loc1Label, loc2Label, state.root, vertSeparator, separator, auxLabel, teacher1Label, teacher2Label, timeFrame))
	state.updateCycleTask.add_done_callback(exc_handler)
	state.root.protocol("WM_DELETE_WINDOW", state.root.withdraw)
	state.tkPumpTask = state.runtime.create_task(state.tkPump(state.root))
	state.tkPumpTask.add_done_callback(exc_handler)
	state.tray = traySetup()
	logger.info("Startup complete")
	await sleep(0.1)

def findInstance(name:str) -> bool:
	"""Check if another instance of the application is running, and returns `True` if there is, otherwise `False`"""
	k32 = windll.kernel32
	mutex = k32.CreateMutexW(None, BOOL(True), name)
	if k32.GetLastError() == 183:
		return True
	return False
def main(dummyDate:datetime|None = None):
	loc = state.settings.localization
	if (platform != "win32"):
		logger.critical(f"User is not using windows (platform: {platform})")
		messagebox.showerror(
			loc.messages.windowsOnly.title, 
			loc.messages.windowsOnly.message, 
			icon="error"
		)
		return
	if (findInstance(state.windowHandle)):
		logger.critical("Another instance is already running.\nClosing application.")
		messagebox.showerror(
			loc.messages.anotherInstance.title, 
			loc.messages.anotherInstance.message, 
			icon="error"
		)
		return
	debug:bool
	# region Debug mode setup
	if __name__ == "__main__":
		debug = environ.get('TERM_PROGRAM') == 'vscode'
		if not debug:
			from argparse import ArgumentParser
			parser = ArgumentParser()
			parser.add_argument("-d", "--debug", help="Debug mode switch", action="store_true")
			debug = parser.parse_args().debug
	else:
		debug = True # Not ran from this file directly, a.k.a. testing another module, Always True
	# endregion
	if not state.settings.ignoreUpdates:
		checkUpdate()
	if dummyDate is not None:
		state.dummyDate = dummyDate
		del dummyDate
	def log_namer(default_name:str):
		dirname = path.dirname(default_name)
		filename = path.basename(default_name)
		_, _, date = filename.rpartition(".")
		return path.join(dirname, f"{date}.log")
	handler = TimedRotatingFileHandler("logs/latest.log", when="midnight", interval=1, backupCount=5)
	handler.suffix = "%Y-%m-%d"
	formatter = Formatter(f"%(asctime)s:%(name)-15s:%(funcName)-15s:%(lineno)-3d:%(levelname)-7s:%(message)s", datefmt="%Y-%m-%d %H:%M:%S")
	handler.setFormatter(formatter)
	handler.namer = log_namer
	logger.addHandler(handler)
	logger.setLevel(DEBUG if debug else INFO)
	logger.info(f"Application Starting up (v{VERSION})")
	state.root = Tk()
	state.runtime = new_event_loop()
	set_event_loop(state.runtime)
	_ = state.runtime.create_task(startup())
	_.add_done_callback(exc_handler)
	state.runtime.run_forever()

try:
	if environ.get('TERM_PROGRAM') == 'vscode':
		main()
		#main(datetime(year=2026, month=1, day=15, hour=12))
	else:
		main()
except KeyboardInterrupt: pass
except Exception as e:
	logger.exception("An error occurred during runtime", exc_info=e)
	messagebox.showerror(
		state.settings.localization.messages.error.title, 
		state.settings.localization.messages.error.message, 
		icon="error"
	)
finally:
	if state.tray:
		state.tray.quit()
