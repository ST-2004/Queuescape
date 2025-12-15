import json
import boto3
import os
import time
import uuid

dynamodb = boto3.resource('dynamodb')
entries_table = dynamodb.Table(os.environ['QUEUE_ENTRIES_TABLE'])
notifications_table = dynamodb.Table(os.environ['USER_NOTIFICATIONS_TABLE'])
sns = boto3.client('sns')

def create_user_topic(ticket_number, email):
    """
    Create a unique SNS topic for this user and subscribe their email.
    Returns the topic ARN.
    """
    try:
        # Create topic with unique name
        topic_name = f"QueueUser-{ticket_number}"
        response = sns.create_topic(Name=topic_name)
        topic_arn = response['TopicArn']
        
        # Subscribe the email
        sns.subscribe(
            TopicArn=topic_arn,
            Protocol='email',
            Endpoint=email
        )
        
        print(f"Created topic {topic_arn} and subscribed {email}")
        return topic_arn
        
    except Exception as e:
        print(f"Error creating topic: {str(e)}")
        return None

def lambda_handler(event, context):
    try:
        # Parse body
        body = json.loads(event.get('body', '{}'))
        email = body.get('email', '').strip()
        
        if not email:
            return {
                'statusCode': 400,
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Content-Type",
                    "Access-Control-Allow-Methods": "OPTIONS,GET,POST",
                    "Content-Type": "application/json"
                },
                'body': json.dumps({'error': 'Email is required'})
            }
        
        # Generate Ticket Details
        queue_id = body.get('queueId', 'main_queue')
        ticket_number = str(uuid.uuid4())[:8]
        timestamp = int(time.time() * 1000000)
        
        # Create SNS topic for this user
        topic_arn = create_user_topic(ticket_number, email)
        
        # Save to QueueEntries
        item = {
            'queueId': queue_id,
            'ticketNumber': ticket_number,
            'status': 'WAITING',
            'joinTime': timestamp,
            'email': email
        }
        entries_table.put_item(Item=item)
        
        # Save to UserNotifications with notification tracking
        notification_item = {
            'ticketNumber': ticket_number,
            'email': email,
            'topicArn': topic_arn if topic_arn else 'NONE',
            'subscriptionConfirmed': False,
            'notificationsSent': [],  # Track which milestones were sent
            'lastNotifiedPosition': 999999  # Start high
        }
        notifications_table.put_item(Item=notification_item)
        
        return {
            'statusCode': 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "OPTIONS,GET,POST",
                "Content-Type": "application/json"
            },
            'body': json.dumps({
                'ticketNumber': ticket_number,
                'position': 'Calculated on next poll',
                'message': 'Joined successfully! Check your email to confirm subscription for notifications.',
                'subscriptionNote': 'You will receive a confirmation email. Please confirm to get position updates.'
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "OPTIONS,GET,POST",
                "Content-Type": "application/json"
            },
            'body': json.dumps({'error': str(e)})
        }