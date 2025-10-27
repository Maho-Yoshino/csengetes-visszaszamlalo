import tkinter as tk, asyncio, pystray, logging
from tkinter import Tk
from tkinter.ttk import Separator
from sys import platform, executable, argv
from tkinter.font import Font
from ctypes import windll, c_byte, byref, Structure
from datetime import datetime, time, timedelta, date
from time import perf_counter
from os import path, chdir, mkdir, environ
from threading import Thread
from PIL import Image
from json import load as jload, dump as jdump
from typing import Optional, Any, Literal
from pathlib import Path
logger = logging.getLogger(__name__)
logging.getLogger("PIL").setLevel(logging.WARNING)
logging.getLogger("pystray").setLevel(logging.WARNING)

# Setting PATH
if path.splitext(argv[0])[1].lower() != ".exe":
	print("not an .exe")
	current_dir = path.dirname(path.abspath(__file__))
else:
	current_dir = path.dirname(path.abspath(executable))
chdir(current_dir)
# Logging prints
def print_info(text):
	print(text)
	logger.info(text)
def print_debug(text):
	print(text)
	logger.debug(text)
def print_warning(text):
	print(text)
	logger.warning(text)
def print_error(text):
	print(text)
	logger.error(text)
def print_critical(text):
	print(text)
	logger.critical(text)

delayRoot:Tk|None = None
# Settings window
async def setup_tray(root:Tk):
	def on_quit(icon, item):
		print_info("Closing application")
		icon.stop()
		global root, update_cycle_task, transparency_task
		update_cycle_task.cancel()
		transparency_task.cancel()
		root.quit()
		runtime.stop()
	def settings_callback(): runtime.create_task(open_settings(root))
	def setDelayWindow(icon, item):
		global delayRoot
		async def CreateWindow():
			def saveValue(event=None):
				settings.delay = int(val.get())
				delayRoot.destroy()
			delayRoot = tk.Toplevel(root)
			delayRoot.title("Delay Time Input")
			delayRoot.geometry(f"+{delayRoot.winfo_screenwidth()//2-25}+{delayRoot.winfo_screenheight()//2-25}")
			delayRoot.resizable(False, False)
			delayRoot.grid(1, 6, 150, 50)
			tk.Label(delayRoot, text="Set Delay Time (in seconds)").grid(row=0, column=0)
			val = tk.Entry(delayRoot, textvariable=tk.IntVar(value=settings.delay))
			val.grid(row=1, column=0)
			tk.Label(delayRoot, text="Negative = Earlier\nPositive = Later").grid(row=2, column=0, rowspan=2)
			tk.Button(delayRoot, text="Save", command=saveValue).grid(row=5, column=0)
			delayRoot.focus_force()
			delayRoot.bind('<Return>', saveValue)
			asyncio.create_task(updateFast(delayRoot))
		runtime.create_task(CreateWindow())
	def ScheduleWindow(icon, item):
		async def CreateWindow():
			scheduleRoot = tk.Toplevel(root)
			scheduleRoot.title("Schedule")
			windowHeight = max([len(i) for i in settings.default_schedule], [len(val) for key, val in settings.special_days.items() if datetime.strptime(key, "%Y-%m-%d").strftime("%V") == (await get_rn()).strftime("%V")])
			windowWidth = len(settings.default_schedule)
			days:list[Schedule] = []
			if specialDayThisWeek := any([datetime.strptime(key, "%Y-%m-%d").strftime("%V") == (await get_rn()).strftime("%V") for key in settings.special_days.keys()]):
				windowWidth += 1
			scheduleRoot.grid(windowWidth, windowHeight, 300, 150)
			frames:list[list[tk.Frame]] = []
			for col in range(windowWidth):
				frames.append([])
				for row in range(windowHeight):
					temp = tk.Frame(scheduleRoot, highlightbackground="white", highlightcolor="black")
					temp.grid(row=row, column=col)
					frames[col].append(temp)
			for num, frame in enumerate(frames):
				
				...
			scheduleRoot.update()
		runtime.create_task(CreateWindow())
	icon = pystray.Icon("Csengetés időzítő", Image.open("icon.ico"), menu=pystray.Menu(
		pystray.MenuItem(lambda item: f"Delay: {settings.delay}", setDelayWindow),
		pystray.MenuItem("Fullscreen Schedule", ScheduleWindow),
		pystray.MenuItem("Settings", settings_callback),
		pystray.MenuItem("Quit", lambda icon, item: on_quit(icon, item))
	))
	Thread(target=icon.run, daemon=True).start()
class Settings:
	def __init__(self, filename: str = "settings.json", encoding:str="utf-8"):
		self.filename = filename
		self.encoding = encoding
		self._data: dict[str, Any] = {}
		self.load_settings()
	def load_settings(self):
		try:
			with open(self.filename, "r", encoding=self.encoding) as f:
				self._data = jload(f)
				print_info("Settings loaded properly")
		except FileNotFoundError:
			print_warning("Settings file not found, creating a default one.")
			with open(self.filename, "x", encoding=self.encoding) as f:
				jdump({
					"classlist":{},
					"teacherlist":{},
					"default_schedule": [[],[],[],[],[]],
					"special_days":{},
					"classtimes":[],
					"breaktimes":[],
					"special_classtimes":{},
					"special_breaktimes":{},
					"special_begintimes":{},
					"classes_begin":800,
					"delay":0,
					"alpha": {
						"default":0.75, 
						"onHover":0.25
					},
					"display_next_time":10
				}, f, indent=4)
			with open(self.filename, "r", encoding=self.encoding) as f:
				self._data = jload(f)
		# Set default values if missing
		self._data.setdefault("teacherlist", {})
		self._data.setdefault("special_days", None)
		self._data.setdefault("debug", False)
		self._data.setdefault("special_classtimes", {})
		self._data.setdefault("special_breaktimes", {})
		self._data.setdefault("special_begintimes", {})
		self._data.setdefault("delay", 0)
		self._data.setdefault("classes_begin", 800)
		self._data.setdefault("alpha", {"default":0.75,"onHover":0.25})
	def save(self):
		with open(self.filename, "w", encoding="utf-8") as f:
			jdump(self._data, f, indent=4, ensure_ascii=False)
	@property # classlist
	def classlist(self) -> dict[str, list[str]]:
		return self._data["classlist"]
	@classlist.setter
	def classlist(self, value: dict[str, list[str]]):
		self._data["classlist"] = value
		self.save()
	@property # default_schedule
	def default_schedule(self) -> list[list[str]]:
		return self._data["default_schedule"]
	@default_schedule.setter
	def default_schedule(self, value: list[list[str]]):
		self._data["default_schedule"] = value
		self.save()
	@property # teacherlist
	def teacherlist(self) -> dict[str, str]:
		return self._data["teacherlist"]
	@teacherlist.setter
	def teacherlist(self, key: str, value: str):
		if self._data["teacherlist"].get(key, None) is not None:
			self._data["teacherlist"][key] = value
		else:
			self._data["teacherlist"].update({key:value})
		self.save()
	@property # special_days
	def special_days(self) -> Optional[dict[str, list[str]]]:
		return self._data["special_days"]
	@special_days.setter
	def special_days(self, value: Optional[dict[str, list[str]]]):
		self._data["special_days"] = value
		self.save()
	@property # debug
	def debug(self) -> bool:
		return self._data["debug"]
	@property # classtimes
	def classtimes(self) -> list[int]:
		return self._data["classtimes"]
	@classtimes.setter
	def classtimes(self, value: list[int]):
		self._data["classtimes"] = value
		self.save()
	@property # breaktimes
	def breaktimes(self) -> list[int]:
		return self._data["breaktimes"]
	@breaktimes.setter
	def breaktimes(self, value: list[int]):
		self._data["breaktimes"] = value
		self.save()
	@property # special_classtimes
	def special_classtimes(self) -> dict[date, list[int]]:
		return {
			datetime.strptime(_date, "%Y-%m-%d").date(): values
			for _date, values in self._data["special_classtimes"].items()
   		}
	@special_classtimes.setter
	def special_classtimes(self, value: dict[date, list[int]]):
		serializable: dict[str, list[int]] = {
			d.strftime("%Y-%m-%d"): values for d, values in value.items()
		}
		self._data["special_classtimes"] = serializable
		self.save()
	@property # special_breaktimes
	def special_breaktimes(self) -> dict[date, list[int]]:
		return {
			datetime.strptime(_date, "%Y-%m-%d").date(): values
			for _date, values in self._data["special_breaktimes"].items()
   		}
	@special_breaktimes.setter
	def special_breaktimes(self, value: dict[date, list[int]]):
		serializable: dict[str, list[int]] = {
			d.strftime("%Y-%m-%d"): values for d, values in value.items()
		}
		self._data["special_breaktimes"] = serializable
		self.save()
	@property # special_begintimes
	def special_begintimes(self) -> dict[date, list[int]]:
		return {
			datetime.strptime(_date, "%Y-%m-%d").date(): values
			for _date, values in self._data["special_begintimes"].items()
   		}
	@special_begintimes.setter
	def special_begintimes(self, value: dict[date, list[int]]):
		serializable: dict[str, list[int]] = {
			d.strftime("%Y-%m-%d"): values for d, values in value.items()
		}
		self._data["special_begintimes"] = serializable
		self.save()
	@property # classes_begin
	def classes_begin(self) -> list[int]:
		return self._data["classes_begin"]
	@classes_begin.setter
	def classes_begin(self, value: list[int]):
		self._data["classes_begin"] = value
		self.save()
	@property # delay
	def delay(self) -> int:
		return self._data["delay"]
	@delay.setter
	def delay(self, value: int):
		self._data["delay"] = value
		self.save()
	@property # alpha
	def alpha(self) -> dict[Literal["onHover"]|Literal["default"], float]:
		return self._data["alpha"]
	@alpha.setter
	def alpha(self, key:Literal["onHover"]|Literal["default"], value: float):
		self._data["alpha"][key] = value
		self.save()
	@property # display_next_time
	def display_next_time(self) -> int:
		return self._data["display_next_time"]
	@display_next_time.setter
	def display_next_time(self, value: int):
		self._data["display_next_time"] = value
		self.save()
settings = Settings()
_settings:tk.Toplevel|None = None
async def updateFast(_root:Tk):
	while True:
		_root.update()
		await asyncio.sleep(0.01) 
async def open_settings(root:Tk):
	global _settings
	_settings = tk.Toplevel(root)
	_settings.title("Settings")
	_settings.grid(10, 10, 50, 25)
	menu = tk.Menu(_settings)
	# TODO: Finish implementing the settings menu
	menu.add_command(label="Not implemented yet")
	_settings.config(menu=menu)
	tk.Label(_settings, text="Settings window", font=font_size(20)).grid(row=0, column=0, columnspan=10)
	await updateFast(_settings)

# Clock Window
runtime:asyncio.AbstractEventLoop
transparency_task:asyncio.Task = None
update_cycle_task:asyncio.Task = None
dummy_date:datetime|None = None
root:Tk
def font_size(size:int): return Font(size=size)
async def set_click_through():
	if platform != "win32":
		return print(f"User is not on windows. ({platform} instead)")
	print("Setting click-through window")
	try:
		hwnd = windll.user32.FindWindowW(None, u"Csengetés időzítő")  # Get correct window handle
		styles = windll.user32.GetWindowLongW(hwnd, -20)
		styles |= 0x00000020  # WS_EX_LAYERED (Allows transparency)	
		styles |= 0x00000080  # WS_EX_TRANSPARENT (Click-through)
		windll.user32.SetWindowLongW(hwnd, -20, styles)
	except Exception as e:
		print(f"An error occured during transparency setting: {e}")
async def is_battery_saver_on(on_val, off_val):
	class SYSTEM_POWER_STATUS(Structure):
		_fields_ = [
			("ACLineStatus", c_byte),
			("BatteryFlag", c_byte),
			("BatteryLifePercent", c_byte),
			("SystemStatusFlag", c_byte)
		]
	status = SYSTEM_POWER_STATUS()
	if windll.kernel32.GetSystemPowerStatus(byref(status)) == 0:
		return off_val # Failed to get status, assume OFF
	return on_val if bool(status.SystemStatusFlag & 1) else off_val  # 1 means Battery Saver is ON
async def transparency_check(root:Tk):
	async def is_cursor_over_window(root:Tk):
		win_x = root.winfo_rootx()
		win_y = root.winfo_rooty()
		return (win_x <= root.winfo_pointerx() <= win_x + root.winfo_width() and 
				win_y <= root.winfo_pointery() <= win_y + root.winfo_height())
	while True:
		if not await is_cursor_over_window(root) and root.wm_attributes("-alpha") != 0.65: 
			root.wm_attributes("-alpha", settings.alpha["default"])
		elif await is_cursor_over_window(root) and root.wm_attributes("-alpha") != 0.10: 
			root.wm_attributes("-alpha", settings.alpha["onHover"])
		await asyncio.sleep(await is_battery_saver_on(1, 0.1))
async def get_rn(): return datetime.now() if dummy_date is None else dummy_date
async def startup(root:Tk):
	global transparency_task, update_cycle_task
	root.configure(background="black")
	root.attributes("-topmost", True)
	root.title("Csengetés időzítő")
	root.resizable(False, False)
	root.overrideredirect(True)
	root.wm_attributes("-alpha", settings.alpha["default"])
	root.grid(3, 5, root.winfo_screenwidth()//4, root.winfo_screenheight()//8)
	root.config(padx=15, pady=15, border=1, borderwidth=1)
	init_data = {
		"text":"Initializing...",
		"bg":"black",
		"fg":"white"
	}
	mainlabel = tk.Label(root, init_data, font=font_size(20))
	mainlabel.grid(row=0, column=0, sticky="nsew", columnspan=3)
	mainlabel.grid_rowconfigure(0, weight=1)
	timelabel = tk.Label(root, init_data, font=font_size(30))
	timelabel.grid_rowconfigure(1, weight=1)
	separator = Separator(root, orient="horizontal")
	separator.grid_rowconfigure(2, weight=1)
	class1label = tk.Label(root, init_data, font=font_size(10), padx=5, anchor="center", justify="center")
	class1label.grid_rowconfigure(3, weight=1)
	class2label = tk.Label(root, init_data, font=font_size(10), padx=5, anchor="center", justify="center")
	loc2label = tk.Label(root, init_data, font=font_size(10), padx=5, anchor="center", justify="center")
	loc1label = tk.Label(root, init_data, font=font_size(10), padx=5, anchor="center", justify="center")
	aux_label = tk.Label(root, init_data, font=font_size(10), padx=5, anchor="center", justify="center")
	vert_separator = Separator(root, orient="vertical")
	asyncio.create_task(set_click_through())
	transparency_task = asyncio.create_task(transparency_check(root))
	del init_data
	await setup_tray(root)
	root.columnconfigure(0, weight=1)
	root.columnconfigure(1, weight=0)
	root.columnconfigure(2, weight=1)
	root.update()
	update_cycle_task = asyncio.create_task(update_cycle(mainlabel, timelabel, class1label, class2label, loc1label, loc2label, root, vert_separator, separator, schedule, aux_label))
	root.protocol("WM_DELETE_WINDOW", root.withdraw)
	print_info("Startup complete")

class Schedule:
	classes:list["ClassData", list["ClassData"]] = []
	_date:date = None
	special_day:bool = False
	class ClassData:
		begin:time
		end:time
		begin_datetime:datetime
		end_datetime:datetime
		classname:str = None 
		room:str = None 
		teacher:str = None
		def __init__(self, _class:str|None, index:int, parent:"Schedule"):
			tmp = settings.classlist.get(_class, [])
			if len(parent.classes) > 0:
				self.begin_datetime = (parent.classes[-1].end_datetime if not isinstance(parent.classes[-1], list) else parent.classes[-1][0].end_datetime) + timedelta(minutes=(settings.special_breaktimes[parent._date] if parent.special_day else settings.breaktimes)[index-1])
				self.begin = self.begin_datetime.time()
			else:
				temp = (settings.special_begintimes.get(parent._date) if parent.special_day else settings.classes_begin)
				self.begin_datetime = datetime.strptime(f"{parent._date.strftime("%Y.%m.%d")} {temp//100}:{temp%100}", "%Y.%m.%d %H:%M")
				self.begin = self.begin_datetime.time()
			self.end_datetime = (self.begin_datetime + timedelta(minutes=(settings.special_classtimes if parent.special_day else settings.classtimes)[index]))
			self.end = self.end_datetime.time()
			if tmp:
				self.classname = tmp[0]
				self.room = tmp[1]
				self.teacher = settings.teacherlist.get(_class, None)
	def __init__(self, other_date:datetime|None=None):
		if other_date is not None:
			self._date = other_date.date()
			weekday = self._date.weekday()
		else:
			self._date = (datetime.now() if dummy_date is None else dummy_date).date()
			weekday = self._date.weekday()
		self.special_day = any([day == self._date for day in settings.special_days])
		if weekday in [5,6] and not self.special_day:
			return
		if self.special_day:
			tmp = settings.special_days.get(self._date)
			if tmp is None:
				tmp = settings.default_schedule[weekday]
		else: 
			tmp = settings.default_schedule[weekday]
		for ind, classinfo in enumerate(tmp):
			if classinfo is not None and isinstance(classinfo, list):
				self.classes.append([self.ClassData(_, ind, self) for _ in classinfo])
			else:
				self.classes.append(self.ClassData(classinfo, ind, self))
		print_debug("Initialized Schedule class")
schedule:Schedule|None = None
async def update_cycle(mainlabel:tk.Label, timelabel:tk.Label, class1label:tk.Label, class2label:tk.Label, loc1label:tk.Label, loc2label:tk.Label, root:Tk, vert_separator:Separator, separator:Separator, schedule:Schedule, aux_label:tk.Label):
	async def set_dynamic_size():
		root.geometry(f"+{root.winfo_screenwidth()-root.winfo_width()}+0")
		root.update()
	prev_day:datetime = (await get_rn()).date()
	schedule = Schedule()
	global dummy_date
	while True:
		_start = perf_counter()
		delay = settings.delay
		if prev_day != schedule._date:
			prev_day = (await get_rn()).date()
			print_debug("Day changed since last cycle")
			schedule = Schedule()
			if len(schedule.classes) == 0: await asyncio.sleep(60*30)
		now = (await get_rn())
		now_time = now.time()
		if all([not i.winfo_ismapped() for i in [class1label,loc1label,timelabel]]):
			class1label.grid(row=3, column=0, sticky="nsew")
			loc1label.grid(row=4, column=0, sticky="nsew")
			timelabel.grid(row=1, column=0, sticky="nsew", columnspan=3)
		for num, _class in enumerate(schedule.classes):
			tmp_class:Schedule.ClassData|None = None
			if isinstance(_class, list):
				tmp_class = _class[1]
				_class = _class[0]
			if ((_class.begin_datetime + timedelta(seconds=delay)).time() > now_time):
				tmp = datetime.combine((await get_rn()), _class.begin) - datetime.combine((await get_rn()), now_time) + timedelta(seconds=delay)
				mainlabel.config(text=f"Szünet végéig")
				timelabel.config(text=f"{f"{tmp.seconds//3600:02}:" if tmp.seconds//3600 != 0 else ""}{(tmp.seconds//60)%60:02}:{tmp.seconds%60:02}")
				class1label.config(text=f"{_class.classname}", anchor="center")
				if aux_label.winfo_ismapped():
					aux_label.grid_forget()
					root.rowconfigure(4, weight=0, minsize=0)
				if tmp_class is not None:
					if not class2label.winfo_ismapped(): class2label.grid(row=3, column=2, sticky="nsew")
					if not loc2label.winfo_ismapped(): loc2label.grid(row=4, column=2, sticky="nsew")
					if not vert_separator.winfo_ismapped(): vert_separator.grid(row=3, column=1, sticky="ns", padx=5, pady=5, rowspan=2)
					class1label.grid_configure(columnspan=1)
					loc1label.grid_configure(columnspan=1)
					class2label.config(text=f"{tmp_class.classname}", anchor="center", wraplength=class2label.winfo_width())
					loc1label.config(text=f"{_class.room}", wraplength=loc1label.winfo_width())
					loc2label.config(text=f"{tmp_class.room}", wraplength=loc2label.winfo_width())
				else:
					if class2label.winfo_ismapped(): class2label.grid_forget()
					if loc2label.winfo_ismapped(): loc2label.grid_forget()
					if vert_separator.winfo_ismapped(): vert_separator.grid_forget()
					class1label.grid_configure(columnspan=3)
					loc1label.grid_configure(columnspan=3)
					loc1label.config(text=_class.room, wraplength=loc1label.winfo_width())
				if not separator.winfo_ismapped(): separator.grid(row=2, column=0, sticky="ew", padx=5, pady=5, columnspan=3, ipadx=100)
				await set_dynamic_size()
				break
			elif ((_class.end_datetime + timedelta(seconds=delay)).time() > now_time):
				tmp = datetime.combine((await get_rn()), _class.end) - datetime.combine((await get_rn()).date(), now_time) + timedelta(seconds=delay)
				mainlabel.config(text=f"{num+1}. Óra végéig")
				timelabel.config(text=f"{f"{tmp.seconds//3600:02}:" if tmp.seconds//3600 != 0 else ""}{(tmp.seconds//60)%60:02}:{tmp.seconds%60:02}")
				class1label.config(text=f"{_class.classname}", anchor="center")
				if tmp_class is not None:
					if not class2label.winfo_ismapped(): class2label.grid(row=3, column=2, sticky="nsew")
					if not loc2label.winfo_ismapped(): loc2label.grid(row=4, column=2, sticky="nsew")
					if (tmp.seconds > 60*10):
						if aux_label.winfo_ismapped(): 
							aux_label.grid_forget()
							root.rowconfigure(4, weight=0, minsize=0)
						if not vert_separator.winfo_ismapped(): vert_separator.grid(row=3, column=1, sticky="ns", padx=5, pady=5, rowspan=2)
						class1label.grid_configure(columnspan=1)
						loc1label.grid_configure(columnspan=1)
						class2label.config(text=f"{tmp_class.classname}", anchor="center")
						loc1label.config(text=f"{_class.room}")
						loc2label.config(text=f"{tmp_class.room}")
					else:
						if not aux_label.winfo_ismapped():
							aux_label.grid(row=5, column=0, sticky="nsew", columnspan=3)
							aux_label.config(text="Következő óra")
							root.rowconfigure(4, weight=1)
						if isinstance(next_class := schedule.classes[num+1], list) and len(next_class) > 1:
							if not vert_separator.winfo_ismapped(): vert_separator.grid(row=3, column=1, sticky="ns", padx=5, pady=5, rowspan=2)
							class1label.config(text=f"{next_class[0].classname}", anchor="center")
							class2label.config(text=f"{next_class[1].classname}", anchor="center")
							loc1label.config(text=f"{next_class[0].room}")
							loc2label.config(text=f"{next_class[1].room}")
						else:
							if class2label.winfo_ismapped(): class2label.grid_forget()
							if loc2label.winfo_ismapped(): loc2label.grid_forget()
							class1label.grid_configure(columnspan=3)
							loc1label.grid_configure(columnspan=3)
							class1label.config(text=f"{next_class.classname}", anchor="center")
							loc1label.config(text=f"{next_class.room}")
							if vert_separator.winfo_ismapped(): vert_separator.grid_forget()
					if not separator.winfo_ismapped(): separator.grid(row=2, column=0, sticky="ew", padx=5, pady=5, columnspan=3, ipadx=100)
				else:
					if (tmp.seconds > 60*10):
						if class2label is not None: class2label = class2label.grid_forget()
						if loc2label is not None: loc2label = loc2label.grid_forget()
						class1label.grid_configure(columnspan=3)
						loc1label.grid_configure(columnspan=3)
						class1label.config(text=f"{_class.classname}", anchor="center")
						loc1label.config(text=f"{_class.room}")
						if aux_label.winfo_ismapped():
							aux_label.grid_forget()
							root.rowconfigure(4, weight=0, minsize=0)
					else:
						if isinstance(next_class := schedule.classes[num+1], list) and len(next_class) > 1:
							if not class2label.winfo_ismapped(): class2label.grid(row=3, column=2, sticky="nsew")
							if not loc2label.winfo_ismapped(): loc2label.grid(row=4, column=2, sticky="nsew")
							class1label.config(text=f"{next_class[0].classname}", anchor="center")
							class2label.config(text=f"{next_class[1].classname}", anchor="center")
							loc1label.config(text=f"{next_class[0].room}")
							loc2label.config(text=f"{next_class[1].room}")
							if not vert_separator.winfo_ismapped(): vert_separator.grid(row=3, column=1, sticky="ns", padx=5, pady=5, rowspan=2)
						else:
							if class2label.winfo_ismapped(): class2label.grid_forget()
							if loc2label.winfo_ismapped(): loc2label.grid_forget()
							class1label.grid_configure(columnspan=3)
							class1label.config(text=f"{next_class.classname}", anchor="center")
							loc1label.config(text=f"{next_class.room}")
							loc1label.grid_configure(columnspan=3)
							if vert_separator.winfo_ismapped(): vert_separator.grid_forget()
						if not aux_label.winfo_ismapped():
							aux_label.grid(row=5, column=0, sticky="nsew", columnspan=3)
							aux_label.config(text="Következő óra")
							root.rowconfigure(4, weight=1)
				if not separator.winfo_ismapped(): separator.grid(row=2, column=0, sticky="ew", padx=5, pady=5, columnspan=3, ipadx=100)
				await set_dynamic_size()
				break
		else:
			mainlabel.config(text="A napnak vége")
			[i.grid_forget() for i in [timelabel,class1label,class2label,loc1label,loc2label,separator,vert_separator,aux_label] if i.winfo_ismapped()]
			await set_dynamic_size()
			root.update()
			await asyncio.sleep(60)
			continue
		class1label.config(wraplength=class1label.winfo_width())
		class2label.config(wraplength=class2label.winfo_width())
		root.update()
		await set_dynamic_size()
		update_delay = await is_battery_saver_on(5, 1)
		if dummy_date is not None:
			dummy_date = dummy_date + timedelta(seconds=1)
		delay = min(max(0, update_delay - (perf_counter() - _start)), 10)
		await asyncio.sleep(delay)

MAX_LOGS:int=5
def main(_dummy_date:datetime|None = None):
	if _dummy_date is not None:
		global dummy_date
		dummy_date = _dummy_date
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
	logging.basicConfig(filename=filename, encoding='utf-8', level=logging.DEBUG if environ.get('TERM_PROGRAM') == 'vscode' else logging.WARNING, format=log_format, datefmt="%Y-%m-%dT%H:%M:%S")
	cleanup_old_logs()
	print_info("Application Starting up")
	global root, runtime
	root = Tk()
	runtime = asyncio.new_event_loop()
	asyncio.set_event_loop(runtime)
	runtime.create_task(startup(root))
	runtime.run_forever()
	runtime.close()

if environ.get('TERM_PROGRAM') == 'vscode':
	main()
	#main(datetime(year=2025, month=10, day=3, hour=10, minute=25, second=30))
else:
	main()