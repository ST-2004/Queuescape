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

########################################
# CORS for /queue/join (OPTIONS)
########################################

resource "aws_api_gateway_method" "options_queue_join" {
  rest_api_id   = aws_api_gateway_rest_api.queueescape.id
  resource_id   = aws_api_gateway_resource.queue_join.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "options_queue_join_integration" {
  rest_api_id = aws_api_gateway_rest_api.queueescape.id
  resource_id = aws_api_gateway_resource.queue_join.id
  http_method = aws_api_gateway_method.options_queue_join.http_method
  type        = "MOCK"
  integration_http_method = "POST"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "options_queue_join_200" {
  rest_api_id = aws_api_gateway_rest_api.queueescape.id
  resource_id = aws_api_gateway_resource.queue_join.id
  http_method = aws_api_gateway_method.options_queue_join.http_method
  status_code = "200"

  response_models = {
    "application/json" = "Empty"
  }

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = true
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
  }
}

resource "aws_api_gateway_integration_response" "options_queue_join_200" {
  rest_api_id = aws_api_gateway_rest_api.queueescape.id
  resource_id = aws_api_gateway_resource.queue_join.id
  http_method = aws_api_gateway_method.options_queue_join.http_method
  status_code = aws_api_gateway_method_response.options_queue_join_200.status_code

  depends_on = [
    aws_api_gateway_integration.options_queue_join_integration
  ]
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = "'*'" # or "'*'" for dev
    "method.response.header.Access-Control-Allow-Headers" = "'*'"
    "method.response.header.Access-Control-Allow-Methods" = "'OPTIONS,POST'"
  }

  response_templates = {
    "application/json" = ""
  }
}

###############################################
# CORS for GET /queue/status/{queueId}/{ticketNumber}
###############################################

resource "aws_api_gateway_method" "options_status" {
  rest_api_id   = aws_api_gateway_rest_api.queueescape.id
  resource_id   = aws_api_gateway_resource.queue_status_ticket_number.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "options_status_integration" {
  rest_api_id             = aws_api_gateway_rest_api.queueescape.id
  resource_id             = aws_api_gateway_resource.queue_status_ticket_number.id
  http_method             = aws_api_gateway_method.options_status.http_method
  type                    = "MOCK"
  integration_http_method = "POST"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "options_status_200" {
  rest_api_id = aws_api_gateway_rest_api.queueescape.id
  resource_id = aws_api_gateway_resource.queue_status_ticket_number.id
  http_method = aws_api_gateway_method.options_status.http_method
  status_code = "200"

  response_models = {
    "application/json" = "Empty"
  }

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = true
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
  }
}

resource "aws_api_gateway_integration_response" "options_status_200" {
  rest_api_id = aws_api_gateway_rest_api.queueescape.id
  resource_id = aws_api_gateway_resource.queue_status_ticket_number.id
  http_method = aws_api_gateway_method.options_status.http_method
  status_code = aws_api_gateway_method_response.options_status_200.status_code

  depends_on = [
    aws_api_gateway_integration.options_status_integration
  ]

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
    "method.response.header.Access-Control-Allow-Headers" = "'*'"
    "method.response.header.Access-Control-Allow-Methods" = "'OPTIONS,GET'"
  }

  response_templates = {
    "application/json" = ""
  }
}

###########################################
# CORS for GET /queue/staff/summary
###########################################

resource "aws_api_gateway_method" "options_staff_summary" {
  rest_api_id   = aws_api_gateway_rest_api.queueescape.id
  resource_id   = aws_api_gateway_resource.queue_staff_summary.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "options_staff_summary_integration" {
  rest_api_id             = aws_api_gateway_rest_api.queueescape.id
  resource_id             = aws_api_gateway_resource.queue_staff_summary.id
  http_method             = aws_api_gateway_method.options_staff_summary.http_method
  type                    = "MOCK"
  integration_http_method = "POST"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "options_staff_summary_200" {
  rest_api_id = aws_api_gateway_rest_api.queueescape.id
  resource_id = aws_api_gateway_resource.queue_staff_summary.id
  http_method = aws_api_gateway_method.options_staff_summary.http_method
  status_code = "200"

  response_models = {
    "application/json" = "Empty"
  }

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = true
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
  }
}

resource "aws_api_gateway_integration_response" "options_staff_summary_200" {
  rest_api_id = aws_api_gateway_rest_api.queueescape.id
  resource_id = aws_api_gateway_resource.queue_staff_summary.id
  http_method = aws_api_gateway_method.options_staff_summary.http_method
  status_code = aws_api_gateway_method_response.options_staff_summary_200.status_code

  depends_on = [
    aws_api_gateway_integration.options_staff_summary_integration
  ]

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
    "method.response.header.Access-Control-Allow-Headers" = "'*'"
    "method.response.header.Access-Control-Allow-Methods" = "'OPTIONS,GET'"
  }

  response_templates = {
    "application/json" = ""
  }
}

###########################################
# CORS for POST /queue/staff/next
###########################################

resource "aws_api_gateway_method" "options_staff_next" {
  rest_api_id   = aws_api_gateway_rest_api.queueescape.id
  resource_id   = aws_api_gateway_resource.queue_staff_next.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "options_staff_next_integration" {
  rest_api_id             = aws_api_gateway_rest_api.queueescape.id
  resource_id             = aws_api_gateway_resource.queue_staff_next.id
  http_method             = aws_api_gateway_method.options_staff_next.http_method
  type                    = "MOCK"
  integration_http_method = "POST"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "options_staff_next_200" {
  rest_api_id = aws_api_gateway_rest_api.queueescape.id
  resource_id = aws_api_gateway_resource.queue_staff_next.id
  http_method = aws_api_gateway_method.options_staff_next.http_method
  status_code = "200"

  response_models = {
    "application/json" = "Empty"
  }

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = true
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
  }
}

resource "aws_api_gateway_integration_response" "options_staff_next_200" {
  rest_api_id = aws_api_gateway_rest_api.queueescape.id
  resource_id = aws_api_gateway_resource.queue_staff_next.id
  http_method = aws_api_gateway_method.options_staff_next.http_method
  status_code = aws_api_gateway_method_response.options_staff_next_200.status_code

  depends_on = [
    aws_api_gateway_integration.options_staff_next_integration
  ]

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
    "method.response.header.Access-Control-Allow-Headers" = "'*'"
    "method.response.header.Access-Control-Allow-Methods" = "'OPTIONS,POST'"
  }

  response_templates = {
    "application/json" = ""
  }
}

###########################################
# CORS for POST /queue/staff/complete
###########################################

resource "aws_api_gateway_method" "options_staff_complete" {
  rest_api_id   = aws_api_gateway_rest_api.queueescape.id
  resource_id   = aws_api_gateway_resource.queue_staff_complete.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "options_staff_complete_integration" {
  rest_api_id             = aws_api_gateway_rest_api.queueescape.id
  resource_id             = aws_api_gateway_resource.queue_staff_complete.id
  http_method             = aws_api_gateway_method.options_staff_complete.http_method
  type                    = "MOCK"
  integration_http_method = "POST"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "options_staff_complete_200" {
  rest_api_id = aws_api_gateway_rest_api.queueescape.id
  resource_id = aws_api_gateway_resource.queue_staff_complete.id
  http_method = aws_api_gateway_method.options_staff_complete.http_method
  status_code = "200"

  response_models = {
    "application/json" = "Empty"
  }

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = true
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
  }
}

resource "aws_api_gateway_integration_response" "options_staff_complete_200" {
  rest_api_id = aws_api_gateway_rest_api.queueescape.id
  resource_id = aws_api_gateway_resource.queue_staff_complete.id
  http_method = aws_api_gateway_method.options_staff_complete.http_method
  status_code = aws_api_gateway_method_response.options_staff_complete_200.status_code

  depends_on = [
    aws_api_gateway_integration.options_staff_complete_integration
  ]

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
    "method.response.header.Access-Control-Allow-Headers" = "'*'"
    "method.response.header.Access-Control-Allow-Methods" = "'OPTIONS,POST'"
  }

  response_templates = {
    "application/json" = ""
  }
}

###########################################
# CORS for POST /queue/staff/settings
###########################################

resource "aws_api_gateway_method" "options_staff_settings" {
  rest_api_id   = aws_api_gateway_rest_api.queueescape.id
  resource_id   = aws_api_gateway_resource.queue_staff_settings.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "options_staff_settings_integration" {
  rest_api_id             = aws_api_gateway_rest_api.queueescape.id
  resource_id             = aws_api_gateway_resource.queue_staff_settings.id
  http_method             = aws_api_gateway_method.options_staff_settings.http_method
  type                    = "MOCK"
  integration_http_method = "POST"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "options_staff_settings_200" {
  rest_api_id = aws_api_gateway_rest_api.queueescape.id
  resource_id = aws_api_gateway_resource.queue_staff_settings.id
  http_method = aws_api_gateway_method.options_staff_settings.http_method
  status_code = "200"

  response_models = {
    "application/json" = "Empty"
  }

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = true
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
  }
}

resource "aws_api_gateway_integration_response" "options_staff_settings_200" {
  rest_api_id = aws_api_gateway_rest_api.queueescape.id
  resource_id = aws_api_gateway_resource.queue_staff_settings.id
  http_method = aws_api_gateway_method.options_staff_settings.http_method
  status_code = aws_api_gateway_method_response.options_staff_settings_200.status_code

  depends_on = [
    aws_api_gateway_integration.options_staff_settings_integration
  ]

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
    "method.response.header.Access-Control-Allow-Headers" = "'*'"
    "method.response.header.Access-Control-Allow-Methods" = "'OPTIONS,POST'"
  }

  response_templates = {
    "application/json" = ""
  }
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

  # Force new deployment when API definition changes
  triggers = {
    redeployment = sha1(jsonencode(aws_api_gateway_rest_api.queueescape))
  }

  depends_on = [
    aws_api_gateway_integration.post_join_lambda,
    aws_api_gateway_integration.get_status_lambda,
    aws_api_gateway_integration.get_staff_summary_lambda,
    aws_api_gateway_integration.post_staff_next_lambda,
    aws_api_gateway_integration.post_staff_complete_lambda,
    aws_api_gateway_integration.options_queue_join_integration,
    aws_api_gateway_integration.options_status_integration,
    aws_api_gateway_integration.options_staff_summary_integration,
    aws_api_gateway_integration.options_staff_next_integration,
    aws_api_gateway_integration.options_staff_complete_integration,
    aws_api_gateway_integration.options_staff_settings_integration
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

output "queueescape_invoke_url" {
  value = "https://${aws_api_gateway_rest_api.queueescape.id}.execute-api.us-east-1.amazonaws.com/${aws_api_gateway_stage.dev.stage_name}"
}
