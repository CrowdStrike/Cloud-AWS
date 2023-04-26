
[CmdletBinding()]
param()

Write-Output 'Uninstalling Falcon Sensor...'

# Configures the TLS version to use for secure connections
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$agentService = Get-Service -Name CSAgent -ErrorAction SilentlyContinue
if (-not $agentService) {
  Write-Output 'CSAgent service not installed...'
  Exit 0
}

# Retrieves the package for the CrowdStrike Windows Sensor using PowerShell's Get-Package cmdlet
$package = Get-Package -Name 'CrowdStrike Windows Sensor'

# Retrieves the path to the uninstall executable from the package metadata
$uninstallString = $package.Metadata['BundleCachePath']

# Sets up the arguments to be passed to the uninstall executable
$uninstallArgs = '/uninstall /quiet' + $env:UNINSTALLPARAMS

if ($env:MAINTENANCE_TOKEN) {
    $uninstallArgs += ' MAINTENANCE_TOKEN=' + $env:MAINTENANCE_TOKEN
}

# Starts the uninstall process and waits for it to complete
Write-Output "Uninstalling with arguments: $uninstallArgs"
$uninstallProcess = Start-Process -FilePath $uninstallString -ArgumentList $uninstallArgs -PassThru -Wait

# Checks the exit code of the uninstall process and throws an exception if it is not 0
if ($uninstallProcess.ExitCode -ne 0) {
  Write-Output "Failed to uninstall with exit code: $($uninstallProcess.ExitCode)"
  exit 1
}

# Retrieves the status of the CSAgent service and throws an exception if it is still running after the uninstall
$agentService = Get-Service -Name CSAgent -ErrorAction SilentlyContinue
if ($agentService -and $agentService.Status -eq 'Running') {
  Write-Output 'Uninstall process completed, but CSAgent service is still running. Uninstall failed for unknown reason...'
  exit 1 
}

# Checks if the CrowdStrike registry key was successfully removed and throws an exception if it still exists
if (Test-Path -Path HKLM:\System\Crowdstrike) {
  Write-Output "CrowdStrike registry key still exists. Uninstall failed."
  exit 1
}

# Checks if the CrowdStrike driver was successfully removed and throws an exception if it still exists
if (Test-Path -Path "${env:SYSTEMROOT}\System32\drivers\CrowdStrike") {
  Write-Output "CrowdStrike driver still exists. Uninstall failed."
  exit 1
}

Write-Output 'Successfully finished uninstall...'
