from json import load as jload, dump as jdump
from pathlib import Path
from logging import getLogger

logger = getLogger(__name__)

class Schedule:
	# NOTE: Changes are not persisted until save() is called explicitly
	def __init__(self, filename:str = "schedule.json"):
		self.path = Path("config") / filename
		self.path.parent.mkdir(parents=True, exist_ok=True)
		if (not self.path.exists()):
			logger.warning("Schedule file not found, creating a default one.")
			self._data = {}
			self.save()
		else:
			with open(self.path, "r", encoding="utf-8") as f:
				self._data = jload(f)
				logger.info("Schedule settings loaded")
		
		defaults = {
			"default": [{},{},{},{},{}],
			"secondary": {},
			"offsetSecondary": False, # Offset the secondary schedule by 1 week (A-B weeks -> B-A weeks essentially)
			"delay":0
		}
		
		changed = False
		for key, value in defaults.items():
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
	def default(self) -> str|list[str]|None|dict[str, str]|list[dict[str, str]]:
		return self._data["default"]
	def setDefaultSchedule(self, day:int, value:dict[str, str|list[str]|None|dict[str, str]|list[dict[str, str]]]):
		if day not in range(7):
			raise IndexError("Day must be between 0 (Monday) and 6 (Sunday).")
		tmp = self._data["default"]
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
	# endregion
	# region offsetSecondary
	@property
	def offsetSecondary(self) -> bool:
		return self._data["offsetSecondary"]
	@offsetSecondary.setter
	def offsetSecondary(self, value:bool):
		self._data["offsetSecondary"] = value
	# endregion
	# region delay
	@property
	def delay(self) -> int:
		return self._data["delay"]
	@delay.setter
	def delay(self, value: int):
		self._data["delay"] = value
	# endregion