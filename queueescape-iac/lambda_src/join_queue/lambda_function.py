import json
import boto3
import os
import time
import uuid
# No extra imports needed if we use integer microseconds

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['QUEUE_ENTRIES_TABLE'])

def lambda_handler(event, context):
    try:
        # Parse body
        body = json.loads(event.get('body', '{}'))
        email = body.get('email', '')
        
        # Generate Ticket Details
        queue_id = body.get('queueId', 'main_queue')
        ticket_number = str(uuid.uuid4())[:8]
        
        # FIX: Multiply by 1,000,000 to get microseconds. 
        # This ensures even if users click at the same second, the order is kept.
        timestamp = int(time.time() * 1000000)
        
        item = {
            'queueId': queue_id,
            'ticketNumber': ticket_number,
            'status': 'WAITING',
            'joinTime': timestamp,
            'email': email
        }
        
        # Save to DynamoDB
        table.put_item(Item=item)
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'ticketNumber': ticket_number,
                'position': 'Calculated next poll',
                'message': 'Joined successfully'
            })
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }