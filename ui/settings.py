import pystray
if __name__ == "__main__":
	from sys import path as sp
	from os import path
	sp.append(path.abspath(path.join(path.dirname(__file__), '..')))
import tkinter as tk, logging, modules.state as state
from tkinter import ttk
from typing import Optional
from modules.clock import fontSize
logger = logging.getLogger(__name__)

class settingsGUI:
		root:tk.Toplevel
		content:tk.Frame
		def __init__(self):
			self.root = tk.Toplevel(state.root)
			self.root.title("Settings")
			self.root.grid(10, 10, 50, 25)
			menu = tk.Menu(self.root)
			menu.add_command(label="Schedule", command=self._openSchedule)
			menu.add_command(label="Special days", command=self._openSpecialDays)
			menu.add_command(label="Alerts", command=self._openAlerts)
			menu.add_command(label="General", command=self._openGeneral)
			self.root.config(menu=menu)
			self.content = tk.Frame(self.root)
			self.content.grid(row=0, column=0, sticky="nsew")
			self._openSchedule()
		def _clearContent(self, title:str, colspan:int=3) -> None:
			for child in self.content.winfo_children():
				child.destroy()
			tk.Label(self.content, text=title, font=fontSize(20)).grid(row=0, column=0, columnspan=colspan)
		sidebar:Optional[tk.Frame] = None
		def _openSchedule(self):
			self._clearContent("Schedule Settings")
			self.sidebar = tk.Frame(self.content)
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