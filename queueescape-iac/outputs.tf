output "api_base_url" {
  value = aws_api_gateway_stage.dev.invoke_url
}

output "cognito_details" {
  value = {
    user_pool_id     = aws_cognito_user_pool.staff_pool.id
    app_client_id    = aws_cognito_user_pool_client.staff_client.id
    region           = "us-east-1"
  }
  description = "Cognito configuration details"
  sensitive   = true
}