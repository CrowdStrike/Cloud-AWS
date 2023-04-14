
[CmdletBinding()]
param()

Write-Output 'Uninstalling Falcon Sensor...'

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
$uninstallArgs = '/uninstall /quiet'

# Starts the uninstall process and waits for it to complete
$uninstallProcess = Start-Process -FilePath $uninstallString -ArgumentList $uninstallArgs -PassThru -Wait

# Checks the exit code of the uninstall process and throws an exception if it is not 0
if ($uninstallProcess.ExitCode -ne 0) {
  throw "Uninstaller returned exit code $($UninstallerProcess.ExitCode)"
}

# Retrieves the status of the CSAgent service and throws an exception if it is still running after the uninstall
$agentService = Get-Service -Name CSAgent -ErrorAction SilentlyContinue
if ($agentService -and $agentService.Status -eq 'Running') {
  throw 'Service uninstall failed...'
}

# Checks if the CrowdStrike registry key was successfully removed and throws an exception if it still exists
if (Test-Path -Path HKLM:\System\Crowdstrike) {
  throw 'Registry key removal failed...'
}

# Checks if the CrowdStrike driver was successfully removed and throws an exception if it still exists
if (Test-Path -Path "${env:SYSTEMROOT}\System32\drivers\CrowdStrike") {
  throw 'Driver removal failed...'
}

Write-Output 'Successfully finished uninstall...'
