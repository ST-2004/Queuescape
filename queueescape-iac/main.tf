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
}

resource "aws_dynamodb_table" "queue_stats" {
  name         = "QueueStats"
  billing_mode = "PAY_PER_REQUEST"

  hash_key = "queueId"

  attribute {
    name = "queueId"
    type = "S"
  }
}
