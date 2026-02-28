from json import load as jload, dump as jdump
from pathlib import Path
from logging import getLogger
from typing import Literal

ClassKey = Literal["room", "teacher", "name"]
CLASS_KEYS = {"room", "teacher", "name"}
class Classes:
	# NOTE: Changes are not persisted until save() is called explicitly
	def __init__(self):
		self._logger = getLogger(__name__)
		self.path = Path("config") / "classes.json"
		self.path.parent.mkdir(parents=True, exist_ok=True)
		if (not self.path.exists()):
			self._logger.warning("Class list file not found, creating default.")
			self._data = {}
			self.save()
		else:
			with open(self.path, "r", encoding="utf-8") as f:
				self._data = jload(f)
				if not isinstance(self._data, dict):
					self._logger.error("Invalid classlist format, resetting")
					self._data = {}
					self.save()
				self._logger.info("Class list loaded")
	def save(self):
		with self.path.open("w", encoding="utf-8") as f:
			jdump(self._data, f, indent=4, ensure_ascii=False)
	# region classlist
	@property
	def classes(self) -> dict[str, dict[ClassKey, str]]:
		return self._data
	def add(self, _class:str, **values:str):
		for k, v in values.items():
			if k not in CLASS_KEYS:
				raise KeyError(f"Invalid class key: {k}")
			if not isinstance(v, str):
				raise TypeError(f"Class value for '{k}' must be str")
		if _class in self._data:
			raise LookupError(f"Class '{_class}' already exists")
		self._data[_class] = dict(values)
	def set(self, _class:str, key:ClassKey, value:str):
		if key not in CLASS_KEYS:
			raise KeyError(f"Invalid class key: {key}")
		if _class not in self.classes:
			raise LookupError(f"Class '{_class}' does not exist")
		self._data[_class][key] = value
	def remove(self, _class:str):
		if _class not in self.classes:
			raise LookupError(f"Class '{_class}' does not exist")
		self._data.pop(_class)
	def get(self, _class:str, default:str=None) -> dict[str, str]:
		return self._data.get(_class, default)
	# endregion
	