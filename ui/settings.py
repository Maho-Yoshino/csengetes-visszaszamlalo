if __name__ == "__main__":
	from sys import path as sp
	from os import path
	sp.append(path.abspath(path.join(path.dirname(__file__), '..')))
import modules.state as state
from logging import getLogger
from tkinter import ttk, Menu, Toplevel, Label, Frame
from typing import Optional
logger = getLogger(__name__)

class settingsGUI:
		root:Toplevel
		content:Frame
		def __init__(self):
			self.root = Toplevel(state.root)
			loc = state.settings.localization
			self.root.title(loc.settings.title)
			self.root.grid(10, 10, 50, 25)
			menu = Menu(self.root)
			menu.add_command(label=loc.settings.topbar["schedule"], command=self._openSchedule)
			menu.add_command(label=loc.settings.topbar["special_days"], command=self._openSpecialDays)
			menu.add_command(label=loc.settings.topbar["alerts"], command=self._openAlerts)
			menu.add_command(label=loc.settings.topbar["general"], command=self._openGeneral)
			self.root.config(menu=menu)
			self.content = Frame(self.root)
			self.content.grid(row=0, column=0, sticky="nsew")
			self._openSchedule()
		def _clearContent(self, title:str, colspan:int=3) -> None:
			for child in self.content.winfo_children():
				child.destroy()
			Label(self.content, text=title, font=state.fontSize(20)).grid(row=0, column=0, columnspan=colspan)
		sidebar:Optional[Frame] = None
		def _openSchedule(self):
			self._clearContent("Schedule Settings")
			self.sidebar = Frame(self.content)
			self.sidebar.grid(row=1, column=1, rowspan=10)
			self._scheduleSidebarSetup()
		def _openSpecialDays(self):
			self._clearContent("Special Days")
		def _openAlerts(self):
			self._clearContent("Alerts")
		def _openGeneral(self):
			self._clearContent("General settings")
		def _scheduleSidebarSetup(self):
			...