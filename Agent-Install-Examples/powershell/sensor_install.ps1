#Requires -Version 2.0
<#
.SYNOPSIS
Download and install the CrowdStrike Falcon Sensor for Windows
.DESCRIPTION
Uses the CrowdStrike Falcon APIs to check the sensor version assigned to a Windows Sensor Update policy,
downloads that version, then installs it on the local machine. By default, once complete, the script
deletes itself and the downloaded installer package. The individual steps and any related error messages
are logged to 'Windows\Temp\InstallFalcon.log' unless otherwise specified.

Script options can be passed as parameters or defined in the param() block. Default values are listed in
the parameter descriptions.

The script must be run as an administrator on the local machine in order for the Falcon Sensor installation
to complete, and the OAuth2 API Client being used requires 'sensor-update-policies:read' and
'sensor-installers:read' permissions.
.PARAMETER BaseAddress
CrowdStrike Falcon OAuth2 API Hostname [Required]
.PARAMETER ClientId
CrowdStrike Falcon OAuth2 API Client Id [Required]
.PARAMETER ClientSecret
CrowdStrike Falcon OAuth2 API Client Secret [Required]
.PARAMETER MemberCid
Member CID, used only in multi-CID ("Falcon Flight Control") configurations
.PARAMETER PolicyName
Policy name to check for assigned sensor version ['platform_default' if left undefined]
.PARAMETER InstallParams
Sensor installation parameters, without your CID value ['/install /quiet /noreboot' if left undefined]
.PARAMETER LogPath
Script log location ['Windows\Temp\InstallFalcon.log' if left undefined]
.PARAMETER DeleteInstaller
Delete sensor installer package when complete [default: $true]
.PARAMETER DeleteScript
Delete script when complete [default: $true]
.EXAMPLE
PS>.\sensor_install.ps1 -BaseAddress <string> -ClientId <string> -ClientSecret <string>

Run the script and define 'BaseAddress', 'ClientId' and 'ClientSecret' during runtime. All other
parameters will use their default values.
.EXAMPLE
PS>.\sensor_install.ps1

Run the script and use all values that were previously defined within the script.
.NOTES
Updated 2021-10-22 to include 'sensor_version' property when matching policy to sensor installer package.
#>
[CmdletBinding()]
param(
    [Parameter(Position = 1)]
    [ValidateSet('https://api.crowdstrike.com', 'https://api.us-2.crowdstrike.com',
        'https://api.eu-1.crowdstrike.com', 'https://api.laggar.gcw.crowdstrike.com')]
    [string] $BaseAddress,
 
    [Parameter(Position = 2)]
    [ValidatePattern('\w{32}')]
    [string] $ClientId,

    [Parameter(Position = 3)]
    [ValidatePattern('\w{40}')]
    [string] $ClientSecret,

    [Parameter(Position = 4)]
    [ValidatePattern('\w{32}')]
    [string] $MemberCid,

    [Parameter(Position = 5)]
    [string] $PolicyName,

    [Parameter(Position = 6)]
    [string] $InstallParams,

    [Parameter(Position = 7)]
    [string] $LogPath,

    [Parameter(Position = 8)]
    [string] $DeleteInstaller = $true,

    [Parameter(Position = 9)]
    [string] $DeleteScript = $true
)
begin {
    $ScriptName = $MyInvocation.MyCommand.Name
    $ScriptPath = if (!$PSScriptRoot) {
        Split-Path -Parent -Path $MyInvocation.MyCommand.Definition
    } else {
        $PSScriptRoot
    }
    $WinSystem = [Environment]::GetFolderPath('System')
    $WinTemp = $WinSystem -replace 'system32','Temp'
    if (!$LogPath) {
        $LogPath = Join-Path -Path $WinTemp -ChildPath 'InstallFalcon.log'
    }
    $Falcon = New-Object System.Net.WebClient
    $Falcon.Encoding = [System.Text.Encoding]::UTF8
    $Falcon.BaseAddress = $BaseAddress
    $Patterns = @{
        access_token  = '"(?<name>access_token)": "(?<access_token>.*)",'
        build         = '"(?<name>build)": "(?<version>.+)",'
        ccid          = '(?<ccid>\w{32}-\w{2})'
        major_minor   = '"(?<name>sensor_version)": "(?<version>\d{1,}\.\d{1,})\.\d+",'
        policy_id     = '"(?<name>id)": "(?<id>\w{32})",'
        version       = '"(?<name>sensor_version)": "(?<version>.+)",'
    }
    function Get-InstallerHash ([string] $Path) {
        $Output = if (Test-Path $Path) {
            $Algorithm = [System.Security.Cryptography.HashAlgorithm]::Create("SHA256")
            $Hash = [System.BitConverter]::ToString(
                $Algorithm.ComputeHash([System.IO.File]::ReadAllBytes($Path)))
            if ($Hash) {
                $Hash.Replace('-','')
            } else {
                $null
            }
        }
        return $Output
    }
    function Invoke-FalconAuth ([string] $String) {
        $Falcon.Headers.Add('Accept', 'application/json')
        $Falcon.Headers.Add('Content-Type', 'application/x-www-form-urlencoded')
        $Response = $Falcon.UploadString('/oauth2/token', $String)
        if ($Response -match $Patterns.access_token) {
            $AccessToken = [regex]::Matches($Response, $Patterns.access_token)[0].Groups['access_token'].Value
            $Falcon.Headers.Add('Authorization', "bearer $AccessToken")
        }
        $Falcon.Headers.Remove('Content-Type')
    }
    function Invoke-FalconDownload ([string] $Path, [string] $Outfile) {
        $Falcon.Headers.Add('Accept', 'application/octet-stream')
        $Falcon.DownloadFile($Path, $Outfile)
    }
    function Invoke-FalconGet ([string] $Path) {
        $Falcon.Headers.Add('Accept', 'application/json')
        $Request = $Falcon.OpenRead($Path)
        $Stream = New-Object System.IO.StreamReader $Request
        $Output = $Stream.ReadToEnd()
        @($Request, $Stream) | ForEach-Object {
            if ($null -ne $_) {
                $_.Dispose()
            }
        }
        return $Output
    }
    function Write-FalconLog ([string] $Source, [string] $Message) {
        $Content = @(Get-Date -Format 'yyyy-MM-dd hh:MM:ss')
        if ($Source -notmatch '^(StartProcess|Delete(Installer|Script))$' -and
        $Falcon.ResponseHeaders.Keys -contains 'X-Cs-TraceId') {
            $Content += ,"[$($Falcon.ResponseHeaders.Get('X-Cs-TraceId'))]"
        }
        "$(@($Content + $Source) -join ' '): $Message" >> $LogPath
    }
    if (!$PolicyName) {
        $PolicyName = 'platform_default'
    }
    if (!$InstallParams) {
        $InstallParams = '/install /quiet /noreboot'
    }
}
process {
    if (([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator) -eq $false) {
        $Message = 'Unable to proceed without administrative privileges'
        Write-FalconLog 'CheckAdmin' $Message
        throw $Message
    } elseif (Get-Service | Where-Object { $_.Name -eq 'CSFalconService' }) {
        $Message = "'CSFalconService' running"
        Write-FalconLog 'CheckService' $Message
        throw $Message
    } else {
        @($BaseAddress, $ClientId, $ClientSecret).foreach{
            if (!$_) {
                throw "Missing 'BaseAddress', 'ClientId' or 'ClientSecret'"
            }
        }
        if ([Net.ServicePointManager]::SecurityProtocol -notmatch 'Tls12') {
            try {
                [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
            } catch {
                $Message = $_
                Write-FalconLog 'TlsCheck' $Message
                throw $Message
            }
        }
        if (!($PSVersionTable.CLRVersion.ToString() -ge 3.5)) {
            $Message = '.NET Framework 3.5 or newer is required'
            Write-FalconLog 'NetCheck' $Message
            throw $Message
        }
    }
    $ApiClient = "client_id=$ClientId&client_secret=$ClientSecret"
    if ($MemberCid) {
        $ApiClient += "&member_cid=$MemberCid"
    }
    Invoke-FalconAuth $ApiClient
    if ($Falcon.Headers.Keys -contains 'Authorization') {
        Write-FalconLog 'GetAuth' "ClientId: $($ClientId), BaseAddress: $($Falcon.BaseAddress)"
    } else {
        $Message = 'Failed to retrieve authorization token'
        Write-FalconLog 'GetAuth' $Message
        throw $Message
    }
    $Response = Invoke-FalconGet '/sensors/queries/installers/ccid/v1'
    if ($Response -match $Patterns.ccid) {
        $Ccid = [regex]::Matches($Response, $Patterns.ccid)[0].Groups['ccid'].Value
        Write-FalconLog 'GetCcid' 'Retrieved CCID'
        $InstallParams += " CID=$Ccid"
    } else {
        $Message = 'Failed to retrieve CCID'
        Write-FalconLog 'GetCcid' $Message
        throw $Message
    }
    $Response = Invoke-FalconGet ("/policy/combined/sensor-update/v2?filter=platform_name:" +
        "'Windows'%2Bname:'$($PolicyName.ToLower())'")
    $PolicyId = if ($Response -match $Patterns.policy_id) {
        [regex]::Matches($Response, $Patterns.policy_id)[0].Groups['id'].Value
    }
    if ($Response -match $Patterns.build -or $Response -match $Patterns.version) {
        $Build = [regex]::Matches($Response, $Patterns.build)[0].Groups['version'].Value
        $Version = [regex]::Matches($Response, $Patterns.version)[0].Groups['version'].Value
        $MajorMinor = if ($Version) {
            [regex]::Matches($Response, $Patterns.major_minor)[0].Groups['version'].Value
        }
        $Patch = if ($Build) {
            ($Build).Split('|')[0]
        } elseif ($Version) {
            ($Version).Split('.')[-1]
        }
        if ($Patch) {
            Write-FalconLog 'GetVersion' "Policy '$PolicyId' has build '$Patch' assigned"
        } else {
            $Message = "Failed to determine sensor version for policy '$PolicyId'"
            Write-FalconLog 'GetVersion' $Message
            throw $Message
        }
    } else {
        $Message = "Failed to match policy name '$($PolicyName.ToLower())'"
        Write-FalconLog 'GetPolicy' $Message
        throw $Message
    }
    $Response = Invoke-FalconGet "/sensors/combined/installers/v1?filter=platform:'windows'"
    if ($Response) {
        $BuildMatch = '\d{1,}?\.\d{1,}\.' + $Patch
        if ($MajorMinor) {
            $BuildMatch = "($BuildMatch|$([regex]::Escape($MajorMinor))\.\d+)"
        }
        $Installer = '"name": "(?<filename>(\w+\.){1,}?exe)",\n\s+"description": "(.*)?Falcon(.*)",(\n.*){1,}"sh' +
            'a256": "(?<hash>\w{64})",(\n.*){1,}"version": "' + $BuildMatch + '"'
        $Match = $Response.Split('}') | Where-Object { $_ -match $Installer }
        if ($Match) {
            $CloudHash = [regex]::Matches($Match, $Installer)[0].Groups['hash'].Value
            $CloudFile = [regex]::Matches($Match, $Installer)[0].Groups['filename'].Value
            Write-FalconLog 'GetInstaller' "Matched installer '$CloudHash' ($CloudFile)"
        } else {
            $MatchValue = "'$Patch'"
            if ($MajorMinor) {
                $MatchValue += " or '$MajorMinor'"
            }
            $Message = "Unable to match installer using $MatchValue"
            Write-FalconLog 'GetInstaller' $Message
            throw $Message
        }
    } else {
        $Message = 'Failed to retrieve available installer list'
        Write-FalconLog 'GetInstaller' $Message
        throw $Message
    }
    $LocalHash = if ($CloudHash -and $CloudFile) {
        $LocalFile = Join-Path -Path $WinTemp -ChildPath $CloudFile
        Invoke-FalconDownload "/sensors/entities/download-installer/v1?id=$CloudHash" $LocalFile
        if (Test-Path $LocalFile) {
            Get-InstallerHash $LocalFile
            Write-FalconLog 'DownloadFile' "Created '$LocalFile'"
        }
    }
    if ($CloudHash -ne $LocalHash) {
        $Message = "Hash mismatch on download (Local: $LocalHash, Cloud: $CloudHash)"
        Write-FalconLog 'CheckHash' $Message
        throw $Message
    }
    $InstallPid = (Start-Process -FilePath $LocalFile -ArgumentList $InstallParams -PassThru).id
    Write-FalconLog 'StartProcess' "Started '$LocalFile' ($InstallPid)"
    @('DeleteInstaller', 'DeleteScript') | ForEach-Object {
        if ((Get-Variable $_).Value -eq $true) {
            if ($_ -eq 'DeleteInstaller') {
                Wait-Process -Id $InstallPid
            }
            $FilePath = if ($_ -eq 'DeleteInstaller') {
                $LocalFile
            } else {
                Join-Path -Path $ScriptPath -ChildPath $ScriptName
            }
            Remove-Item -Path $FilePath -Force
            if (Test-Path $FilePath) {
                Write-FalconLog $_ "Failed to delete '$FilePath'"
            } else {
                Write-FalconLog $_ "Deleted '$FilePath'"
            }
        }
    }
}
