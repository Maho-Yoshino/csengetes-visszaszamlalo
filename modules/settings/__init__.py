from .classes import Classes
from .config import Config
from .events import Events
from .schedule import Schedule
from .localization import Localization

class Settings:
	def __init__(self):
		self.classes = Classes()
		self.schedule = Schedule()
		self.config = Config()
		self.events = Events()
		self.localization = Localization(self.config.lang)