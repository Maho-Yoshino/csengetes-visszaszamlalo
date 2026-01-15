import pystray
if __name__ == "__main__":
	from sys import path as sp
	from os import path
	sp.append(path.abspath(path.join(path.dirname(__file__), '..')))
import asyncio, logging, modules.state as state
from PIL.Image import open as imgopen
from ui.settings import settingsGUI
from ui.schedule import scheduleGUI
from ui.delay import delayGUI
logger = logging.getLogger(__name__)

class traySetup:
	def __init__(self):
		self.icon = pystray.Icon("Csengetés időzítő", imgopen("assets/icon.ico"), menu=pystray.Menu(
			pystray.MenuItem(
				lambda item: f"Delay: {state.settings.delay}", 
				lambda icon, item: state.runtime.call_soon_threadsafe(lambda: delayGUI())
			),
			pystray.MenuItem(
				"Fullscreen Schedule",
				lambda icon, item: state.runtime.call_soon_threadsafe(lambda: scheduleGUI()),
				enabled=False
			),
			pystray.MenuItem(
				"Settings",
				lambda icon, item: state.runtime.call_soon_threadsafe(lambda: settingsGUI())
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