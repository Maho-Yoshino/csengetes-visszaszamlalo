from .classes import Classes
from .config import Config
from .events import Events
from .schedule import Schedule
from .localization import Localization

class Settings:
	def __init__(self):
		self.classes = Classes()
		self.config = Config()
		self.events = Events()
		self.schedule = Schedule(self.classes, self.events)
		self.localization = Localization(self.config.lang)