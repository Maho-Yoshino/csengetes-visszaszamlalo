from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from datetime import datetime
import asyncio
from tkinter import Tk

if TYPE_CHECKING:
	from modules.settings import Settings
	from modules.clock import Schedule

runtime:Optional[asyncio.AbstractEventLoop] = None
root:Optional[Tk] = None
settings:Optional["Settings"] = None
schedule:Optional["Schedule"] = None
updateCycleTask:Optional[asyncio.Task] = None
transparencyTask:Optional[asyncio.Task] = None
windowHandle:str = u"Csengetés időzítő"
dummyDate:Optional[datetime] = None

async def updateFast(_root:Tk):
	while True:
		_root.update()
		await asyncio.sleep(0.01)
def getTime(): return datetime.now() if dummyDate is None else dummyDate