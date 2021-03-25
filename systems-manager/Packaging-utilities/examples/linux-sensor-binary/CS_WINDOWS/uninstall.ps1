<#
.SYNOPSIS
    Uninstalls CrowdStrike Falcon
#>
[CmdletBinding()]
param()
Write-Output 'Uninstalling Falcon Sensor...'

$UninstallerName = 'CsUninstallTool.exe'
$UninstallerPath = Join-Path -Path $PSScriptRoot -ChildPath $UninstallerName

if (-not (Test-Path -Path $UninstallerPath))
{
    throw "${UninstallerName} not found."
}

$UninstallerArguments = @(
    , '/quiet'
)

Write-Output 'Running uninstall command...'

$UninstallerProcess = Start-Process -FilePath $UninstallerPath -ArgumentList $UninstallerArguments -PassThru -Wait

if ($UninstallerProcess.ExitCode -ne 0)
{
    throw "Uninstaller returned exit code $($UninstallerProcess.ExitCode)"
}

$AgentService = Get-Service -Name CSAgent -ErrorAction SilentlyContinue
if ($AgentService -and $AgentService.Status -eq 'Running')
{
    throw 'Service uninstall failed...'
}

if (Test-Path -Path HKLM:\System\Crowdstrike)
{
    throw 'Registry key removal failed...'
}

if (Test-Path -Path"${env:SYSTEMROOT}\System32\drivers\CrowdStrike")
{
    throw 'Driver removal failed...'
}

Write-Output 'Successfully finished uninstall...'
