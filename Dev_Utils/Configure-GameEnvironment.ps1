#set up windows environment for game play
#install python
$pythonInstaller = "https://www.python.org/ftp/python/3.14.0/python-3.14.0a1-amd64.exe"
$pythonInstallerPath = "$env:TEMP\python-3.14.0a1-amd64.exe"
Invoke-WebRequest -Uri $pythonInstaller -OutFile $pythonInstallerPath
Start-Process -FilePath $pythonInstallerPath -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1" -Wait

#remove installer after installation
Remove-Item -Path $pythonInstallerPath -Force

#validate system path
$pythonPath = (Get-Command python).Source
if(-not $pythonPath) {
    Write-Error "Python installation failed or not found in system path."
    exit 1
}

#install pip if not already installed
if(-not (Get-Command pip -ErrorAction SilentlyContinue)) {  
    $getPipUrl = "https://bootstrap.pypa.io/get-pip.py"
    $getPipPath = "$env:TEMP\get-pip.py"
    Invoke-WebRequest -Uri $getPipUrl -OutFile $getPipPath
    python $getPipPath
}

#install pip packages
pip install -r requirements.txt