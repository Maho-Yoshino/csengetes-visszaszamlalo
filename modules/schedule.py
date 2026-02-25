import modules.state as state
from datetime import date, datetime, time
from logging import getLogger
logger = getLogger(__name__)

class _Class:
	"""A single class in a day"""
	begin:datetime
	end:datetime
	name:str|None = None 
	room:str|None = None 
	teacher:str|None = None
	def __init__(self, classID:dict[str, str]|None, times:str):
		if classID is None:
			logger.debug(f"Class set to none at '{times}'")
			return
		self.begin, self.end = Schedule.parseTimes(times)
		self.beginDatetime = datetime.combine((state.getTime()).date(), self.begin)
		self.endDatetime = datetime.combine((state.getTime()).date(), self.end)
		self.name = classID.get("name", None)
		if (self.name is None):
			logger.warning(f"Parameter 'name' of direct class at time '{times}' does not exist")
		self.room = classID.get("room", None)
		if (self.room is None):
			logger.warning(f"Parameter 'room' of direct class at time '{times}' does not exist")
		self.teacher = classID.get("teacher", None)
		if (self.teacher is None):
			logger.warning(f"Parameter 'teacher' of direct class at time '{times}' does not exist")
		times:list[str] = times.split("-", 1)
		self.begin = datetime.strptime(times[0], "%H:%M")
		self.end = datetime.strptime(times[1], "%H:%M")
class Schedule:
	"""The schedule for a single day. Must be regenerated on day change"""
	classes:list["_Class", list["_Class"]]
	_date:date
	specialDay:bool
	def __init__(self, other_date:datetime|None=None):
		self._date = (other_date if other_date is not None else state.getTime()).date()
		weekday = self._date.weekday()
		weeknum = self._date.isocalendar().week
		self.specialDay = any([day.date() == self._date for day in state.settings.events.specialDays.keys()])
		if weekday not in range(len(state.settings.schedule.default)) and not self.specialDay:
			return
		self.classes:list[_Class|list[_Class]|None] = []
		if len(tmp := state.settings.schedule.getUnifiedSchedule(week_of=other_date)) > weekday:
			schedule:dict[str, str|list[str]|None] = tmp[weekday]
			for time, _class in schedule.items():
				if isinstance(_class, list):
					self.classes.append([_Class(_, time) for _ in _class])
				elif isinstance(_class, str):
					self.classes.append(_Class(_class, time))	
				else:
					self.classes.append(None)
		logger.debug(f"Initialized Schedule class (len {len(self.classes)})")
	def parseTimes(times:str) -> tuple[time]:
		times:list[str] = times.split("-", 1)
		return datetime.strptime(times[0], "%H:%M").time(), datetime.strptime(times[1], "%H:%M").time()