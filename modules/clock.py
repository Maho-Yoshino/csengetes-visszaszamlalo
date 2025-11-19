if __name__ == "__main__": 
	from pathlib import Path
	from sys import path
	ROOT = Path(__file__).resolve().parent.parent
	if str(ROOT) not in path:
		path.insert(0, str(ROOT))
import logging, tkinter as tk, asyncio
import modules.state as state
from datetime import datetime, time, date, timedelta
from tkinter import Tk
from tkinter.font import Font
from tkinter.ttk import Separator
from ctypes import windll, c_byte, byref, Structure
from time import perf_counter
from sys import platform
logger = logging.getLogger(__name__)

class Schedule:
	classes:list["ClassData", list["ClassData"]] = []
	_date:date = None
	specialDay:bool = False
	class ClassData:
		begin:time
		end:time
		begin_datetime:datetime
		end_datetime:datetime
		name:str|None = None 
		room:str|None = None 
		teacher:str|None = None
		def __init__(self, classID:str|None, times:str):
			classData:dict[str, str] = state.settings.classlist.get(classID, {})
			times:list[str] = times.split("-", 1)
			self.begin_datetime = datetime.strptime(times[0], "%H:%M")
			self.end_datetime = datetime.strptime(times[1], "%H:%M")
			self.begin = self.begin_datetime.time()
			self.end = self.end_datetime.time()
			self.name = classData.get("name", None)
			self.room = classData.get("room", None)
			self.teacher = classData.get("teacher", None)
	def __init__(self, other_date:datetime|None=None):
		if other_date is not None:
			self._date = other_date.date()
		else:
			self._date = (datetime.now() if state.dummyDate is None else state.dummyDate).date()
		weekday = self._date.weekday()
		weeknum = self._date.isocalendar().week
		self.specialDay = any([datetime.strptime(day, "%Y-%m-%d").date() == self._date for day in state.settings.specialDays.keys()])
		if weekday not in range(len(state.settings.defaultSchedule)-1) and not self.specialDay:
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
		return datetime.strptime(times[0], "%H:%M"), datetime.strptime(times[1], "%H:%M")
async def getTime(): return datetime.now() if state.dummyDate is None else state.dummyDate
async def updateCycle(mainlabel:tk.Label, timelabel:tk.Label, class1label:tk.Label, class2label:tk.Label, loc1label:tk.Label, loc2label:tk.Label, root:Tk, vert_separator:Separator, separator:Separator, aux_label:tk.Label):
	def setDynamicSize():
		root.geometry(f"+{root.winfo_screenwidth()-root.winfo_width()}+0")
		root.update()
		logger.debug(f"window size: {root.winfo_width()}x{root.winfo_height()}+{root.winfo_screenwidth()-root.winfo_width()}+0")
	def setClassLabels(A_class:Schedule.ClassData, B_class:Schedule.ClassData|None = None):
		if not all([i.winfo_ismapped() for i in [class1label,loc1label,timelabel]]):
			class1label.grid(row=3, column=0, sticky="nsew")
			loc1label.grid(row=4, column=0, sticky="nsew")
			timelabel.grid(row=1, column=0, sticky="nsew", columnspan=3)
		class1label.config(text=f"{A_class.name}", anchor="center")
		loc1label.config(text=f"{A_class.room}")
		if not separator.winfo_ismapped(): separator.grid(row=2, column=0, sticky="ew", padx=5, pady=5, columnspan=3, ipadx=100)
		if B_class is not None:
			if not class2label.winfo_ismapped(): class2label.grid(row=3, column=2, sticky="nsew")
			if not loc2label.winfo_ismapped(): loc2label.grid(row=4, column=2, sticky="nsew")
			if not vert_separator.winfo_ismapped(): vert_separator.grid(row=3, column=1, sticky="ns", padx=5, pady=5, rowspan=2)
			class1label.grid_configure(columnspan=1)
			loc1label.grid_configure(columnspan=1)
			class2label.config(text=f"{B_class.name}", anchor="center", wraplength=root.winfo_width()//2)
			loc1label.config(wraplength=root.winfo_width()//2)
			loc2label.config(text=f"{B_class.room}", wraplength=root.winfo_width()//2)
			class1label.config(wraplength=root.winfo_width()//2)
			class2label.config(wraplength=root.winfo_width()//2)
		else:
			if class2label.winfo_ismapped(): class2label.grid_forget()
			if loc2label.winfo_ismapped(): loc2label.grid_forget()
			if vert_separator.winfo_ismapped(): vert_separator.grid_forget()
			class1label.grid_configure(columnspan=3)
			loc1label.grid_configure(columnspan=3)
			class1label.config(wraplength=root.winfo_width())
			loc1label.config(wraplength=root.winfo_width())
	prev_day:datetime = (await getTime()).date()
	state.schedule = Schedule()
	while True:
		_start = perf_counter()
		delay = state.settings.delay
		if prev_day != state.schedule._date:
			prev_day = (await getTime()).date()
			logger.debug("Day changed since last cycle")
			state.schedule = Schedule()
			if len(state.schedule.classes) == 0: await asyncio.sleep(60*30)
		now = (await getTime())
		now_time = now.time()
		for num, _class in enumerate(state.schedule.classes):
			tmp_class:Schedule.ClassData|None = None
			if isinstance(_class, list): # If 2 classes then split in 2
				tmp_class = _class[1]
				_class = _class[0]
			if tmp_class is None and _class.name is None and _class.room is None and _class.teacher is None:
				continue
			if ((_class.begin_datetime + timedelta(seconds=delay)).time() > now_time):
				tmp = datetime.combine((await getTime()), _class.begin) - datetime.combine((await getTime()), now_time) + timedelta(seconds=delay)
				mainlabel.config(text=f"Szünet végéig")
				timelabel.config(text=f"{f"{tmp.seconds//3600:02}:" if tmp.seconds//3600 != 0 else ""}{(tmp.seconds//60)%60:02}:{tmp.seconds%60:02}")
				if aux_label.winfo_ismapped():
					aux_label.grid_forget()
					root.rowconfigure(4, weight=0, minsize=0)
				setClassLabels(_class, tmp_class)
				break
			elif ((_class.end_datetime + timedelta(seconds=delay)).time() > now_time): # if class ends after now
				tmp = datetime.combine((await getTime()), _class.end) - datetime.combine((await getTime()).date(), now_time) + timedelta(seconds=delay)
				mainlabel.config(text=f"{num+1}. Óra végéig")
				timelabel.config(text=f"{f"{tmp.seconds//3600:02}:" if tmp.seconds//3600 != 0 else ""}{(tmp.seconds//60)%60:02}:{tmp.seconds%60:02}")
				if tmp_class is not None: # If split class
					if (tmp.seconds > 60*10 or num == len(state.schedule.classes)-1): # More than 10 mins left, or last class
						if aux_label.winfo_ismapped(): 
							aux_label.grid_forget()
							root.rowconfigure(4, weight=0, minsize=0)
						setClassLabels(_class, tmp_class)
					else: # Less than 10 mins left
						if not aux_label.winfo_ismapped():
							aux_label.grid(row=5, column=0, sticky="nsew", columnspan=3)
							aux_label.config(text="Következő óra")
							root.rowconfigure(4, weight=1)
						if isinstance(next_class := state.schedule.classes[num+1], list): # If next class is split
							setClassLabels(next_class[0], next_class[1])
						else: # Next class is together
							setClassLabels(next_class, None)
				else: # If class is together
					if (tmp.seconds > 60*10 or num == len(state.schedule.classes)-1): # More than 10 minutes left or last class
						if aux_label.winfo_ismapped():
							aux_label.grid_forget()
							root.rowconfigure(4, weight=0, minsize=0)
						setClassLabels(_class, tmp_class)
					else: # Less than 10 minutes
						if isinstance(next_class := state.schedule.classes[num+1], list): # Next class is split
							setClassLabels(next_class[0], next_class[1])
						else: # Next class is together
							setClassLabels(next_class, None)
						if not aux_label.winfo_ismapped():
							aux_label.grid(row=5, column=0, sticky="nsew", columnspan=3)
							aux_label.config(text="Következő óra")
							root.rowconfigure(4, weight=1)
				break
		else: # No class ends after now (No If branch broke the loop)
			mainlabel.config(text="A napnak vége")
			[i.grid_forget() for i in [timelabel,class1label,class2label,loc1label,loc2label,aux_label] if i.winfo_ismapped()]
			if separator.winfo_ismapped():
				separator.grid_forget()
			if vert_separator.winfo_ismapped():
				vert_separator.grid_forget()
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
	if platform != "win32":
		return logger.warning(f"User is not on windows. ({platform} instead)")
	logger.info("Setting click-through window")
	try:
		while True:
			hwnd = windll.user32.FindWindowW(None, state.windowHandle)  # Get correct window handle
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
	main(datetime(year=2025, month=11, day=12, hour=12, minute=21, second=30))