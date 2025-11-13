import tkinter as tk, asyncio, logging, modules.state as state
from tkinter import Tk
from tkinter.ttk import Separator
from sys import executable, argv
from datetime import datetime
from os import path, chdir, mkdir, environ
from pathlib import Path
from github import Github
from modules.settings import Settings
from modules.tray import setup_tray
from modules.clock import update_cycle, Schedule, set_click_through, font_size, transparency_check
logger = logging.getLogger(__name__)
logging.getLogger("PIL").setLevel(logging.WARNING)
logging.getLogger("pystray").setLevel(logging.WARNING)
logging.getLogger("settings")
VERSION_STRING:str="3.0.0"

# region Setting PATH
if path.splitext(argv[0])[1].lower() != ".exe":
	current_dir = path.dirname(path.abspath(__file__))
else:
	current_dir = path.dirname(path.abspath(executable))
chdir(current_dir)
# endregion
# region update handler
def check_update():
	user = Github()
	user.get_repo("Maho-Yoshino/csengetes-visszaszamlalo").get_releases()
	...
# endregion
state.settings = Settings()
state.schedule = Schedule()
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
	mainlabel = tk.Label(state.root, init_data, font=font_size(20))
	mainlabel.grid(row=0, column=0, sticky="nsew", columnspan=3)
	mainlabel.grid_rowconfigure(0, weight=1)
	timelabel = tk.Label(state.root, init_data, font=font_size(30), anchor="center")
	timelabel.grid_rowconfigure(1, weight=1)
	separator = Separator(state.root, orient="horizontal")
	separator.grid_rowconfigure(2, weight=1)
	class1label = tk.Label(state.root, init_data, font=font_size(10), padx=5, anchor="center", justify="center", wraplength=128)
	class1label.grid_rowconfigure(3, weight=1)
	class2label = tk.Label(state.root, init_data, font=font_size(10), padx=5, anchor="center", justify="center")
	loc2label = tk.Label(state.root, init_data, font=font_size(10), padx=5, anchor="center", justify="center")
	loc1label = tk.Label(state.root, init_data, font=font_size(10), padx=5, anchor="center", justify="center")
	aux_label = tk.Label(state.root, init_data, font=font_size(10), padx=5, anchor="center", justify="center")
	vert_separator = Separator(state.root, orient="vertical")
	asyncio.create_task(set_click_through())
	state.transparency_task = asyncio.create_task(transparency_check(state.root))
	del init_data
	await setup_tray(state.root)
	state.root.columnconfigure(0, weight=1)
	state.root.columnconfigure(1, weight=0)
	state.root.columnconfigure(2, weight=1)
	state.update_cycle_task = asyncio.create_task(update_cycle(mainlabel, timelabel, class1label, class2label, loc1label, loc2label, state.root, vert_separator, separator, aux_label))
	state.root.protocol("WM_DELETE_WINDOW", state.root.withdraw)
	logger.info("Startup complete")
MAX_LOGS:int=5
def main(_dummy_date:datetime|None = None):
	if environ.get('TERM_PROGRAM') == 'vscode':
		...#check_update()
	if _dummy_date is not None:
		state.dummy_date = _dummy_date
		del _dummy_date
	def cleanup_old_logs(log_folder: str = "logs", prefix: str = "timer_"):
		"""Delete old log files, keeping only the last MAX_LOGS."""
		folder = Path(log_folder)
		# get all files that start with prefix and end with .log
		log_files = sorted(folder.glob(f"{prefix}*.log"), key=lambda f: f.stat().st_mtime, reverse=True)
		# keep only the first MAX_LOGS, delete the rest
		for old_file in log_files[MAX_LOGS:]:
			old_file.unlink()
	filename = f"logs/timer_{datetime.now().date().isoformat().replace('-', '_')}.log"
	if (not path.isdir("logs")): mkdir("logs")
	log_format = "%(asctime)s::%(levelname)-8s:%(message)s"
	logging.basicConfig(filename=filename, encoding='utf-8', level=logging.DEBUG if environ.get('TERM_PROGRAM') == 'vscode' else logging.INFO, format=log_format, datefmt="%Y-%m-%dT%H:%M:%S")
	cleanup_old_logs()
	logger.info(f"Application Starting up (v{VERSION_STRING})")
	state.root = Tk()
	state.runtime = asyncio.new_event_loop()
	asyncio.set_event_loop(state.runtime)
	state.runtime.create_task(startup(state.root))
	state.runtime.run_forever()
	state.runtime.close()

if environ.get('TERM_PROGRAM') == 'vscode':
	#main()
	main(datetime(year=2025, month=11, day=13, hour=14, minute=5, second=30))
else:
	main()