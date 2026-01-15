if __name__ == "__main__":
	from sys import path as sp
	from os import path
	sp.append(path.abspath(path.join(path.dirname(__file__), '..')))
import tkinter as tk, logging, modules.state as state
from tkinter import ttk
logger = logging.getLogger(__name__)

class delayGUI:
		root:tk.Toplevel
		def __init__(self):
			self.root = tk.Toplevel(state.root)
			self.root.title("Delay Time Input")
			self.root.geometry(f"+{self.root.winfo_screenwidth()//2-25}+{self.root.winfo_screenheight()//2-25}")
			self.root.resizable(False, False)
			self.root.grid(1, 6, 150, 50)
			self.delayvar = tk.IntVar(value=state.settings.delay)
			tk.Label(self.root, text="Set Delay Time (in seconds)").grid(row=0, column=0)
			tk.Entry(self.root, textvariable=self.delayvar).grid(row=1, column=0)
			tk.Label(self.root, text="Negative = Earlier\nPositive = Later").grid(row=2, column=0, rowspan=2)
			tk.Button(self.root, text="Save", command=self.saveValue).grid(row=5, column=0)
			self.root.focus_force()
			self.root.bind('<Up>', lambda _: self.delayvar.set(self.delayvar.get() + 1))
			self.root.bind('<Down>', lambda _: self.delayvar.set(self.delayvar.get() - 1))
			self.root.bind('<Return>', lambda _: self.saveValue())
		def saveValue(self):
			state.settings.delay = self.delayvar.get()
			self.root.destroy()