import modules.state as state
from datetime import datetime, timedelta
from asyncio import sleep as asleep
from time import perf_counter
from logging import getLogger
from tkinter import Label, Frame, messagebox
from tksvg import SvgImage
from ctypes import windll, c_byte, byref, Structure
from modules.schedule import Schedule, _Class

class Clock:
	def __init__(self):
		state.schedule = Schedule()
		self.logger = getLogger(__name__)
		self.root = state.root
		self.root.iconbitmap(default="assets/icon.ico")
		self.root.configure(bg=f"#{state.settings.config.background:06x}", )
		self.root.attributes("-topmost", True)
		self.root.title(state.windowHandle)
		self.root.resizable(False, False)
		self.root.overrideredirect(True)
		self.root.wm_attributes("-alpha", state.settings.config.alpha["default"])
		self.root.grid(3, 5, self.root.winfo_screenwidth()//4, self.root.winfo_screenheight()//8)
		self.root.config(padx=15, pady=15, border=1, borderwidth=1)
		init_data = {
			"text":"",
			"bg":f"#{state.settings.config.background:06x}",
			"fg":f"#{state.settings.config.foreground:06x}"
		}
		self.mainLabel = Label(self.root, init_data, font=state.fontSize(20))
		self.mainLabel.grid(row=0, column=0, sticky="nsew", columnspan=3)
		self.mainLabel.grid_rowconfigure(0, weight=1)
		self.timeFrame = Frame(self.root, bg=init_data["bg"])
		self.timeFrame.grid(column=0, row=1, columnspan=4)
		self.timeFrame.grid_rowconfigure(0, weight=0)
		self.timeFrame.grid_rowconfigure(1, weight=1)
		self.timeLabel = Label(self.timeFrame, init_data, font=state.fontSize(30), anchor="center")
		self.timeLabel.grid(column=1)
		self.timeLabel.grid_columnconfigure(1, weight=1)
		self.separator = Frame(self.root, bg=init_data["fg"], height=1, width=self.root.winfo_width())
		self.separator.grid_rowconfigure(2, weight=1)
		self.class1Label = Label(self.root, init_data, font=state.fontSize(10), padx=5, anchor="center", justify="center", wraplength=128)
		self.class1Label.grid_rowconfigure(3, weight=1)
		self.class2Label = Label(self.root, init_data, font=state.fontSize(10), padx=5, anchor="center", justify="center")
		self.loc2Label = Label(self.root, init_data, font=state.fontSize(10), padx=5, anchor="center", justify="center")
		self.loc1Label = Label(self.root, init_data, font=state.fontSize(10), padx=5, anchor="center", justify="center")
		self.teacher1Label = Label(self.root, init_data, font=state.fontSize(10), padx=5, anchor="center", justify="center")
		self.teacher2Label = Label(self.root, init_data, font=state.fontSize(10), padx=5, anchor="center", justify="center")
		self.auxLabel = Label(self.root, init_data, font=state.fontSize(10), padx=5, anchor="center", justify="center")
		self.vertSeparator = Frame(self.root, bg=init_data["fg"], width=1, height=self.root.winfo_height())
		del init_data
		self.root.columnconfigure(0, weight=1)
		self.root.columnconfigure(1, weight=0)
		self.root.columnconfigure(2, weight=1)
		self.root.protocol("WM_DELETE_WINDOW", self.root.withdraw)
		self.homeworkIcon = self.loadSvg("homework")
		self.homeworkLabel = Label(
			self.timeFrame, 
			image=self.homeworkIcon, 
			bg=f"#{state.settings.config.background:06x}",
			fg=f"#{state.settings.config.foreground:06x}"
		)
		self.homeworkLabel.image = self.homeworkIcon
		self.examIcon = self.loadSvg("exam")
		self.examLabel = Label(
			self.timeFrame, 
			image=self.examIcon, 
			bg=f"#{state.settings.config.background:06x}",
			fg=f"#{state.settings.config.foreground:06x}"
		)
		self.examLabel.image = self.examIcon
		self.mainloopTask = state.runtime.create_task(self.mainloop())
		self.mainloopTask.add_done_callback(state.exc_handler)
		self.setClickThroughTask = state.runtime.create_task(self.setClickThrough())
		self.setClickThroughTask.add_done_callback(state.exc_handler)
		self.transparencyTask = state.runtime.create_task(self.transparencyCheck())
		self.transparencyTask.add_done_callback(state.exc_handler)
		self.logger.info("Clock setup complete")
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
		if (self.lastWidth != self.root.winfo_width()):
			self.logger.debug(f"window size: {self.root.winfo_width()}x{self.root.winfo_height()}+{self.root.winfo_screenwidth()-self.root.winfo_width()}+0")
			self.lastWidth = self.root.winfo_width()
		self.root.geometry(f"+{self.root.winfo_screenwidth()-self.root.winfo_width()}+0")
	async def setClickThrough(self):
		self.logger.debug("Setting click-through window")
		while not self.root.winfo_viewable():
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
		except ImportError:
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
			except Exception:
				self.logger.exception("An error happened during transparency check")
	def setClassLabels(self, A_class:_Class, B_class:_Class|None = None, aux:bool = False):			
		if self.class1Label.winfo_ismapped():
			self.class1Label.grid(row=3, column=0, sticky="nsew")
		if self.loc1Label.winfo_ismapped():
			self.loc1Label.grid(row=4, column=0, sticky="nsew")
		if self.timeLabel.winfo_ismapped():
			self.timeLabel.grid(row=1, column=0, sticky="nsew", columnspan=3)

		if state.settings.events.current_exam():
			if self.homeworkLabel.winfo_ismapped():
				self.homeworkLabel.grid_forget()
			self.examLabel.grid(row=1, column=3)
		elif state.settings.events.current_homework():
			if self.examLabel.winfo_ismapped():
				self.examLabel.grid_forget()
			self.homeworkLabel.grid(row=1, column=3)
		else:
			if self.examLabel.winfo_ismapped():
				self.examLabel.grid_forget()
			if self.homeworkLabel.winfo_ismapped():
				self.homeworkLabel.grid_forget()
		
		self.class1Label.config(text=f"{A_class.name}", anchor="center")
		self.loc1Label.config(text=f"{A_class.room}")
		
		if not aux and self.auxLabel.winfo_ismapped():
			self.auxLabel.grid_forget()
			self.root.rowconfigure(6, weight=0, minsize=0)
		elif aux and not self.auxLabel.winfo_ismapped():
			self.auxLabel.grid(row=6, column=0, sticky="nsew", columnspan=3)
			self.auxLabel.config(text=state.settings.localization.nextClass)
			self.root.rowconfigure(6, weight=1)
		if not self.separator.winfo_ismapped(): 
			self.separator.grid(row=2, column=0, sticky="ew", padx=5, pady=5, columnspan=3, ipadx=100)
		
		if state.settings.config.showTeacher:
			self.root.rowconfigure(5, weight=1, minsize=20)
			if B_class is None:
				if self.teacher2Label.winfo_ismapped():
					self.teacher2Label.grid_forget()
				if not self.teacher1Label.winfo_ismapped(): 
					self.teacher1Label.grid(row=5, column=0, sticky="nsew", columnspan=3)
				else:
					self.teacher1Label.grid_configure(columnspan=3)
				self.teacher1Label.config(
					text=f"{A_class.teacher}", 
					anchor="center", 
					wraplength=self.root.winfo_width()
				)
			else:
				if not self.teacher2Label.winfo_ismapped(): 
					self.teacher2Label.grid(row=5, column=2, sticky="nsew")
				if not self.teacher1Label.winfo_ismapped(): 
					self.teacher1Label.grid(row=5, column=0, sticky="nsew", columnspan=1)
				else:
					self.teacher1Label.grid_configure(columnspan=1)
				self.teacher2Label.config(
					text=f"{B_class.teacher}", 
					anchor="center", 
					wraplength=self.root.winfo_width()//2
				)
				self.teacher1Label.config(
					text=f"{A_class.teacher}", 
					anchor="center", 
					wraplength=self.root.winfo_width()//2
				)
		else:
			self.root.rowconfigure(5, weight=0, minsize=0)
		
		if B_class is not None:
			if not self.class2Label.winfo_ismapped(): 
				self.class2Label.grid(row=3, column=2, sticky="nsew")
			if not self.loc2Label.winfo_ismapped(): 
				self.loc2Label.grid(row=4, column=2, sticky="nsew")
			if not self.vertSeparator.winfo_ismapped(): 
				self.vertSeparator.grid(row=3, column=1, sticky="ns", padx=5, pady=5, rowspan=2)
			self.class1Label.grid_configure(columnspan=1)
			self.loc1Label.grid_configure(columnspan=1)
			self.class2Label.config(text=f"{B_class.name}", anchor="center", wraplength=self.root.winfo_width()//2)
			self.loc1Label.config(wraplength=self.root.winfo_width()//2)
			self.loc2Label.config(text=f"{B_class.room}", wraplength=self.root.winfo_width()//2)
			self.class1Label.config(wraplength=self.root.winfo_width()//2)
			self.class2Label.config(wraplength=self.root.winfo_width()//2)
		else:
			if self.class2Label.winfo_ismapped(): 
				self.class2Label.grid_forget()
			if self.loc2Label.winfo_ismapped(): 
				self.loc2Label.grid_forget()
			if self.vertSeparator.winfo_ismapped(): 
				self.vertSeparator.grid_forget()
			self.class1Label.grid_configure(columnspan=3)
			self.loc1Label.grid_configure(columnspan=3)
			self.class1Label.config(wraplength=self.root.winfo_width())
			self.loc1Label.config(wraplength=self.root.winfo_width())
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
	prev_day:datetime = state.getTime().date()
	async def mainloop(self):
		while True:
			_start = perf_counter()
			delay = state.settings.schedule.delay
			if self.prev_day != state.schedule._date:
				self.prev_day = state.getTime().date()
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
					self.setClassLabels(_class, tmp_class)
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
						self.setClassLabels(_class, tmp_class)
					else: # Less than 10 mins left
						state.currentClassIndex = num + 2
						if isinstance(next_class := state.schedule.classes[num+1], list): # Next class is split
							self.setClassLabels(next_class[0], next_class[1], True)
						else: # Next class is together
							self.setClassLabels(next_class, None, True)
					break
			else: # No class ends after now (No If branch broke the loop)
				self.mainLabel.config(text=loc.mainlabel.dayOver)
				state.currentClassIndex = -1
				[i.grid_forget() for i in [self.class1Label,self.class2Label,self.loc1Label,self.loc2Label,self.auxLabel,self.teacher1Label,self.teacher2Label] if i.winfo_ismapped()]
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
