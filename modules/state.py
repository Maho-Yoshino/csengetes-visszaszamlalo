from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from datetime import datetime
import asyncio
from tkinter import Tk
import tkinter as tk

if TYPE_CHECKING:
	from modules.tray import traySetup
	from modules.settings import Settings
	from modules.clock import Schedule

runtime:Optional[asyncio.AbstractEventLoop] = None
root:Optional[Tk] = None
settings:Optional["Settings"] = None
schedule:Optional["Schedule"] = None
updateCycleTask:Optional[asyncio.Task] = None
transparencyTask:Optional[asyncio.Task] = None
setClickThroughTask: Optional[asyncio.Task] = None
tkPumpTask: Optional[asyncio.Task] = None
windowHandle:str = u"Csengetés időzítő"
dummyDate:Optional[datetime] = None
tray:Optional[traySetup] = None

async def tkPump(root: Tk):
	try:
		while True:
			try:
				root.update_idletasks()
				root.update()
			except tk.TclError:
				break
			await asyncio.sleep(1/60) # 60 FPS
	except asyncio.CancelledError:
		pass
def getTime(): return datetime.now() if dummyDate is None else dummyDate