if __name__ == "__main__":
	from sys import path as sp
	from os import path
	sp.append(path.abspath(path.join(path.dirname(__file__), '..')))
import logging, asyncio, tkinter as tk, pystray, modules.state as state
from tkinter import Tk
from json import load as jload, dump as jdump
from typing import Any, Optional, Literal
from datetime import datetime, date
from threading import Thread
from PIL import Image
from modules.clock import font_size, get_rn
logger = logging.getLogger(__name__)
# region Settings
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
				logger.info("Settings loaded properly")
		except FileNotFoundError:
			logger.warning("Settings file not found, creating a default one.")
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
# endregion
# region Tray
async def setup_tray(root:Tk):
	def on_quit(icon, item):
		logger.info("Closing application")
		icon.stop()
		global root, update_cycle_task, transparency_task
		update_cycle_task.cancel()
		transparency_task.cancel()
		state.root.quit()
		state.runtime.stop()
	def settings_callback(): state.runtime.create_task(open_settings(root))
	def setDelayWindow(icon, item):
		async def CreateWindow():
			global delayRoot
			def saveValue(event=None):
				state.settings.delay = int(val.get())
				delayWindowTask.cancel()
				delayRoot.destroy()
			delayRoot = tk.Toplevel(root)
			delayRoot.title("Delay Time Input")
			delayRoot.geometry(f"+{delayRoot.winfo_screenwidth()//2-25}+{delayRoot.winfo_screenheight()//2-25}")
			delayRoot.resizable(False, False)
			delayRoot.grid(1, 6, 150, 50)
			tk.Label(delayRoot, text="Set Delay Time (in seconds)").grid(row=0, column=0)
			val = tk.Entry(delayRoot, textvariable=tk.IntVar(value=state.settings.delay))
			val.grid(row=1, column=0)
			tk.Label(delayRoot, text="Negative = Earlier\nPositive = Later").grid(row=2, column=0, rowspan=2)
			tk.Button(delayRoot, text="Save", command=saveValue).grid(row=5, column=0)
			delayRoot.focus_force()
			delayRoot.bind('<Return>', saveValue)
			delayWindowTask = asyncio.create_task(updateFast(delayRoot))
		state.runtime.create_task(CreateWindow())
	def ScheduleWindow(icon, item):
		async def CreateWindow():
			scheduleRoot = tk.Toplevel(root)
			scheduleRoot.title("Schedule")
			windowHeight = max([len(i) for i in state.settings.default_schedule], [len(val) for key, val in state.settings.special_days.items() if datetime.strptime(key, "%Y-%m-%d").strftime("%V") == (await get_rn()).strftime("%V")])
			windowWidth = len(state.settings.default_schedule)
			if specialDayThisWeek := any([datetime.strptime(key, "%Y-%m-%d").strftime("%V") == (await get_rn()).strftime("%V") for key in state.settings.special_days.keys()]):
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
		state.runtime.create_task(CreateWindow())
	icon = pystray.Icon("Csengetés időzítő", Image.open("icon.ico"), menu=pystray.Menu(
		pystray.MenuItem(lambda item: f"Delay: {state.settings.delay}", setDelayWindow),
		pystray.MenuItem("Fullscreen Schedule", ScheduleWindow),
		pystray.MenuItem("Settings", settings_callback),
		pystray.MenuItem("Quit", lambda icon, item: on_quit(icon, item))
	))
	Thread(target=icon.run, daemon=True).start()
async def updateFast(_root:Tk):
	while True:
		_root.update()
		await asyncio.sleep(0.01)
_settings:tk.Toplevel|None = None 
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
# endregion

if __name__ == "__main__": 
	from csengo import main
	main()