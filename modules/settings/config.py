from json import load as jload, dump as jdump
from pathlib import Path
from logging import getLogger
from typing import Literal
from ..utils import clamp

logger = getLogger(__name__)

class Config:
	# NOTE: Changes are not persisted until save() is called explicitly
	def __init__(self, filename:str = "config.json"):
		self.path = Path("config") / filename
		self.path.parent.mkdir(parents=True, exist_ok=True)
		if (not self.path.exists()):
			logger.warning("Config file not found, creating a default one.")
			self._data = {}
			self.save()
		else:
			with open(self.path, "r", encoding="utf-8") as f:
				self._data = jload(f)
				logger.info("Configs loaded")
		
		defaults = {
			"background": "#000000",
			"foreground": "#FFFFFF",
			"lang": "en",
			"ignoreUpdates": False,
			"alpha": {"default": 0.75, "onHover":0.25},
			"showTeacher": False
		}

		changed = False
		for key, value in defaults.items():
			if key not in self._data:
				self._data[key] = value
				changed = True
		self._data.setdefault("alpha", {})
		self._data["alpha"].setdefault("default", 0.75)
		self._data["alpha"].setdefault("onHover", 0.25)
		if changed:
			self.save()
	def save(self):
		with self.path.open("w", encoding="utf-8") as f:
			jdump(self._data, f, indent=4, ensure_ascii=False)
	# region Update
	@property # ignoreUpdates
	def ignoreUpdates(self) -> bool:
		return self._data["ignoreUpdates"]
	@ignoreUpdates.setter
	def ignoreUpdates(self, value:bool):
		self._data["ignoreUpdates"] = value
	# endregion
	# region alpha
	@property
	def alpha(self) -> dict[str, float]:
		return self._data["alpha"]
	def setAlpha(self, _type:Literal["default"]|Literal["onHover"], value:float):
		self._data["alpha"][_type] = clamp(value,0,1)
	# endregion
	# region showTeacher
	@property
	def showTeacher(self) -> bool:
		return self._data["showTeacher"]
	@showTeacher.setter
	def showTeacher(self, value:bool):
		self._data["showTeacher"] = value
	# endregion
	# region debug
	@property
	def debug(self) -> bool:
		return self._data.get("debug", False)
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
	# region Background color
	@property
	def background(self) -> int:
		return int(self._data["background"].removeprefix("#"), 16)
	@background.setter
	def background(self, value:int):
		self._data["background"] = f"#{value:06X}"
	# endregion
	# region Foreground color
	@property
	def foreground(self) -> int:
		return int(self._data["foreground"].removeprefix("#"), 16)
	@foreground.setter
	def foreground(self, value:int):
		self._data["foreground"] = f"#{value:06X}"
	# endregion
	# region Language
	@property
	def lang(self) -> str:
		return self._data["lang"]
	# endregion
	