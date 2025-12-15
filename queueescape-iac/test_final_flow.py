#!/usr/bin/env python3
"""
QueueEscape Complete Integration Test Suite with Self-Service Signup
End-to-end testing including staff signup, Cognito authentication, and full queue flow
"""

import boto3
import json
import time
import sys
import requests
import random
import string
from datetime import datetime
from decimal import Decimal
from botocore.exceptions import ClientError

# ============================================================================
# CONFIGURATION - UPDATE THESE VALUES
# ============================================================================

# Cognito Configuration
USER_POOL_ID = "us-east-1_LSkUhawY5"  # CHANGE THIS
CLIENT_ID = "6v6on9bsj9hcgopi6mrk0g1bsp"  # CHANGE THIS

# API Gateway Configuration
API_BASE_URL = "https://tbmndj28ib.execute-api.us-east-1.amazonaws.com/dev"  # CHANGE THIS

# Test Configuration
QUEUE_ID = "main_queue"
TEST_EMAIL = "s.tiwari.fr@gmail.com"  # CHANGE THIS - for customer notifications

# Staff signup test - will be auto-generated
TEST_STAFF_EMAIL = f"teststaff{random.randint(1000,9999)}@test.com"
TEST_STAFF_PASSWORD = "TestStaff123!"

# ============================================================================
# AWS CLIENTS
# ============================================================================

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
dynamodb_client = boto3.client('dynamodb', region_name='us-east-1')
sns = boto3.client('sns', region_name='us-east-1')
lambda_client = boto3.client('lambda', region_name='us-east-1')
events = boto3.client('events', region_name='us-east-1')
logs = boto3.client('logs', region_name='us-east-1')
cognito = boto3.client('cognito-idp', region_name='us-east-1')

# ============================================================================
# COLOR CODES FOR OUTPUT
# ============================================================================

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(70)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}\n")

def print_section(text):
    print(f"\n{Colors.BOLD}{Colors.MAGENTA}{'─'*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.MAGENTA}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.MAGENTA}{'─'*70}{Colors.END}\n")

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

# ============================================================================
# TEST RESULTS TRACKER
# ============================================================================

test_results = {
    'passed': 0,
    'failed': 0,
    'warnings': 0,
    'skipped': 0
}

def test_passed():
    test_results['passed'] += 1

def test_failed():
    test_results['failed'] += 1

def test_warning():
    test_results['warnings'] += 1

def test_skipped():
    test_results['skipped'] += 1

# ============================================================================
# AUTHENTICATION CLASS
# ============================================================================

class CognitoAuth:
    def __init__(self):
        self.id_token = None
        self.access_token = None
        self.refresh_token = None
        self.username = None
        self.user_sub = None
    
    def signup(self, email, password):
        """Sign up a new staff user"""
        try:
            response = cognito.sign_up(
                ClientId=CLIENT_ID,
                Username=email,
                Password=password,
                UserAttributes=[
                    {'Name': 'email', 'Value': email}
                ]
            )
            
            self.user_sub = response.get('UserSub')
            return True, response
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_msg = e.response['Error']['Message']
            print_error(f"Signup failed: {error_code}")
            print_info(f"Message: {error_msg}")
            return False, None
    
    def confirm_signup(self, email, code):
        """Confirm signup with verification code"""
        try:
            response = cognito.confirm_sign_up(
                ClientId=CLIENT_ID,
                Username=email,
                ConfirmationCode=code
            )
            return True
            
        except ClientError as e:
            print_error(f"Confirmation failed: {e.response['Error']['Code']}")
            return False
    
    def auto_confirm_user(self, email):
        """Admin confirm user (for testing without email verification)"""
        try:
            cognito.admin_confirm_sign_up(
                UserPoolId=USER_POOL_ID,
                Username=email
            )
            return True
        except ClientError as e:
            print_error(f"Auto-confirm failed: {e}")
            return False
    
    def authenticate(self, username, password):
        """Authenticate staff user with Cognito"""
        try:
            response = cognito.initiate_auth(
                ClientId=CLIENT_ID,
                AuthFlow='USER_PASSWORD_AUTH',
                AuthParameters={
                    'USERNAME': username,
                    'PASSWORD': password
                }
            )
            
            if 'AuthenticationResult' in response:
                self.id_token = response['AuthenticationResult']['IdToken']
                self.access_token = response['AuthenticationResult']['AccessToken']
                self.refresh_token = response['AuthenticationResult']['RefreshToken']
                self.username = username
                return True
            return False
            
        except ClientError as e:
            print_error(f"Authentication failed: {e.response['Error']['Code']}")
            print_info(f"Message: {e.response['Error']['Message']}")
            return False
    
    def get_headers(self):
        """Get authorization headers"""
        return {
            'Authorization': f'Bearer {self.id_token}',
            'Content-Type': 'application/json'
        }
    
    def delete_user(self):
        """Delete the test user (cleanup)"""
        try:
            cognito.admin_delete_user(
                UserPoolId=USER_POOL_ID,
                Username=self.username
            )
            return True
        except ClientError as e:
            print_warning(f"Could not delete user: {e}")
            return False

# ============================================================================
# PHASE 1: INFRASTRUCTURE VALIDATION
# ============================================================================

def test_cognito_user_pool():
    """Verify Cognito User Pool exists and allows self-registration"""
    print_test("Test 1.1: Checking Cognito User Pool Configuration")
    
    try:
        response = cognito.describe_user_pool(UserPoolId=USER_POOL_ID)
        pool = response['UserPool']
        
        print_success(f"User Pool exists: {pool['Name']}")
        print_info(f"  Pool ID: {pool['Id']}")
        print_info(f"  Creation Date: {pool['CreationDate']}")
        
        # Check self-registration
        admin_create_only = pool.get('AdminCreateUserConfig', {}).get('AllowAdminCreateUserOnly', True)
        
        if not admin_create_only:
            print_success("  ✓ Self-registration ENABLED")
        else:
            print_error("  ✗ Self-registration DISABLED")
            print_warning("  Update Cognito config: allow_admin_create_user_only = false")
            test_failed()
            return False
        
        # Check auto-verified attributes
        auto_verified = pool.get('AutoVerifiedAttributes', [])
        if 'email' in auto_verified:
            print_success("  ✓ Email auto-verification enabled")
        else:
            print_warning("  Email auto-verification not enabled")
            test_warning()
        
        test_passed()
        return True
        
    except ClientError as e:
        print_error(f"User Pool not found: {e}")
        test_failed()
        return False
    
def test_cognito_app_client(): 
    """Verify Cognito App Client supports required auth flows"""
    print_test("Test 1.2: Checking Cognito App Client")
    
    try:
        response = cognito.describe_user_pool_client(
            UserPoolId=USER_POOL_ID,
            ClientId=CLIENT_ID
        )
        client = response['UserPoolClient']
        
        print_success(f"App Client exists: {client['ClientName']}")
        print_info(f"  Client ID: {client['ClientId']}")
        
        # Check auth flows
        auth_flows = client.get('ExplicitAuthFlows', [])
        
        required_flows = ['ALLOW_USER_PASSWORD_AUTH', 'ALLOW_USER_SRP_AUTH']
        missing_flows = [flow for flow in required_flows if flow not in auth_flows]
        
        if not missing_flows:
            print_success("  ✓ All required auth flows enabled")
        else:
            print_warning(f"  Missing auth flows: {missing_flows}")
            test_warning()
        
        # Check if client secret is disabled
        if not client.get('ClientSecret'):
            print_success("  ✓ No client secret (correct for frontend)")
        else:
            print_warning("  Client secret exists (should be disabled for frontend)")
            test_warning()
        
        test_passed()
        return True
        
    except ClientError as e:
        print_error(f"App Client not found: {e}")
        test_failed()
        return False

def test_api_gateway_authorizer():
    """Verify API Gateway Cognito Authorizer exists"""
    print_test("Test 1.3: Checking API Gateway Cognito Authorizer")
    
    try:
        api_id = API_BASE_URL.split('//')[1].split('.')[0]
        
        apigw = boto3.client('apigateway', region_name='us-east-1')
        response = apigw.get_authorizers(restApiId=api_id)
        
        cognito_authorizers = [
            a for a in response.get('items', [])
            if a.get('type') == 'COGNITO_USER_POOLS'
        ]
        
        if cognito_authorizers:
            auth = cognito_authorizers[0]
            print_success(f"Cognito Authorizer exists: {auth['name']}")
            print_info(f"  Authorizer ID: {auth['id']}")
            
            provider_arns = auth.get('providerARNs', [])
            if any(USER_POOL_ID in arn for arn in provider_arns):
                print_success("  ✓ Linked to correct User Pool")
            else:
                print_warning("  Not linked to our User Pool")
                test_warning()
            
            test_passed()
            return True
        else:
            print_error("No Cognito Authorizer found")
            test_failed()
            return False
            
    except Exception as e:
        print_error(f"Error checking authorizer: {e}")
        test_failed()
        return False

def test_dynamodb_tables():
    """Verify all required DynamoDB tables exist"""
    print_test("Test 1.4: Checking DynamoDB Tables")
    
    required_tables = ['QueueEntries', 'QueueStats', 'UserNotifications']
    all_exist = True
    
    for table_name in required_tables:
        try:
            table = dynamodb.Table(table_name)
            table.load()
            
            if table.table_status == 'ACTIVE':
                print_success(f"  ✓ {table_name}: ACTIVE")
            else:
                print_warning(f"  {table_name}: {table.table_status}")
                test_warning()
                
        except ClientError as e:
            print_error(f"  ✗ {table_name}: Not found")
            all_exist = False
    
    if all_exist:
        test_passed()
    else:
        test_failed()
    
    return all_exist

def test_lambda_functions():
    """Verify all required Lambda functions exist"""
    print_test("Test 1.5: Checking Lambda Functions")
    
    required_functions = [
        'JoinQueueLambda',
        'GetStatusLambda',
        'GetSummaryLambda',
        'StaffNextLambda',
        'StaffCompleteLambda',
        'SendNotificationsLambda'
    ]
    
    all_exist = True
    
    for func_name in required_functions:
        try:
            response = lambda_client.get_function(FunctionName=func_name)
            print_success(f"  ✓ {func_name}")
        except ClientError:
            print_error(f"  ✗ {func_name}: Not found")
            all_exist = False
    
    if all_exist:
        test_passed()
    else:
        test_failed()
    
    return all_exist

def test_sns_topic():
    """Verify SNS topic exists"""
    print_test("Test 1.6: Checking SNS Topics")
    
    try:
        response = sns.list_topics()
        topics = response.get('Topics', [])
        
        alerts_topic = [t for t in topics if 'queueescape-alerts' in t['TopicArn']]
        
        if alerts_topic:
            print_success(f"  ✓ Main alerts topic exists")
            test_passed()
            return True
        else:
            print_error("  ✗ Main alerts topic not found")
            test_failed()
            return False
            
    except ClientError as e:
        print_error(f"Error checking SNS: {e}")
        test_failed()
        return False

# ============================================================================
# PHASE 2: STAFF SIGNUP TESTING
# ============================================================================

def test_staff_signup(auth):
    """Test staff self-service signup"""
    print_test("Test 2.1: Staff Self-Service Signup")
    
    print_info(f"Creating test staff account: {TEST_STAFF_EMAIL}")
    
    success, response = auth.signup(TEST_STAFF_EMAIL, TEST_STAFF_PASSWORD)
    
    if success:
        print_success("Signup request successful")
        print_info(f"  User Sub: {auth.user_sub}")
        
        # Check if user needs confirmation
        user_confirmed = response.get('UserConfirmed', False)
        
        if not user_confirmed:
            print_info("  User needs email verification")
            print_info("  Auto-confirming user for testing...")
            
            if auth.auto_confirm_user(TEST_STAFF_EMAIL):
                print_success("  ✓ User auto-confirmed")
            else:
                print_error("  ✗ Auto-confirm failed")
                test_failed()
                return False
        else:
            print_success("  ✓ User confirmed automatically")
        
        # Verify user exists in Cognito
        time.sleep(2)
        
        try:
            user_response = cognito.admin_get_user(
                UserPoolId=USER_POOL_ID,
                Username=TEST_STAFF_EMAIL
            )
            
            print_success("  ✓ User verified in Cognito")
            print_info(f"    Username: {user_response['Username']}")
            print_info(f"    Status: {user_response['UserStatus']}")
            
            # Check attributes
            attributes = {attr['Name']: attr['Value'] for attr in user_response['UserAttributes']}
            
            if attributes.get('email') == TEST_STAFF_EMAIL:
                print_success("  ✓ Email attribute correct")
            
            if attributes.get('email_verified') == 'true':
                print_success("  ✓ Email verified")
            else:
                print_warning("  Email not verified yet")
                test_warning()
            
        except ClientError as e:
            print_error(f"  ✗ User not found in Cognito: {e}")
            test_failed()
            return False
        
        test_passed()
        return True
    else:
        print_error("Signup failed")
        test_failed()
        return False

def test_duplicate_signup(auth):
    """Test that duplicate signups are prevented"""
    print_test("Test 2.2: Duplicate Signup Prevention")
    
    print_info(f"Attempting duplicate signup: {TEST_STAFF_EMAIL}")
    
    success, response = auth.signup(TEST_STAFF_EMAIL, TEST_STAFF_PASSWORD)
    
    if not success:
        print_success("Duplicate signup correctly rejected")
        test_passed()
        return True
    else:
        print_error("Duplicate signup was allowed (should be rejected)")
        test_failed()
        return False

def test_weak_password_rejection():
    """Test that weak passwords are rejected"""
    print_test("Test 2.3: Weak Password Rejection")
    
    weak_passwords = [
        ("short", "Short password"),
        ("alllowercase", "No uppercase"),
        ("ALLUPPERCASE", "No lowercase"),
        ("NoNumbers!", "No numbers"),
    ]
    
    test_email = f"weakpass{random.randint(1000,9999)}@test.com"
    all_rejected = True
    
    for weak_pass, reason in weak_passwords:
        try:
            cognito.sign_up(
                ClientId=CLIENT_ID,
                Username=test_email,
                Password=weak_pass,
                UserAttributes=[{'Name': 'email', 'Value': test_email}]
            )
            print_error(f"  ✗ Weak password accepted: {reason}")
            all_rejected = False
        except ClientError as e:
            if 'InvalidPasswordException' in str(e) or 'InvalidParameterException' in str(e):
                print_success(f"  ✓ Rejected: {reason}")
            else:
                print_warning(f"  ? Unexpected error for {reason}: {e}")
    
    if all_rejected:
        test_passed()
    else:
        test_failed()
    
    return all_rejected

# ============================================================================
# PHASE 3: AUTHENTICATION TESTING
# ============================================================================

def test_staff_authentication(auth):
    """Test staff authentication after signup"""
    print_test("Test 3.1: Staff Authentication")
    
    print_info(f"Authenticating as: {TEST_STAFF_EMAIL}")
    
    if auth.authenticate(TEST_STAFF_EMAIL, TEST_STAFF_PASSWORD):
        print_success("Authentication successful")
        print_info(f"  ID Token (first 50 chars): {auth.id_token[:50]}...")
        print_info(f"  Access Token (first 50 chars): {auth.access_token[:50]}...")
        test_passed()
        return True
    else:
        print_error("Authentication failed")
        test_failed()
        return False

def test_wrong_password_rejection(auth):
    """Test that wrong passwords are rejected"""
    print_test("Test 3.2: Wrong Password Rejection")
    
    wrong_auth = CognitoAuth()
    
    if not wrong_auth.authenticate(TEST_STAFF_EMAIL, "WrongPassword123!"):
        print_success("Wrong password correctly rejected")
        test_passed()
        return True
    else:
        print_error("Wrong password was accepted")
        test_failed()
        return False

def test_nonexistent_user_rejection():
    """Test that non-existent users are rejected"""
    print_test("Test 3.3: Non-existent User Rejection")
    
    fake_auth = CognitoAuth()
    
    if not fake_auth.authenticate("nonexistent@test.com", "Password123!"):
        print_success("Non-existent user correctly rejected")
        test_passed()
        return True
    else:
        print_error("Non-existent user was accepted")
        test_failed()
        return False

# CONTINUE TO PART 2...

# ============================================================================
# PHASE 4: API AUTHORIZATION TESTING
# ============================================================================

def test_public_endpoint_no_auth():
    """Test public endpoint without authentication"""
    print_test("Test 4.1: Public Endpoint (No Auth)")
    
    url = f"{API_BASE_URL}/queue/join"
    print_info(f"Testing: POST {url}")
    
    try:
        response = requests.post(
            url,
            json={'queueId': QUEUE_ID, 'name': 'Test Customer'},
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print_info(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print_success("Public endpoint accessible without auth")
            test_passed()
            return True
        else:
            print_warning(f"Unexpected status: {response.status_code}")
            test_warning()
            return False
            
    except Exception as e:
        print_error(f"Request failed: {e}")
        test_failed()
        return False

def test_protected_endpoint_no_auth():
    """Test protected endpoint without authentication (should fail)"""
    print_test("Test 4.2: Protected Endpoint Without Auth (Should Fail)")
    
    url = f"{API_BASE_URL}/queue/staff/summary"
    print_info(f"Testing: GET {url}")
    
    try:
        response = requests.get(url, timeout=10)
        
        print_info(f"Status: {response.status_code}")
        
        if response.status_code in [401, 403]:
            print_success(f"Correctly rejected: {response.status_code}")
            test_passed()
            return True
        else:
            print_error(f"Expected 401/403, got {response.status_code}")
            print_warning("Protected endpoint is NOT secured!")
            test_failed()
            return False
            
    except Exception as e:
        print_error(f"Request failed: {e}")
        test_failed()
        return False

def test_protected_endpoint_with_auth(auth):
    """Test protected endpoint with valid authentication"""
    print_test("Test 4.3: Protected Endpoint With Auth (Should Succeed)")
    
    url = f"{API_BASE_URL}/queue/staff/summary"
    print_info(f"Testing: GET {url}")
    
    try:
        response = requests.get(url, headers=auth.get_headers(), timeout=10)
        
        print_info(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print_success("Successfully authenticated!")
            try:
                data = response.json()
                print_info(f"Response keys: {list(data.keys())}")
            except:
                pass
            test_passed()
            return True
        elif response.status_code == 401:
            print_error("Authentication failed with valid token!")
            print_warning("Check API Gateway authorizer configuration")
            test_failed()
            return False
        else:
            print_warning(f"Unexpected status: {response.status_code}")
            test_warning()
            return False
            
    except Exception as e:
        print_error(f"Request failed: {e}")
        test_failed()
        return False

def test_protected_endpoint_invalid_token():
    """Test protected endpoint with invalid token"""
    print_test("Test 4.4: Protected Endpoint With Invalid Token (Should Fail)")
    
    url = f"{API_BASE_URL}/queue/staff/summary"
    print_info(f"Testing: GET {url}")
    
    fake_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.token"
    
    try:
        response = requests.get(
            url,
            headers={'Authorization': f'Bearer {fake_token}'},
            timeout=10
        )
        
        print_info(f"Status: {response.status_code}")
        
        if response.status_code in [401, 403]:
            print_success("Correctly rejected invalid token")
            test_passed()
            return True
        else:
            print_error(f"Expected 401/403, got {response.status_code}")
            print_warning("Invalid tokens are being accepted!")
            test_failed()
            return False
            
    except Exception as e:
        print_error(f"Request failed: {e}")
        test_failed()
        return False

# ============================================================================
# PHASE 5: CUSTOMER FLOW TESTING
# ============================================================================

def test_customer_join_queue():
    """Test customer joining the queue"""
    print_test("Test 5.1: Customer Join Queue")
    
    url = f"{API_BASE_URL}/queue/join"
    print_info(f"Testing: POST {url}")
    print_info(f"Email: {TEST_EMAIL}")
    
    try:
        response = requests.post(
            url,
            json={'queueId': QUEUE_ID, 'email': TEST_EMAIL},
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print_info(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            ticket_number = data.get('ticketNumber')
            
            print_success("Successfully joined queue")
            print_info(f"  Ticket Number: {ticket_number}")
            
            # Verify in DynamoDB
            time.sleep(2)
            
            entries_table = dynamodb.Table('QueueEntries')
            entry = entries_table.get_item(
                Key={'queueId': QUEUE_ID, 'ticketNumber': ticket_number}
            )
            
            if 'Item' in entry:
                print_success("  ✓ Entry verified in QueueEntries")
                print_info(f"    Status: {entry['Item']['status']}")
            else:
                print_error("  ✗ Entry NOT found in DynamoDB")
                test_failed()
                return None
            
            test_passed()
            return ticket_number
        else:
            print_error(f"Failed to join queue: {response.text}")
            test_failed()
            return None
            
    except Exception as e:
        print_error(f"Request failed: {e}")
        test_failed()
        return None

def test_customer_check_status(ticket_number):
    """Test customer checking queue status"""
    print_test("Test 5.2: Customer Check Status")
    
    url = f"{API_BASE_URL}/queue/status/{QUEUE_ID}/{ticket_number}"
    print_info(f"Testing: GET {url}")
    
    try:
        response = requests.get(url, timeout=10)
        
        print_info(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print_success("Status retrieved successfully")
            print_info(f"  Position: {data.get('position')}")
            print_info(f"  Status: {data.get('status')}")
            
            test_passed()
            return True
        else:
            print_error(f"Failed to get status: {response.text}")
            test_failed()
            return False
            
    except Exception as e:
        print_error(f"Request failed: {e}")
        test_failed()
        return False

# ============================================================================
# PHASE 6: STAFF FLOW TESTING
# ============================================================================

def test_staff_get_summary(auth):
    """Test staff getting queue summary"""
    print_test("Test 6.1: Staff Get Summary")
    
    url = f"{API_BASE_URL}/queue/staff/summary"
    print_info(f"Testing: GET {url}")
    
    try:
        response = requests.get(url, headers=auth.get_headers(), timeout=10)
        
        print_info(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print_success("Summary retrieved successfully")
            print_info(f"  Total in Queue: {data.get('totalInQueue', 0)}")
            
            test_passed()
            return True
        else:
            print_error(f"Failed to get summary: {response.text}")
            test_failed()
            return False
            
    except Exception as e:
        print_error(f"Request failed: {e}")
        test_failed()
        return False

def test_staff_call_next(auth, ticket_number):
    """Test staff calling next customer"""
    print_test("Test 6.2: Staff Call Next")
    
    url = f"{API_BASE_URL}/queue/staff/next"
    print_info(f"Testing: POST {url}")
    
    try:
        response = requests.post(
            url,
            json={'queueId': QUEUE_ID},
            headers=auth.get_headers(),
            timeout=10
        )
        
        print_info(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print_success("Next customer called")
            
            # Verify status change
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
                else:
                    print_warning(f"  Status is {status}")
                    test_warning()
            
            test_passed()
            return True
        else:
            print_error(f"Failed to call next: {response.text}")
            test_failed()
            return False
            
    except Exception as e:
        print_error(f"Request failed: {e}")
        test_failed()
        return False

def test_staff_complete(auth, ticket_number):
    """Test staff completing customer service"""
    print_test("Test 6.3: Staff Complete Service")
    
    url = f"{API_BASE_URL}/queue/staff/complete"
    print_info(f"Testing: POST {url}")
    
    try:
        response = requests.post(
            url,
            json={'queueId': QUEUE_ID, 'ticketNumber': ticket_number},
            headers=auth.get_headers(),
            timeout=10
        )
        
        print_info(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print_success("Service completed")
            
            # Verify status change
            time.sleep(2)
            
            entries_table = dynamodb.Table('QueueEntries')
            entry = entries_table.get_item(
                Key={'queueId': QUEUE_ID, 'ticketNumber': ticket_number}
            )
            
            if 'Item' in entry:
                status = entry['Item'].get('status')
                
                if status == 'COMPLETED':
                    print_success("  ✓ Status updated to COMPLETED")
                else:
                    print_warning(f"  Status is {status}")
                    test_warning()
            
            test_passed()
            return True
        else:
            print_error(f"Failed to complete: {response.text}")
            test_failed()
            return False
            
    except Exception as e:
        print_error(f"Request failed: {e}")
        test_failed()
        return False

# ============================================================================
# PHASE 7: CLEANUP & USER MANAGEMENT
# ============================================================================

def test_user_cleanup(auth):
    """Test deleting the test user"""
    print_test("Test 7.1: User Cleanup")
    
    print_info(f"Deleting test user: {TEST_STAFF_EMAIL}")
    
    if auth.delete_user():
        print_success("Test user deleted successfully")
        
        # Verify deletion
        time.sleep(2)
        
        try:
            cognito.admin_get_user(
                UserPoolId=USER_POOL_ID,
                Username=TEST_STAFF_EMAIL
            )
            print_error("  ✗ User still exists after deletion")
            test_failed()
            return False
        except ClientError as e:
            if 'UserNotFoundException' in str(e):
                print_success("  ✓ User confirmed deleted")
                test_passed()
                return True
            else:
                print_warning(f"  Unexpected error: {e}")
                test_warning()
                return False
    else:
        print_warning("Could not delete test user")
        test_warning()
        return False

# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def print_test_summary():
    """Print comprehensive test summary"""
    print_header("📊 COMPLETE TEST SUMMARY")
    
    total = sum(test_results.values())
    passed = test_results['passed']
    failed = test_results['failed']
    warnings = test_results['warnings']
    skipped = test_results['skipped']
    
    print(f"\n{Colors.BOLD}Total Tests: {total}{Colors.END}")
    print(f"{Colors.GREEN}✅ Passed: {passed}{Colors.END}")
    print(f"{Colors.RED}❌ Failed: {failed}{Colors.END}")
    print(f"{Colors.YELLOW}⚠️  Warnings: {warnings}{Colors.END}")
    print(f"{Colors.CYAN}⏭️  Skipped: {skipped}{Colors.END}")
    
    if total > 0:
        success_rate = (passed / total) * 100
        print(f"\n{Colors.BOLD}Success Rate: {success_rate:.1f}%{Colors.END}")
    
    print()
    
    if failed == 0 and warnings == 0:
        print(f"{Colors.GREEN}{Colors.BOLD}🎉 PERFECT! ALL TESTS PASSED!{Colors.END}")
        print(f"{Colors.GREEN}Your QueueEscape with self-service signup is fully operational!{Colors.END}")
    elif failed == 0:
        print(f"{Colors.YELLOW}{Colors.BOLD}✅ ALL TESTS PASSED (with warnings){Colors.END}")
        print(f"{Colors.YELLOW}Review warnings above for improvements.{Colors.END}")
    else:
        print(f"{Colors.RED}{Colors.BOLD}❌ TESTS FAILED{Colors.END}")
        print(f"{Colors.RED}Please review and fix the errors above.{Colors.END}")

def run_all_tests():
    """Execute all test phases"""
    
    print_header("🚀 QueueEscape Complete Test Suite - Self-Service Signup")
    print_info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_info(f"API Base URL: {API_BASE_URL}")
    print_info(f"Test Staff Email: {TEST_STAFF_EMAIL}")
    print_info(f"Customer Email: {TEST_EMAIL}")
    print()
    
    # Initialize auth object
    auth = CognitoAuth()
    ticket_number = None
    
    # ========================================================================
    # PHASE 1: INFRASTRUCTURE VALIDATION
    # ========================================================================
    
    print_section("PHASE 1: INFRASTRUCTURE VALIDATION")
    
    if not test_cognito_user_pool():
        print_error("\n❌ Cognito User Pool validation failed.")
        print_warning("Make sure allow_admin_create_user_only = false in cognito.tf")
        return False
    
    if not test_cognito_app_client():
        print_error("\n❌ Cognito App Client validation failed. Aborting.")
        return False
    
    test_api_gateway_authorizer()
    
    if not test_dynamodb_tables():
        print_error("\n❌ DynamoDB validation failed. Aborting.")
        return False
    
    if not test_lambda_functions():
        print_error("\n❌ Lambda validation failed. Aborting.")
        return False
    
    test_sns_topic()
    
    print_success("\n✅ Phase 1 Complete: Infrastructure validated")
    
    # ========================================================================
    # PHASE 2: STAFF SIGNUP TESTING
    # ========================================================================
    
    print_section("PHASE 2: STAFF SIGNUP TESTING")
    
    if not test_staff_signup(auth):
        print_error("\n❌ Staff signup failed. Cannot continue.")
        return False
    
    test_duplicate_signup(auth)
    test_weak_password_rejection()
    
    print_success("\n✅ Phase 2 Complete: Staff signup verified")
    
    # ========================================================================
    # PHASE 3: AUTHENTICATION TESTING
    # ========================================================================
    
    print_section("PHASE 3: AUTHENTICATION TESTING")
    
    if not test_staff_authentication(auth):
        print_error("\n❌ Authentication failed. Cannot test protected endpoints.")
        return False
    
    test_wrong_password_rejection(auth)
    test_nonexistent_user_rejection()
    
    print_success("\n✅ Phase 3 Complete: Authentication verified")
    
    # ========================================================================
    # PHASE 4: API AUTHORIZATION TESTING
    # ========================================================================
    
    print_section("PHASE 4: API AUTHORIZATION TESTING")
    
    test_public_endpoint_no_auth()
    test_protected_endpoint_no_auth()
    
    if not test_protected_endpoint_with_auth(auth):
        print_error("\n❌ Protected endpoint access failed.")
        return False
    
    test_protected_endpoint_invalid_token()
    
    print_success("\n✅ Phase 4 Complete: API authorization verified")
    
    # ========================================================================
    # PHASE 5: CUSTOMER FLOW TESTING
    # ========================================================================
    
    print_section("PHASE 5: CUSTOMER FLOW TESTING")
    
    ticket_number = test_customer_join_queue()
    
    if not ticket_number:
        print_error("\n❌ Customer join failed. Skipping flow tests.")
    else:
        test_customer_check_status(ticket_number)
        print_success("\n✅ Phase 5 Complete: Customer flow verified")
    
    # ========================================================================
    # PHASE 6: STAFF FLOW TESTING
    # ========================================================================
    
    print_section("PHASE 6: STAFF FLOW TESTING")
    
    test_staff_get_summary(auth)
    
    if ticket_number:
        test_staff_call_next(auth, ticket_number)
        test_staff_complete(auth, ticket_number)
    
    print_success("\n✅ Phase 6 Complete: Staff flow verified")
    
    # ========================================================================
    # PHASE 7: CLEANUP
    # ========================================================================
    
    print_section("PHASE 7: CLEANUP")
    
    test_user_cleanup(auth)
    
    print_success("\n✅ Phase 7 Complete: Cleanup done")
    
    # ========================================================================
    # FINAL SUMMARY
    # ========================================================================
    
    print_test_summary()
    
    return test_results['failed'] == 0

def validate_configuration():
    """Validate configuration before running tests"""
    errors = []
    
    if USER_POOL_ID == "us-east-1_XXXXXXXXX":
        errors.append("USER_POOL_ID not configured")
    
    if CLIENT_ID == "XXXXXXXXXXXXXXXXXXXXXXXXXX":
        errors.append("CLIENT_ID not configured")
    
    if "YOUR_API_ID" in API_BASE_URL:
        errors.append("API_BASE_URL not configured")
    
    if errors:
        print_error("❌ Configuration Errors:")
        for error in errors:
            print_info(f"   - {error}")
        print()
        return False
    
    return True

def get_configuration_from_terraform():
    """Try to get configuration from Terraform outputs"""
    print_test("Attempting to read Terraform outputs...")
    
    try:
        import subprocess
        
        result = subprocess.run(
            ['terraform', 'output', '-raw', 'cognito_user_pool_id'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0 and result.stdout:
            global USER_POOL_ID
            USER_POOL_ID = result.stdout.strip()
            print_success(f"  ✓ User Pool ID: {USER_POOL_ID}")
        
        result = subprocess.run(
            ['terraform', 'output', '-raw', 'cognito_client_id'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0 and result.stdout:
            global CLIENT_ID
            CLIENT_ID = result.stdout.strip()
            print_success(f"  ✓ Client ID: {CLIENT_ID[:20]}...")
        
        result = subprocess.run(
            ['terraform', 'output', '-raw', 'queueescape_invoke_url'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0 and result.stdout:
            global API_BASE_URL
            API_BASE_URL = result.stdout.strip()
            print_success(f"  ✓ API URL: {API_BASE_URL}")
        
        print_success("Configuration loaded from Terraform")
        return True
        
    except Exception as e:
        print_warning(f"Could not read Terraform outputs: {e}")
        return False

# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    print_header("QueueEscape - Self-Service Signup Test Suite")
    print_info("Testing: Staff Signup + Auth + Queue Flow")
    print()
    
    print_section("CONFIGURATION")
    
    terraform_loaded = get_configuration_from_terraform()
    
    if not terraform_loaded:
        print_info("Using manual configuration from script...")
    
    if not validate_configuration():
        sys.exit(1)
    
    print_success("✅ Configuration validated")
    print()
    
    print_info("This test will:")
    print_info("  1. Validate infrastructure (Cognito with self-signup enabled)")
    print_info(f"  2. Create test staff account: {TEST_STAFF_EMAIL}")
    print_info("  3. Test signup, login, and authentication")
    print_info("  4. Test API authorization")
    print_info("  5. Test complete queue flow")
    print_info("  6. Clean up test data")
    print()
    
    response = input("Ready to start? (y/n): ").strip().lower()
    
    if response != 'y':
        print_warning("Test cancelled by user")
        sys.exit(0)
    
    print()
    print_info("Starting tests in 3 seconds...")
    time.sleep(3)
    
    try:
        success = run_all_tests()
        
        print()
        print_info("=" * 70)
        
        if success:
            print_success("🎉 Test suite completed successfully!")
            print_info("\nYour QueueEscape with self-service signup is ready!")
            print_info("Staff can now:")
            print_info("  1. Sign up with email + password")
            print_info("  2. Verify email (automatic in test)")
            print_info("  3. Log in and access dashboard")
            sys.exit(0)
        else:
            print_error("❌ Test suite completed with failures")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print()
        print_warning("\n⚠️  Test interrupted by user")
        sys.exit(130)
        
    except Exception as e:
        print()
        print_error(f"\n❌ Unexpected error:")
        print_error(f"   {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)