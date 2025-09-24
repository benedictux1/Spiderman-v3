#!/bin/bash
# Comprehensive System Diagnostic Script
# Usage: ./diagnose_system.sh [WEB_SERVICE_URL]

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
WEB_SERVICE_URL="${1:-https://kith-platform.onrender.com}"  # Replace with actual URL
TIMEOUT=10

echo "=== KITH PLATFORM DIAGNOSTIC FRAMEWORK ==="
echo "Timestamp: $(date)"
echo "Web Service URL: $WEB_SERVICE_URL"
echo "Timeout: ${TIMEOUT}s"
echo ""

# Utility functions
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

test_endpoint() {
    local endpoint="$1"
    local method="${2:-GET}"
    local data="${3:-}"
    local expected_status="${4:-200}"

    if [[ -n "$data" ]]; then
        response=$(curl -s -w "%{http_code}" -X "$method" "$WEB_SERVICE_URL$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data" \
            --connect-timeout $TIMEOUT \
            --max-time $TIMEOUT)
    else
        response=$(curl -s -w "%{http_code}" -X "$method" "$WEB_SERVICE_URL$endpoint" \
            --connect-timeout $TIMEOUT \
            --max-time $TIMEOUT)
    fi

    http_code="${response: -3}"
    body="${response%???}"

    if [[ "$http_code" == "$expected_status" ]]; then
        echo "$body"
        return 0
    else
        echo "HTTP $http_code: $body"
        return 1
    fi
}

# TIER 1 TESTS - CRITICAL INFRASTRUCTURE
echo "=== TIER 1: CRITICAL INFRASTRUCTURE ==="

echo ""
echo "1.1 Testing Basic Service Health..."
if health_response=$(test_endpoint "/health"); then
    print_success "Service health check passed"
    echo "   Service Response: $health_response"
else
    print_error "Service health check FAILED"
    echo "   Response: $health_response"
    echo "   This indicates the web service is down or unreachable"
fi

echo ""
echo "1.2 Testing Redis Broker Connectivity..."
if redis_response=$(test_endpoint "/api/diagnostics/redis-test" "POST"); then
    print_success "Redis connectivity test passed"
    echo "   Redis Response: $redis_response"
else
    print_error "Redis connectivity test FAILED"
    echo "   Response: $redis_response"
    echo "   This is likely the root cause of 503 errors"
    echo "   Check: REDIS_URL environment variable on web service"
fi

echo ""
echo "1.3 Testing Celery Configuration..."
if celery_response=$(test_endpoint "/api/diagnostics/celery-info"); then
    print_success "Celery configuration check passed"
    echo "   Available Tasks: $(echo "$celery_response" | jq -r '.task_count // "unknown"') total"
    test_tasks=$(echo "$celery_response" | jq -r '.test_tasks[]? // empty' | tr '\n' ' ')
    if [[ -n "$test_tasks" ]]; then
        print_success "Test tasks found: $test_tasks"
    else
        print_warning "No test tasks found in registry (this may be normal)"
    fi
else
    print_warning "Celery configuration check failed or endpoint unavailable"
    echo "   Response: $celery_response"
fi

echo ""
echo "1.4 Testing Worker Health..."
if worker_response=$(test_endpoint "/api/diagnostics/worker-ping" "POST"); then
    print_success "Worker ping test passed"
    echo "   Worker Response: $worker_response"
else
    print_error "Worker ping test FAILED"
    echo "   Response: $worker_response"
    echo "   Worker may be down, unresponsive, or unreachable"
    echo "   Check: Worker service status and logs"
fi

# TIER 2 TESTS - CONFIGURATION ISSUES
echo ""
echo "=== TIER 2: CONFIGURATION AND PROTOCOL ==="

echo ""
echo "2.1 Testing Task Execution (Actual Test Run)..."
test_data='{"markers": ["unit"], "parallel": false}'
if task_response=$(test_endpoint "/api/analytics/test-runs" "POST" "$test_data" "202"); then
    print_success "Task execution test passed"
    task_id=$(echo "$task_response" | jq -r '.task_id // "unknown"')
    echo "   Task ID: $task_id"
    echo "   Status: $(echo "$task_response" | jq -r '.status // "unknown"')"
else
    print_error "Task execution test FAILED"
    echo "   Response: $task_response"
    echo "   This confirms the 503 error issue"
fi

echo ""
echo "2.2 Testing Environment Variables..."
if env_response=$(test_endpoint "/api/diagnostics/env-check"); then
    print_success "Environment variables test passed"
    echo "   Environment Status: $env_response"
else
    print_warning "Environment variables check failed or endpoint unavailable"
    echo "   Response: $env_response"
fi

# TIER 3 TESTS - RESOURCE MONITORING
echo ""
echo "=== TIER 3: RESOURCE AND PERFORMANCE ==="

echo ""
echo "3.1 Testing System Resources..."
if resource_response=$(test_endpoint "/api/diagnostics/resource-status"); then
    print_success "Resource monitoring test passed"
    echo "   Resource Status: $resource_response"
else
    print_warning "Resource monitoring failed or endpoint unavailable"
    echo "   Response: $resource_response"
fi

echo ""
echo "3.2 Testing Queue Status..."
if queue_response=$(test_endpoint "/api/diagnostics/queue-status"); then
    print_success "Queue status test passed"
    echo "   Queue Status: $queue_response"
else
    print_warning "Queue status check failed or endpoint unavailable"
    echo "   Response: $queue_response"
fi

# SUMMARY AND RECOMMENDATIONS
echo ""
echo "=== DIAGNOSTIC SUMMARY ==="
echo ""

# Analyze results and provide recommendations
if [[ "$health_response" == *"healthy"* ]]; then
    if [[ "$redis_response" == *"success"* ]]; then
        if [[ "$worker_response" == *"success"* ]]; then
            if [[ "$task_response" == *"task_id"* ]]; then
                print_success "ALL CRITICAL SYSTEMS OPERATIONAL"
                echo "   The 503 error issue appears to be resolved."
                echo "   Monitor task execution for completion."
            else
                print_error "TASK EXECUTION FAILING"
                echo "   Root Cause: Task dispatch failure despite healthy subsystems"
                echo "   Check: Task routing, serialization, or worker capacity"
            fi
        else
            print_error "WORKER UNAVAILABLE"
            echo "   Root Cause: Celery worker not responding"
            echo "   Action: Check worker service status: render logs -s Spiderman-v3-1"
        fi
    else
        print_error "REDIS CONNECTIVITY FAILED"
        echo "   Root Cause: Cannot connect to Redis broker"
        echo "   Action: Verify REDIS_URL environment variable on kith-platform service"
        echo "   Command: render env get -s kith-platform | grep REDIS_URL"
    fi
else
    print_error "WEB SERVICE UNHEALTHY"
    echo "   Root Cause: Web service is down or unreachable"
    echo "   Action: Check service status and recent deployments"
    echo "   Command: render services list"
fi

echo ""
echo "=== NEXT STEPS ==="
echo ""

# Provide specific next steps based on results
if [[ "$redis_response" != *"success"* ]]; then
    echo "🔧 IMMEDIATE ACTION REQUIRED:"
    echo "   1. Check Redis URL configuration:"
    echo "      render env get -s kith-platform | grep REDIS_URL"
    echo "   2. If missing, set REDIS_URL environment variable:"
    echo "      render env set -s kith-platform REDIS_URL=redis://your-redis-url"
    echo "   3. Redeploy the service:"
    echo "      render deploy -s kith-platform"
fi

if [[ "$worker_response" != *"success"* ]]; then
    echo "🔧 WORKER TROUBLESHOOTING:"
    echo "   1. Check worker service status:"
    echo "      render services list | grep Spiderman-v3"
    echo "   2. Check worker logs for errors:"
    echo "      render logs -s Spiderman-v3-1 --tail 100"
    echo "   3. Check worker resource usage:"
    echo "      render metrics -s Spiderman-v3-1 --period 1h"
fi

echo ""
echo "📊 MONITORING COMMANDS:"
echo "   • Web service logs: render logs -s kith-platform --tail 100"
echo "   • Worker logs:      render logs -s Spiderman-v3-1 --tail 100"
echo "   • Service status:   render services list"
echo "   • Recent deploys:   render deploys list -s kith-platform"
echo ""

echo "🔄 RE-RUN THIS DIAGNOSTIC:"
echo "   ./diagnose_system.sh $WEB_SERVICE_URL"
echo ""

# Exit with appropriate code
if [[ "$redis_response" == *"success"* ]] && [[ "$worker_response" == *"success"* ]] && [[ "$task_response" == *"task_id"* ]]; then
    exit 0  # All systems operational
elif [[ "$health_response" != *"healthy"* ]]; then
    exit 2  # Service down
else
    exit 1  # Partial system failure
fi