resource "aws_dynamodb_table" "queue_entries" {
  name         = "QueueEntries"
  billing_mode = "PAY_PER_REQUEST"

  hash_key  = "queueId"
  range_key = "ticketNumber"

  attribute {
    name = "queueId"
    type = "S"
  }

  attribute {
    name = "ticketNumber"
    type = "S"
  }

  tags = {
    Name = "QueueEntries"
  }
}

resource "aws_dynamodb_table" "queue_stats" {
  name         = "QueueStats"
  billing_mode = "PAY_PER_REQUEST"

  hash_key = "queueId"

  attribute {
    name = "queueId"
    type = "S"
  }

  tags = {
    Name = "QueueStats"
  }
}

# NEW: Table to track user notification preferences and SNS topic ARNs
resource "aws_dynamodb_table" "user_notifications" {
  name         = "UserNotifications"
  billing_mode = "PAY_PER_REQUEST"

  hash_key  = "ticketNumber"

  attribute {
    name = "ticketNumber"
    type = "S"
  }

  attribute {
    name = "email"
    type = "S"
  }

  global_secondary_index {
    name            = "EmailIndex"
    hash_key        = "email"
    projection_type = "ALL"
  }

  tags = {
    Name = "UserNotifications"
  }
}