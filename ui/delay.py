if __name__ == "__main__":
	from sys import path as sp
	from os import path
	sp.append(path.abspath(path.join(path.dirname(__file__), '..')))
import modules.state as state
from tkinter import Toplevel, IntVar
from logging import getLogger 
from tkinter import ttk
logger = getLogger(__name__)

class delayGUI:
		root:Toplevel
		def __init__(self):
			self.root = Toplevel(state.root)
			loc = state.settings.localization
			self.root.title(loc.delaySetting.title)
			self.root.geometry(f"+{self.root.winfo_screenwidth()//2-25}+{self.root.winfo_screenheight()//2-25}")
			self.root.resizable(False, False)
			self.root.grid(1, 6, 150, 50)
			self.delayvar = IntVar(value=state.settings.schedule.delay)
			ttk.Label(self.root, text=loc.delaySetting.label).grid(row=0, column=0)
			ttk.Entry(self.root, textvariable=self.delayvar).grid(row=1, column=0)
			ttk.Label(self.root, text=loc.delaySetting.help).grid(row=2, column=0, rowspan=2)
			ttk.Button(self.root, text=loc.delaySetting.btn, command=self.saveValue).grid(row=5, column=0)
			self.root.focus_force()
			self.root.bind('<Up>', lambda _: self.delayvar.set(self.delayvar.get() + 1))
			self.root.bind('<Down>', lambda _: self.delayvar.set(self.delayvar.get() - 1))
			self.root.bind('<Return>', lambda _: self.saveValue())
		def saveValue(self):
			state.settings.schedule.delay = self.delayvar.get()
			self.root.destroy()