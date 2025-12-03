#############################
# API Gateway: QueueEscapeAPI
#############################

resource "aws_api_gateway_rest_api" "queueescape" {
  name        = "QueueEscapeAPI"
  description = "REST API for QueueEscape virtual queue system"
}

#############################
# Base resource: /queue
#############################

resource "aws_api_gateway_resource" "queue" {
  rest_api_id = aws_api_gateway_rest_api.queueescape.id
  parent_id   = aws_api_gateway_rest_api.queueescape.root_resource_id
  path_part   = "queue"
}

########################################
# 1) POST /queue/join  -> JoinQueueLambda
########################################

resource "aws_api_gateway_resource" "queue_join" {
  rest_api_id = aws_api_gateway_rest_api.queueescape.id
  parent_id   = aws_api_gateway_resource.queue.id
  path_part   = "join"
}

resource "aws_api_gateway_method" "post_join" {
  rest_api_id   = aws_api_gateway_rest_api.queueescape.id
  resource_id   = aws_api_gateway_resource.queue_join.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "post_join_lambda" {
  rest_api_id             = aws_api_gateway_rest_api.queueescape.id
  resource_id             = aws_api_gateway_resource.queue_join.id
  http_method             = aws_api_gateway_method.post_join.http_method
  type                    = "AWS_PROXY"
  integration_http_method = "POST"
  uri                     = aws_lambda_function.join_queue.invoke_arn
}

###############################################
# 2) GET /queue/status/{queueId}/{ticketNumber}
#    -> GetStatusLambda
###############################################

# /queue/status
resource "aws_api_gateway_resource" "queue_status" {
  rest_api_id = aws_api_gateway_rest_api.queueescape.id
  parent_id   = aws_api_gateway_resource.queue.id
  path_part   = "status"
}

# /queue/status/{queueId}
resource "aws_api_gateway_resource" "queue_status_queue_id" {
  rest_api_id = aws_api_gateway_rest_api.queueescape.id
  parent_id   = aws_api_gateway_resource.queue_status.id
  path_part   = "{queueId}"
}

# /queue/status/{queueId}/{ticketNumber}
resource "aws_api_gateway_resource" "queue_status_ticket_number" {
  rest_api_id = aws_api_gateway_rest_api.queueescape.id
  parent_id   = aws_api_gateway_resource.queue_status_queue_id.id
  path_part   = "{ticketNumber}"
}

resource "aws_api_gateway_method" "get_status" {
  rest_api_id   = aws_api_gateway_rest_api.queueescape.id
  resource_id   = aws_api_gateway_resource.queue_status_ticket_number.id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "get_status_lambda" {
  rest_api_id             = aws_api_gateway_rest_api.queueescape.id
  resource_id             = aws_api_gateway_resource.queue_status_ticket_number.id
  http_method             = aws_api_gateway_method.get_status.http_method
  type                    = "AWS_PROXY"
  integration_http_method = "POST"
  uri                     = aws_lambda_function.get_status.invoke_arn
}

###########################################
# Staff base resource: /queue/staff
###########################################

resource "aws_api_gateway_resource" "queue_staff" {
  rest_api_id = aws_api_gateway_rest_api.queueescape.id
  parent_id   = aws_api_gateway_resource.queue.id
  path_part   = "staff"
}

###########################################
# 3) GET /queue/staff/summary -> GetSummaryLambda
###########################################

resource "aws_api_gateway_resource" "queue_staff_summary" {
  rest_api_id = aws_api_gateway_rest_api.queueescape.id
  parent_id   = aws_api_gateway_resource.queue_staff.id
  path_part   = "summary"
}

resource "aws_api_gateway_method" "get_staff_summary" {
  rest_api_id   = aws_api_gateway_rest_api.queueescape.id
  resource_id   = aws_api_gateway_resource.queue_staff_summary.id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "get_staff_summary_lambda" {
  rest_api_id             = aws_api_gateway_rest_api.queueescape.id
  resource_id             = aws_api_gateway_resource.queue_staff_summary.id
  http_method             = aws_api_gateway_method.get_staff_summary.http_method
  type                    = "AWS_PROXY"
  integration_http_method = "POST"
  uri                     = aws_lambda_function.get_summary.invoke_arn
}

###########################################
# 4) POST /queue/staff/next -> StaffNextLambda
###########################################

resource "aws_api_gateway_resource" "queue_staff_next" {
  rest_api_id = aws_api_gateway_rest_api.queueescape.id
  parent_id   = aws_api_gateway_resource.queue_staff.id
  path_part   = "next"
}

resource "aws_api_gateway_method" "post_staff_next" {
  rest_api_id   = aws_api_gateway_rest_api.queueescape.id
  resource_id   = aws_api_gateway_resource.queue_staff_next.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "post_staff_next_lambda" {
  rest_api_id             = aws_api_gateway_rest_api.queueescape.id
  resource_id             = aws_api_gateway_resource.queue_staff_next.id
  http_method             = aws_api_gateway_method.post_staff_next.http_method
  type                    = "AWS_PROXY"
  integration_http_method = "POST"
  uri                     = aws_lambda_function.staff_next.invoke_arn
}

#############################################
# 5) POST /queue/staff/complete -> StaffCompleteLambda
#############################################

resource "aws_api_gateway_resource" "queue_staff_complete" {
  rest_api_id = aws_api_gateway_rest_api.queueescape.id
  parent_id   = aws_api_gateway_resource.queue_staff.id
  path_part   = "complete"
}

resource "aws_api_gateway_method" "post_staff_complete" {
  rest_api_id   = aws_api_gateway_rest_api.queueescape.id
  resource_id   = aws_api_gateway_resource.queue_staff_complete.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "post_staff_complete_lambda" {
  rest_api_id             = aws_api_gateway_rest_api.queueescape.id
  resource_id             = aws_api_gateway_resource.queue_staff_complete.id
  http_method             = aws_api_gateway_method.post_staff_complete.http_method
  type                    = "AWS_PROXY"
  integration_http_method = "POST"
  uri                     = aws_lambda_function.staff_complete.invoke_arn
}

###########################################
# Lambda permissions for API Gateway
###########################################

resource "aws_lambda_permission" "apigw_join" {
  statement_id  = "AllowAPIGatewayInvokeJoin"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.join_queue.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.queueescape.execution_arn}/*/*"
}

resource "aws_lambda_permission" "apigw_status" {
  statement_id  = "AllowAPIGatewayInvokeStatus"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.get_status.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.queueescape.execution_arn}/*/*"
}

resource "aws_lambda_permission" "apigw_staff_summary" {
  statement_id  = "AllowAPIGatewayInvokeStaffSummary"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.get_summary.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.queueescape.execution_arn}/*/*"
}

resource "aws_lambda_permission" "apigw_staff_next" {
  statement_id  = "AllowAPIGatewayInvokeStaffNext"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.staff_next.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.queueescape.execution_arn}/*/*"
}

resource "aws_lambda_permission" "apigw_staff_complete" {
  statement_id  = "AllowAPIGatewayInvokeStaffComplete"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.staff_complete.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.queueescape.execution_arn}/*/*"
}

###########################################
# Deployment + Stage
###########################################

resource "aws_api_gateway_deployment" "queueescape_deployment" {
  rest_api_id = aws_api_gateway_rest_api.queueescape.id

  depends_on = [
    aws_api_gateway_integration.post_join_lambda,
    aws_api_gateway_integration.get_status_lambda,
    aws_api_gateway_integration.get_staff_summary_lambda,
    aws_api_gateway_integration.post_staff_next_lambda,
    aws_api_gateway_integration.post_staff_complete_lambda
  ]
}

resource "aws_api_gateway_stage" "dev" {
  rest_api_id   = aws_api_gateway_rest_api.queueescape.id
  deployment_id = aws_api_gateway_deployment.queueescape_deployment.id
  stage_name    = "dev"
}

# Resource: /queue/staff/settings
resource "aws_api_gateway_resource" "queue_staff_settings" {
  rest_api_id = aws_api_gateway_rest_api.queueescape.id
  parent_id   = aws_api_gateway_resource.queue_staff.id
  path_part   = "settings"
}

resource "aws_api_gateway_method" "post_staff_settings" {
  rest_api_id   = aws_api_gateway_rest_api.queueescape.id
  resource_id   = aws_api_gateway_resource.queue_staff_settings.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "post_staff_settings_lambda" {
  rest_api_id             = aws_api_gateway_rest_api.queueescape.id
  resource_id             = aws_api_gateway_resource.queue_staff_settings.id
  http_method             = aws_api_gateway_method.post_staff_settings.http_method
  type                    = "AWS_PROXY"
  integration_http_method = "POST"
  uri                     = aws_lambda_function.set_settings.invoke_arn
}

resource "aws_lambda_permission" "apigw_staff_settings" {
  statement_id  = "AllowAPIGatewayInvokeStaffSettings"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.set_settings.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.queueescape.execution_arn}/*/*"
}