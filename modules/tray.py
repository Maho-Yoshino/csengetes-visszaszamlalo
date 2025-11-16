if __name__ == "__main__":
	from sys import path as sp
	from os import path
	sp.append(path.abspath(path.join(path.dirname(__file__), '..')))
import asyncio, tkinter as tk, pystray, modules.state as state, logging
from tkinter import Tk
from threading import Thread
from PIL import Image
from modules.clock import getTime
from datetime import datetime
logger = logging.getLogger(__name__)

async def setup_tray(root:Tk):
	def on_quit(icon, item):
		logger.info("Closing application")
		icon.stop()
		if (state.updateCycleTask is not None):
			state.updateCycleTask.cancel()
		if (state.transparencyTask is not None):
			state.transparencyTask.cancel()
		state.root.quit()
		state.runtime.stop()
	def settings_callback(): state.runtime.create_task(state.settings.open_settings(root))
	def setDelayWindow(icon, item):
		async def CreateWindow():
			global delayRoot
			def saveValue(event=None):
				state.settings.delay = int(val.get())
				delayWindowTask.cancel()
				delayRoot.destroy()
			delayRoot = tk.Toplevel(root)
			delayRoot.title("Delay Time Input")
			delayRoot.geometry(f"+{delayRoot.winfo_screenwidth()//2-25}+{delayRoot.winfo_screenheight()//2-25}")
			delayRoot.resizable(False, False)
			delayRoot.grid(1, 6, 150, 50)
			tk.Label(delayRoot, text="Set Delay Time (in seconds)").grid(row=0, column=0)
			val = tk.Entry(delayRoot, textvariable=tk.IntVar(value=state.settings.delay))
			val.grid(row=1, column=0)
			tk.Label(delayRoot, text="Negative = Earlier\nPositive = Later").grid(row=2, column=0, rowspan=2)
			tk.Button(delayRoot, text="Save", command=saveValue).grid(row=5, column=0)
			delayRoot.focus_force()
			delayRoot.bind('<Return>', saveValue)
			delayWindowTask = asyncio.create_task(state.updateFast(delayRoot))
		state.runtime.create_task(CreateWindow())
	def ScheduleWindow(icon, item):
		async def CreateWindow():
			scheduleRoot = tk.Toplevel(root)
			scheduleRoot.title("Schedule")
			windowHeight = max([len(i) for i in state.settings.default_schedule], [len(val) for key, val in state.settings.special_days.items() if datetime.strptime(key, "%Y-%m-%d").strftime("%V") == (await getTime()).strftime("%V")])
			windowWidth = len(state.settings.default_schedule)
			if specialDayThisWeek := any([datetime.strptime(key, "%Y-%m-%d").strftime("%V") == (await getTime()).strftime("%V") for key in state.settings.special_days.keys()]):
				windowWidth += 1
			scheduleRoot.grid(windowWidth, windowHeight, 300, 150)
			frames:list[list[tk.Frame]] = []
			for col in range(windowWidth):
				frames.append([])
				for row in range(windowHeight):
					temp = tk.Frame(scheduleRoot, highlightbackground="white", highlightcolor="black")
					temp.grid(row=row, column=col)
					frames[col].append(temp)
			for num, frame in enumerate(frames):
				# TODO: Finish fullscreen schedule
				...
			scheduleRoot.update()
		state.runtime.create_task(CreateWindow())
	icon = pystray.Icon("Csengetés időzítő", Image.open("icon.ico"), menu=pystray.Menu(
		pystray.MenuItem(lambda item: f"Delay: {state.settings.delay}", setDelayWindow),
		pystray.MenuItem("Fullscreen Schedule", ScheduleWindow),
		pystray.MenuItem("Settings", settings_callback),
		pystray.MenuItem("Quit", lambda icon, item: on_quit(icon, item))
	))
	Thread(target=icon.run, daemon=True).start()
