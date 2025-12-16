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

settings:Optional["Settings"] = None
schedule:Optional["Schedule"] = None
tray:Optional[traySetup] = None

windowHandle:str = u"Csengetés időzítő"
root:Optional[Tk] = None
dummyDate:Optional[datetime] = None

runtime:Optional[asyncio.AbstractEventLoop] = None
setClickThroughTask: Optional[asyncio.Task] = None
tkPumpTask: Optional[asyncio.Task] = None
updateCycleTask:Optional[asyncio.Task] = None
transparencyTask:Optional[asyncio.Task] = None

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