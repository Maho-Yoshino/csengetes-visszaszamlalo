if __name__ == "__main__":
	from sys import path as sp
	from os import path
	sp.append(path.abspath(path.join(path.dirname(__file__), '..')))
import modules.state as state
from tkinter import Toplevel, Frame
from logging import getLogger
from tkinter import ttk
from datetime import datetime
logger = getLogger(__name__)

class scheduleGUI:
	root:Toplevel
	def __init__(self):
		self.root = Toplevel(state.root)
		self.root.title("Schedule")
		windowHeight = max(max([len(i) for i in state.settings.schedule.default]), max([len(val) for key, val in state.settings.events.specialDays.items() if datetime.strptime(key, "%Y-%m-%d").strftime("%V") == (state.getTime()).strftime("%V")]))
		windowWidth = len(state.settings.schedule.default)
		if specialDayThisWeek := any([datetime.strptime(key, "%Y-%m-%d").strftime("%V") == (state.getTime()).strftime("%V") for key in state.settings.events.specialDays.keys()]):
			windowWidth += 1
		self.root.grid(windowWidth, windowHeight, 300, 150)
		frames:list[list[Frame]] = []
		for col in range(windowWidth):
			frames.append([])
			for row in range(windowHeight):
				temp = Frame(self.root, highlightbackground="white", highlightcolor="black")
				temp.grid(row=row, column=col)
				frames[col].append(temp)
		for num, frame in enumerate(frames):
			# TODO: Finish fullscreen schedule
			...