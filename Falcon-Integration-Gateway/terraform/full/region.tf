#You enter the region ID you wish to use before 
#you will able to deploy the environment.
variable "region" {
        type = string
        default = "<<REGION_HERE>>"
}
provider "aws" {
        region = var.region
}
