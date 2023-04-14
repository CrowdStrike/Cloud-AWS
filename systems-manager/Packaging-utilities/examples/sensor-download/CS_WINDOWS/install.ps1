[CmdletBinding()]
param()

Write-Output 'Installing Falcon Sensor...'

# Configures the TLS version to use for secure connections
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 

$agentService = Get-Service -Name CSAgent -ErrorAction SilentlyContinue

if ($agentService) {
  Write-Output 'CSAgent service already installed...'
  Exit 0
}

# If the SSM_CS_HOST environment variable does not begin with 'https://', prepends it
if (!$env:SSM_CS_HOST.StartsWith('https://')) {
  $env:SSM_CS_HOST = 'https://' + $env:SSM_CS_HOST
}

# Removes any trailing slashes from the SSM_CS_HOST environment variable
if ($env:SSM_CS_HOST.EndsWith('/')) {
  $env:SSM_CS_HOST = $env:SSM_CS_HOST.TrimEnd('/')
}

# Sends a GET request to the CrowdStrike API to retrieve the latest installer information
$installerQueryResp = Invoke-RestMethod -Method Get -Uri "${env:SSM_CS_HOST}/sensors/combined/installers/v1?offset=1&limit=1&sort=version&filter=platform:'windows'" -Headers @{'Authorization' = "Bearer ${env:SSM_CS_AUTH_TOKEN}" } -ErrorAction Stop

# If the API response does not contain a valid sha256 value, throws an exception
if (!$installerQueryResp.resources[0].sha256) {
  throw 'API response does not contain a valid sha256 value'
}

# Extracts the sha256 hash and name of the installer from the API response
$installerSha256 = $installerQueryResp.resources[0].sha256
$installerName = $installerQueryResp.resources[0].name

# Constructs the URL to download the installer
$downloadUrl = "${env:SSM_CS_HOST}/sensors/entities/download-installer/v1?id=$installerSha256"

# Constructs the full path to save the installer to
$installerPath = Join-Path -Path $PSScriptRoot -ChildPath $installerName

# Downloads the installer and saves it to the specified path
$downloadSensorResp = Invoke-WebRequest -Uri $downloadUrl -OutFile $installerPath -Headers @{'Authorization' = "Bearer ${env:SSM_CS_AUTH_TOKEN}" } -ErrorAction Stop

# If the installer fails to download, throws an exception
if (-not (Test-Path -Path $installerPath)) {
  throw "Failed to download the file. Error $(ConvertTo-Json $downloadSensorResp -Depth 10)"
}

# If the SSM_CS_CCID environment variable is not set, throws an exception
if (-not $env:SSM_CS_CCID) {
  throw "Missing required param $($env:SSM_CS_CCID). Ensure the target instance is running the latest SSM agent version"
}

Write-Host "Installer downloaded to: $installerPath"

# Constructs the arguments to pass to the installer executable
$installArguments = @(
  , '/install'
  , '/quiet'
  , '/norestart'
  , "CID=${env:SSM_CS_CCID}"
  , 'ProvWaitTime=1200000'
)

# If the SSM_CS_INSTALLTOKEN environment variable is set, include it in the installer arguments
if ($env:SSM_CS_INSTALLTOKEN) {
  $installArguments += "ProvToken=${env:SSM_CS_INSTALLTOKEN}"
}

# If the SsmCsInstallParams environment is set, include it in the installer arguments
$space = ' '
if ($env:SsmCsInstallParams) {
  $installArguments += $env:SsmCsInstallParams.Split($space)
}

Write-Output 'Running installer...'
$installerProcess = Start-Process -FilePath $installerPath -ArgumentList $installArguments -PassThru -Wait

# If the installer process returns a non-zero exit code, throws an exception
if ($installerProcess.ExitCode -ne 0) {
  throw "Installer returned exit code $($installerProcess.ExitCode)"
}

# Verify teh CSAgent service is running
$agentService = Get-Service -Name CSAgent -ErrorAction SilentlyContinue
if (-not $agentService) {
  throw 'Installer completed, but CSAgent service is missing...'
}
elseif ($agentService.Status -eq 'Running') {
  Write-Output 'CSAgent service running...'
}
else {
  throw 'Installer completed, but CSAgent service is not running...'
}

Write-Output 'Successfully completed installation...'
