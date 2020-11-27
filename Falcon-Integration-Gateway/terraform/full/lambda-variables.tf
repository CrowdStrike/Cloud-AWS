#This points to the lambda package archive maintained
#in the install folder of this repository. This is used
#to pull in the most recent code during deployment.
variable "lambda_filename" {
    type = string
    default = "../../install/fig-identify-detections_lambda.zip"
}