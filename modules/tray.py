import pystray
if __name__ == "__main__":
	from sys import path as sp
	from os import path
	sp.append(path.abspath(path.join(path.dirname(__file__), '..')))
import asyncio, tkinter as tk, logging, modules.state as state
from tkinter import Tk
from PIL.Image import open as imgopen
from datetime import datetime
from modules.clock import fontSize
logger = logging.getLogger(__name__)

class traySetup:
	class delayWindow:
		root:tk.Toplevel
		def __init__(self):
			self.root = tk.Toplevel(state.root)
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
		def __init__(self):
			self.root = tk.Toplevel(state.root)
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
	class settingsWindow:
		root:tk.Toplevel|None = None 
		def __init__(self):
			self.root = tk.Toplevel(state.root)
			self.root.title("Settings")
			self.root.grid(10, 10, 50, 25)
			menu = tk.Menu(self.root)
			menu.add_command(label="Schedule", command=self.openSchedule)
			menu.add_command(label="Special days", command=self.openSpecialDays)
			menu.add_command(label="Alerts", command=self.openAlerts)
			menu.add_command(label="General", command=self.openGeneral)
			menu.activate(0)
			self.root.config(menu=menu)
			self.content = tk.Frame(self.root)
			self.content.grid(row=0, column=0, sticky="nsew")
		def _clearContent(self, title:str) -> None:
			for child in self.content.winfo_children():
				child.destroy()
			tk.Label(self.content, text=title, font=fontSize(20)).grid(row=0, column=0, columnspan=3)
		def openSchedule(self):
			self._clearContent("Schedule Settings")
		def openSpecialDays(self):
			self._clearContent("Special Days")
		def openAlerts(self):
			self._clearContent("Alerts")
		def openGeneral(self):
			self._clearContent("General settings")
	def __init__(self):
		self.icon = pystray.Icon("Csengetés időzítő", imgopen("icon.ico"), menu=pystray.Menu(
			pystray.MenuItem(
				lambda item: f"Delay: {state.settings.delay}", 
				lambda icon, item: state.runtime.call_soon_threadsafe(lambda: self.delayWindow())
			),
			pystray.MenuItem(
				"Fullscreen Schedule",
				lambda icon, item: state.runtime.call_soon_threadsafe(lambda: self.scheduleWindow())
			),
			pystray.MenuItem(
				"Settings",
				lambda icon, item: state.runtime.call_soon_threadsafe(lambda: self.settingsWindow())
			),
			pystray.MenuItem(
				"Quit",
				lambda icon, item: state.runtime.call_soon_threadsafe(self.quit)
			)
		))
		self.icon.run_detached()
	def quit(self):
		logger.info("Closing application")
		self.icon.stop()
		state.runtime.create_task(self._shutdown())
	async def _shutdown(self):
		tasks = []
		for task in (state.updateCycleTask, state.transparencyTask, state.tkPumpTask):
			if task and not task.done():
				task.cancel()
				tasks.append(task)
		if tasks:
			await asyncio.gather(*tasks, return_exceptions=True)
		state.root.quit()
		state.runtime.stop()


