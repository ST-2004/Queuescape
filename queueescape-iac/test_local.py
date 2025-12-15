#!/usr/bin/env python3
"""
QueueEscape SNS Integration Test Suite
Complete end-to-end testing of the notification system
"""

import boto3
import json
import time
import sys
from datetime import datetime
from decimal import Decimal
from botocore.exceptions import ClientError

# Configuration
QUEUE_ID = "main_queue"
TEST_EMAIL = "s.tiwari.fr@gmail.com"  # CHANGE THIS
API_GATEWAY_ENDPOINT = "https://tbmndj28ib.execute-api.us-east-1.amazonaws.com/dev"  # CHANGE THIS

# AWS Clients
dynamodb = boto3.resource('dynamodb')
dynamodb_client = boto3.client('dynamodb')
sns = boto3.client('sns')
lambda_client = boto3.client('lambda')
events = boto3.client('events')
logs = boto3.client('logs')

# Color codes for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}\n")

def print_test(text):
    print(f"{Colors.BLUE}🧪 {text}{Colors.END}")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def print_info(text):
    print(f"{Colors.CYAN}ℹ️  {text}{Colors.END}")

# Test Results Tracker
test_results = {
    'passed': 0,
    'failed': 0,
    'warnings': 0
}

def test_passed():
    test_results['passed'] += 1

def test_failed():
    test_results['failed'] += 1

def test_warning():
    test_results['warnings'] += 1

# ============================================================================
# TEST 1: Infrastructure Validation
# ============================================================================

def test_dynamodb_tables():
    """Verify all required DynamoDB tables exist"""
    print_test("Test 1: Checking DynamoDB Tables")
    
    required_tables = ['QueueEntries', 'QueueStats', 'UserNotifications']
    
    for table_name in required_tables:
        try:
            table = dynamodb.Table(table_name)
            table.load()
            print_success(f"Table '{table_name}' exists")
            
            # Check table status
            if table.table_status == 'ACTIVE':
                print_info(f"  Status: ACTIVE")
            else:
                print_warning(f"  Status: {table.table_status}")
                test_warning()
                
            test_passed()
        except ClientError as e:
            print_error(f"Table '{table_name}' not found: {e}")
            test_failed()
            return False
    
    return True

def test_lambda_functions():
    """Verify all required Lambda functions exist and are configured correctly"""
    print_test("\nTest 2: Checking Lambda Functions")
    
    required_functions = {
        'JoinQueueLambda': ['QUEUE_ENTRIES_TABLE', 'USER_NOTIFICATIONS_TABLE'],
        'GetStatusLambda': ['QUEUE_ENTRIES_TABLE', 'QUEUE_STATS_TABLE'],
        'SendNotificationsLambda': ['QUEUE_ENTRIES_TABLE', 'USER_NOTIFICATIONS_TABLE', 'NOTIFICATION_THRESHOLDS'],
        'StaffNextLambda': ['QUEUE_ENTRIES_TABLE', 'USER_NOTIFICATIONS_TABLE'],
        'StaffCompleteLambda': ['QUEUE_ENTRIES_TABLE', 'USER_NOTIFICATIONS_TABLE']
    }
    
    for func_name, required_env_vars in required_functions.items():
        try:
            response = lambda_client.get_function(FunctionName=func_name)
            print_success(f"Function '{func_name}' exists")
            
            # Check environment variables
            env_vars = response['Configuration'].get('Environment', {}).get('Variables', {})
            
            for env_var in required_env_vars:
                if env_var in env_vars:
                    print_info(f"  ✓ {env_var}: {env_vars[env_var]}")
                else:
                    print_warning(f"  ✗ Missing env var: {env_var}")
                    test_warning()
            
            # Check VPC configuration
            vpc_config = response['Configuration'].get('VpcConfig', {})
            if vpc_config.get('SubnetIds'):
                print_info(f"  ✓ VPC configured with {len(vpc_config['SubnetIds'])} subnets")
            else:
                print_warning(f"  ✗ No VPC configuration")
                test_warning()
            
            test_passed()
            
        except ClientError as e:
            print_error(f"Function '{func_name}' not found: {e}")
            test_failed()
            return False
    
    return True

def test_sns_topic():
    """Verify SNS topic exists"""
    print_test("\nTest 3: Checking SNS Topics")
    
    try:
        response = sns.list_topics()
        topics = response.get('Topics', [])
        
        alerts_topic = [t for t in topics if 'queueescape-alerts' in t['TopicArn']]
        
        if alerts_topic:
            print_success(f"Main alerts topic exists: {alerts_topic[0]['TopicArn']}")
            test_passed()
        else:
            print_error("Main alerts topic not found")
            test_failed()
            return False
        
        # Check for any user topics
        user_topics = [t for t in topics if 'QueueUser-' in t['TopicArn']]
        if user_topics:
            print_info(f"Found {len(user_topics)} existing user topics")
        
        return True
        
    except ClientError as e:
        print_error(f"Error checking SNS topics: {e}")
        test_failed()
        return False

def test_eventbridge_rule():
    """Verify EventBridge rule is configured and enabled"""
    print_test("\nTest 4: Checking EventBridge Rule")
    
    try:
        rule = events.describe_rule(Name='queueescape-notification-scheduler')
        
        print_success(f"EventBridge rule exists")
        print_info(f"  State: {rule['State']}")
        print_info(f"  Schedule: {rule.get('ScheduleExpression', 'N/A')}")
        
        if rule['State'] == 'ENABLED':
            print_success("  Rule is ENABLED")
        else:
            print_warning("  Rule is DISABLED")
            test_warning()
        
        # Check targets
        targets = events.list_targets_by_rule(Rule='queueescape-notification-scheduler')
        if targets['Targets']:
            print_success(f"  Found {len(targets['Targets'])} target(s)")
            for target in targets['Targets']:
                print_info(f"    - {target['Arn']}")
        else:
            print_error("  No targets configured")
            test_failed()
            return False
        
        test_passed()
        return True
        
    except ClientError as e:
        print_error(f"EventBridge rule not found: {e}")
        test_failed()
        return False

# ============================================================================
# TEST 2: Functional Testing
# ============================================================================

def test_join_queue():
    """Test joining the queue and SNS topic creation"""
    print_test("\nTest 5: Testing Queue Join & SNS Topic Creation")
    
    try:
        # Invoke JoinQueue Lambda directly
        payload = {
            'body': json.dumps({
                'queueId': QUEUE_ID,
                'email': TEST_EMAIL
            })
        }
        
        print_info(f"Joining queue with email: {TEST_EMAIL}")
        
        response = lambda_client.invoke(
            FunctionName='JoinQueueLambda',
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        result = json.loads(response['Payload'].read())
        
        if result.get('statusCode') == 200:
            body = json.loads(result['body'])
            ticket_number = body.get('ticketNumber')
            
            print_success(f"Successfully joined queue")
            print_info(f"  Ticket Number: {ticket_number}")
            print_info(f"  Message: {body.get('message')}")
            
            # Verify DynamoDB entry
            time.sleep(2)  # Wait for writes to propagate
            
            # Check QueueEntries
            entries_table = dynamodb.Table('QueueEntries')
            entry = entries_table.get_item(
                Key={'queueId': QUEUE_ID, 'ticketNumber': ticket_number}
            )
            
            if 'Item' in entry:
                print_success(f"  ✓ Entry found in QueueEntries table")
                print_info(f"    Status: {entry['Item']['status']}")
            else:
                print_error(f"  ✗ Entry NOT found in QueueEntries table")
                test_failed()
                return None
            
            # Check UserNotifications
            notif_table = dynamodb.Table('UserNotifications')
            notif = notif_table.get_item(
                Key={'ticketNumber': ticket_number}
            )
            
            if 'Item' in notif:
                print_success(f"  ✓ Entry found in UserNotifications table")
                topic_arn = notif['Item'].get('topicArn')
                print_info(f"    Topic ARN: {topic_arn}")
                
                # Verify SNS topic exists
                if topic_arn and topic_arn != 'NONE':
                    try:
                        attrs = sns.get_topic_attributes(TopicArn=topic_arn)
                        print_success(f"  ✓ SNS topic verified")
                        
                        # Check subscriptions
                        subs = sns.list_subscriptions_by_topic(TopicArn=topic_arn)
                        if subs['Subscriptions']:
                            print_success(f"  ✓ Found {len(subs['Subscriptions'])} subscription(s)")
                            for sub in subs['Subscriptions']:
                                print_info(f"    - {sub['Protocol']}: {sub['Endpoint']} ({sub['SubscriptionArn']})")
                        else:
                            print_warning(f"  No subscriptions yet")
                    except ClientError as e:
                        print_error(f"  ✗ SNS topic not found: {e}")
                        test_failed()
                        return None
                else:
                    print_error(f"  ✗ Invalid topic ARN")
                    test_failed()
                    return None
            else:
                print_error(f"  ✗ Entry NOT found in UserNotifications table")
                test_failed()
                return None
            
            test_passed()
            return ticket_number
            
        else:
            print_error(f"Failed to join queue: {result}")
            test_failed()
            return None
            
    except Exception as e:
        print_error(f"Error joining queue: {e}")
        test_failed()
        return None

def test_notification_lambda(ticket_number):
    """Test the SendNotifications Lambda function"""
    print_test("\nTest 6: Testing Notification Lambda")
    
    try:
        print_info("Invoking SendNotificationsLambda...")
        
        response = lambda_client.invoke(
            FunctionName='SendNotificationsLambda',
            InvocationType='RequestResponse',
            Payload=json.dumps({})
        )
        
        result = json.loads(response['Payload'].read())
        
        if result.get('statusCode') == 200:
            body = json.loads(result['body'])
            print_success("SendNotifications Lambda executed successfully")
            print_info(f"  Tickets Processed: {body.get('ticketsProcessed', 0)}")
            print_info(f"  Notifications Sent: {body.get('notificationsSent', 0)}")
            
            # Check if notification was recorded
            time.sleep(2)
            
            notif_table = dynamodb.Table('UserNotifications')
            notif = notif_table.get_item(
                Key={'ticketNumber': ticket_number}
            )
            
            if 'Item' in notif:
                last_pos = notif['Item'].get('lastNotifiedPosition', 999999)
                sent = notif['Item'].get('notificationsSent', [])
                
                print_info(f"  Last Notified Position: {last_pos}")
                print_info(f"  Notifications Sent: {sent}")
                
                if last_pos < 999999:
                    print_success("  ✓ Notification status updated")
                else:
                    print_warning("  Notification not sent (might be outside threshold)")
            
            test_passed()
            return True
        else:
            print_error(f"Lambda execution failed: {result}")
            test_failed()
            return False
            
    except Exception as e:
        print_error(f"Error invoking notification lambda: {e}")
        test_failed()
        return False

def test_staff_next(ticket_number):
    """Test the Staff Next function"""
    print_test("\nTest 7: Testing Staff Next (Your Turn Notification)")
    
    try:
        payload = {
            'body': json.dumps({
                'queueId': QUEUE_ID
            })
        }
        
        print_info("Calling next user in queue...")
        
        response = lambda_client.invoke(
            FunctionName='StaffNextLambda',
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        result = json.loads(response['Payload'].read())
        
        if result.get('statusCode') == 200:
            body = json.loads(result['body'])
            served_ticket = body.get('served', {})
            
            print_success("Staff Next executed successfully")
            print_info(f"  Served Ticket: {served_ticket.get('ticketNumber')}")
            
            # Verify status changed to BEING_SERVED
            time.sleep(2)
            
            entries_table = dynamodb.Table('QueueEntries')
            entry = entries_table.get_item(
                Key={'queueId': QUEUE_ID, 'ticketNumber': ticket_number}
            )
            
            if 'Item' in entry:
                status = entry['Item'].get('status')
                print_info(f"  Updated Status: {status}")
                
                if status == 'BEING_SERVED':
                    print_success("  ✓ Status updated to BEING_SERVED")
                    test_passed()
                    return True
                else:
                    print_warning(f"  Status is {status}, expected BEING_SERVED")
                    test_warning()
                    return False
            else:
                print_error("  ✗ Entry not found")
                test_failed()
                return False
        else:
            print_error(f"Staff Next failed: {result}")
            test_failed()
            return False
            
    except Exception as e:
        print_error(f"Error calling staff next: {e}")
        test_failed()
        return False

def test_staff_complete(ticket_number):
    """Test the Staff Complete function and cleanup"""
    print_test("\nTest 8: Testing Staff Complete (Cleanup)")
    
    try:
        payload = {
            'body': json.dumps({
                'queueId': QUEUE_ID,
                'ticketNumber': ticket_number
            })
        }
        
        print_info("Completing ticket and cleaning up...")
        
        # Get topic ARN before deletion
        notif_table = dynamodb.Table('UserNotifications')
        notif = notif_table.get_item(Key={'ticketNumber': ticket_number})
        topic_arn = None
        
        if 'Item' in notif:
            topic_arn = notif['Item'].get('topicArn')
        
        response = lambda_client.invoke(
            FunctionName='StaffCompleteLambda',
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        result = json.loads(response['Payload'].read())
        
        if result.get('statusCode') == 200:
            print_success("Staff Complete executed successfully")
            
            # Verify status changed to COMPLETED
            time.sleep(2)
            
            entries_table = dynamodb.Table('QueueEntries')
            entry = entries_table.get_item(
                Key={'queueId': QUEUE_ID, 'ticketNumber': ticket_number}
            )
            
            if 'Item' in entry:
                status = entry['Item'].get('status')
                print_info(f"  Updated Status: {status}")
                
                if status == 'COMPLETED':
                    print_success("  ✓ Status updated to COMPLETED")
                else:
                    print_warning(f"  Status is {status}, expected COMPLETED")
                    test_warning()
            
            # Verify notification record deleted
            notif = notif_table.get_item(Key={'ticketNumber': ticket_number})
            
            if 'Item' not in notif:
                print_success("  ✓ UserNotifications record deleted")
            else:
                print_warning("  UserNotifications record still exists")
                test_warning()
            
            # Verify SNS topic deleted
            if topic_arn and topic_arn != 'NONE':
                try:
                    sns.get_topic_attributes(TopicArn=topic_arn)
                    print_warning("  SNS topic still exists (may take time to delete)")
                    test_warning()
                except ClientError as e:
                    if 'NotFound' in str(e):
                        print_success("  ✓ SNS topic deleted")
                    else:
                        print_error(f"  Error checking topic: {e}")
            
            test_passed()
            return True
        else:
            print_error(f"Staff Complete failed: {result}")
            test_failed()
            return False
            
    except Exception as e:
        print_error(f"Error completing ticket: {e}")
        test_failed()
        return False

def test_cloudwatch_logs():
    """Check CloudWatch logs for errors"""
    print_test("\nTest 9: Checking CloudWatch Logs for Errors")
    
    lambda_functions = [
        'JoinQueueLambda',
        'SendNotificationsLambda',
        'StaffNextLambda',
        'StaffCompleteLambda'
    ]
    
    has_errors = False
    
    for func_name in lambda_functions:
        log_group = f'/aws/lambda/{func_name}'
        
        try:
            # Get recent log events
            end_time = int(time.time() * 1000)
            start_time = end_time - (10 * 60 * 1000)  # Last 10 minutes
            
            response = logs.filter_log_events(
                logGroupName=log_group,
                startTime=start_time,
                endTime=end_time,
                filterPattern='ERROR'
            )
            
            errors = response.get('events', [])
            
            if errors:
                print_warning(f"{func_name}: Found {len(errors)} error(s)")
                for event in errors[:3]:  # Show first 3 errors
                    print_info(f"  {event['message'][:100]}...")
                has_errors = True
                test_warning()
            else:
                print_success(f"{func_name}: No errors in last 10 minutes")
                
        except ClientError as e:
            if 'ResourceNotFoundException' in str(e):
                print_info(f"{func_name}: No logs yet")
            else:
                print_warning(f"{func_name}: Error checking logs: {e}")
    
    if not has_errors:
        test_passed()
    
    return not has_errors

# ============================================================================
# TEST 3: Multi-User Scenario
# ============================================================================

def test_multiple_users_scenario():
    """Test with multiple users to verify threshold notifications"""
    print_test("\nTest 10: Multi-User Threshold Testing")
    
    print_info("This test requires manual setup:")
    print_info("1. Add 50+ dummy users to the queue")
    print_info("2. Add yourself with a real email")
    print_info("3. Confirm SNS subscription")
    print_info("4. Wait for EventBridge to trigger (every 2 min)")
    print_info("5. Call Staff Next multiple times")
    print_info("")
    print_info("You should receive notifications at positions: 50,40,30,20,10,5,3,1,0")
    
    response = input("\nHave you completed multi-user testing? (y/n): ").strip().lower()
    
    if response == 'y':
        print_success("Multi-user testing completed")
        test_passed()
        return True
    else:
        print_warning("Multi-user testing skipped")
        test_warning()
        return False

# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def run_all_tests():
    """Run all tests in sequence"""
    
    print_header("🚀 QueueEscape SNS Integration Test Suite")
    print_info(f"Test Email: {TEST_EMAIL}")
    print_info(f"Queue ID: {QUEUE_ID}")
    print_info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Phase 1: Infrastructure Tests
    print_header("PHASE 1: Infrastructure Validation")
    
    if not test_dynamodb_tables():
        print_error("Infrastructure tests failed. Aborting.")
        return False
    
    if not test_lambda_functions():
        print_error("Lambda validation failed. Aborting.")
        return False
    
    if not test_sns_topic():
        print_error("SNS validation failed. Aborting.")
        return False
    
    if not test_eventbridge_rule():
        print_error("EventBridge validation failed. Aborting.")
        return False
    
    # Phase 2: Functional Tests
    print_header("PHASE 2: Functional Testing")
    
    ticket_number = test_join_queue()
    
    if not ticket_number:
        print_error("Queue join failed. Aborting functional tests.")
        return False
    
    print_warning("\n⏸️  IMPORTANT: Check your email and confirm SNS subscription!")
    print_info(f"Look for: 'AWS Notification - Subscription Confirmation'")
    
    response = input("Have you confirmed the subscription? (y/n): ").strip().lower()
    
    if response != 'y':
        print_warning("Skipping notification tests (subscription not confirmed)")
    else:
        test_notification_lambda(ticket_number)
    
    test_staff_next(ticket_number)
    test_staff_complete(ticket_number)
    test_cloudwatch_logs()
    
    # Phase 3: Advanced Tests
    print_header("PHASE 3: Advanced Testing")
    test_multiple_users_scenario()
    
    # Print Summary
    print_header("📊 TEST SUMMARY")
    
    total_tests = test_results['passed'] + test_results['failed']
    
    print(f"\n{Colors.BOLD}Total Tests Run: {total_tests}{Colors.END}")
    print(f"{Colors.GREEN}✅ Passed: {test_results['passed']}{Colors.END}")
    print(f"{Colors.RED}❌ Failed: {test_results['failed']}{Colors.END}")
    print(f"{Colors.YELLOW}⚠️  Warnings: {test_results['warnings']}{Colors.END}")
    
    if test_results['failed'] == 0:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 ALL TESTS PASSED!{Colors.END}")
        print(f"{Colors.GREEN}Your SNS integration is working perfectly!{Colors.END}")
        return True
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ SOME TESTS FAILED{Colors.END}")
        print(f"{Colors.RED}Please review the errors above and fix the issues.{Colors.END}")
        return False

if __name__ == "__main__":
    print(f"\n{Colors.BOLD}QueueEscape SNS Integration Test Suite{Colors.END}")
    print(f"{Colors.CYAN}This script will test your entire notification system{Colors.END}\n")
    
    # Validate configuration
    if TEST_EMAIL == "your-test-email@example.com":
        print_error("❌ Please update TEST_EMAIL in the script!")
        sys.exit(1)
    
    if "YOUR-API-ID" in API_GATEWAY_ENDPOINT:
        print_warning("⚠️  API_GATEWAY_ENDPOINT not configured (will use Lambda invoke)")
    
    print_info("Starting tests in 3 seconds...")
    time.sleep(3)
    
    success = run_all_tests()
    
    sys.exit(0 if success else 1)