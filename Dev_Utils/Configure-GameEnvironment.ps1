#set up windows environment for game play
#install python
$pythonInstaller = "https://www.python.org/ftp/python/3.10.4/python-3.10.4-amd64.exe"
$pythonInstallerPath = "$env:TEMP\python-3.10.4-amd64.exe"
Invoke-WebRequest -Uri $pythonInstaller -OutFile $pythonInstallerPath
Start-Process -FilePath $pythonInstallerPath -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1" -Wait
#install pip packages
pip install -r requirements.txt