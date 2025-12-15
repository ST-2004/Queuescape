######################
# Cognito User Pool
######################

resource "aws_cognito_user_pool" "staff_pool" {
  name = "queueescape-staff-pool"

  # Username configuration - allow email as username
  username_attributes      = ["email"]
  auto_verified_attributes = ["email"]

  # Password policy
  password_policy {
    minimum_length    = 8
    require_lowercase = true
    require_uppercase = true
    require_numbers   = true
    require_symbols   = false
  }

  # ALLOW SELF-REGISTRATION
  admin_create_user_config {
    allow_admin_create_user_only = false  # ← Changed to false
  }

  # Email configuration
  email_configuration {
    email_sending_account = "COGNITO_DEFAULT"
  }

  # Account recovery
  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
  }

  # Email verification message
  verification_message_template {
    default_email_option = "CONFIRM_WITH_CODE"
    email_subject        = "QueueEscape - Verify your email"
    email_message        = "Your verification code is {####}"
  }

  # Schema attributes
  schema {
    name                = "email"
    attribute_data_type = "String"
    required            = true
    mutable             = true

    string_attribute_constraints {
      min_length = 1
      max_length = 256
    }
  }

  tags = {
    Name = "queueescape-staff-pool"
  }
}

######################
# Cognito User Pool Client
######################

resource "aws_cognito_user_pool_client" "staff_client" {
  name         = "queueescape-staff-client"
  user_pool_id = aws_cognito_user_pool.staff_pool.id

  # No client secret (for frontend apps)
  generate_secret = false

  # Auth flows - ADD USER_SRP_AUTH for signup
  explicit_auth_flows = [
    "ALLOW_USER_PASSWORD_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_USER_SRP_AUTH"
  ]

  # Token validity
  refresh_token_validity = 30
  access_token_validity  = 60
  id_token_validity      = 60

  token_validity_units {
    refresh_token = "days"
    access_token  = "minutes"
    id_token      = "minutes"
  }

  # Prevent user existence errors
  prevent_user_existence_errors = "ENABLED"

  # OAuth settings
  allowed_oauth_flows_user_pool_client = false
  
  # Read and write attributes
  read_attributes = [
    "email",
    "email_verified"
  ]

  write_attributes = [
    "email"
  ]
}

######################
# API Gateway Authorizer
######################

resource "aws_api_gateway_authorizer" "cognito_authorizer" {
  name            = "CognitoStaffAuthorizer"
  rest_api_id     = aws_api_gateway_rest_api.queueescape.id
  type            = "COGNITO_USER_POOLS"
  identity_source = "method.request.header.Authorization"

  provider_arns = [
    aws_cognito_user_pool.staff_pool.arn
  ]
}

######################
# Outputs
######################

output "cognito_user_pool_id" {
  value       = aws_cognito_user_pool.staff_pool.id
  description = "Cognito User Pool ID"
}

output "cognito_user_pool_arn" {
  value       = aws_cognito_user_pool.staff_pool.arn
  description = "Cognito User Pool ARN"
}

output "cognito_client_id" {
  value       = aws_cognito_user_pool_client.staff_client.id
  description = "Cognito App Client ID"
  sensitive   = true
}

output "cognito_user_pool_endpoint" {
  value       = aws_cognito_user_pool.staff_pool.endpoint
  description = "Cognito User Pool Endpoint"
}