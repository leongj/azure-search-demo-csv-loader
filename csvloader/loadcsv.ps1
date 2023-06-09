
# Test that the csvloader folder exists as a subdirectory
if (-not (Test-Path -Path "./csvloader")) {
  Write-Host "Error: ./csvloader folder not found.`n NOTE: You need to be in the parent folder and run ./csvloader/loadcsv.ps1"
  exit 1
}

Write-Host ""
Write-Host "Loading azd .env file from current environment"
Write-Host ""

$output = azd env get-values

foreach ($line in $output) {
  if (!$line.Contains('=')) {
    continue
  }

  $name, $value = $line.Split("=")
  $value = $value -replace '^\"|\"$'
  [Environment]::SetEnvironmentVariable($name, $value)
}

Write-Host "Environment variables set."

$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
  # fallback to python3 if python not found
  $pythonCmd = Get-Command python3 -ErrorAction SilentlyContinue
}

Write-Host 'Creating python virtual environment "csvloader/.venv"'
Start-Process -FilePath ($pythonCmd).Source -ArgumentList "-m venv ./csvloader/.venv" -Wait -NoNewWindow

$venvPythonPath = "./csvloader/.venv/scripts/python.exe"
if (Test-Path -Path "/usr") {
  # fallback to Linux venv path
  $venvPythonPath = "./csvloader/.venv/bin/python"
}

Write-Host 'Installing dependencies from "requirements.txt" into virtual environment'
Start-Process -FilePath $venvPythonPath -ArgumentList "-m pip install -r ./csvloader/requirements.txt" -Wait -NoNewWindow

Write-Host 'Running "loadcsv.py"'
$cwd = (Get-Location)
Start-Process -FilePath $venvPythonPath -ArgumentList "./csvloader/loadcsv.py $cwd/csvloader/*.csv --storageaccount $env:AZURE_STORAGE_ACCOUNT --container $env:AZURE_STORAGE_CONTAINER --searchservice $env:AZURE_SEARCH_SERVICE --index $env:AZURE_SEARCH_INDEX --tenantid $env:AZURE_TENANT_ID $(if ($args.Contains('--deleteindex')) {'--deleteindex'}) -v" -Wait -NoNewWindow
