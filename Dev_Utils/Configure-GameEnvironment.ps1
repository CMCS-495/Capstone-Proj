function Invoke-DownloadFileWithProgress {
    param(
        [Parameter(Mandatory)][string]$Url,
        [Parameter(Mandatory)][string]$Destination
    )

    $fileName = [System.IO.Path]::GetFileName($Destination)
    $destDir  = Split-Path -Parent $Destination
    
    if(-not (Test-Path $destDir)){
        New-Item -ItemType Directory -Path $destDir | Out-Null
    }

    $wc = New-Object System.Net.WebClient
    $dlEvent = Register-ObjectEvent -InputObject $wc -EventName DownloadProgressChanged -Action {
        $percent = $EventArgs.ProgressPercentage
        
        Write-Progress -Activity "Downloading $fileName" -Status "$percent% complete" -PercentComplete $percent
    }

    try {
        $wc.DownloadFile($Url, $Destination)
    }finally{
        Unregister-Event -SourceIdentifier $dlEvent.Name
        $wc.Dispose()
        Write-Progress -Activity "Download complete" -Completed
    }
}

#----------------------------------------
# Define URLs and paths
#----------------------------------------
$pythonInstaller       = "https://www.python.org/ftp/python/3.14.0/python-3.14.0a1-amd64.exe"
$pythonInstallerPath   = "$env:TEMP\python-3.14.0a1-amd64.exe"
$getPipUrl             = "https://bootstrap.pypa.io/get-pip.py"
$getPipPath            = "$env:TEMP\get-pip.py"
$sevenZipInstaller     = "https://www.7-zip.org/a/7z1900-x64.exe"
$sevenZipInstallerPath = "$env:TEMP\7z1900-x64.exe"
$sevenZipInstallDir    = Join-Path $env:ProgramFiles "7-Zip"
$sevenZipExePath       = Join-Path $sevenZipInstallDir "7z.exe"
$ffmpegInstaller       = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-full.7z"
$ffmpegInstallerPath   = "$env:TEMP\ffmpeg-release-full.7z"

#----------------------------------------
# 1) Relaunch elevated if not running as Administrator
#----------------------------------------
if(-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
          ).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){
    $startargs = "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`""
    Start-Process powershell -ArgumentList $startargs -Verb RunAs
    exit
}

#----------------------------------------
# 2) Install Python if missing
#----------------------------------------
if(-not (Get-Command python -ErrorAction SilentlyContinue)){
    
    Write-Host "Python not found. Installing..."
    
    try{
        Invoke-DownloadFileWithProgress -Url $pythonInstaller -Destination $pythonInstallerPath
    }catch{
        Write-Error "Download failed: $_"; exit 1
    }

    if(-not (Test-Path $pythonInstallerPath)){
        Write-Error "Installer missing at $pythonInstallerPath"; exit 1
    }

    try{
        Start-Process -FilePath $pythonInstallerPath -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1" -Wait -Verb RunAs
    }catch{
        Write-Error "Python install failed: $_"; exit 1
    }

    if(-not (Get-Command python -ErrorAction SilentlyContinue)){
        Write-Error "Python still unavailable after install"; exit 1
    }

    Remove-Item -Path $pythonInstallerPath -Force -ErrorAction SilentlyContinue
}else{
    Write-Host "Python is already installed."
}

#----------------------------------------
# 3) Install pip if missing
#----------------------------------------
if(-not (Get-Command pip -ErrorAction SilentlyContinue)){
    
    Write-Host "pip not found. Installing..."
    
    try{
        Invoke-DownloadFileWithProgress -Url $getPipUrl -Destination $getPipPath
    }catch{
        Write-Error "Failed to download get-pip.py: $_"; exit 1
    }

    if(-not (Test-Path $getPipPath)){
        Write-Error "get-pip.py missing at $getPipPath"; exit 1
    }

    try{
        python $getPipPath
    }catch{
        Write-Error "pip installation failed: $_"; exit 1
    }

    # Install project requirements if present
    $scriptDir   = Split-Path -Parent $MyInvocation.MyCommand.Path
    $projectRoot = Resolve-Path "$scriptDir\.."
    
    if(Test-Path "$projectRoot\requirements.txt"){
        pip install "$projectRoot\requirements.txt"
    }

    Remove-Item -Path $getPipPath -Force -ErrorAction SilentlyContinue
}else{
    Write-Host "pip is already installed."
}

#----------------------------------------
# 4) Install 7-Zip if missing
#----------------------------------------
if(-not (Test-Path $sevenZipExePath)){
    
    Write-Host "7-Zip not found. Installing..."
    
    try{
        Invoke-DownloadFileWithProgress -Url $sevenZipInstaller -Destination $sevenZipInstallerPath
    }catch{
        Write-Error "Failed to download 7-Zip installer: $_"; exit 1
    }

    if(-not (Test-Path $sevenZipInstallerPath)){
        Write-Error "Installer missing at $sevenZipInstallerPath"; exit 1
    }

    try{
        Start-Process -FilePath $sevenZipInstallerPath -ArgumentList "/S" -Wait -Verb RunAs
    }catch{
        Write-Error "7-Zip install failed: $_"; exit 1
    }

    if(-not (Test-Path $sevenZipExePath)){
        Write-Error "7z.exe not found in $sevenZipInstallDir"; exit 1
    }

    if(-not $env:Path.Contains($sevenZipInstallDir)){
        $env:Path += ";$sevenZipInstallDir"
    }

    Remove-Item -Path $sevenZipInstallerPath -Force -ErrorAction SilentlyContinue
}else{
    Write-Host "7-Zip is already installed."
}

#----------------------------------------
# 5) Install / Extract FFmpeg if missing
#----------------------------------------
if(-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)){
    
    Write-Host "FFmpeg not found. Installing..."
    
    try{
        Invoke-DownloadFileWithProgress -Url $ffmpegInstaller -Destination $ffmpegInstallerPath
    }catch{
        Write-Error "Failed to download FFmpeg: $_"; exit 1
    }

    if(-not (Test-Path $ffmpegInstallerPath)){
        Write-Error "FFmpeg archive missing at $ffmpegInstallerPath"; exit 1
    }

    try {
        & $sevenZipExePath x $ffmpegInstallerPath -o"$env:ProgramFiles\ffmpeg" -y
    }catch{
        Write-Error "FFmpeg extraction failed: $_"; exit 1
    }

    #get the path to ffmpeg.exe including the version
    $ffmpegPath = Get-ChildItem -Path "$env:ProgramFiles\ffmpeg\" -Filter "ffmpeg.exe" -Recurse | Select-Object -First 1
    
    if($ffmpegPath){
        $env:Path += ";$($ffmpegPath.DirectoryName)"
        Write-Host "FFmpeg installed to $($ffmpegPath.DirectoryName)"
    }else{
        Write-Error "ffmpeg.exe not found in extracted files"; exit 1
    }

    Remove-Item -Path $ffmpegInstallerPath -Force -ErrorAction SilentlyContinue

    #add ffmpeg to the PATH if not already present
    if(-not $env:Path.Contains($ffmpegPath.DirectoryName)){
        $env:Path += ";$($ffmpegPath.DirectoryName)"
        Write-Host "FFmpeg path added to environment variables."
    }else{
        Write-Host "FFmpeg path already exists in environment variables."
    }
}else{
    Write-Host "FFmpeg is already installed."
}

Read-Host -Prompt "Game environment configured successfully. Press Enter to continue..."