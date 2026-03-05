if __name__ == "__main__":
	from sys import path as sp
	from os import path
	sp.append(path.abspath(path.join(path.dirname(__file__), '..')))
from tkinter import Toplevel, Menu, Frame
from logging import getLogger 
from tkinter import ttk
from datetime import timedelta
import modules.state as state
from copy import deepcopy

class settingsGUI(Toplevel):
	content:Frame
	def __init__(self):
		self.logger = getLogger(__name__)
		# region Check other window
		if state.openGUIs.get("settings", None) is not None:
			state.openGUIs["settings"].focus_force()
			return self.logger.debug("Settings opened more than once. Focus set to older window")
		super().__init__(state.clock)
		state.openGUIs["settings"] = self
		self.protocol("WM_DELETE_WINDOW", self._closeFunc)
		# endregion
		# region Styling
		self.style = ttk.Style(self)
		self.style.configure("mainText.Label", foreground="#FFFFFF", background="#202020")
		self.style.configure("scheduleElement.Label", foreground="#000000", background="#8A8A8A")
		self.configure(background=self.style.lookup("mainText.Label", "background"))
		# endregion
		# region Window Setup
		loc = state.settings.localization
		self.title(loc.settings.title)
		self.scheduleHeight = max(*[len(i) for i in state.settings.schedule.default])
		self.geometry(f"+{self.winfo_screenwidth()//2-150}+{self.winfo_screenheight()//2-150}")
		menu = Menu(self, background=self.style.lookup("mainText.Label", "background"), fg=self.style.lookup("mainText.Label", "foreground"), relief="ridge")
		menu.add_command(label=loc.settings.topbar["schedule"], command=self._openSchedule)
		menu.add_command(label=loc.settings.topbar["special_days"], command=self._openSpecialDays)
		menu.add_command(label=loc.settings.topbar["alerts"], command=self._openAlerts)
		menu.add_command(label=loc.settings.topbar["general"], command=self._openGeneral)
		self.config(menu=menu)
		self._openSchedule()
		# endregion
	def _closeFunc(self):
		state.openGUIs.pop("settings")
		self.destroy()
	def _clearContent(self):
		for child in self.winfo_children():
			child.destroy()
	def resize(self, width:int, height:int):
		self.geometry(f"{width}x{height}+{self.winfo_rootx()}+{self.winfo_rooty()}")
	def _openSchedule(self):
		self._clearContent()
		schedule = deepcopy(state.settings.schedule.default)
		isOffset = state.getTime().isocalendar().week % 2 == int(state.settings.schedule.offsetSecondary)
		# Merge primary and secondary schedule 
		if isOffset:
			for day, _schedule in state.settings.schedule.secondary.items():
				if int(day) not in range(7):
					raise ValueError(f"No such day (Must be between 0 and 6, is {day})")
				for time, _class in _schedule.items(): 
					schedule[int(day)][time] = _class
		# Merge schedule and special days
		_ = state.getTime().date()
		weekstart = _
		while weekstart.weekday() != 0:
			weekstart -= timedelta(days=1)
		days = len(schedule)
		ttk.Label(self, anchor="center", text=f"Week {weekstart.isocalendar().week}", style="mainText.Label").grid(column=0, columnspan=days, row=0)
		for i in range(days):
			_ = weekstart + timedelta(days=i)
			ttk.Label(self, anchor="center", text=_.strftime("%A\n%B %d"), style="mainText.Label").grid(column=i, row=1)
			for day, data in state.settings.events.specialDays.items():
				if _ != day.date():
					continue
				if data["full"]:
					schedule[int(day.weekday())] = data["classes"]
				else:
					for time, _class in data["classes"].items():
						schedule[int(day.weekday())][time] = _class
		# Generate grid
		maxClasses = max(*[len(i) for i in schedule])
		self.resize(maxClasses*100+maxClasses*15, days*50+days*45)
		ttk.Label(self, text="Schedule", style="mainText.Label")
		for i in range(days):
			classes = list(schedule[i].keys())
			for j in range(len(classes)):
				if (_class := schedule[i].get(classes[j], None)) is None:
					continue
				classFrame = Frame(self, borderwidth=5, highlightcolor=self.style.lookup("scheduleElement.Label", "foreground"), background=self.style.lookup("scheduleElement.Label", "background"), padx=15, pady=45, width=100, height=50)
				classFrame.grid(row=j+2, column=i, padx=10, pady=5)
				ttk.Label(classFrame, anchor="center", justify="center", text=_class, style="scheduleElement.Label")
	def _openSpecialDays(self):
		self._clearContent()
	def _openAlerts(self):
		self._clearContent()
	def _openGeneral(self):
		self._clearContent()