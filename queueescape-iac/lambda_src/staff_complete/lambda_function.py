import json
import boto3
import os

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['QUEUE_ENTRIES_TABLE'])

def lambda_handler(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        ticket_number = body.get('ticketNumber')
        queue_id = body.get('queueId', 'main_queue')  
              
        if not ticket_number:
            return {'statusCode': 400, 'body': json.dumps({'error': 'ticketNumber required'})}

        # Update Status to COMPLETED
        table.update_item(
            Key={'queueId': queue_id, 'ticketNumber': ticket_number},
            UpdateExpression="set #s = :val",
            ExpressionAttributeNames={'#s': 'status'},
            ExpressionAttributeValues={':val': 'COMPLETED'}
        )
        
        return {
            'statusCode': 200,
            "headers": {
                    "Access-Control-Allow-Origin": "*",  # or "http://localhost:3000"
                    "Access-Control-Allow-Headers": "Content-Type",
                    "Access-Control-Allow-Methods": "OPTIONS,GET,POST",
                    "Content-Type": "application/json"},
            'body': json.dumps({'message': 'Ticket completed', 'ticketNumber': ticket_number})
        }
    except Exception as e:
        return {'statusCode': 500, 
                "headers": {
                    "Access-Control-Allow-Origin": "*",  # or "http://localhost:3000"
                    "Access-Control-Allow-Headers": "Content-Type",
                    "Access-Control-Allow-Methods": "OPTIONS,GET,POST",
                    "Content-Type": "application/json"},
                'body': json.dumps({'error': str(e)})}