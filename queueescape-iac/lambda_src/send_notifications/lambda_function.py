import json
import boto3
import os
from boto3.dynamodb.conditions import Key
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
entries_table = dynamodb.Table(os.environ['QUEUE_ENTRIES_TABLE'])
notifications_table = dynamodb.Table(os.environ['USER_NOTIFICATIONS_TABLE'])
stats_table = dynamodb.Table(os.environ['QUEUE_STATS_TABLE'])
sns = boto3.client('sns')

# Get notification thresholds from environment
THRESHOLDS = [int(x) for x in os.environ.get('NOTIFICATION_THRESHOLDS', '50,40,30,20,10,5,3,1').split(',')]

def get_notification_settings(queue_id):
    """
    Fetch custom notification thresholds from QueueStats if configured by staff.
    Falls back to environment variable defaults.
    """
    try:
        response = stats_table.get_item(Key={'queueId': queue_id})
        if 'Item' in response and 'notification_thresholds' in response['Item']:
            custom = response['Item']['notification_thresholds']
            return [int(x) for x in custom.split(',')]
    except Exception as e:
        print(f"Error fetching custom thresholds: {e}")
    
    return THRESHOLDS

def calculate_position(ticket, queue_id):
    """
    Calculate current position in queue for a given ticket.
    """
    scan_resp = entries_table.scan(
        FilterExpression=Key('status').eq('WAITING') & Key('queueId').eq(queue_id)
    )
    
    position = 0
    for item in scan_resp['Items']:
        if item['joinTime'] < ticket['joinTime']:
            position += 1
    
    return position

def should_notify(current_position, last_notified_position, notifications_sent, thresholds):
    """
    Determine if we should send a notification based on current position.
    Returns (should_send, milestone) tuple.
    """
    # Check if we've crossed a threshold
    for threshold in thresholds:
        if current_position <= threshold and last_notified_position > threshold:
            # We've crossed this threshold
            if threshold not in notifications_sent:
                return True, threshold
    
    return False, None

def send_position_notification(topic_arn, ticket_number, position, estimated_wait):
    """
    Send notification about queue position.
    """
    try:
        if position == 0:
            message = f"""
🎉 Your Turn!

Ticket Number: {ticket_number}

Please proceed to the service counter immediately. Your turn has arrived!

Thank you for using QueueEscape.
            """
            subject = "🔔 Your Turn - Please Proceed!"
        elif position <= 3:
            message = f"""
⚠️ Almost Your Turn!

Ticket Number: {ticket_number}
Current Position: {position}
Estimated Wait: {estimated_wait} minutes

You're next in line! Please be ready to proceed to the counter.

Thank you for using QueueEscape.
            """
            subject = f"⚠️ Position Update - You're #{position}!"
        else:
            message = f"""
📍 Queue Position Update

Ticket Number: {ticket_number}
Current Position: {position}
Estimated Wait: {estimated_wait} minutes

You're getting closer! We'll notify you again as you move up in the queue.

Thank you for using QueueEscape.
            """
            subject = f"📍 Position Update - You're #{position}"
        
        sns.publish(
            TopicArn=topic_arn,
            Message=message,
            Subject=subject
        )
        
        print(f"Sent notification for ticket {ticket_number} at position {position}")
        return True
        
    except Exception as e:
        print(f"Error sending notification: {str(e)}")
        return False

def lambda_handler(event, context):
    """
    This function should be triggered periodically (e.g., every 1-2 minutes via EventBridge)
    to check all waiting tickets and send notifications as needed.
    """
    try:
        # Get all waiting tickets
        scan_resp = entries_table.scan(
            FilterExpression=Key('status').eq('WAITING')
        )
        
        waiting_tickets = scan_resp.get('Items', [])
        notifications_sent_count = 0
        
        for ticket in waiting_tickets:
            ticket_number = ticket['ticketNumber']
            queue_id = ticket['queueId']
            
            # Get notification settings for this ticket
            try:
                notif_resp = notifications_table.get_item(Key={'ticketNumber': ticket_number})
                
                if 'Item' not in notif_resp:
                    print(f"No notification record for {ticket_number}")
                    continue
                
                notif_record = notif_resp['Item']
                topic_arn = notif_record.get('topicArn')
                
                if not topic_arn or topic_arn == 'NONE':
                    continue
                
                # Get current position
                current_position = calculate_position(ticket, queue_id)
                last_notified = notif_record.get('lastNotifiedPosition', 999999)
                sent_milestones = notif_record.get('notificationsSent', [])
                
                # Get thresholds for this queue
                thresholds = get_notification_settings(queue_id)
                
                # Check if we should notify
                should_send, milestone = should_notify(
                    current_position, 
                    last_notified, 
                    sent_milestones,
                    thresholds
                )
                
                if should_send:
                    # Calculate estimated wait time
                    from datetime import datetime, timezone, timedelta
                    
                    # Get wait time per person (reuse logic from get_status)
                    wait_per_person = 5  # Default
                    try:
                        stats_resp = stats_table.get_item(Key={'queueId': queue_id})
                        if 'Item' in stats_resp:
                            config = stats_resp['Item']
                            start_hour = int(config.get('config_start_hour', 17))
                            end_hour = int(config.get('config_end_hour', 22))
                            
                            utc_now = datetime.now(timezone.utc)
                            local_time = utc_now + timedelta(hours=-4)
                            current_hour = local_time.hour
                            
                            if start_hour <= current_hour < end_hour:
                                wait_per_person = 15
                    except Exception:
                        pass
                    
                    estimated_wait = current_position * wait_per_person
                    
                    # Send notification
                    if send_position_notification(topic_arn, ticket_number, current_position, estimated_wait):
                        # Update notification record
                        sent_milestones.append(milestone)
                        notifications_table.update_item(
                            Key={'ticketNumber': ticket_number},
                            UpdateExpression="SET lastNotifiedPosition = :pos, notificationsSent = :sent",
                            ExpressionAttributeValues={
                                ':pos': current_position,
                                ':sent': sent_milestones
                            }
                        )
                        notifications_sent_count += 1
                        
            except Exception as e:
                print(f"Error processing ticket {ticket_number}: {str(e)}")
                continue
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Notification check complete',
                'ticketsProcessed': len(waiting_tickets),
                'notificationsSent': notifications_sent_count
            })
        }
        
    except Exception as e:
        print(f"Error in notification lambda: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }