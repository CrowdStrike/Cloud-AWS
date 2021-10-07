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
to complete.
.PARAMETER BaseAddress
CrowdStrike Falcon OAuth2 API Hostname [Required]
.PARAMETER ClientId
CrowdStrike Falcon OAuth2 API Client Id [Required]
.PARAMETER ClientSecret
CrowdStrike Falcon OAuth2 API Client Secret [Required]
.PARAMETER MemberCid
Member CID, used only in multi-CID ("Falcon Flight Control") configurations
.PARAMETER PolicyName
Policy name to check for assigned sensor version [default: 'platform_default']
.PARAMETER InstallParams
Sensor installation parameters, without your CID value [default: '/install /quiet /noreboot']
.PARAMETER LogPath
Script log location [default: undefined, which uses 'Windows\Temp\InstallFalcon.log']
.PARAMETER DeleteInstaller
Delete sensor installer package when complete [default: $true]
.PARAMETER DeleteScript
Delete script when complete [default: $true]
.EXAMPLE
PS>.\sensor_install.ps1 -Hostname <string> -ClientId <string> -ClientSecret <string>

Run the script and define 'Hostname', 'ClientId' and 'ClientSecret' during runtime. All other
parameters will use their default values.
.EXAMPLE
PS>.\sensor_install.ps1

Run the script and use all values that were previously defined within the script.
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
    [string] $PolicyName = 'platform_default',

    [Parameter(Position = 6)]
    [string] $InstallParams = '/install /quiet /noreboot',

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
        build_version = '"(?<name>build)": "(?<version>.+)",'
        ccid          = '(?<ccid>\w{32}-\w{2})'
        policy_id     = '"(?<name>id)": "(?<id>\w{32})",'
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
        @('ClientId', 'ClientSecret') | ForEach-Object {
            if (!(Get-Variable $_).Value) {
                $Message = "Missing '$((Get-Variable $_).Name)'"
                Write-FalconLog 'CheckClient' $Message
                throw $Message
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
    if ($Response -match $Patterns.build_version) {
        $PolicyId = [regex]::Matches($Response, $Patterns.policy_id)[0].Groups['id'].Value
        $Version = [regex]::Matches($Response, $Patterns.build_version)[0].Groups['version'].Value
        $MinorVersion = ($Version).Split('\|')[0]
        if ($Version) {
            Write-FalconLog 'GetVersion' "'$PolicyId' has build '$Version' assigned"
        } else {
            $Message = "Failed to determine build version for '$PolicyId'"
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
        $Installer = '{\n.*"name": "(?<filename>\w+\.exe)",(\n.*){1,}"sha256": "(?<hash>\w{64})",(\n.*){1,}' +
        '"version": "\d{1,}?\.\d{1,}\.' + $MinorVersion + '",(\n.*){1,}\},'
        if ($Response -match $Installer) {
            $CloudHash = [regex]::Matches($Response, $Installer)[0].Groups['hash'].Value
            $CloudFile = [regex]::Matches($Response, $Installer)[0].Groups['filename'].Value
            Write-FalconLog 'GetInstaller' "Matched installer '$CloudHash' ($CloudFile)"
        } else {
            $Message = "Unable to match installer from list using build '$MinorVersion'"
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
