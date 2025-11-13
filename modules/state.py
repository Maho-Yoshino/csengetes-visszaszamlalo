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
update_cycle_task:Optional[asyncio.Task] = None
transparency_task:Optional[asyncio.Task] = None
windowHandle:str = u"Csengetés időzítő"
dummy_date:Optional[datetime] = None
