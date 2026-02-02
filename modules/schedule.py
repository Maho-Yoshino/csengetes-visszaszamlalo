import modules.state as state
from datetime import date, datetime, time
from logging import getLogger
logger = getLogger(__name__)

class _Class:
	"""A single class in a day"""
	begin:time
	end:time
	beginDatetime:datetime
	endDatetime:datetime
	name:str|None = None 
	room:str|None = None 
	teacher:str|None = None
	def __init__(self, classID:str|dict[str, str]|None, times:str):
		if isinstance(classID, dict):
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
			return
		classData:dict[str, str] = state.settings.classes.get(classID, {})
		times:list[str] = times.split("-", 1)
		self.beginDatetime = datetime.strptime(times[0], "%H:%M")
		self.endDatetime = datetime.strptime(times[1], "%H:%M")
		self.begin = self.beginDatetime.time()
		self.end = self.endDatetime.time()
		if (state.settings.classes.get(classID, None) is None and classID is not None):
			logger.warning(f"Class '{classID}' does not exist in classlist. Ignoring in countdown.")
			return
		self.name = classData.get("name", None)
		if (self.name is None and classID is not None):
			logger.warning(f"Parameter 'name' of class '{classID}' does not exist")
		self.room = classData.get("room", None)
		if (self.room is None and classID is not None):
			logger.warning(f"Parameter 'room' of class '{classID}' does not exist")
		self.teacher = classData.get("teacher", None)
		if (self.teacher is None and classID is not None):
			logger.warning(f"Parameter 'teacher' of class '{classID}' does not exist")
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
		schedule:list[dict[str, str|list[str]]] = state.settings.schedule.default[weekday]
		if weeknum % 2 == int(state.settings.schedule.offsetSecondary) and str(weekday) in state.settings.schedule.secondary:
			for times, classID in state.settings.schedule.secondary[str(weekday)].items():
				if times in state.settings.schedule.default[weekday]:
					schedule[times] = classID
		if self.specialDay:
			tmp = state.settings.events.specialDays.get(self._date.strftime("%Y-%m-%d"), None)
			if tmp is None:
				tmp = schedule
			else:
				if tmp[...]:
					...
		else: 
			tmp = schedule
		times = list(tmp.keys())
		self.classes = []
		for classinfo in tmp.items():
			if classinfo[0] is not None and isinstance(classinfo[1], list):
				self.classes.append([_Class(_, classinfo[0]) for _ in classinfo[1]])
			else:
				self.classes.append(_Class(classinfo[1], classinfo[0]))
		logger.debug("Initialized Schedule class")
	def parseTimes(times:str) -> tuple[time]:
		times:list[str] = times.split("-", 1)
		return datetime.strptime(times[0], "%H:%M").time(), datetime.strptime(times[1], "%H:%M").time()