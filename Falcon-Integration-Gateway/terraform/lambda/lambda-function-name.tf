#This is the name of the detections lambda function
#that will be deployed to your environment
variable "lambda_function_name" {
    type = string
    default = "fig-identify-detections-example"
}
