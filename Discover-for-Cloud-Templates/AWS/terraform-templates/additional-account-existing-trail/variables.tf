variable "CSAssumingRoleName" {
  type = string
  default = "CS-Prod-HG-CsCloudconnectaws"
}
variable "RoleName" {
}
variable "ExternalID" {
}
variable "CSAccountNumber" {
  type = string
  default = "292230061137"
}
variable "CloudTrailS3BucketName" {
  type = string
}
variable "CloudTrailS3BucketAccountNumber" {
  type = string
}
variable "aws_region" {
  type = string
}
variable "aws_local_account" {
  type = string
}