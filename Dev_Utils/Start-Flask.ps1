$scriptDir   = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Resolve-Path "$scriptDir\.."
Push-Location $projectRoot
$env:FLASK_APP = 'Flask.flask_app'

Start-Process "http://127.0.0.1:5000/"
flask run

Pop-Location
