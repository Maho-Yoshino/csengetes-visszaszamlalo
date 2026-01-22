import pystray
if __name__ == "__main__":
	from sys import path as sp
	from os import path
	sp.append(path.abspath(path.join(path.dirname(__file__), '..')))
import modules.state as state
from asyncio import sleep, gather
from logging import getLogger
from PIL.Image import open as imgopen
from ui.settings import settingsGUI
from ui.schedule import scheduleGUI
from ui.delay import delayGUI
logger = getLogger(__name__)

class traySetup:
	shutting_down:bool = False
	def __init__(self):
		loc = state.settings.localization
		self.icon = pystray.Icon(loc.tray.name, imgopen("assets/icon.ico"), menu=pystray.Menu(
			pystray.MenuItem(
				lambda item: loc.format(f"{loc.tray.delay}", time=f"{f"{state.settings.delay//60} {loc.tray.delayMinutesDisplay} " if state.settings.delay >= 60 else ""}{state.settings.delay%60} {loc.tray.delaySecondsDisplay}"), 
				lambda icon, item: state.runtime.call_soon_threadsafe(lambda: delayGUI())
			),
			pystray.MenuItem(
				loc.tray.fullscreen_schedule,
				lambda icon, item: state.runtime.call_soon_threadsafe(lambda: scheduleGUI()),
				enabled=False
			),
			pystray.MenuItem(
				loc.tray.settings,
				lambda icon, item: state.runtime.call_soon_threadsafe(lambda: settingsGUI())
			),
			pystray.MenuItem(
				loc.tray.close,
				lambda icon, item: state.runtime.call_soon_threadsafe(self.quit)
			)
		))
		self.icon.run_detached()
	def quit(self):
		if self.shutting_down:
			return
		self.shutting_down = True
		logger.info("Closing application")
		self.icon.stop()
		state.root.quit()
		state.root.destroy()
		state.runtime.create_task(self._shutdown())
	async def _shutdown(self):
		tasks = []
		for task in (state.updateCycleTask, state.transparencyTask, state.tkPumpTask, state.setClickThroughTask):
			if task and not task.done():
				task.cancel()
				tasks.append(task)
		if tasks:
			await gather(*tasks, return_exceptions=True)
		if state.runtime is not None: 
			state.runtime.stop()
			while state.runtime.is_running():
				await sleep(0.05)
			state.runtime.close()