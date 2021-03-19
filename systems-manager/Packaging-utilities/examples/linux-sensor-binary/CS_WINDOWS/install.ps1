<#
.SYNOPSIS
    Installs CrowdStrike Falcon
#>
[CmdletBinding()]
param()
Write-Output 'Installing Falcon Sensor...'

$InstallerName = 'WindowsSensor.exe'
$InstallerPath = Join-Path -Path $PSScriptRoot -ChildPath $InstallerName

if (-not (Test-Path -Path $InstallerPath))
{
    throw "${InstallerName} not found."
}

if (-not $env:SSM_CS_CCID)
{
    throw 'Missing required param SSM_CS_CCID. Ensure the target instance is running the latest SSM agent version'
}

$InstallArguments = @(
    , '/install'
    , '/quiet'
    , '/norestart'
    , "CID=${env:SSM_CS_CCID}"
    , 'ProvWaitTime=1200000'
)

if ($env:SSM_CS_INSTALLTOKEN)
{
    $InstallArguments += "ProvToken=${env:SSM_CS_INSTALLTOKEN}"
}

$Space = ' '
if ($env:SSM_CS_INSTALLPARAMS)
{
    $InstallArguments += $env:SSM_CS_INSTALLPARAMS.Split($Space)
}

Write-Output 'Running installer...'
$InstallerProcess = Start-Process -FilePath $InstallerPath -ArgumentList $InstallArguments -PassThru -Wait

if ($InstallerProcess.ExitCode -ne 0)
{
    throw "Installer returned exit code $($InstallerProcess.ExitCode)"
}

$AgentService = Get-Service -Name CSAgent -ErrorAction SilentlyContinue
if (-not $AgentService)
{
    throw 'Installer completed, but CSAgent service is missing...'
}
elseif ($AgentService.Status -eq 'Running')
{
    Write-Output 'CSAgent service running...'
}
else
{
    throw 'Installer completed, but CSAgent service is not running...'
}

Write-Output 'Successfully completed installation...'
