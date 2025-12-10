data "archive_file" "join_queue" {
  type        = "zip"
  source_dir  = "${path.module}/lambda_src/join_queue"
  output_path = "${path.module}/lambda_src/join_queue.zip"
}

data "archive_file" "get_status" {
  type        = "zip"
  source_dir  = "${path.module}/lambda_src/get_status"
  output_path = "${path.module}/lambda_src/get_status.zip"
}

data "archive_file" "get_summary" {
  type        = "zip"
  source_dir  = "${path.module}/lambda_src/get_summary"
  output_path = "${path.module}/lambda_src/get_summary.zip"
}

data "archive_file" "staff_next" {
  type        = "zip"
  source_dir  = "${path.module}/lambda_src/staff_next"
  output_path = "${path.module}/lambda_src/staff_next.zip"
}

data "archive_file" "staff_complete" {
  type        = "zip"
  source_dir  = "${path.module}/lambda_src/staff_complete"
  output_path = "${path.module}/lambda_src/staff_complete.zip"
}

data "archive_file" "set_settings" {
  type        = "zip"
  source_dir  = "${path.module}/lambda_src/set_settings"
  output_path = "${path.module}/lambda_src/set_settings.zip"
}

locals {
  lambda_env = {
    QUEUE_ENTRIES_TABLE = "QueueEntries"
    QUEUE_STATS_TABLE   = "QueueStats"
    ALERTS_TOPIC_ARN    = aws_sns_topic.alerts.arn
  }
}

resource "aws_lambda_function" "join_queue" {
  function_name = "JoinQueueLambda"
  role          = var.lambda_execution_role_arn
  runtime       = "python3.12"
  handler       = "lambda_function.lambda_handler"

  filename         = data.archive_file.join_queue.output_path
  source_code_hash = data.archive_file.join_queue.output_base64sha256

  timeout = 60
  memory_size = 512

  environment {
    variables = merge(
      local.lambda_env,
      { LOG_LEVEL = "DEBUG" }
    )
  }

  vpc_config {
    subnet_ids = [
      aws_subnet.private_a.id,
      aws_subnet.private_b.id
    ]
    security_group_ids = [aws_security_group.lambda_sg.id]
  }
}

resource "aws_lambda_function" "get_status" {
  function_name = "GetStatusLambda"
  role          = var.lambda_execution_role_arn
  runtime       = "python3.12"
  handler       = "lambda_function.lambda_handler"

  filename         = data.archive_file.get_status.output_path
  source_code_hash = data.archive_file.get_status.output_base64sha256

  timeout = 60
  memory_size = 512

  environment {
    variables = merge(
      local.lambda_env,
      { LOG_LEVEL = "DEBUG" }
    )
  }

  vpc_config {
    subnet_ids = [
      aws_subnet.private_a.id,
      aws_subnet.private_b.id
    ]
    security_group_ids = [aws_security_group.lambda_sg.id]
  }
}

resource "aws_lambda_function" "get_summary" {
  function_name = "GetSummaryLambda"
  role          = var.lambda_execution_role_arn
  runtime       = "python3.12"
  handler       = "lambda_function.lambda_handler"

  filename         = data.archive_file.get_summary.output_path
  source_code_hash = data.archive_file.get_summary.output_base64sha256

  timeout = 60
  memory_size = 512

  environment {
    variables = merge(
      local.lambda_env,
      { LOG_LEVEL = "DEBUG" }
    )
  }

  vpc_config {
    subnet_ids = [
      aws_subnet.private_a.id,
      aws_subnet.private_b.id
    ]
    security_group_ids = [aws_security_group.lambda_sg.id]
  }
}

resource "aws_lambda_function" "staff_next" {
  function_name = "StaffNextLambda"
  role          = var.lambda_execution_role_arn
  runtime       = "python3.12"
  handler       = "lambda_function.lambda_handler"

  filename         = data.archive_file.staff_next.output_path
  source_code_hash = data.archive_file.staff_next.output_base64sha256

  timeout = 60
  memory_size = 512

  environment {
    variables = merge(
      local.lambda_env,
      { LOG_LEVEL = "DEBUG" }
    )
  }

  vpc_config {
    subnet_ids = [
      aws_subnet.private_a.id,
      aws_subnet.private_b.id
    ]
    security_group_ids = [aws_security_group.lambda_sg.id]
  }
}

resource "aws_lambda_function" "staff_complete" {
  function_name = "StaffCompleteLambda"
  role          = var.lambda_execution_role_arn
  runtime       = "python3.12"
  handler       = "lambda_function.lambda_handler"

  filename         = data.archive_file.staff_complete.output_path
  source_code_hash = data.archive_file.staff_complete.output_base64sha256

  timeout = 60
  memory_size = 512

  environment {
    variables = merge(
      local.lambda_env,
      { LOG_LEVEL = "DEBUG" }
    )
  }

  vpc_config {
    subnet_ids = [
      aws_subnet.private_a.id,
      aws_subnet.private_b.id
    ]
    security_group_ids = [aws_security_group.lambda_sg.id]
  }
}

resource "aws_lambda_function" "set_settings" {
  function_name = "SetSettingsLambda"
  role          = var.lambda_execution_role_arn
  runtime       = "python3.12"
  handler       = "lambda_function.lambda_handler"
  filename      = data.archive_file.set_settings.output_path
  source_code_hash = data.archive_file.set_settings.output_base64sha256

  timeout = 60
  memory_size = 512

  environment {
    variables = merge(
      local.lambda_env,
      { LOG_LEVEL = "DEBUG" }
    )
  }

 vpc_config {
    subnet_ids = [
      aws_subnet.private_a.id,
      aws_subnet.private_b.id
    ]
    security_group_ids = [aws_security_group.lambda_sg.id]
  }
}