if __name__ == "__main__":
	from sys import path as sp
	from os import path
	sp.append(path.abspath(path.join(path.dirname(__file__), '..')))
import logging, tkinter as tk, modules.state as state
from tkinter import Tk
from json import load as jload, dump as jdump
from typing import Any, Optional, Literal
from datetime import datetime, date
from modules.clock import fontSize
logger = logging.getLogger(__name__)

class Settings:
	def __init__(self, filename: str = "settings.json", encoding:str="utf-8"):
		self.filename = filename
		self.encoding = encoding
		self._data: dict[str, Any] = {}
		self.load_settings()
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
		tk.Label(_settings, text="Settings window", font=fontSize(20)).grid(row=0, column=0, columnspan=10)
		await state.updateFast(_settings)
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
					"default_schedule": [{},{},{},{},{}],
					"showTeacher":False,
					"special_days":{},
					"special_begintimes":{},
					"classes_begin":800,
					"delay":0,
					"alpha": {
						"default":0.75, 
						"onHover":0.25
					}
				}, f, indent=4)
			with open(self.filename, "r", encoding=self.encoding) as f:
				self._data = jload(f)
				logger.info("Settings file created successfully")
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
		self._data.setdefault("version", 1)
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
	@property # version
	def version(self) -> int:
		return self._data["version"]

if __name__ == "__main__": 
	from csengo import main
	main()