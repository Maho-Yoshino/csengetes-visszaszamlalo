# csengetes-visszaszamlalo  
Ez egy visszaszámláló program óra végéig diákok és tanárok számára egyaránt  

## Automatikus indulás gépindításkor  
- Win+R > "taskschd.msc"  
- "Create Basic task"  
	- Név: Akármi lehet  
	- Trigger = "When I log on" (Amikor bejelentkezek)  
	- Action = "Start a program" (Program indítása)  
	- Action > Start a program  
		- Program/script = "C:\WINDOWS\System32\cmd.exe"  
		- Add arguments = "/c python {a csengo.py elérési útvonala}"  
## Build from source  
- Git clone the repo  
- run "setup.bat"  
- If running raw python  
	- run "csengo.bat"  
- else if building an exe  
	- run "package.bat"  
# Development  
[Trello board](https://trello.com/b/SpFVKoKa)  
## Requirements  
- Python 3.12+  
- Windows 10+  
