resource "aws_sns_topic" "alerts" {
  name = "queueescape-alerts"
  display_name = "QueueEscape Notifications"

  tags = {
    Name = "queueescape-alerts"
  }
}

# This is a general topic for system alerts
# User-specific topics will be created dynamically by Lambda

output "alerts_topic_arn" {
  value       = aws_sns_topic.alerts.arn
  description = "ARN of the alerts SNS topic"
}