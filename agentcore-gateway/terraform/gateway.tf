# AgentCore Gateway interceptor registration.
#
# The Terraform AWS provider does not yet have a native resource for
# bedrock-agentcore gateway interceptor configuration. This null_resource
# calls the AWS CLI as a workaround. It re-runs whenever the Lambda ARN or
# gateway ID changes.
#
# Replace with an aws_bedrockagentcore_gateway resource once the provider
# adds support.

# resource "null_resource" "gateway_interceptor" {
#   triggers = {
#     lambda_arn = aws_lambda_function.interceptor.arn
#     gateway_id = var.gateway_id
#   }

#   provisioner "local-exec" {
#     command = <<-EOT
#       aws bedrock-agentcore update-gateway \
#         --gateway-identifier ${var.gateway_id} \
#         --interceptor-configurations '[{
#           "interceptor": {
#             "lambda": {"arn": "${aws_lambda_function.interceptor.arn}"}
#           },
#           "interceptionPoints": ["REQUEST", "RESPONSE"],
#           "inputConfiguration": {
#             "passRequestHeaders": true
#           }
#         }]' \
#         --region ${var.aws_region}
#     EOT
#   }
# }
