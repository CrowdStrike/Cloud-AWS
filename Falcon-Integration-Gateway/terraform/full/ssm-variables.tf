#This Falcon Client ID used by FIG to connect to your Falcon environment

#DO NOT ENTER YOUR CLIENT ID HERE - PASS IT TO TERRAFORM ON THE COMMAND LINE
#terraform apply --var falcon_client_id="CLIENT_ID_GOES_HERE"
variable "falcon_client_id" {
	type = string
	default = ""
}

#This Falcon Client ID used by FIG to connect to your Falcon environment

#DO NOT ENTER YOUR CLIENT SECRET HERE - PASS IT TO TERRAFORM ON THE COMMAND LINE
#terraform apply --var falcon_client_secret="CLIENT_SECRET_GOES_HERE"
variable "falcon_client_secret" {
	type = string
	default = ""
}

#The application ID used by FIG to identify itself to the CrowdStrike API
variable "app_id" {
	type = string
	default = "fig-example-app-id"
}

#Severity threshold filter value
variable "severity_threshold" {
	type = string
	default = "3"
}
