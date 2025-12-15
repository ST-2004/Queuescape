#!/bin/bash

# Quick SNS Integration Health Check for QueueEscape
# This script provides a fast overview of system status

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

echo -e "${BOLD}${CYAN}"
echo "========================================================"
echo "   QueueEscape SNS Integration - Quick Health Check"
echo "========================================================"
echo -e "${NC}"

# Counter for pass/fail
CHECKS_PASSED=0
CHECKS_FAILED=0

# Function to check status
check_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ PASS${NC}"
        ((CHECKS_PASSED++))
    else
        echo -e "${RED}❌ FAIL${NC}"
        ((CHECKS_FAILED++))
    fi
}

# ============================================================================
# 1. Check DynamoDB Tables
# ============================================================================
echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}1. Checking DynamoDB Tables${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

TABLES=("QueueEntries" "QueueStats" "UserNotifications")

for table in "${TABLES[@]}"; do
    echo -n "   Checking $table... "
    if aws dynamodb describe-table --table-name "$table" &>/dev/null; then
        echo -e "${GREEN}✅ EXISTS${NC}"
        ((CHECKS_PASSED++))
    else
        echo -e "${RED}❌ NOT FOUND${NC}"
        ((CHECKS_FAILED++))
    fi
done

# ============================================================================
# 2. Check Lambda Functions
# ============================================================================
echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}2. Checking Lambda Functions${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

LAMBDAS=("JoinQueueLambda" "GetStatusLambda" "SendNotificationsLambda" "StaffNextLambda" "StaffCompleteLambda")

for lambda in "${LAMBDAS[@]}"; do
    echo -n "   Checking $lambda... "
    if aws lambda get-function --function-name "$lambda" &>/dev/null; then
        echo -e "${GREEN}✅ EXISTS${NC}"
        ((CHECKS_PASSED++))
    else
        echo -e "${RED}❌ NOT FOUND${NC}"
        ((CHECKS_FAILED++))
    fi
done

# ============================================================================
# 3. Check SNS Topics
# ============================================================================
echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}3. Checking SNS Topics${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -n "   Main alerts topic... "
ALERTS_TOPIC=$(aws sns list-topics --query "Topics[?contains(TopicArn, 'queueescape-alerts')].TopicArn" --output text)
if [ -n "$ALERTS_TOPIC" ]; then
    echo -e "${GREEN}✅ FOUND${NC}"
    echo -e "      ${CYAN}ARN: $ALERTS_TOPIC${NC}"
    ((CHECKS_PASSED++))
else
    echo -e "${RED}❌ NOT FOUND${NC}"
    ((CHECKS_FAILED++))
fi

echo -n "   User-specific topics... "
USER_TOPIC_COUNT=$(aws sns list-topics --query "Topics[?contains(TopicArn, 'QueueUser-')]" --output json | jq '. | length')
if [ "$USER_TOPIC_COUNT" -gt 0 ]; then
    echo -e "${YELLOW}⚠️  $USER_TOPIC_COUNT active${NC}"
else
    echo -e "${CYAN}ℹ️  None (normal if no active users)${NC}"
fi

# ============================================================================
# 4. Check EventBridge Rule
# ============================================================================
echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}4. Checking EventBridge Rule${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -n "   Notification scheduler rule... "
RULE_STATE=$(aws events describe-rule --name queueescape-notification-scheduler --query 'State' --output text 2>/dev/null)
if [ -n "$RULE_STATE" ]; then
    if [ "$RULE_STATE" == "ENABLED" ]; then
        echo -e "${GREEN}✅ ENABLED${NC}"
        ((CHECKS_PASSED++))
    else
        echo -e "${YELLOW}⚠️  $RULE_STATE${NC}"
        ((CHECKS_FAILED++))
    fi
    
    SCHEDULE=$(aws events describe-rule --name queueescape-notification-scheduler --query 'ScheduleExpression' --output text)
    echo -e "      ${CYAN}Schedule: $SCHEDULE${NC}"
else
    echo -e "${RED}❌ NOT FOUND${NC}"
    ((CHECKS_FAILED++))
fi

echo -n "   EventBridge targets... "
TARGET_COUNT=$(aws events list-targets-by-rule --rule queueescape-notification-scheduler --query 'Targets | length(@)' --output text 2>/dev/null)
if [ -n "$TARGET_COUNT" ] && [ "$TARGET_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✅ $TARGET_COUNT target(s)${NC}"
    ((CHECKS_PASSED++))
else
    echo -e "${RED}❌ NO TARGETS${NC}"
    ((CHECKS_FAILED++))
fi

# ============================================================================
# 5. Check VPC Configuration
# ============================================================================
echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}5. Checking VPC Configuration${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -n "   Lambda VPC config... "
VPC_CONFIG=$(aws lambda get-function-configuration --function-name JoinQueueLambda --query 'VpcConfig.SubnetIds' --output text 2>/dev/null)
if [ -n "$VPC_CONFIG" ] && [ "$VPC_CONFIG" != "None" ]; then
    echo -e "${GREEN}✅ CONFIGURED${NC}"
    ((CHECKS_PASSED++))
else
    echo -e "${YELLOW}⚠️  NOT IN VPC${NC}"
    ((CHECKS_FAILED++))
fi

echo -n "   SNS VPC Endpoint... "
SNS_ENDPOINT=$(aws ec2 describe-vpc-endpoints --filters "Name=service-name,Values=com.amazonaws.us-east-1.sns" --query 'VpcEndpoints[0].VpcEndpointId' --output text 2>/dev/null)
if [ -n "$SNS_ENDPOINT" ] && [ "$SNS_ENDPOINT" != "None" ]; then
    echo -e "${GREEN}✅ EXISTS${NC}"
    echo -e "      ${CYAN}ID: $SNS_ENDPOINT${NC}"
    ((CHECKS_PASSED++))
else
    echo -e "${YELLOW}⚠️  NOT FOUND${NC}"
    ((CHECKS_FAILED++))
fi

# ============================================================================
# 6. Check Current Queue State
# ============================================================================
echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}6. Checking Current Queue State${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -n "   Active tickets in queue... "
WAITING_COUNT=$(aws dynamodb scan --table-name QueueEntries \
    --filter-expression "attribute_exists(ticketNumber) AND #status = :waiting" \
    --expression-attribute-names '{"#status":"status"}' \
    --expression-attribute-values '{":waiting":{"S":"WAITING"}}' \
    --select COUNT --output text 2>/dev/null | awk '{print $1}')

if [ -n "$WAITING_COUNT" ]; then
    if [ "$WAITING_COUNT" -gt 0 ]; then
        echo -e "${CYAN}ℹ️  $WAITING_COUNT waiting${NC}"
    else
        echo -e "${CYAN}ℹ️  0 (queue empty)${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Unable to check${NC}"
fi

echo -n "   Notification records... "
NOTIF_COUNT=$(aws dynamodb scan --table-name UserNotifications --select COUNT --output text 2>/dev/null | awk '{print $1}')
if [ -n "$NOTIF_COUNT" ]; then
    echo -e "${CYAN}ℹ️  $NOTIF_COUNT active${NC}"
else
    echo -e "${YELLOW}⚠️  Unable to check${NC}"
fi

# ============================================================================
# 7. Check Recent Lambda Invocations
# ============================================================================
echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}7. Checking Recent Activity (Last 5 minutes)${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

END_TIME=$(date -u +%s)
START_TIME=$((END_TIME - 300))
START_TIME_MS=$((START_TIME * 1000))
END_TIME_MS=$((END_TIME * 1000))

for lambda in "JoinQueueLambda" "SendNotificationsLambda"; do
    echo -n "   $lambda invocations... "
    
    INVOCATIONS=$(aws cloudwatch get-metric-statistics \
        --namespace AWS/Lambda \
        --metric-name Invocations \
        --dimensions Name=FunctionName,Value=$lambda \
        --start-time $(date -u -d "@$START_TIME" +%Y-%m-%dT%H:%M:%S) \
        --end-time $(date -u -d "@$END_TIME" +%Y-%m-%dT%H:%M:%S) \
        --period 300 \
        --statistics Sum \
        --query 'Datapoints[0].Sum' \
        --output text 2>/dev/null)
    
    if [ -n "$INVOCATIONS" ] && [ "$INVOCATIONS" != "None" ]; then
        echo -e "${CYAN}ℹ️  ${INVOCATIONS} times${NC}"
    else
        echo -e "${CYAN}ℹ️  0 times${NC}"
    fi
done

# ============================================================================
# 8. Check for Recent Errors
# ============================================================================
echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}8. Checking for Errors (Last 10 minutes)${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

HAS_ERRORS=0

for lambda in "JoinQueueLambda" "SendNotificationsLambda" "StaffNextLambda" "StaffCompleteLambda"; do
    LOG_GROUP="/aws/lambda/$lambda"
    
    ERROR_COUNT=$(aws logs filter-log-events \
        --log-group-name "$LOG_GROUP" \
        --start-time $START_TIME_MS \
        --end-time $END_TIME_MS \
        --filter-pattern "ERROR" \
        --query 'events | length(@)' \
        --output text 2>/dev/null)
    
    if [ -n "$ERROR_COUNT" ] && [ "$ERROR_COUNT" != "0" ] && [ "$ERROR_COUNT" != "None" ]; then
        echo -e "   ${RED}❌ $lambda: $ERROR_COUNT error(s)${NC}"
        HAS_ERRORS=1
    fi
done

if [ $HAS_ERRORS -eq 0 ]; then
    echo -e "   ${GREEN}✅ No errors found${NC}"
    ((CHECKS_PASSED++))
else
    echo -e "   ${YELLOW}⚠️  Check CloudWatch logs for details${NC}"
    ((CHECKS_FAILED++))
fi

# ============================================================================
# SUMMARY
# ============================================================================
echo -e "\n${BOLD}${CYAN}"
echo "========================================================"
echo "                    SUMMARY"
echo "========================================================"
echo -e "${NC}"

TOTAL_CHECKS=$((CHECKS_PASSED + CHECKS_FAILED))

echo -e "${BOLD}Total Checks: $TOTAL_CHECKS${NC}"
echo -e "${GREEN}✅ Passed: $CHECKS_PASSED${NC}"
echo -e "${RED}❌ Failed: $CHECKS_FAILED${NC}"

echo ""

if [ $CHECKS_FAILED -eq 0 ]; then
    echo -e "${GREEN}${BOLD}🎉 ALL CHECKS PASSED!${NC}"
    echo -e "${GREEN}Your SNS integration appears to be configured correctly.${NC}"
    exit 0
else
    echo -e "${YELLOW}${BOLD}⚠️  SOME CHECKS FAILED${NC}"
    echo -e "${YELLOW}Review the failures above and fix the configuration.${NC}"
    exit 1
fi