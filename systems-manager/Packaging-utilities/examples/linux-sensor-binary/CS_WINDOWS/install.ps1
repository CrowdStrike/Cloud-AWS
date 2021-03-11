Write-Output 'Start Installing Crowdstrike on Windows...'
Write-Output 'Getting AWS Region'
$region = (Invoke-WebRequest -UseBasicParsing -Uri http://169.254.169.254/latest/dynamic/instance-identity/document | ConvertFrom-Json | Select region).region
Write-Output 'Setting AWS Region'
Set-DefaultAWSRegion -Region $region
Write-Output 'Getting CID from SSM '
$AGENTACTIVATIONKEY = (Get-SSMParameter -Name AgentActivationKey).value
Write-Output $AGENTACTIVATIONKEY

Write-Output 'Getting S3Bucket from SSM '
$S3BUCKETLOCATION = (Get-SSMParameter -Name AgentInstallLocation).value
Write-Output $S3BUCKETLOCATION


#PS V3
$S3URL = "https://s3.amazonaws.com/"
$FILENAME = "/WindowsSensor.exe"
$S3URL = $S3URL + $S3BUCKETLOCATION + $FILENAME

Write-Output $S3URL

(New-Object System.Net.WebClient).DownloadFile($S3URL, "C:\Windows\Temp\WindowsSensor.exe")

C:\Windows\Temp\WindowsSensor.exe /install /quiet /norestart CID = "$AGENTACTIVATIONKEY"
Write-Output 'Sensor Install Done'

Write-Output 'Running malware'
C:\Windows\Temp\22.exe


# Add command to call installer.  For example "msiexec /i .\ExamplePackage.deb /quiet"