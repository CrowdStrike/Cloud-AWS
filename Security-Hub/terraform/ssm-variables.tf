variable "falcon_client_id" {
	type = string
	default = ""
}
variable "falcon_client_secret" {
	type = string
	default = ""
}
variable "app_id" {
	type = string
	default = "cs-sechub-int-example"
}
variable "severity_threshold" {
	type = string
	default = "3"
}
variable "ssl_verify" {
    description = "Enable / Disable SSL verification boolean (Requests library)"
    type        = string
    default     = "True"
}

variable "base_url" {
    description = "CrowdStrike API Base URL"
    type        = string
    default     = "https://api.crowdstrike.com"
}