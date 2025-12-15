import json
import boto3
import os
from boto3.dynamodb.conditions import Key
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
entries_table = dynamodb.Table(os.environ['QUEUE_ENTRIES_TABLE'])
notifications_table = dynamodb.Table(os.environ['USER_NOTIFICATIONS_TABLE'])
sns = boto3.client('sns')

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj)
        return super(DecimalEncoder, self).default(obj)

def send_your_turn_notification(ticket_number):
    """
    Send immediate notification that it's the user's turn.
    """
    try:
        notif_resp = notifications_table.get_item(Key={'ticketNumber': ticket_number})
        
        if 'Item' in notif_resp:
            notif_record = notif_resp['Item']
            topic_arn = notif_record.get('topicArn')
            
            if topic_arn and topic_arn != 'NONE':
                message = f"""
🎉 YOUR TURN HAS ARRIVED!

Ticket Number: {ticket_number}

Please proceed to the service counter IMMEDIATELY.

Thank you for your patience!
- QueueEscape Team
                """
                
                sns.publish(
                    TopicArn=topic_arn,
                    Message=message,
                    Subject="🔔 YOUR TURN - Please Proceed Now!"
                )
                
                # Update notification record
                notifications_table.update_item(
                    Key={'ticketNumber': ticket_number},
                    UpdateExpression="SET lastNotifiedPosition = :pos",
                    ExpressionAttributeValues={':pos': 0}
                )
                
                print(f"Sent 'your turn' notification for {ticket_number}")
                
    except Exception as e:
        print(f"Error sending your-turn notification: {str(e)}")

def lambda_handler(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        queue_id = body.get('queueId', 'main_queue')        
        
        # Find oldest WAITING ticket
        scan_resp = entries_table.scan(
            FilterExpression=Key('status').eq('WAITING') & Key('queueId').eq(queue_id)
        )
        items = scan_resp.get('Items', [])
        
        if not items:
            return {
                'statusCode': 200, 
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'message': 'No waiting tickets'})
            }
            
        # Sort to find the first one
        items.sort(key=lambda x: x['joinTime'])
        next_person = items[0]
        
        # Update Status to BEING_SERVED
        entries_table.update_item(
            Key={'queueId': queue_id, 'ticketNumber': next_person['ticketNumber']},
            UpdateExpression="set #s = :val",
            ExpressionAttributeNames={'#s': 'status'},
            ExpressionAttributeValues={':val': 'BEING_SERVED'}
        )
        
        # Send immediate notification
        send_your_turn_notification(next_person['ticketNumber'])

        return {
            'statusCode': 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Allow-Methods": "OPTIONS,GET,POST",
                "Content-Type": "application/json"
            },
            'body': json.dumps({'served': next_person}, cls=DecimalEncoder)
        }
        
    except Exception as e:
        print(e)
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