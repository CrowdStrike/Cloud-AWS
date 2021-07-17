variable "region" {
        type = string
        default = "us-east-2"
}
variable "availability_zone" {
    description = "Availability zone to create subnet"
    type        = string
    default     = "us-east-2a"
}
provider "aws" {
        region = var.region
}
