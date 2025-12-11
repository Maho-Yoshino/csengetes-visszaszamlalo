import pystray
if __name__ == "__main__":
	from sys import path as sp
	from os import path
	sp.append(path.abspath(path.join(path.dirname(__file__), '..')))
import asyncio, tkinter as tk, logging, modules.state as state
from tkinter import Tk
from PIL.Image import open as imgopen
from datetime import datetime
logger = logging.getLogger(__name__)

class traySetup:
	class delayWindow:
		root:tk.Toplevel
		def __init__(self, mainroot:Tk):
			self.root = tk.Toplevel(mainroot)
			self.root.title("Delay Time Input")
			self.root.geometry(f"+{self.root.winfo_screenwidth()//2-25}+{self.root.winfo_screenheight()//2-25}")
			self.root.resizable(False, False)
			self.root.grid(1, 6, 150, 50)
			tk.Label(self.root, text="Set Delay Time (in seconds)").grid(row=0, column=0)
			val = tk.Entry(self.root, textvariable=tk.IntVar(value=state.settings.delay))
			val.grid(row=1, column=0)
			tk.Label(self.root, text="Negative = Earlier\nPositive = Later").grid(row=2, column=0, rowspan=2)
			tk.Button(self.root, text="Save", command=lambda: self.saveValue(val)).grid(row=5, column=0)
			self.root.focus_force()
			self.root.bind('<Return>', lambda _: self.saveValue(val))
		def saveValue(self, val:tk.Entry):
			state.settings.delay = int(val.get())
			self.root.destroy()
	class scheduleWindow:
		root:tk.Toplevel
		def __init__(self, mainroot:Tk):
			self.root = tk.Toplevel(mainroot)
			self.root.title("Schedule")
			windowHeight = max(max([len(i) for i in state.settings.defaultSchedule]), max([len(val) for key, val in state.settings.specialDays.items() if datetime.strptime(key, "%Y-%m-%d").strftime("%V") == (state.getTime()).strftime("%V")]))
			windowWidth = len(state.settings.defaultSchedule)
			if specialDayThisWeek := any([datetime.strptime(key, "%Y-%m-%d").strftime("%V") == (state.getTime()).strftime("%V") for key in state.settings.specialDays.keys()]):
				windowWidth += 1
			self.root.grid(windowWidth, windowHeight, 300, 150)
			frames:list[list[tk.Frame]] = []
			for col in range(windowWidth):
				frames.append([])
				for row in range(windowHeight):
					temp = tk.Frame(self.root, highlightbackground="white", highlightcolor="black")
					temp.grid(row=row, column=col)
					frames[col].append(temp)
			for num, frame in enumerate(frames):
				# TODO: Finish fullscreen schedule
				...
	def __init__(self, root:Tk):
		self.root = root
		self.icon = pystray.Icon("Csengetés időzítő", imgopen("icon.ico"), menu=pystray.Menu(
			pystray.MenuItem(lambda item: f"Delay: {state.settings.delay}", lambda icon, item: state.runtime.call_soon_threadsafe(lambda: self.delayWindow(self.root))),
			pystray.MenuItem("Fullscreen Schedule", lambda icon, item: state.runtime.call_soon_threadsafe(lambda: self.scheduleWindow(self.root))),
			pystray.MenuItem("Settings", lambda icon, item: state.runtime.call_soon_threadsafe(self.settings_callback())),
			pystray.MenuItem("Quit", lambda icon, item: self.quit())
		))
		self.icon.run_detached()
	def settings_callback(self): state.runtime.create_task(state.settings.open_settings(self.root))
	def quit(self):
		logger.info("Closing application")
		self.icon.stop()
		if (state.updateCycleTask is not None):
			state.updateCycleTask.cancel()
		if (state.transparencyTask is not None):
			state.transparencyTask.cancel()
		state.root.quit()
		state.runtime.stop()
