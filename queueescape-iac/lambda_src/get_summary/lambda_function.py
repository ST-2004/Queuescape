import json
import boto3
import os
from boto3.dynamodb.conditions import Key, Attr
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['QUEUE_ENTRIES_TABLE'])

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj)
        return super(DecimalEncoder, self).default(obj)

def lambda_handler(event, context):
    try:
        params = event.get('queryStringParameters') or {}
        queue_id = params.get('queueId', 'main_queue')        
        # Scan for everyone not completed
        # valid statuses: WAITING, BEING_SERVED
        response = table.scan(
            FilterExpression=Key('queueId').eq(queue_id) & Attr('status').ne('COMPLETED')
        )
        
        items = response.get('Items', [])
        
        # Sort by join time
        items.sort(key=lambda x: x['joinTime'])

        return {
            'statusCode': 200,
            "headers": {
                    "Access-Control-Allow-Origin": "*",  # or "http://localhost:3000"
                    "Access-Control-Allow-Headers": "Content-Type",
                    "Access-Control-Allow-Methods": "OPTIONS,GET,POST",
                    "Content-Type": "application/json"},            
            'body': json.dumps({'tickets': items}, cls=DecimalEncoder)
        }
    except Exception as e:
        return {'statusCode': 500, 
                "headers": {
                    "Access-Control-Allow-Origin": "*",  # or "http://localhost:3000"
                    "Access-Control-Allow-Headers": "Content-Type",
                    "Access-Control-Allow-Methods": "OPTIONS,GET,POST",
                    "Content-Type": "application/json"},
                'body': json.dumps({'error': str(e)})}