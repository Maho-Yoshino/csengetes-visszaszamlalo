if __name__ == "__main__":
	from sys import path as sp
	from os import path
	sp.append(path.abspath(path.join(path.dirname(__file__), '..')))
import modules.state as state
from tkinter import Toplevel, IntVar
from logging import getLogger 
from tkinter import ttk
logger = getLogger(__name__)

class delayGUI(Toplevel):
	def __init__(self):
		super().__init__(state.root)
		loc = state.settings.localization
		self.title(loc.delaySetting.title)
		self.geometry(f"+{self.winfo_screenwidth()//2-25}+{self.winfo_screenheight()//2-25}")
		self.resizable(False, False)
		self.grid(1, 6, 150, 50)
		self.delayvar = IntVar(value=state.settings.schedule.delay)
		ttk.Label(self, text=loc.delaySetting.label).grid(row=0, column=0)
		ttk.Entry(self, textvariable=self.delayvar).grid(row=1, column=0)
		ttk.Label(self, text=loc.delaySetting.help).grid(row=2, column=0, rowspan=2)
		ttk.Button(self, text=loc.delaySetting.btn, command=self.saveValue).grid(row=5, column=0)
		self.focus_force()
		self.bind('<Up>', lambda _: self.delayvar.set(self.delayvar.get() + 1))
		self.bind('<Down>', lambda _: self.delayvar.set(self.delayvar.get() - 1))
		self.bind('<Return>', lambda _: self.saveValue())
	def saveValue(self):
		state.settings.schedule.delay = self.delayvar.get()
		self.destroy()