import json
import boto3
import os
from boto3.dynamodb.conditions import Key
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['QUEUE_ENTRIES_TABLE'])
sns = boto3.client('sns')
TOPIC_ARN = os.environ['ALERTS_TOPIC_ARN']

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj)
        return super(DecimalEncoder, self).default(obj)

def lambda_handler(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        queue_id = body.get('queueId', 'main_queue')        
        # 1. Find oldest WAITING ticket
        scan_resp = table.scan(
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
        
        # 2. Update Status
        table.update_item(
            Key={'queueId': queue_id, 'ticketNumber': next_person['ticketNumber']},
            UpdateExpression="set #s = :val",
            ExpressionAttributeNames={'#s': 'status'},
            ExpressionAttributeValues={':val': 'BEING_SERVED'}
        )
        
        # 3. Notify via SNS
        if next_person.get('email'):
            try:
                sns.publish(
                    TopicArn=TOPIC_ARN,
                    Message=f"Hello! It is your turn. Please proceed to the counter.\nTicket: {next_person['ticketNumber']}",
                    Subject="Your Turn - QueueEscape"
                )
            except Exception as sns_error:
                print(f"SNS Error: {sns_error}")

        return {
            'statusCode': 200,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'served': next_person}, cls=DecimalEncoder)
        }
    except Exception as e:
        print(e)
        return {'statusCode': 500, 'headers': {'Access-Control-Allow-Origin': '*'}, 'body': json.dumps({'error': str(e)})}