import boto3
import json
import os
import sys
import unittest
from moto import mock_aws
import time

# Add lambda_src to path so we can import the functions
sys.path.append('./lambda_src')

@mock_aws
class TestQueueSystem(unittest.TestCase):

    def setUp(self):
        """Runs before every test. Sets up a fake DynamoDB and SNS."""
        # 1. Setup Environment Variables
        os.environ['QUEUE_ENTRIES_TABLE'] = 'QueueEntries'
        os.environ['QUEUE_STATS_TABLE'] = 'QueueStats'
        os.environ['ALERTS_TOPIC_ARN'] = 'arn:aws:sns:us-east-1:123456789012:queueescape-alerts'
        os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

        # 2. Create Fake DynamoDB Tables
        self.dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        self.entries_table = self.dynamodb.create_table(
            TableName='QueueEntries',
            KeySchema=[{'AttributeName': 'queueId', 'KeyType': 'HASH'}, {'AttributeName': 'ticketNumber', 'KeyType': 'RANGE'}],
            AttributeDefinitions=[{'AttributeName': 'queueId', 'AttributeType': 'S'}, {'AttributeName': 'ticketNumber', 'AttributeType': 'S'}],
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )
        self.stats_table = self.dynamodb.create_table(
            TableName='QueueStats',
            KeySchema=[{'AttributeName': 'queueId', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'queueId', 'AttributeType': 'S'}],
            ProvisionedThroughput={'ReadCapacityUnits': 1, 'WriteCapacityUnits': 1}
        )

        # 3. Create Fake SNS
        self.sns = boto3.client('sns', region_name='us-east-1')
        self.sns.create_topic(Name='queueescape-alerts')

    def test_full_flow(self):
        print("\n--- TESTING FULL FLOW ---")

        # --- IMPORT YOUR LAMBDAS HERE (Must be after mock setup) ---
        from join_queue import lambda_function as join_lambda
        from get_status import lambda_function as status_lambda
        from staff_next import lambda_function as next_lambda
        from staff_complete import lambda_function as complete_lambda
        from get_summary import lambda_function as summary_lambda
        
        # 1. USER A JOINS
        print("1. User A Joining...")
        event_a = {'body': json.dumps({'email': 'userA@test.com'})}
        response_a = join_lambda.lambda_handler(event_a, None)
        body_a = json.loads(response_a['body'])
        ticket_a = body_a['ticketNumber']
        self.assertEqual(response_a['statusCode'], 200)
        print(f"   User A Ticket: {ticket_a}")

        time.sleep(0.1)

        # 2. USER B JOINS
        print("2. User B Joining...")
        event_b = {'body': json.dumps({'email': 'userB@test.com'})}
        response_b = join_lambda.lambda_handler(event_b, None)
        body_b = json.loads(response_b['body'])
        ticket_b = body_b['ticketNumber']
        print(f"   User B Ticket: {ticket_b}")

        # 3. CHECK STATUS (User B should be behind User A)
        print("3. Checking User B Status...")
        event_status = {'pathParameters': {'ticketNumber': ticket_b}}
        response_status = status_lambda.lambda_handler(event_status, None)
        body_status = json.loads(response_status['body'])
        
        print(f"   User B Position: {body_status['position']}")
        # User B should be at position 1 (User A is at 0 ahead of them)
        self.assertEqual(body_status['position'], 1) 
        self.assertEqual(body_status['status'], 'WAITING')

        # 4. STAFF CHECKS SUMMARY
        print("4. Staff checking summary...")
        response_summary = summary_lambda.lambda_handler({}, None)
        body_summary = json.loads(response_summary['body'])
        print(f"   People in line: {len(body_summary['tickets'])}")
        self.assertEqual(len(body_summary['tickets']), 2)

        # 5. STAFF CALLS NEXT (Should pick User A)
        print("5. Staff calling Next...")
        response_next = next_lambda.lambda_handler({}, None)
        body_next = json.loads(response_next['body'])
        served_ticket = body_next['served']['ticketNumber']
        print(f"   Serving Ticket: {served_ticket}")
        self.assertEqual(served_ticket, ticket_a)

        # 6. CHECK STATUS AGAIN (User B should now be at position 0)
        print("6. Checking User B Status again...")
        response_status_2 = status_lambda.lambda_handler(event_status, None)
        body_status_2 = json.loads(response_status_2['body'])
        print(f"   User B New Position: {body_status_2['position']}")
        self.assertEqual(body_status_2['position'], 0)

        # 7. STAFF COMPLETES USER A
        print("7. Staff completing User A...")
        event_complete = {'body': json.dumps({'ticketNumber': ticket_a})}
        complete_lambda.lambda_handler(event_complete, None)
        
        # Check that User A is COMPLETED in DB
        db_item = self.entries_table.get_item(Key={'queueId': 'main_queue', 'ticketNumber': ticket_a})
        self.assertEqual(db_item['Item']['status'], 'COMPLETED')
        print("   User A marked COMPLETED.")
    
    def test_large_queue(self):
        print("\n--- TESTING LARGE QUEUE (10 Users) ---")
        
        import time
        from join_queue import lambda_function as join_lambda
        from get_status import lambda_function as status_lambda
        from staff_next import lambda_function as next_lambda

        # 1. JOIN PHASE: 10 Users join rapidly
        tickets = []
        for i in range(10):
            email = f"user{i}@test.com"
            event = {'body': json.dumps({'email': email})}
            
            response = join_lambda.lambda_handler(event, None)
            ticket = json.loads(response['body'])['ticketNumber']
            tickets.append(ticket)
            
            print(f"   User {i} joined. Ticket: {ticket}")
            time.sleep(0.01) # Small pause to ensure unique timestamps

        # 2. VERIFY POSITIONS (Initial State)
        # The last person (User 9) should have 9 people ahead of them (Users 0-8)
        print("\n   Checking User 9's position...")
        event_check = {'pathParameters': {'ticketNumber': tickets[9]}}
        resp = status_lambda.lambda_handler(event_check, None)
        pos = json.loads(resp['body'])['position']
        print(f"   User 9 Position: {pos} (Expected: 9)")
        self.assertEqual(pos, 9)

        # 3. SERVICE PHASE: Staff serves 3 people (User 0, 1, 2)
        print("\n   Staff serving 3 people...")
        for i in range(3):
            next_lambda.lambda_handler({}, None)
            print(f"   Served User {i}")

        # 4. VERIFY POSITIONS (After Shift)
        # User 9 should now have: 
        # Original 9 ahead - 3 served = 6 people ahead (Users 3,4,5,6,7,8)
        print("\n   Checking User 9's position again...")
        resp = status_lambda.lambda_handler(event_check, None)
        new_pos = json.loads(resp['body'])['position']
        print(f"   User 9 New Position: {new_pos} (Expected: 6)")
        self.assertEqual(new_pos, 6)

        # 5. VERIFY THE NEXT PERSON (User 3)
        # User 3 was originally at pos 3. Now they should be at pos 0 (Next in line)
        print("   Checking User 3's position...")
        event_check_3 = {'pathParameters': {'ticketNumber': tickets[3]}}
        resp_3 = status_lambda.lambda_handler(event_check_3, None)
        pos_3 = json.loads(resp_3['body'])['position']
        print(f"   User 3 Position: {pos_3} (Expected: 0)")
        self.assertEqual(pos_3, 0)

if __name__ == '__main__':
    unittest.main()