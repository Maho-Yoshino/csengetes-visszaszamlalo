if __name__ == "__main__":
	from sys import path as sp
	from os import path
	sp.append(path.abspath(path.join(path.dirname(__file__), '..')))
import logging, tkinter as tk
import modules.state as state
from tkinter import Tk
from json import load as jload, dump as jdump
from typing import Any, Literal
from datetime import datetime, time
from modules.clock import fontSize
from pathlib import Path
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
		if (not Path("settings.json").exists()):
			logger.warning("Settings file not found, creating a default one.")
			with open(self.filename, "x", encoding=self.encoding) as f:
				logger.info("Created default settings file")
		with open(self.filename, "r", encoding=self.encoding) as f:
			self._data = jload(f)
			logger.info("Settings loaded properly")
		# Set default values if missing
		defaults = {
			"classlist": {}, 
			# ex. 
			# "ID": {
			#	 "name": "...",
			#	 "teacher": "...",
			#	 "location": "...",
			# }
			"defaultSchedule": [{},{},{},{},{}], 
			"secondarySchedule": {}, # ex. "3": {"13:25-14:15": "MAT"} (0 = Monday, 1 = Tuesday, etc.; "MAT" = ID defined in classlist) 
			"offsetSecondarySchedule": False,
			"showTeacher": False,
			"specialDays": {}, # ex. "2023-12-24": {"09:00-10:00": "ANG"} ("ANG" = ID defined in classlist)
			"delay": 0, # Delay of the bell in minutes (positive = late, negative = early)
			"alpha": {"default":0.75,"onHover":0.25}, # Values between 1 and 0
			"version": CURRENT_VERSION,
			"ignoreUpdates": False, # If true, update checks will be ignored
			"alertTimes": [] # ex. (During 1st class on 2025.11.05, show alert 5 minutes before end of class, and delete alert afterward)
			# "; 5": {
			#	"date":"2025-11-05",
			# 	"time":"8:40",
			# 	"keep": False
			# } 
		}
		for key, value in defaults.items():
			self._data.setdefault(key, value)
		self.save()
	def save(self):
		with open(self.filename, "w", encoding="utf-8") as f:
			jdump(self._data, f, indent=4, ensure_ascii=False)
	# region classlist
	@property
	def classlist(self) -> dict[str, dict[str, str]]:
		return self._data["classlist"]
	def setClasslist(self, _class:str, key:str, value:str):
		if _class not in self._data["classlist"]:
			self._data["classlist"][_class] = {}
		self._data["classlist"][_class][key] = value
		self.save()
	# endregion
	# region defaultSchedule
	@property
	def defaultSchedule(self) -> list[dict[str, str|list[str]|None]]:
		return self._data["defaultSchedule"]
	def setDefaultSchedule(self, day:int, value:dict[str, str|list[str]|None]):
		if day not in range(7):
			raise IndexError("Day must be between 0 (Monday) and 6 (Sunday).")
		while len(self.defaultSchedule) < day+1:
			self.defaultSchedule.append({})
		self.defaultSchedule[day] = value
		self.save()
	# endregion
	# region secondarySchedule
	@property
	def secondarySchedule(self) -> dict[int, dict[str, str|list[str]|None]]:
		return self._data["secondarySchedule"]
	def setSecondarySchedule(self, index:int, value:dict[str, str|list[str]|None]):
		self.secondarySchedule[index] = value
		self.save()
	# endregion
	# region showTeacher
	@property
	def showTeacher(self) -> bool:
		return self._data["showTeacher"]
	@showTeacher.setter
	def setShowTeacher(self, value:bool):
		self.showTeacher = value
		self.save()
	# endregion
	# region specialDays
	@property 
	def specialDays(self) -> dict[datetime, dict[str, str|list[str]|None]]:
		return {
			datetime.strptime(date_str, "%Y-%m-%d"):schedule
			for date_str, schedule in self._data["specialDays"].items()
		}
	def setSpecialDays(self, day:datetime, schedule:dict[str, str|list[str]|None]):
		self._data["specialDays"][day.strftime("%Y-%m-%d")] = schedule
		self.save()
	# endregion
	# region debug
	@property
	def debug(self) -> bool:
		return self._data.get("debug", False)
	# endregion
	# region delay
	@property
	def delay(self) -> int:
		return self._data["delay"]
	@delay.setter
	def delay(self, value: int):
		self._data["delay"] = value
		self.save()
	# endregion
	# region alpha
	@property
	def alpha(self) -> dict[str, float]:
		return self._data["alpha"]
	def setAlpha(self, _type:Literal["default"]|Literal["onHover"], value:float):
		self._data["alpha"][_type] = clamp(value,0,1)
		self.save()
	# endregion
	# region version & updates
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
	# endregion
	# region alertTimes
	@property # alertTimes
	def alertTimes(self) -> list[dict[str, int|bool|str]]:
		change:bool = False
		newAlerts = []
		for alert in self._data["alertTimes"]:
			alert:dict[str, int|bool|str]
			new = {
				"message":alert["message"],
				"time":alert["time"],
				"keep":alert.get("keep", False)
			}
			if (_date := alert.get("date", None)) is not None:
				new.update({"date": _date})
				if not datetime.strptime(_date, "%Y-%m-%d") > state.getTime():
					newAlerts.append(new)
				else:
					change = True
			else:
				rn = state.getTime()
				if (datetime.strptime(new["time"], "%H:%M").time() > rn.time()):
					newAlerts.append(new)
		if change:
			self.save()
		return self._data["alertTimes"]
	def setAlertTime(self, time:time, *, day:datetime=datetime.fromtimestamp(0), keep:bool=False, message:str="Értesítés ideje elérkezett!"):
		tmp = {
			"message": message,
			"keep": keep,
			"time": time.strftime("%H:%M")
		}
		if day is not None:
			tmp.update({"date": day.strftime("%Y-%m-%d")})
		self.alertTimes.append()
		self.save()
	# endregion
	# region logLevel
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
		return self._data.get("logLevel", 10)	
	# endregion

if __name__ == "__main__": 
	from csengo import main
	main()