$scriptDir   = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Resolve-Path "$scriptDir\.."
Push-Location $projectRoot
$env:FLASK_APP = 'Flask.flask_app'

flask run

Pop-Location