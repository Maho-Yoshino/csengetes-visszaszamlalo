if __name__ == "__main__":
	from sys import path as sp
	from os import path
	sp.append(path.abspath(path.join(path.dirname(__file__), '..')))
import logging, tkinter as tk, asyncio, modules.state as state
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
	special_day:bool = False
	class ClassData:
		begin:time
		end:time
		begin_datetime:datetime
		end_datetime:datetime
		classname:str = None 
		room:str = None 
		teacher:str = None
		def __init__(self, _class:str|None, index:int, parent:"Schedule"):
			tmp = state.settings.classlist.get(_class, [])
			if len(parent.classes) > 0:
				self.begin_datetime = (parent.classes[-1].end_datetime if not isinstance(parent.classes[-1], list) else parent.classes[-1][0].end_datetime) + timedelta(minutes=(state.settings.special_breaktimes[parent._date] if parent.special_day else state.settings.breaktimes)[index-1])
				self.begin = self.begin_datetime.time()
			else:
				temp = (state.settings.special_begintimes.get(parent._date) if parent.special_day else state.settings.classes_begin)
				self.begin_datetime = datetime.strptime(f"{parent._date.strftime("%Y.%m.%d")} {temp//100}:{temp%100}", "%Y.%m.%d %H:%M")
				self.begin = self.begin_datetime.time()
			self.end_datetime = (self.begin_datetime + timedelta(minutes=(state.settings.special_classtimes if parent.special_day else state.settings.classtimes)[index]))
			self.end = self.end_datetime.time()
			if tmp:
				self.classname = tmp[0]
				self.room = tmp[1]
				self.teacher = state.settings.teacherlist.get(_class, None)
	def __init__(self, other_date:datetime|None=None):
		if other_date is not None:
			self._date = other_date.date()
			weekday = self._date.weekday()
		else:
			self._date = (datetime.now() if state.dummy_date is None else state.dummy_date).date()
			weekday = self._date.weekday()
		self.special_day = any([datetime.strptime(day, "") == self._date for day in state.settings.special_days.keys()])
		if weekday in [5,6] and not self.special_day:
			return
		if self.special_day:
			tmp = state.settings.special_days.get(self._date)
			if tmp is None:
				tmp = state.settings.default_schedule[weekday]
		else: 
			tmp = state.settings.default_schedule[weekday]
		for ind, classinfo in enumerate(tmp):
			if classinfo is not None and isinstance(classinfo, list):
				self.classes.append([self.ClassData(_, ind, self) for _ in classinfo])
			else:
				self.classes.append(self.ClassData(classinfo, ind, self))
		logger.debug("Initialized Schedule class")
async def get_rn(): return datetime.now() if state.dummy_date is None else state.dummy_date
async def update_cycle(mainlabel:tk.Label, timelabel:tk.Label, class1label:tk.Label, class2label:tk.Label, loc1label:tk.Label, loc2label:tk.Label, root:Tk, vert_separator:Separator, separator:Separator, aux_label:tk.Label):
	def set_dynamic_size():
		logger.debug(f"Setting dynamic size ({root.winfo_screenwidth()-root.winfo_width()})")
		root.geometry(f"+{root.winfo_screenwidth()-root.winfo_width()}+0")
		root.update()
	prev_day:datetime = (await get_rn()).date()
	state.schedule = Schedule()
	global dummy_date
	while True:
		_start = perf_counter()
		delay = state.settings.delay
		if prev_day != state.schedule._date:
			prev_day = (await get_rn()).date()
			logger.debug("Day changed since last cycle")
			state.schedule = Schedule()
			if len(state.schedule.classes) == 0: await asyncio.sleep(60*30)
		now = (await get_rn())
		now_time = now.time()
		if all([not i.winfo_ismapped() for i in [class1label,loc1label,timelabel]]):
			class1label.grid(row=3, column=0, sticky="nsew")
			loc1label.grid(row=4, column=0, sticky="nsew")
			timelabel.grid(row=1, column=0, sticky="nsew", columnspan=3)
		for num, _class in enumerate(state.schedule.classes):
			tmp_class:Schedule.ClassData|None = None
			if isinstance(_class, list):
				tmp_class = _class[1]
				_class = _class[0]
			if ((_class.begin_datetime + timedelta(seconds=delay)).time() > now_time):
				tmp = datetime.combine((await get_rn()), _class.begin) - datetime.combine((await get_rn()), now_time) + timedelta(seconds=delay)
				mainlabel.config(text=f"Szünet végéig")
				timelabel.config(text=f"{f"{tmp.seconds//3600:02}:" if tmp.seconds//3600 != 0 else ""}{(tmp.seconds//60)%60:02}:{tmp.seconds%60:02}")
				class1label.config(text=f"{_class.classname}", anchor="center")
				if aux_label.winfo_ismapped():
					aux_label.grid_forget()
					root.rowconfigure(4, weight=0, minsize=0)
				if tmp_class is not None:
					if not class2label.winfo_ismapped(): class2label.grid(row=3, column=2, sticky="nsew")
					if not loc2label.winfo_ismapped(): loc2label.grid(row=4, column=2, sticky="nsew")
					if not vert_separator.winfo_ismapped(): vert_separator.grid(row=3, column=1, sticky="ns", padx=5, pady=5, rowspan=2)
					class1label.grid_configure(columnspan=1)
					loc1label.grid_configure(columnspan=1)
					class2label.config(text=f"{tmp_class.classname}", anchor="center", wraplength=class2label.winfo_width())
					loc1label.config(text=f"{_class.room}", wraplength=loc1label.winfo_width())
					loc2label.config(text=f"{tmp_class.room}", wraplength=loc2label.winfo_width())
				else:
					if class2label.winfo_ismapped(): class2label.grid_forget()
					if loc2label.winfo_ismapped(): loc2label.grid_forget()
					if vert_separator.winfo_ismapped(): vert_separator.grid_forget()
					class1label.grid_configure(columnspan=3)
					loc1label.grid_configure(columnspan=3)
					loc1label.config(text=_class.room, wraplength=loc1label.winfo_width())
				if not separator.winfo_ismapped(): separator.grid(row=2, column=0, sticky="ew", padx=5, pady=5, columnspan=3, ipadx=100)
				break
			elif ((_class.end_datetime + timedelta(seconds=delay)).time() > now_time):
				tmp = datetime.combine((await get_rn()), _class.end) - datetime.combine((await get_rn()).date(), now_time) + timedelta(seconds=delay)
				mainlabel.config(text=f"{num+1}. Óra végéig")
				timelabel.config(text=f"{f"{tmp.seconds//3600:02}:" if tmp.seconds//3600 != 0 else ""}{(tmp.seconds//60)%60:02}:{tmp.seconds%60:02}")
				class1label.config(text=f"{_class.classname}", anchor="center")
				if tmp_class is not None:
					if not class2label.winfo_ismapped(): class2label.grid(row=3, column=2, sticky="nsew")
					if not loc2label.winfo_ismapped(): loc2label.grid(row=4, column=2, sticky="nsew")
					if (tmp.seconds > 60*10 or num == len(state.schedule.classes)-1):
						if aux_label.winfo_ismapped(): 
							aux_label.grid_forget()
							root.rowconfigure(4, weight=0, minsize=0)
						if not vert_separator.winfo_ismapped(): vert_separator.grid(row=3, column=1, sticky="ns", padx=5, pady=5, rowspan=2)
						class1label.grid_configure(columnspan=1)
						loc1label.grid_configure(columnspan=1)
						class2label.config(text=f"{tmp_class.classname}", anchor="center")
						loc1label.config(text=f"{_class.room}")
						loc2label.config(text=f"{tmp_class.room}")
					else:
						if not aux_label.winfo_ismapped():
							aux_label.grid(row=5, column=0, sticky="nsew", columnspan=3)
							aux_label.config(text="Következő óra")
							root.rowconfigure(4, weight=1)
						if isinstance(next_class := state.schedule.classes[num+1], list) and len(next_class) > 1:
							if not vert_separator.winfo_ismapped(): vert_separator.grid(row=3, column=1, sticky="ns", padx=5, pady=5, rowspan=2)
							class1label.config(text=f"{next_class[0].classname}", anchor="center")
							class2label.config(text=f"{next_class[1].classname}", anchor="center")
							loc1label.config(text=f"{next_class[0].room}")
							loc2label.config(text=f"{next_class[1].room}")
						else:
							if class2label.winfo_ismapped(): class2label.grid_forget()
							if loc2label.winfo_ismapped(): loc2label.grid_forget()
							class1label.grid_configure(columnspan=3)
							loc1label.grid_configure(columnspan=3)
							class1label.config(text=f"{next_class.classname}", anchor="center")
							loc1label.config(text=f"{next_class.room}")
							if vert_separator.winfo_ismapped(): vert_separator.grid_forget()
					if not separator.winfo_ismapped(): separator.grid(row=2, column=0, sticky="ew", padx=5, pady=5, columnspan=3, ipadx=100)
				else:
					if (tmp.seconds > 60*10 or num == len(state.schedule.classes)-1):
						if class2label.winfo_ismapped(): class2label.grid_forget()
						if loc2label.winfo_ismapped(): loc2label.grid_forget()
						class1label.grid_configure(columnspan=3)
						loc1label.grid_configure(columnspan=3)
						class1label.config(text=f"{_class.classname}", anchor="center", wraplength=len(_class.classname))
						loc1label.config(text=f"{_class.room}")
						if aux_label.winfo_ismapped():
							aux_label.grid_forget()
							root.rowconfigure(4, weight=0, minsize=0)
					else:
						if isinstance(next_class := state.schedule.classes[num+1], list) and len(next_class) > 1:
							if not class2label.winfo_ismapped(): class2label.grid(row=3, column=2, sticky="nsew")
							if not loc2label.winfo_ismapped(): loc2label.grid(row=4, column=2, sticky="nsew")
							class1label.config(text=f"{next_class[0].classname}", anchor="center")
							class2label.config(text=f"{next_class[1].classname}", anchor="center")
							loc1label.config(text=f"{next_class[0].room}")
							loc2label.config(text=f"{next_class[1].room}")
							if not vert_separator.winfo_ismapped(): vert_separator.grid(row=3, column=1, sticky="ns", padx=5, pady=5, rowspan=2)
						else:
							if class2label.winfo_ismapped(): class2label.grid_forget()
							if loc2label.winfo_ismapped(): loc2label.grid_forget()
							class1label.grid_configure(columnspan=3)
							class1label.config(text=f"{next_class.classname}", anchor="center")
							loc1label.config(text=f"{next_class.room}")
							loc1label.grid_configure(columnspan=3)
							if vert_separator.winfo_ismapped(): vert_separator.grid_forget()
						if not aux_label.winfo_ismapped():
							aux_label.grid(row=5, column=0, sticky="nsew", columnspan=3)
							aux_label.config(text="Következő óra")
							root.rowconfigure(4, weight=1)
				if not separator.winfo_ismapped(): separator.grid(row=2, column=0, sticky="ew", padx=5, pady=5, columnspan=3, ipadx=100)
				break
		else:
			mainlabel.config(text="A napnak vége")
			[i.grid_forget() for i in [timelabel,class1label,class2label,loc1label,loc2label,separator,vert_separator,aux_label] if i.winfo_ismapped()]
			set_dynamic_size()
			await asyncio.sleep(60)
			continue
		class1label.config(wraplength=class1label.winfo_width())
		class2label.config(wraplength=class2label.winfo_width())
		set_dynamic_size()
		update_delay = await batterySaverEnabled(5, 1)
		if dummy_date is not None:
			dummy_date = dummy_date + timedelta(seconds=1)
		delay = min(max(0, update_delay - (perf_counter() - _start)), 10)
		await asyncio.sleep(delay)
def font_size(size:int): return Font(size=size)
async def set_click_through():
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
async def transparency_check(root:Tk):
	async def is_cursor_over_window(root:Tk):
		win_x = root.winfo_rootx()
		win_y = root.winfo_rooty()
		return (win_x <= root.winfo_pointerx() <= win_x + root.winfo_width() and 
				win_y <= root.winfo_pointery() <= win_y + root.winfo_height())
	while True:
		if not await is_cursor_over_window(root) and root.wm_attributes("-alpha") != 0.65: 
			root.wm_attributes("-alpha", state.settings.alpha["default"])
		elif await is_cursor_over_window(root) and root.wm_attributes("-alpha") != 0.10: 
			root.wm_attributes("-alpha", state.settings.alpha["onHover"])
		await asyncio.sleep(await batterySaverEnabled(1, 0.1))

if __name__ == "__main__": 
	from csengo import main
	main()