from __future__ import annotations
import modules.state as state
from datetime import date, datetime, time
from logging import getLogger
from .settings.schedule import _classData

logger = getLogger(__name__)

class _Class:
	"""A single class in a day"""
	begin:datetime
	end:datetime
	name:str
	room:str|None = None
	teacher:str|None = None
	def __init__(self, _class:_classData, times:str):
		_date = state.getTime().date()
		self.begin, self.end = Schedule.parseTimes(times)
		self.begin = datetime.combine(_date, self.begin)
		self.end = datetime.combine(_date, self.end)
		self.name = _class.name
		if (self.name is None):
			raise ValueError(f"Parameter 'name' of class at time '{times}' does not exist")
		self.room = _class.room
		if (self.room is None):
			logger.warning(f"Parameter 'room' of class at time '{times}' does not exist")
		self.teacher = _class.teacher
		if (self.teacher is None):
			logger.warning(f"Parameter 'teacher' of class at time '{times}' does not exist")
class Schedule:
	"""The schedule for a single day. Must be regenerated on day change"""
	classes:list[list["_Class"]]
	_date:date
	specialDay:bool
	def __init__(self, other_date:datetime|None=None):
		self._date = (other_date if other_date is not None else state.getTime()).date()
		weekday = self._date.weekday()
		self.specialDay = any([day.date() == self._date for day in state.settings.events.specialDays.keys()])
		if weekday not in range(len(state.settings.schedule.default)) and not self.specialDay:
			return
		self.classes = []
		if len(tmp := state.settings.schedule.getUnifiedSchedule(week_of=other_date)) > weekday:
			schedule:dict[str, _classData|list[_classData]] = tmp[weekday]
			for time, _class in schedule.items():
				if isinstance(_class, list):
					self.classes.append([(_2 if (_2 := _Class(_, time)).name != None else None) for _ in _class])
				elif isinstance(_class, _classData):
					self.classes.append([_Class(_class, time) if _class.name is not None else None])
				else:
					self.classes.append([])
		logger.debug(f"Initialized Schedule class (len {len(self.classes)})")
	def parseTimes(times:str) -> tuple[time]:
		times:list[str] = times.split("-", 1)
		return datetime.strptime(times[0], "%H:%M").time(), datetime.strptime(times[1], "%H:%M").time()