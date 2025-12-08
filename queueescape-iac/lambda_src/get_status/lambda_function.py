import json
import boto3
import os
from boto3.dynamodb.conditions import Key
from decimal import Decimal
from datetime import datetime, timezone, timedelta

dynamodb = boto3.resource('dynamodb')
entries_table = dynamodb.Table(os.environ['QUEUE_ENTRIES_TABLE'])
stats_table = dynamodb.Table(os.environ['QUEUE_STATS_TABLE'])

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def get_wait_time_per_person(queue_id):
    """
    Fetches staff settings from DB and compares with current time.
    """
    # 1. Default values (if staff never set anything)
    current_wait_per_person = 5 # Standard
    
    try:
        # 2. Fetch Settings
        response = stats_table.get_item(Key={'queueId': queue_id})
        
        if 'Item' in response:
            config = response['Item']
            start_hour = int(config.get('config_start_hour', 17))
            end_hour = int(config.get('config_end_hour', 22))
            
            # 3. Check Current Time (Adjust -4 for your Timezone)
            utc_now = datetime.now(timezone.utc)
            local_time = utc_now + timedelta(hours=-4) 
            current_hour = local_time.hour
            
            # 4. Logic: Are we in the peak window?
            if start_hour <= current_hour < end_hour:
                return 15 # Peak Time (Slow)
            else:
                return 5  # Off-Peak (Fast)
                
    except Exception as e:
        print(f"Error fetching stats: {e}")
        
    return current_wait_per_person

def lambda_handler(event, context):
    try:
        ticket_number = event['pathParameters']['ticketNumber']
        queue_id = event['pathParameters'].get('queueId', 'main_queue')
        # 1. Get Ticket
        response = entries_table.get_item(Key={'queueId': queue_id, 'ticketNumber': ticket_number})
        if 'Item' not in response:
            return {'statusCode': 404, 'headers': {'Access-Control-Allow-Origin': '*'}, 'body': json.dumps({'error': 'Not found'})}
            
        my_ticket = response['Item']
        
        # 2. Calculate Position
        scan_resp = entries_table.scan(
            FilterExpression=Key('status').eq('WAITING') & Key('queueId').eq(queue_id)
        )
        
        position = 0
        for item in scan_resp['Items']:
            if item['joinTime'] < my_ticket['joinTime']:
                position += 1
        
        if my_ticket['status'] == 'BEING_SERVED':
            position = 0

        # 3. Dynamic Calculation
        minutes_per_person = get_wait_time_per_person(queue_id)
        total_wait = position * minutes_per_person

        return {
            'statusCode': 200,

            "headers": {
            "Access-Control-Allow-Origin": "*",  # or "http://localhost:3000"
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Methods": "OPTIONS,GET,POST",
            "Content-Type": "application/json"},

            'body': json.dumps({
                'ticketNumber': ticket_number,
                'status': my_ticket['status'],
                'position': position,
                'estimatedWaitMinutes': total_wait,
                'calculationMode': f"{minutes_per_person} mins/person"
            }, cls=DecimalEncoder)
        }
    except Exception as e:
        return {'statusCode': 500,
                "headers": {
                    "Access-Control-Allow-Origin": "*",  # or "http://localhost:3000"
                    "Access-Control-Allow-Headers": "Content-Type",
                    "Access-Control-Allow-Methods": "OPTIONS,GET,POST",
                    "Content-Type": "application/json"},
                'body': json.dumps({'error': str(e)})}