if __name__ == "__main__": 
	from pathlib import Path
	from sys import path
	ROOT = Path(__file__).resolve().parent.parent
	if str(ROOT) not in path:
		path.insert(0, str(ROOT))
import logging, tkinter as tk, asyncio 
import modules.state as state
from datetime import datetime, time, date, timedelta
from tkinter import Tk, messagebox
from tkinter.font import Font
from tkinter.ttk import Separator
from ctypes import windll, c_byte, byref, Structure
from time import perf_counter
logger = logging.getLogger(__name__)

class Schedule:
	classes:list["ClassData", list["ClassData"]] = []
	_date:date = None
	specialDay:bool = False
	class ClassData:
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
			classData:dict[str, str] = state.settings.classlist.get(classID, {})
			times:list[str] = times.split("-", 1)
			self.beginDatetime = datetime.strptime(times[0], "%H:%M")
			self.endDatetime = datetime.strptime(times[1], "%H:%M")
			self.begin = self.beginDatetime.time()
			self.end = self.endDatetime.time()
			if (state.settings.classlist.get(classID, None) is None and classID is not None):
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
	def __init__(self, other_date:datetime|None=None):
		self._date = (other_date if other_date is not None else state.getTime()).date()
		weekday = self._date.weekday()
		weeknum = self._date.isocalendar().week
		self.specialDay = any([datetime.strptime(day, "%Y-%m-%d").date() == self._date for day in state.settings.specialDays.keys()])
		if weekday not in range(len(state.settings.defaultSchedule)) and not self.specialDay:
			return
		schedule:list[dict[str, str|list[str]]] = state.settings.defaultSchedule
		if weeknum % 2 == 1 and str(weekday) in state.settings.secondarySchedule:
			for times, classID in state.settings.secondarySchedule[str(weekday)].items():
				if times in state.settings.defaultSchedule[weekday]:
					schedule[weekday][times] = classID
		if self.specialDay:
			tmp = state.settings.specialDays.get(self._date.strftime("%Y-%m-%d"), None)
			if tmp is None:
				tmp = schedule[weekday]
		else: 
			tmp = schedule[weekday]
		times = list(schedule[weekday].keys())
		for classinfo in tmp.items():
			if classinfo[0] is not None and isinstance(classinfo[1], list):
				self.classes.append([self.ClassData(_, classinfo[0]) for _ in classinfo[1]])
			else:
				self.classes.append(self.ClassData(classinfo[1], classinfo[0]))
		logger.debug("Initialized Schedule class")
	def parseTimes(times:str) -> tuple[time]:
		times:list[str] = times.split("-", 1)
		return datetime.strptime(times[0], "%H:%M").time(), datetime.strptime(times[1], "%H:%M").time()
async def updateCycle(mainLabel:tk.Label, timeLabel:tk.Label, class1Label:tk.Label, class2Label:tk.Label, loc1Label:tk.Label, loc2label:tk.Label, root:Tk, vertSep:Separator, separator:Separator, auxLabel:tk.Label, teacher1Label:tk.Label, teacher2Label:tk.Label):
	lastWidth:int = root.winfo_width()
	def setDynamicSize():
		nonlocal lastWidth
		if (lastWidth != root.winfo_width()):
			logger.debug(f"window size: {root.winfo_width()}x{root.winfo_height()}+{root.winfo_screenwidth()-root.winfo_width()}+0")
			lastWidth = root.winfo_width()
		root.geometry(f"+{root.winfo_screenwidth()-root.winfo_width()}+0")
		root.update()
	def setClassLabels(A_class:Schedule.ClassData, B_class:Schedule.ClassData|None = None, aux:bool = False):
		if not all([i.winfo_ismapped() for i in [class1Label,loc1Label,timeLabel]]):
			class1Label.grid(row=3, column=0, sticky="nsew")
			loc1Label.grid(row=4, column=0, sticky="nsew")
			timeLabel.grid(row=1, column=0, sticky="nsew", columnspan=3)
		class1Label.config(text=f"{A_class.name}", anchor="center")
		loc1Label.config(text=f"{A_class.room}")
		if not aux and auxLabel.winfo_ismapped():
			auxLabel.grid_forget()
			root.rowconfigure(6, weight=0, minsize=0)
		elif aux and not auxLabel.winfo_ismapped():
			auxLabel.grid(row=6, column=0, sticky="nsew", columnspan=3)
			auxLabel.config(text="Következő óra")
			root.rowconfigure(6, weight=1)
		if not separator.winfo_ismapped(): separator.grid(row=2, column=0, sticky="ew", padx=5, pady=5, columnspan=3, ipadx=100)
		if state.settings.showTeacher:
			root.rowconfigure(5, weight=1, minsize=20)
			if B_class is None:
				if teacher2Label.winfo_ismapped():
					teacher2Label.grid_forget()
				if not teacher1Label.winfo_ismapped(): 
					teacher1Label.grid(row=5, column=0, sticky="nsew", columnspan=3)
				else:
					teacher1Label.grid_configure(columnspan=3)
				teacher1Label.config(text=f"{A_class.teacher}", anchor="center", wraplength=root.winfo_width())
			else:
				if not teacher2Label.winfo_ismapped(): 
					teacher2Label.grid(row=5, column=2, sticky="nsew")
				if not teacher1Label.winfo_ismapped(): 
					teacher1Label.grid(row=5, column=0, sticky="nsew", columnspan=1)
				else:
					teacher1Label.grid_configure(columnspan=1)
				teacher2Label.config(text=f"{B_class.teacher}", anchor="center", wraplength=root.winfo_width()//2)
				teacher1Label.config(text=f"{A_class.teacher}", anchor="center", wraplength=root.winfo_width()//2)
		else:
			root.rowconfigure(5, weight=0, minsize=0)
		if B_class is not None:
			if not class2Label.winfo_ismapped(): class2Label.grid(row=3, column=2, sticky="nsew")
			if not loc2label.winfo_ismapped(): loc2label.grid(row=4, column=2, sticky="nsew")
			if not vertSep.winfo_ismapped(): vertSep.grid(row=3, column=1, sticky="ns", padx=5, pady=5, rowspan=2)
			class1Label.grid_configure(columnspan=1)
			loc1Label.grid_configure(columnspan=1)
			class2Label.config(text=f"{B_class.name}", anchor="center", wraplength=root.winfo_width()//2)
			loc1Label.config(wraplength=root.winfo_width()//2)
			loc2label.config(text=f"{B_class.room}", wraplength=root.winfo_width()//2)
			class1Label.config(wraplength=root.winfo_width()//2)
			class2Label.config(wraplength=root.winfo_width()//2)
		else:
			if class2Label.winfo_ismapped(): class2Label.grid_forget()
			if loc2label.winfo_ismapped(): loc2label.grid_forget()
			if vertSep.winfo_ismapped(): vertSep.grid_forget()
			class1Label.grid_configure(columnspan=3)
			loc1Label.grid_configure(columnspan=3)
			class1Label.config(wraplength=root.winfo_width())
			loc1Label.config(wraplength=root.winfo_width())
	alerted:datetime = datetime.fromtimestamp(0)
	def sendAlert():
		nonlocal alerted
		if len(list(state.settings.alertTimes.keys())) == 0:
			return
		for time, i in state.settings.alertTimes.items():
			try:
				time = datetime.strptime(time, "%Y-%m-%d;%H:%M")
			except ValueError:
				time = datetime.strptime(time, "%w;%H:%M")
			if (
				alerted-timedelta(minutes=1) < (rn := state.getTime().replace(second=0, microsecond=0, year=1970, month=1, day=1)) and 
	   			time.replace(second=0, microsecond=0, year=1970, month=1, day=1) == rn
				):
				async def msg():
					messagebox.showinfo("Értesítés", f"{i.get("message", "Értesítés ideje elérkezett!")}")
				asyncio.create_task(msg())
				logger.info(f"Sent alert at '{time.strftime("%H:%M")}' with message: '{i.get("message", "Értesítés ideje elérkezett!")}'")
				alerted = state.getTime().replace(second=0, microsecond=0)
	prev_day:datetime = state.getTime().date()
	state.schedule = Schedule()
	while True:
		_start = perf_counter()
		delay = state.settings.delay
		if prev_day != state.schedule._date:
			prev_day = state.getTime().date()
			logger.debug("Day changed since last cycle")
			state.schedule = Schedule()
			if len(state.schedule.classes) == 0: await asyncio.sleep(60*30)
		now = state.getTime()
		now_time = now.time()
		sendAlert()
		for num, _class in enumerate(state.schedule.classes):
			tmp_class:Schedule.ClassData|None = None
			if isinstance(_class, list): # If 2 classes then split in 2
				tmp_class = _class[1]
				_class = _class[0]
			if tmp_class is None and _class.name is None and _class.room is None and _class.teacher is None:
				sendAlert()
				continue
			if ((_class.beginDatetime + timedelta(seconds=delay)).time() > now_time):
				tmp = datetime.combine(state.getTime(), _class.begin) - datetime.combine(state.getTime(), now_time) + timedelta(seconds=delay)
				mainLabel.config(text=f"Szünet végéig")
				timeLabel.config(text=f"{f"{tmp.seconds//3600:02}:" if tmp.seconds//3600 != 0 else ""}{(tmp.seconds//60)%60:02}:{tmp.seconds%60:02}")
				setClassLabels(_class, tmp_class)
				break
			elif ((_class.endDatetime + timedelta(seconds=delay)).time() > now_time): # if class ends after now
				tmp = datetime.combine(state.getTime(), _class.end) - datetime.combine(state.getTime().date(), now_time) + timedelta(seconds=delay)
				mainLabel.config(text=f"{num+1}. Óra végéig")
				timeLabel.config(text=f"{f"{tmp.seconds//3600:02}:" if tmp.seconds//3600 != 0 else ""}{(tmp.seconds//60)%60:02}:{tmp.seconds%60:02}")
				if tmp_class is not None: # If split class
					if (tmp.seconds > 60*10 or num == len(state.schedule.classes)-1): # More than 10 mins left, or last class
						setClassLabels(_class, tmp_class)
					else: # Less than 10 mins left
						if isinstance(next_class := state.schedule.classes[num+1], list): # If next class is split
							setClassLabels(next_class[0], next_class[1], True)
						else: # Next class is together
							setClassLabels(next_class, None, True)
				else: # If class is together
					if (tmp.seconds > 60*10 or num == len(state.schedule.classes)-1): # More than 10 minutes left or last class
						setClassLabels(_class, tmp_class)
					else: # Less than 10 minutes
						if isinstance(next_class := state.schedule.classes[num+1], list): # Next class is split
							setClassLabels(next_class[0], next_class[1], True)
						else: # Next class is together
							setClassLabels(next_class, None, True)
				break
		else: # No class ends after now (No If branch broke the loop)
			mainLabel.config(text="A napnak vége")
			[i.grid_forget() for i in [timeLabel,class1Label,class2Label,loc1Label,loc2label,auxLabel,teacher1Label,teacher2Label] if i.winfo_ismapped()]
			if separator.winfo_ismapped():
				separator.grid_forget()
			if vertSep.winfo_ismapped():
				vertSep.grid_forget()
			setDynamicSize()
			await asyncio.sleep(10)
			continue
		setDynamicSize()
		update_delay = await batterySaverEnabled(5, 1)
		if state.dummyDate is not None:
			state.dummyDate = state.dummyDate + timedelta(seconds=1)
		delay = min(max(0, update_delay - (perf_counter() - _start)), 10)
		await asyncio.sleep(delay)
def fontSize(size:int): return Font(size=size)
async def setClickThrough():
	logger.info("Setting click-through window")
	try:
		while True:
			hwnd = windll.user32.FindWindowW(None, state.root.title())
			styles = windll.user32.GetWindowLongW(hwnd, -20)
			styles |= 0x00000020  # WS_EX_LAYERED (Allows transparency)	
			styles |= 0x00000080  # WS_EX_TRANSPARENT (Click-through)
			windll.user32.SetWindowLongW(hwnd, -20, styles)
			if (windll.user32.GetWindowLongW(hwnd, -20)) & 0x00000080 == 0x00000080:
				break
			await asyncio.sleep(0.5)
	except Exception as e:
		logger.error(f"An error occured during transparency setting: {e}")
async def batterySaverEnabled(on_val, off_val):
	class SYSTEM_POWER_STATUS(Structure):
		_fields_ = [
			("ACLineStatus", c_byte),
			("BatteryFlag", c_byte),
			("BatteryLifePercent", c_byte),
			("SystemStatusFlag", c_byte)
		]
	status = SYSTEM_POWER_STATUS()
	if windll.kernel32.GetSystemPowerStatus(byref(status)) == 0:
		return off_val # Failed to get status, assume OFF
	return on_val if bool(status.SystemStatusFlag & 1) else off_val  # 1 means Battery Saver is ON
async def transparencyCheck(root:Tk):
	async def isCursorOverWindow(root:Tk):
		win_x = root.winfo_rootx()
		win_y = root.winfo_rooty()
		return (win_x <= root.winfo_pointerx() <= win_x + root.winfo_width() and 
				win_y <= root.winfo_pointery() <= win_y + root.winfo_height())
	while True:
		if not await isCursorOverWindow(root) and root.wm_attributes("-alpha") != 0.65: 
			root.wm_attributes("-alpha", state.settings.alpha["default"])
		elif await isCursorOverWindow(root) and root.wm_attributes("-alpha") != 0.10: 
			root.wm_attributes("-alpha", state.settings.alpha["onHover"])
		await asyncio.sleep(await batterySaverEnabled(1, 0.1))

if __name__ == "__main__": 
	from csengo import main
	main()