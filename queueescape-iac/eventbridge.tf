# EventBridge rule to trigger notification lambda every 2 minutes
resource "aws_cloudwatch_event_rule" "notification_scheduler" {
  name                = "queueescape-notification-scheduler"
  description         = "Trigger notification check every 2 minutes"
  schedule_expression = "rate(2 minutes)"

  tags = {
    Name = "queueescape-notification-scheduler"
  }
}

resource "aws_cloudwatch_event_target" "notification_lambda" {
  rule      = aws_cloudwatch_event_rule.notification_scheduler.name
  target_id = "SendNotificationsLambda"
  arn       = aws_lambda_function.send_notifications.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.send_notifications.function_name
    principal     = "events.amazonaws.com"
    source_arn    = aws_cloudwatch_event_rule.notification_scheduler.arn
}