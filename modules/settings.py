if __name__ == "__main__":
	from sys import path as sp
	from os import path
	sp.append(path.abspath(path.join(path.dirname(__file__), '..')))
import logging, tkinter as tk
import modules.state as state
from tkinter import Tk
from json import load as jload, dump as jdump
from typing import Any, Literal
from datetime import datetime
from modules.clock import fontSize
logger = logging.getLogger(__name__)
CURRENT_VERSION:int = 2

def clamp(num:int|float, _min:int|float, _max:int|float):
	return max(_min, min(num, _max))
class Settings:
	def __init__(self, filename: str = "settings.json", encoding:str="utf-8"):
		self.filename = filename
		self.encoding = encoding
		self._data: dict[str, Any] = {}
		self.load_settings()
	_settings:tk.Toplevel|None = None 
	async def open_settings(self, root:Tk):
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
					"defaultSchedule": [{},{},{},{},{}],
					"secondarySchedule": {},
					"showTeacher":False,
					"specialDays":{},
					"delay":0,
					"alpha": {
						"default":0.75, 
						"onHover":0.25
					},
					"version":1
				}, f, indent=4)
			with open(self.filename, "r", encoding=self.encoding) as f:
				self._data = jload(f)
				logger.info("Settings file created successfully")
		# Set default values if missing
		self._data.setdefault("classlist", {})
		self._data.setdefault("defaultSchedule", [{},{},{},{},{}])
		self._data.setdefault("secondarySchedule", {})
		self._data.setdefault("showTeacher", False)
		self._data.setdefault("specialDays", {})
		self._data.setdefault("debug", False)
		self._data.setdefault("delay", 0)
		self._data.setdefault("alpha", {"default":0.75,"onHover":0.25})
		self._data.setdefault("version", 0)
		self._data.setdefault("ignoreUpdates", False)
		self._data.setdefault("alertTimes", [])
		self._data.setdefault("logLevel", 10)
	def save(self):
		with open(self.filename, "w", encoding="utf-8") as f:
			jdump(self._data, f, indent=4, ensure_ascii=False)
	@property # classlist
	def classlist(self) -> dict[str, dict[str, str]]:
		return self._data["classlist"]
	def setClasslist(self, _class:str, key:str, value:str):
		if _class not in self._data["classlist"]:
			self._data["classlist"][_class] = {}
		self._data["classlist"][_class][key] = value
		self.save()
	@property # defaultSchedule
	def defaultSchedule(self) -> list[dict[str, str|list[str]|None]]:
		return self._data["defaultSchedule"]
	def setDefaultSchedule(self, day:int, value:dict[str, str|list[str]|None]):
		while len(self.defaultSchedule) <= day:
			self.defaultSchedule.append({})
		self.defaultSchedule[day] = value
		self.save()
	@property # secondarySchedule
	def secondarySchedule(self) -> dict[int, dict[str, str|list[str]|None]]:
		return self._data["secondarySchedule"]
	def setSecondarySchedule(self, index:int, value:dict[str, str|list[str]|None]):
		self.secondarySchedule[index] = value
		self.save()
	@property # showTeacher
	def showTeacher(self) -> bool:
		return self._data["showTeacher"]
	@showTeacher.setter
	def setShowTeacher(self, value:bool):
		self.showTeacher = value
		self.save()
	@property # specialDays
	def specialDays(self) -> dict[datetime, dict[str, str|list[str]|None]]:
		return {
			datetime.strptime(date_str, "%Y-%m-%d"):schedule
			for date_str, schedule in self._data["specialDays"].items()
		}
	def setSpecialDays(self, day:datetime, schedule:dict[str, str|list[str]|None]):
		self._data["specialDays"][day.strftime("%Y-%m-%d")] = schedule
		self.save()
	@property # debug
	def debug(self) -> bool:
		return self._data["debug"]
	@property # delay
	def delay(self) -> int:
		return self._data["delay"]
	@delay.setter
	def delay(self, value: int):
		self._data["delay"] = value
		self.save()
	@property # alpha
	def alpha(self) -> dict[str, float]:
		return self._data["alpha"]
	def setAlpha(self, _type:Literal["default"]|Literal["onHover"], value:float):
		self._data["alpha"][_type] = clamp(value,0,1)
		self.save()
	@property # version
	def version(self) -> int:
		return self._data["version"]
	@property # ignoreUpdates
	def ignoreUpdates(self) -> bool:
		return self._data["ignoreUpdates"]
	@ignoreUpdates.setter
	def ignoreUpdates(self, value:bool):
		self.ignoreUpdates = value
		self.save()
	@property # alertTimes
	def alertTimes(self) -> list[datetime]:
		return [
			datetime.strptime(i, "%Y-%m-%dT%H:%M") 
			for i in self._data["alertTimes"] 
			if datetime.strptime(i, "%Y-%m-%dT%H:%M") < (datetime.now() if state.dummyDate is None else state.dummyDate)
		]
	@alertTimes.setter
	def alertTimes(self, values:list[datetime]):
		self.alertTimes = [
			i.strftime("%Y-%m-%dT%H:%M")
			for i in values
		]
		self.save()
	@property # logLevel
	def logLevel(self) -> Literal[10, 20, 30, 40, 50]:
		"""
		Logging levels:
		------------
		0 - Unset  
		10 - DEBUG  
		20 - INFO  
		30 - WARNING / WARN  
		40 - ERROR  
		50 - FATAL / CRITICAL  
		"""
		return self._data["logLevel"]

if __name__ == "__main__": 
	from csengo import main
	main()