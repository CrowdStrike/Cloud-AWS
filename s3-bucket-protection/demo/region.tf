provider "aws" {
    region = var.region
}
variable "region" {
    type = string
    default = "us-east-2"
}