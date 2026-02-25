import modules.state as state
from datetime import datetime, timedelta
from asyncio import sleep as asleep, CancelledError
from time import perf_counter
from logging import getLogger
from tkinter import Label, Frame, messagebox, TclError, Tk
from tksvg import SvgImage
from ctypes import windll, c_byte, byref, Structure
from modules.schedule import Schedule, _Class

init_data:dict[str, int|str] = {}
class classFrame(Frame):
	_data:dict[str, int|str]
	def __init__(self, master, *, _class:_Class=None):
		self._data = {
			"wraplength": 0,
			"bg":init_data["bg"],
			"fg":init_data["fg"],
			"class":_class
		}
		self._logger = getLogger(__name__)
		super().__init__(master, bg=init_data["bg"])
		self.nameLabel = Label(self, cnf=init_data, padx=5, anchor="center", justify="center")
		self.roomLabel = Label(self, cnf=init_data, padx=5, anchor="center", justify="center")
		self.teacherLabel = Label(self, cnf=init_data, padx=5, anchor="center", justify="center")
		self._class = _class
	# region Class
	@property
	def _class(self) -> _Class|None:
		return self._data["class"]
	@_class.setter
	def _class(self, value:_Class|None):
		self._data["class"] = value
		if value is not None:
			self.nameLabel.config(text=value.name)
			self.nameLabel.grid(row=0)
			self.roomLabel.config(text=value.room)
			self.roomLabel.grid(row=1)
			self.teacherLabel.config(text=value.teacher)
			if state.settings.config.showTeacher:
				self.teacherLabel.grid(row=2)
	# endregion
	# region Background
	@property
	def bg(self) -> str:
		return self._data["bg"]
	@bg.setter
	def bg(self, value:str):
		self._data["bg"] = value
		self.nameLabel.config(bg=value)
		self.roomLabel.config(bg=value)
		self.teacherLabel.config(bg=value)
		self.config(bg=value)
	# endregion
	# region Foreground
	@property
	def fg(self) -> str:
		return self._data["fg"]
	@fg.setter
	def fg(self, value:str):
		self._data["fg"] = value
		self.nameLabel.config(fg=value)
		self.roomLabel.config(fg=value)
		self.teacherLabel.config(fg=value)
	# endregion
	# region Wraplength
	@property
	def wraplength(self) -> int:
		return self._data["wraplength"]
	@wraplength.setter
	def wraplength(self, value:int):
		self._data["wraplength"] = value
		self.nameLabel.config(wraplength=value)
		self.roomLabel.config(wraplength=value)
		self.teacherLabel.config(wraplength=value)
	# endregion
class Clock(Tk):
	def __init__(self):
		global init_data
		init_data = {
			"text":"",
			"bg":f"#{state.settings.config.background:06x}",
			"fg":f"#{state.settings.config.foreground:06x}"
		}
		state.schedule = Schedule()
		# region Misc config
		super().__init__()
		state.root = self
		self.logger = getLogger(__name__)
		# endregion
		# region Main config
		self.iconbitmap(default="assets/icon.ico")
		self.configure(bg=f"#{state.settings.config.background:06x}")
		self.attributes("-topmost", True)
		self.title(state.windowHandle)
		self.resizable(False, False)
		self.overrideredirect(True)
		self.wm_attributes("-alpha", state.settings.config.alpha["default"])
		self.pxwidth = self.winfo_screenwidth()//4
		self.pxheight = self.winfo_screenheight()//8
		self.geometry(f"{self.pxwidth}x{self.pxheight}+{self.winfo_screenwidth()-self.pxwidth}+{self.winfo_screenheight()-self.pxheight}")
		self.grid(baseWidth=1, widthInc=self.pxwidth)
		self.config(padx=15, pady=15, border=1, borderwidth=1)
		# endregion
		# region Main text and time config
		self.columnconfigure(0, weight=1)

		self.mainLabel = Label(self, init_data, font=state.fontSize(20))
		self.mainLabel.grid(row=0, column=0, sticky="nsew")
		self.mainLabel.grid_rowconfigure(0, weight=1)

		self.timeFrame = Frame(self, bg=init_data["bg"]) # Frame so the exam and homework icons can happen
		self.timeFrame.grid_rowconfigure(0, weight=1)
		self.timeFrame.grid_rowconfigure(1, weight=1)
		self.timeLabel = Label(self.timeFrame, init_data, font=state.fontSize(30), anchor="center")
		self.timeLabel.grid(column=1)
		self.timeLabel.grid_columnconfigure(1, weight=1)
		self.homeworkIcon = self.loadSvg("homework")
		self.homeworkLabel = Label(self.timeFrame, image=self.homeworkIcon, bg=init_data["bg"], fg=init_data["fg"])
		self.homeworkLabel.image = self.homeworkIcon
		self.examIcon = self.loadSvg("exam")
		self.examLabel = Label(self.timeFrame, image=self.examIcon, bg=init_data["bg"], fg=init_data["fg"])
		self.examLabel.image = self.examIcon
		# endregion
		# region Classes setup
		self.classesContainer = Frame(self, bg=init_data["bg"])
		self.classFrames:list[classFrame] = []
		maxClassesAtOnce = max(*[max(*[len(j) for j in i.values()]) for i in state.settings.schedule.getUnifiedSchedule()])
		for _ in range(maxClassesAtOnce):
			self.classFrames.append(classFrame(self.classesContainer))
		# endregion
		# region Misc setup
		self.auxLabel = Label(self, init_data, font=state.fontSize(10), padx=5, anchor="center", justify="center", text=state.settings.localization.nextClass)
		self.separator = Frame(self, bg=init_data["fg"], height=1, width=self.winfo_width())
		self.separator.grid_rowconfigure(2, weight=1)
		self.vertSeparator = Frame(self, bg=init_data["fg"], width=1, height=self.winfo_height())
		del init_data
		self.columnconfigure(0, weight=1)
		self.columnconfigure(1, weight=0)
		self.columnconfigure(2, weight=1)
		self.protocol("WM_DELETE_WINDOW", self.withdraw)
		# endregion
		# region Asyncio loops
		self.mainloopTask = state.runtime.create_task(self.mainloop())
		self.mainloopTask.add_done_callback(state.exc_handler)
		self.setClickThroughTask = state.runtime.create_task(self.setClickThrough())
		self.setClickThroughTask.add_done_callback(state.exc_handler)
		self.transparencyTask = state.runtime.create_task(self.transparencyCheck())
		self.transparencyTask.add_done_callback(state.exc_handler)
		# endregion
		self.logger.info("Clock setup complete")
	def changeColors(self, *, fg:str=None, bg:str=None):
		for _class in self.classFrames:
			_class.updateColors(fg, bg)
		if bg:
			self.config(bg=bg)
	def loadSvg(self, filename:str) -> SvgImage:
		try:
			with open(f"assets/{filename}.svg", "r") as file:
				svg_text = file.read().replace("<svg ", f"<svg fill='#{state.settings.config.foreground:06x}' ")
		except FileNotFoundError:
			self.logger.exception(f"File \"assets/{filename}.png\" could not be found")
			raise
		return SvgImage(filename, master=self.timeFrame, data=svg_text, scaletoheight=25)
	lastWidth:int = 0
	def setDynamicSize(self):
		if (self.lastWidth != self.winfo_width()):
			self.logger.debug(f"window size: {self.winfo_width()}x{self.winfo_height()}+{self.winfo_screenwidth()-self.winfo_width()}+0")
			self.lastWidth = self.winfo_width()
		self.geometry(f"+{self.winfo_screenwidth()-self.winfo_width()}+0")
	async def setClickThrough(self):
		self.logger.debug("Setting click-through window")
		while not self.winfo_viewable():
			await asleep(0.05)
		self.logger.debug("Window found")
		try:
			while True:
				hwnd = windll.user32.FindWindowW(None, state.root.title())
				styles = windll.user32.GetWindowLongW(hwnd, -20)
				styles |= 0x00000020  # WS_EX_LAYERED (Allows transparency)	
				styles |= 0x00000080  # WS_EX_TRANSPARENT (Click-through)
				windll.user32.SetWindowLongW(hwnd, -20, styles)
				if (windll.user32.GetWindowLongW(hwnd, -20)) & 0x00000080 == 0x00000080:
					self.logger.debug("Click-through successfully set")
					break
				await asleep(0.5)
		except CancelledError: pass
		except Exception:
			self.logger.exception(f"An error occured while setting transparency setting")
	def batterySaverEnabled(self, on_val, off_val):
		try:
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
		except (ImportError, CancelledError):
			return
		except Exception:
			self.logger.exception("An error occurred while checking battery saver status.") 
	async def transparencyCheck(self):
		root = state.root
		async def isCursorOverWindow():
			win_x = root.winfo_rootx()
			win_y = root.winfo_rooty()
			return (win_x <= root.winfo_pointerx() <= win_x + root.winfo_width() and 
					win_y <= root.winfo_pointery() <= win_y + root.winfo_height())
		while True:
			try:
				if not await isCursorOverWindow() and root.wm_attributes("-alpha") != state.settings.config.alpha["default"]: 
					root.wm_attributes("-alpha", state.settings.config.alpha["default"])
				elif await isCursorOverWindow() and root.wm_attributes("-alpha") != state.settings.config.alpha["onHover"]: 
					root.wm_attributes("-alpha", state.settings.config.alpha["onHover"])
				await asleep(self.batterySaverEnabled(1, 0.1))
			except (CancelledError, TclError): pass
			except Exception:
				self.logger.exception("An error happened during transparency check")
	def setClassLabels(self, *classes:_Class, aux:bool = False):
		self.mainLabel.grid(row=0, column=0)
		self.timeFrame.grid(row=1, column=0)
		self.separator.grid(row=2, column=0)

		self.classesContainer.grid(row=3, column=0)
		for i in range(len(classes)):
			obj = self.classFrames[i]
			if state.settings.schedule.group == -1 or state.settings.schedule.group == i:
				obj.grid(row=0, column=i)
			else:
				obj.grid_forget()
			if state.settings.config.showTeacher:
				obj.teacherLabel.grid(row=2)
				obj.rowconfigure(2, weight=1, minsize=20)
			else:
				obj.teacherLabel.grid_forget()
			obj._class = classes[i]

		if state.settings.events.current_exam():
			self.homeworkLabel.grid_forget()
			self.examLabel.grid(row=1, column=3)
		elif state.settings.events.current_homework():
			self.examLabel.grid_forget()
			self.homeworkLabel.grid(row=1, column=3)
		else:
			self.examLabel.grid_forget()
			self.homeworkLabel.grid_forget()

		if not aux:
			self.auxLabel.grid_forget()
			self.rowconfigure(6, weight=0, minsize=0)
		else:
			self.auxLabel.grid(row=6, column=0, sticky="nsew", columnspan=3)
			self.rowconfigure(6, weight=1)
	alerted:datetime = datetime.fromtimestamp(0)
	def sendAlert(self):
		async def msg(alert:dict[str, str]):
			loc = state.settings.localization
			messagebox.showinfo(loc.alert.title, f"{alert.get("message", loc.alert.defaultText)}")
		if len(state.settings.events.alerts) == 0:
			return
		for alert in state.settings.events.alerts:
			date = None
			if (tmp := alert.get("date", None)) is not None:
				date = datetime.strptime(tmp, "%Y-%m-%d")
			time = datetime.combine(state.getTime().date(), datetime.strptime(alert["time"], "%H:%M").time())
			if (
				alerted < (rn := state.getTime().replace(second=0, microsecond=0)) and 
	   			time.replace(second=0, microsecond=0) == rn and 
				(
					(date is not None and date.date() == rn.date()) or 
					date is None
				)
			):
				state.runtime.create_task(msg(alert))
				self.logger.debug(f"Sent alert")
				alerted = state.getTime().replace(second=0, microsecond=0)
	async def mainloop(self):
		prev_day:datetime = state.getTime().date()
		while True:
			_start = perf_counter()
			delay = state.settings.schedule.delay
			if prev_day != state.schedule._date:
				prev_day = state.getTime().date()
				self.logger.debug("Day changed since last loop")
				state.schedule = Schedule()
				if len(state.schedule.classes) == 0: await asleep(60*30) # 30 min delay
				continue
			now = state.getTime()
			now_time = now.time()
			self.sendAlert()
			loc = state.settings.localization
			for num, _class in enumerate(state.schedule.classes):
				_class:list[_Class]|_Class
				tmp_class:_Class|None = None
				if isinstance(_class, list): # If 2 classes then split in 2
					tmp_class:_Class = _class[1]
					_class:_Class = _class[0]
				if tmp_class is None and _class.name is None and _class.room is None and _class.teacher is None:
					continue
				if ((_class.beginDatetime + timedelta(seconds=delay)).time() > now_time): # Break time
					tmp = datetime.combine(now, _class.begin) - now + timedelta(seconds=delay)
					self.mainLabel.config(text=loc.format(loc.mainlabel.onBreak, num=f"{num+1}{loc.classNumbering.getSuffix(num+1)}"))
					self.timeLabel.config(text=f"{f"{tmp.seconds//3600:02}:" if tmp.seconds//3600 != 0 else ""}{(tmp.seconds//60)%60:02}:{tmp.seconds%60:02}")
					self.old_setClassLabels(_class, tmp_class)
					break
				elif ((_class.endDatetime + timedelta(seconds=delay)).time() > now_time): # In class
					tmp = datetime.combine(now, _class.end) - now + timedelta(seconds=delay)
					self.mainLabel.config(text=loc.format(loc.mainlabel.inClass, num=f"{num+1}{loc.classNumbering.getSuffix(num+1)}"))
					self.timeLabel.config(text=f"{f"{tmp.seconds//3600:02}:" if tmp.seconds//3600 != 0 else ""}{(tmp.seconds//60)%60:02}:{tmp.seconds%60:02}")
					if (
						tmp.seconds > 60*10 or # More than 10 minutes left
						num == len(state.schedule.classes)-1 # Last class of the day
					):
						state.currentClassIndex = num + 1
						self.old_setClassLabels(_class, tmp_class)
					else: # Less than 10 mins left
						state.currentClassIndex = num + 2
						next_classes = state.schedule.classes[num+1]
						self.old_setClassLabels(next_classes[0], next_classes[1], True)
					break
			else: # No class ends after now (No If branch broke the loop)
				self.mainLabel.config(text=loc.mainlabel.dayOver)
				state.currentClassIndex = -1
				for frame in self.classFrames: 
					if frame.winfo_ismapped(): frame.grid_forget()
				if self.auxLabel.winfo_ismapped():
					self.auxLabel.grid_forget()
				if self.separator.winfo_ismapped():
					self.separator.grid_forget()
				if self.vertSeparator.winfo_ismapped():
					self.vertSeparator.grid_forget()
				if self.timeFrame.winfo_ismapped():
					self.timeFrame.grid_forget()
				self.setDynamicSize()
				await asleep(10)
				continue
			self.setDynamicSize()
			update_delay = self.batterySaverEnabled(5, 1)
			if state.dummyDate is not None:
				state.dummyDate = state.dummyDate + timedelta(seconds=1)
			delay = min(max(0.01, update_delay - (perf_counter() - _start)), 10)
			await asleep(delay)
