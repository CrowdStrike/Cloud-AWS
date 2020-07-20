variable "CSAssumingRoleName" {
  type = string
  default = "CS-Prod-HG-CsCloudconnectaws"
}
variable "RoleName" {
}
variable "ExternalID" {
}
variable "CSAccountNumber"  {
  type = string
  default = "292230061137"
}
//variable "SnsTopicRegistration" {
//}
//variable "SnsTopicCloudTrail" {
//}
variable "CloudTrailName" {
}
variable "CloudTrailS3BucketName" {
  type = string
}
variable "CloudTrailS3LogExpiration" {
  type = number
  default = 7
}
variable "aws_region" {
  type = string
}
variable "aws_local_account" {
  type=string
}