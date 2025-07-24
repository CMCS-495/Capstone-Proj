#check if Flask is already running and stop it if necessary
$flaskpid = try{
    Get-NetTCPConnection -LocalPort 5000 -State Listen -ErrorAction Stop | Select-Object -ExpandProperty OwningProcess
}catch{
    $null
}

if($flaskpid){
    Get-Process -Id $flaskpid | Stop-Process -Force -Confirm:$false
}

#build flask path
$scriptDir   = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Resolve-Path "$scriptDir\.."
Push-Location $projectRoot
$env:FLASK_APP = 'Flask.flask_app'

#start flask as a subprocess
Start-Process -NoNewWindow -FilePath "flask" -ArgumentList "run"

#wait for Flask to start
while(-not (Get-NetTCPConnection -LocalPort 5000 -State Listen -ErrorAction SilentlyContinue)) {
    Start-Sleep -Milliseconds 500
}

#open the browser to the Flask app
Start-Process "http://127.0.0.1:5000/"

Pop-Location
