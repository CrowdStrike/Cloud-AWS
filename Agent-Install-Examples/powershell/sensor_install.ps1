#Requires -Version 5.1
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('\w{32}')]
    [string] $ClientId,
    [Parameter(Mandatory = $true)]
    [ValidatePattern('\w{40}')]
    [string] $ClientSecret
)
begin {
    <# USER CONFIG ###############################################################################################>
    # OAuth2 Client with 'sensor-update-policies:read' and 'sensor-installers:read' permissions
    [string] $ApiHost = 'https://api.crowdstrike.com'

    # Member CID, input when installing the sensor in a parent/child CID configuration [default: $null]
    [string] $MemberCID = $null

    # Policy name to check for sensor version to install [default: $null, which uses 'platform_default']
    [string] $PolicyName = $null

    # Installer parameters to include beyond "/install /quiet /noreboot CID=" [default: $null]
    [string] $InstallParams = $null

    # Custom log file path and filename [default: $null, which uses Windows\Temp\InstallFalcon.log]
    [string] $LogLocation = $null

    # Delete sensor installer after installation attempt [default: $true]
    [boolean] $DeleteInstaller = $true

    # Delete this script after installation attempt [default: $true]
    [boolean] $DeleteScript = $true
    <############################################################################################### USER CONFIG #>
    class ApiClient {
        [string] $Hostname
        [string] $ClientId
        [string] $ClientSecret
        [string] $MemberCid
        [string] $Token
        [string] $LogLocation
        [datetime] $Expires
        ApiClient ([object] $ClientParam) {
            @('Hostname', 'ClientId', 'ClientSecret', 'MemberCid', 'LogLocation').foreach{
                if ($ClientParam.$_) {
                    $this.$_ = $ClientParam.$_
                }
            }
        }
        [void] Auth() {
            if (!$this.Token -or ($this.Expires -le (Get-Date).AddSeconds(30))) {
                # Request access token
                $Param = @{
                    Uri    = '/oauth2/token'
                    Method  = 'post'
                    Headers = @{
                        Accept      = 'application/json'
                        ContentType = 'application/x-www-form-urlencoded'
                    }
                    Body = "client_id=$($this.ClientId)&client_secret=$($this.ClientSecret)"
                }
                if ($this.MemberCid) {
                    $Param.Body += "&member_cid=$($this.MemberCid)"
                }
                $Request = $this.Invoke($Param)
                if ($Request.access_token) {
                    # Cache token and expiration time
                    $this.Expires = (Get-Date).AddSeconds($Request.expires_in)
                    $this.Token = "$($Request.token_type) $($Request.access_token)"
                    $this.Log('ApiClient.Auth', "Token granted; expires $($this.Expires)")
                } else {
                    # Clear credentials
                    @('ClientId', 'ClientSecret', 'Hostname', 'MemberCid').foreach{
                        if ($this.$_) {
                            $this.$_ = $null
                        }
                    }
                }
            }
        }
        [string] FullPath([string] $Path) {
            # Convert relative file path to absolute file path
            $Output = if (![IO.Path]::IsPathRooted($Path)) {
                $Absolute = Join-Path -Path (Get-Location).Path -ChildPath $Path
                $Absolute = Join-Path -Path $Absolute -ChildPath '.'
                [IO.Path]::GetFullPath($Absolute)
            } else {
                $Path
            }
            return $Output
        }
        [object] Invoke([object] $Param) {
            if ($Param.Uri -ne '/oauth2/token') {
                # Verify OAuth2 access token
                $this.Auth()
                if ($this.Token) {
                    # Add authorization token
                    $Param.Headers.Add('Authorization', $this.Token)
                }
            }
            # Set URI using Hostname and Param.Path
            $Param.Uri = "$($this.Hostname)$($Param.Uri)"
            $this.Log('ApiClient.Invoke', "$($Param.Method.ToUpper()) $($Param.Uri)")
            $Output = try {
                if ($Param.Body) {
                    if ($Param.Headers.ContentType -eq 'application/json') {
                        # Convert body to Json
                        $Param.Body = ConvertTo-Json $Param.Body
                    }
                }
                # Make request and output result
                $Response = Invoke-WebRequest @Param -UseBasicParsing
                if ($Response.Content -and ($Param.Headers.Accept -eq 'application/json')) {
                    ConvertFrom-Json -InputObject $Response.Content
                } elseif ($Response.Content) {
                    $Response.Content
                } elseif ($Response.StatusCode -and $Response.StatusDescription) {
                    Write-Error "$($Response.StatusCode): $($Response.StatusDescription)"
                } else {
                    $null
                }
            } catch {
                $this.Log('ApiClient.Invoke', "$_")
                throw $_
            } finally {
                $this.WaitRetry($Response)
                # if ($Response) {
                #     $Response.Dispose()
                # }
            }
            return $Output
        }
        [void] Log([string] $Source, [string] $Message) {
            "$(Get-Date -Format 'yyyy-MM-dd hh:MM:ss') [$Source] $Message" >> $this.LogLocation
        }
        [void] WaitRetry([object] $Response) {
            if ($Response.Headers.Keys -contains 'X-Ratelimit-RetryAfter') {
                # Sleep until 'X-Ratelimit-RetryAfter'
                $RetryAfter = $Response.Headers.GetEnumerator().Where({
                    $_.Key -eq 'X-Ratelimit-RetryAfter' }).Value
                $WaitTime = $RetryAfter - ([int] (Get-Date -UFormat %s) + 1)
                $this.Log('ApiClient.WaitRetry', "Rate limited; waiting $WaitTime seconds")
                Start-Sleep -Seconds $WaitTime
            }
        }
    }
    if (!$LogLocation) {
        # Set default log location
        $LogLocation = Join-Path -Path ([Environment]::GetFolderPath('Windows')) -ChildPath (
            'Temp\InstallFalcon.log')
    }
    if ($DeleteInstaller -eq $true) {
        # Capture script name for deletion
        $InstallerScript = "$($MyInvocation.MyCommand.Name)"
    }
    # Disable progress bar to increase Invoke-WebRequest download speed
    $ProgressPreference = 'SilentlyContinue'
}
process {
    if (Get-Service | Where-Object { $_.Name -eq 'CSFalconService' }) {
        $ErrorMessage = 'CrowdStrike Falcon service detected.'
        $ApiClient.Log('ERROR', $ErrorMessage)
        throw $ErrorMessage
    }
    # Initiate ApiClient
    $ClientParam = @{
        ClientId = $ClientId
        ClientSecret = $ClientSecret
        Hostname = $ApiHost
        LogLocation = $LogLocation
    }
    if ($MemberCid) {
        $ClientParam['MemberCid'] = $MemberCid
    }
    $Script:ApiClient = [ApiClient]::New($ClientParam)
    try {
        # Verify presence of TLS 1.2 for API communication
        $TlsCheck = if ([Net.ServicePointManager]::SecurityProtocol -notmatch 'Tls12') {
            [Net.ServicePointManager]::SecurityProtocol += [Net.SecurityProtocolType]::Tls12
            'Added [Net.SecurityProtocolType]::Tls12'
        } else {
            'Tls12 present in [Net.ServicePointManager]::SecurityProtocol'
        }
        $ApiClient.Log('TlsCheck', $TlsCheck)
    } catch {
        throw $_
    }
    try {
        # Check existing policies for proper sensor version, using 'platform_default' if not specified
        $PolicyName = if ($PolicyName) {
            $PolicyName.ToLower()
        } else {
            'platform_default'
        }
        $Param = @{
            Uri     = "/policy/combined/sensor-update/v2?filter=platform_name:'Windows'%2Bname:'$PolicyName'"
            Method  = 'get'
            Headers = @{
                Accept      = 'application/json'
                ContentType = 'application/json'
            }
        }
        $Policy = $ApiClient.Invoke($Param)
    } catch {
        throw $_
    }
    $MinorVersion = ($Policy.resources.settings.build -split '\|')[0]
    $ApiClient.Log('PolicyList', "Policy '$PolicyName' has build $MinorVersion assigned")
    try {
        # Retrieve list of available sensor installer packages
        $Param = @{
            Uri     = "/sensors/combined/installers/v1?filter=platform:'windows'"
            Method  = 'get'
            Headers = @{
                Accept      = 'application/json'
                ContentType = 'application/json'
            }
        }
        $InstallerList = $ApiClient.Invoke($Param)
        $CloudHash = ($InstallerList.resources | Where-Object { $_.version -match $MinorVersion }).sha256
        $ApiClient.Log('InstallerList', "Matched build $MinorVersion with hash $CloudHash")
    } catch {
        throw $_
    }
    try {
        # Retrieve CCID
        $Param = @{
            Uri     = '/sensors/queries/installers/ccid/v1'
            Method  = 'get'
            Headers = @{
                Accept      = 'application/json'
                ContentType = 'application/json'
            }
        }
        $CCID = $ApiClient.Invoke($Param)
    } catch {
        throw $_
    }
    try {
        # Set path for installer package
        $InstallFile = ($InstallerList.resources | Where-Object { $_.version -match $MinorVersion }).name
        $TempPath = Join-Path -Path ([Environment]::GetFolderPath('Windows')) -ChildPath temp -Resolve
        $InstallerPath = Join-Path -Path $TempPath -ChildPath $InstallFile
        # Download installer package
        $Param = @{
            Uri     = "/sensors/entities/download-installer/v1?id=$CloudHash"
            Method  = 'get'
            Headers = @{
                Accept      = 'application/octet-stream'
                ContentType = 'application/json'
            }
            Outfile = $InstallerPath
        }
        $ApiClient.Invoke($Param)
    } catch {
        throw $_
    }
    $LocalHash = (Get-FileHash -Path $InstallerPath -Algorithm SHA256).Hash.ToLower()
    $ApiClient.Log('LocalHash', $LocalHash)
    if ($CloudHash -ne $LocalHash) {
        $ErrorMessage = 'Failed hash check of local installer package'
        $ApiClient.Log('ERROR', $ErrorMessage)
        throw $ErrorMessage
    }
    # Start installer and record process ID
    $ArgumentList = '/install /quiet /noreboot'
    if ($InstallParams) {
        $ArgumentList += " $InstallParams"
    }
    $ApiClient.Log('Start-Process', "Executing $InstallerPath with arguments '$ArgumentList'")
    $ArgumentList += " CID=$($CCID.resources)"
    $InstallPID = (Start-Process -FilePath $InstallerPath -ArgumentList $ArgumentList -PassThru).id
    $ApiClient.Log('Start-Process', "Started $InstallerPath [PID: $InstallPid]")
    @('DeleteInstaller', 'DeleteScript').foreach{
        if ((Get-Variable $_).Value -eq $true) {
            # Delete installer and script
            if ($_ -eq 'DeleteInstaller') {
                # Wait for process to finish
                $ApiClient.Log('Start-Process', 'Waiting for process to complete...')
                Wait-Process $InstallPID
            }
            $FilePath = if ($_ -eq 'DeleteInstaller') {
                $InstallerPath
            } else {
                Join-Path -Path $PSScriptRoot -ChildPath $InstallerScript
            }
            try {
                Remove-Item -Path $FilePath -Force
                $ApiClient.Log('Remove-Item', "Deleted $FilePath")
            } catch {
                $ApiClient.Log('Remove-Item', "Failed to delete $FilePath")
            }
        }
    }
}