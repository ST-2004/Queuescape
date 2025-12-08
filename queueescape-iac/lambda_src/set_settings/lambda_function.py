import json
import boto3
import os

dynamodb = boto3.resource('dynamodb')
stats_table = dynamodb.Table(os.environ['QUEUE_STATS_TABLE'])

def lambda_handler(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        queue_id = "main_queue"
        
        # Staff sends "peak_period": "MORNING", "AFTERNOON", or "EVENING"
        peak_period = body.get('peak_period', 'EVENING').upper()
        
        # Store this in DynamoDB QueueStats
        # We also define what hours constitute these periods
        hours_map = {
            "MORNING": {"start": 8, "end": 12},
            "AFTERNOON": {"start": 12, "end": 17},
            "EVENING": {"start": 17, "end": 22}
        }
        
        selected_hours = hours_map.get(peak_period, hours_map["EVENING"])
        
        stats_table.put_item(
            Item={
                'queueId': queue_id,
                'config_peak_period': peak_period,
                'config_start_hour': selected_hours['start'],
                'config_end_hour': selected_hours['end']
            }
        )
        
        return {
            'statusCode': 200,
            "headers": {
                    "Access-Control-Allow-Origin": "*",  # or "http://localhost:3000"
                    "Access-Control-Allow-Headers": "Content-Type",
                    "Access-Control-Allow-Methods": "OPTIONS,GET,POST",
                    "Content-Type": "application/json"},
            'body': json.dumps({
                'message': f"Queue settings updated. Peak time set to {peak_period}",
                'details': selected_hours
            })
        }
    except Exception as e:
        return {'statusCode': 500, 
                "headers": {
                    "Access-Control-Allow-Origin": "*",  # or "http://localhost:3000"
                    "Access-Control-Allow-Headers": "Content-Type",
                    "Access-Control-Allow-Methods": "OPTIONS,GET,POST",
                    "Content-Type": "application/json"},
                'body': json.dumps({'error': str(e)})}