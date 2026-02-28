from json import load as jload
from pathlib import Path
from logging import getLogger
from tkinter import messagebox
from dataclasses import dataclass
def merge(obj: dict, default: dict) -> dict:
	return {k: obj.get(k, v) for k, v in default.items()}
class Localization:
	@dataclass(slots=True)
	class _trayLoc:
		name:str
		delay:str
		delayMinutesDisplay:str
		delaySecondsDisplay:str
		fullscreen_schedule:str
		settings:str
		close:str
		@classmethod
		def from_dict(cls, obj, default):
			return cls(**merge(obj, default))
	class _delaySettingLoc:
		def __init__(self, obj:dict[str, str], default:dict[str, str]):
			self.title = obj.get("title", default["title"])
			self.label = obj.get("label", default["label"])
			self.help = obj.get("help", default["help"])
			self.btn = obj.get("btn", default["btn"])
	class _settingsLoc:
		topbar:dict[str, str]
		def __init__(self, obj:dict[str, str|dict[str, str]], default:dict[str, str|dict[str, str]]):
			self.title = obj.get("title", default["title"])
			self.topbar = obj.get("topbar", default["topbar"])
	class _alertLoc:
		def __init__(self, obj:dict[str, str], default:dict[str, str]):
			self.title = obj.get("title", default["title"])
			self.defaultText = obj.get("defaultText", default["defaultText"])
	class _mainlabelLoc:
		def __init__(self, obj:dict[str, str], default:dict[str, str]):
			self.inClass = obj.get("inClass", default["inClass"])
			self.onBreak = obj.get("onBreak", default["onBreak"])
			self.dayOver = obj.get("dayOver", default["dayOver"])
	class _numberingLoc:
		def __init__(self, obj:dict[str, str]):
			self.default = obj.get("default")
			self.values = {k: v for k, v in obj.items() if k != "default"}
		def getSuffix(self, _class:int) -> str:
			return self.values.get(str(_class), self.default)
	class _messagesLoc:
		newSettings:_message
		error:_message
		windowsOnly:_message
		anotherInstance:_message
		updatePrompt:_message
		@dataclass(slots=True)
		class _message:
			title:str
			message:str
			@classmethod
			def from_dict(cls, obj:dict, default:dict):
				return cls(**merge(obj, default))
		def __init__(self, obj:dict[str, dict[str, str]], default:dict[str, dict[str, str]]):
			self.newSettings = self._message.from_dict(
				obj.get("newSettings", {}), 
				default["newSettings"]
			)
			self.error = self._message.from_dict(
				obj.get("error", {}),
				default["error"]
			)
			self.windowsOnly = self._message.from_dict(
				obj.get("windowsOnly", {}), 
				default["windowsOnly"]
			)
			self.anotherInstance = self._message.from_dict(
				obj.get("anotherInstance", {}), 
				default["anotherInstance"]
			)
			self.updatePrompt = self._message.from_dict(
				obj.get("updatePrompt", {}), 
				default["updatePrompt"]
			)
	_lang_tag:str
	messages:_messagesLoc
	classNumbering:_numberingLoc # Only required value is "default"
	mainlabel:_mainlabelLoc
	alert:_alertLoc
	nextClass:str
	substitute:str
	delaySetting:_delaySettingLoc
	tray:_trayLoc
	settings:_settingsLoc
	def __init__(self, language:str):
		self.logger = getLogger(__name__)
		if not Path(f"lang\\{language}.json").exists():
			self.logger.warning(f"Given locale '{language}.json' does not exist. Defaulting to english.")
			messagebox.showwarning("Invalid language selected", f"The selected language '{language}' does not exist in the program.\nDefaulting to english.")
			language = "en"
		if language == "en" and not Path("lang\\en.json").exists():
			self.logger.critical("English locale doesn't exist on user's computer")
			return
		with open(f"lang\\{language}.json", "r", encoding="utf-8") as f:
			self._lang:dict = jload(f)
			self.logger.info(f"Locale '{language}' loaded properly")
		with open(f"lang\\en.json", "r", encoding="utf-8") as f:
			self._defaults:dict = jload(f)
		self._lang_tag = language
		self.messages = self._messagesLoc(self._lang.get("messages", {}), self._defaults["messages"])
		self.classNumbering = self._numberingLoc(self._lang.get("classNumbering"))
		self.mainlabel = self._mainlabelLoc(self._lang.get("mainlabel", {}), self._defaults["mainlabel"])
		self.alert = self._alertLoc(self._lang.get("alert", {}), self._defaults["alert"])
		self.nextClass = self._lang.get("nextClass", self._defaults["nextClass"])
		self.substitute = self._lang.get("substitute", self._defaults["substitute"])
		self.delaySetting = self._delaySettingLoc(self._lang.get("delaySetting", {}), self._defaults["delaySetting"])
		self.tray = self._trayLoc.from_dict(self._lang.get("tray", {}), self._defaults["tray"])
		self.settings = self._settingsLoc(self._lang.get("settings", {}), self._defaults["settings"])
	def format(self, text: str, **values) -> str:
		try:
			return text.format_map(values)
		except KeyError as e:
			self.logger.error(f"Missing localization placeholder: {e}")
			return text