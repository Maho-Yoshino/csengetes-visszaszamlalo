if __name__ == "__main__":
	from sys import path as sp
	from os import path
	sp.append(path.abspath(path.join(path.dirname(__file__), '..')))
from tkinter import Toplevel, Menu, Frame
from logging import getLogger 
from tkinter import ttk
import modules.state as state

class settingsGUI(Toplevel):
	content:Frame
	_bg = "#303030"
	_fg = "#FFFFFF"
	def __init__(self):
		self.logger = getLogger(__name__)
		# region Check other window
		if state.openGUIs.get("settings", None) is not None:
			state.openGUIs["settings"].focus_force()
			return self.logger.debug("Settings opened more than once. Focus set to older window")
		super().__init__(state.root)
		state.openGUIs["settings"] = self
		self.protocol("WM_DELETE_WINDOW", self.closeFunc)
		# endregion
		# region Styling
		self.style = ttk.Style()
		self.style.configure("BW.Label", foreground=self._fg, background=self._bg)
		self.configure(background=self.style.lookup("BW.Label", "background"))
		# endregion
		# region Window Setup
		loc = state.settings.localization
		self.title(loc.settings.title)
		self.scheduleHeight = max(*[len(i) for i in state.settings.schedule.default])
		self.geometry(f"+{self.winfo_screenwidth()//2-150}+{self.winfo_screenheight()//2-150}")
		menu = Menu(self, background=self._bg, fg=self._fg, relief="ridge")
		menu.add_command(label=loc.settings.topbar["schedule"], command=self._openSchedule)
		menu.add_command(label=loc.settings.topbar["special_days"], command=self._openSpecialDays)
		menu.add_command(label=loc.settings.topbar["alerts"], command=self._openAlerts)
		menu.add_command(label=loc.settings.topbar["general"], command=self._openGeneral)
		self.config(menu=menu)
		self.content = Frame(self, bg=self._bg)
		self.content.grid(row=0, column=0, sticky="nsew")
		self._openSchedule()
		# endregion
		for child in self.content.winfo_children():
	def _closeFunc(self):
		state.openGUIs.pop("settings")
		self.destroy()
	def _clearContent(self):
			child.destroy()
	def resize(self, width:int, height:int):
		self.geometry(f"{width}x{height}+{self.winfo_rootx()}+{self.winfo_rooty()}")
	def _openSchedule(self):
		self._clearContent()
		schedule = state.settings.schedule.default
		isOffset = state.getTime().isocalendar().week % 2 == int(state.settings.schedule.offsetSecondary) 
		if isOffset:
			for day, _schedule in state.settings.schedule.secondary.items():
				if int(day) not in range(7):
					raise ValueError(f"No such day (Must be between 0 and 6, is {day})")
				for time, _class in _schedule.items(): 
					schedule[int(day)][time] = _class
		height = len(schedule)
		width = max(*[len(i) for i in schedule])
		self.resize(height*100+height*15, width*50+width*45)
		ttk.Label(self.content, text="Schedule", style="BW.Label")
		for i in range(8):
			for j in range(self.scheduleHeight):
				_ = Frame(self.content, borderwidth=5, highlightcolor=self.style.lookup("BW.Label", "foreground"), background="#397AC1", padx=15, pady=45, width=100, height=50)
				_.grid(row=j, column=i)
	def _openSpecialDays(self):
		self._clearContent()
	def _openAlerts(self):
		self._clearContent()
	def _openGeneral(self):
		self._clearContent()