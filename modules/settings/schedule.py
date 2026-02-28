from json import load as jload, dump as jdump
from pathlib import Path
from logging import getLogger
from datetime import timedelta, datetime
from copy import deepcopy
from typing import TYPE_CHECKING
if TYPE_CHECKING:
	from .classes import Classes
	from .events import Events
from ..state import getTime

class _classData:
	def __init__(self, data:dict[str, str]):
		self.name = data.get("name")
		self.room = data.get("room")
		self.teacher = data.get("teacher")

_defaults = {
	"default": [{},{},{},{},{}],
	"secondary": {},
	"offsetSecondary": False, # Offset the secondary schedule by 1 week (A-B weeks -> B-A weeks essentially)
	"delay":0,
	"group":-1 # In case more than 1 class is given for a class, display the n-th one; If -1 then display all 
}
class Schedule:
	# NOTE: Changes are not persisted until save() is called explicitly
	def __init__(self, classes:'Classes', events:'Events'):
		self._logger = getLogger(__name__)
		self.classes = classes
		self.events = events
		self.path = Path("config") / "schedule.json"
		self.path.parent.mkdir(parents=True, exist_ok=True)
		if (not self.path.exists()):
			self._logger.warning("Schedule file not found, creating a default one.")
			self._data = {}
			self.save()
		else:
			with open(self.path, "r", encoding="utf-8") as f:
				self._data = jload(f)
				self._logger.info("Schedule settings loaded")

		changed = False
		for key, value in _defaults.items():
			if key not in self._data:
				self._data[key] = value
				changed = True
		if changed:
			self.save()
	def save(self):
		with self.path.open("w", encoding="utf-8") as f:
			jdump(self._data, f, indent=4, ensure_ascii=False)
	# region default
	@property
	def default(self) -> list[dict[str, str|None|_classData|list[_classData|None]]]:
		returnData:list[dict[str, '_classData'|None]] = []
		for ind, day in enumerate(self._data["default"]):
			returnData.append({})
			for key, value in day.items():
				returnData[ind][key] = self.convertToClassData(value) 
		return returnData
	def setDefaultSchedule(self, day:int, value:dict[str, str|None|dict[str, str]]):
		if day not in range(7):
			raise IndexError("Day must be between 0 (Monday) and 6 (Sunday).")
		tmp = self.default
		while len(self.default) < day+1:
			tmp.append({})
		tmp[day] = value
		self._data["default"] = tmp
	# endregion
	# region secondary
	@property
	def secondary(self) -> dict[str, dict[str, str|list[str]|None]]:
		return self._data["secondary"]
	def setSecondary(self, index:int, value:dict[str, str|list[str]|None]):
		self._data["secondary"][str(index)] = value
	@property
	def offsetSecondary(self) -> bool:
		return self._data["offsetSecondary"]
	@offsetSecondary.setter
	def offsetSecondary(self, value:bool):
		self._data["offsetSecondary"] = value
	def currentlySecondaryWeek(self) -> bool:
		return getTime().date().isocalendar().week % 2 == int(self.offsetSecondary)
	# endregion
	# region delay
	@property
	def delay(self) -> int:
		return self._data["delay"]
	@delay.setter
	def delay(self, value: int):
		self._data["delay"] = value
	# endregion
	# region Class group
	@property
	def group(self) -> int:
		return self._data["group"]
	@group.setter
	def group(self, value:int):
		self._data["group"] = value
		self.save()
	# endregion
	# region Unified schedule (Primary, Secondary and Special days combined)
	def convertToClassData(self, data:str|dict[str, str]|None|list[str|dict[str, str]]) -> list[_classData|None]|_classData|None:
		if isinstance(data, str):
			return _classData(self.classes.get(data))
		elif isinstance(data, dict):
			return _classData(data)
		elif isinstance(data, list):
			_ = []
			for data in data:
				if isinstance(data, str):
					_.append(_classData(self.classes.get(data)))
				elif isinstance(data, dict):
					_.append(_classData(data))
				elif data is None:
					_.append(None)
				else:
					raise ValueError(f"Invalid type ({type(data)}) given")
			return _
		elif data is None:
			return None
		else:
			raise ValueError(f"Invalid type ({type(data)}) given")
	def getUnifiedSchedule(self, *, week_of:datetime|None=None) -> list[dict[str, str | _classData | list[_classData | None] | None]]:
		finalSchedule = deepcopy(self.default)
		if week_of is None: _date = getTime().date() # Get current week if other week is not given
		else: _date = week_of.date()
		weekstart = _date - timedelta(days=_date.weekday()) # Get monday
		if self.currentlySecondaryWeek():
			for dayInd, data in self.secondary.items():
				for times, classID in data.items():
					if times in self.default[int(dayInd)]:
						finalSchedule[times] = classID
		for day, data in self.events.specialDays.items(): # Merge special days with the new schedule
			day:datetime; data:dict[str, bool|dict[str, str|None|list[str]]]
			if weekstart > day.date() > (weekstart + timedelta(days=7)):
				continue
			full_schedule:bool = data.get("full", False)
			_classes:dict[str, str|None|list[str]] = data.get("classes")
			if not full_schedule: # Replace only the given items
				new_timetable = finalSchedule[day.weekday()]
				for time, _class in _classes.items():
					if time not in new_timetable:
						continue
					new_timetable[time] = self.convertToClassData(_class)
				finalSchedule[day.weekday()] = new_timetable
			else: # Replace every item in the day
				new_timetable = {}
				for time, _class in _classes.items():
					new_timetable[time] = self.convertToClassData(_class)
		return finalSchedule
	# endregion