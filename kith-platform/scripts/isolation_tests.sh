#!/bin/bash
# Component Isolation Testing Script
# Tests individual system components in isolation to pinpoint failures

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_header "COMPONENT ISOLATION TESTING"
echo "Timestamp: $(date)"
echo ""

# Test 1: Direct Redis Connection (bypassing application)
print_header "TEST 1: DIRECT REDIS CONNECTIVITY"
echo "Testing Redis connection directly, bypassing application logic..."

if command -v redis-cli &> /dev/null; then
    if [[ -n "$REDIS_URL" ]]; then
        echo "Using REDIS_URL from environment: ${REDIS_URL:0:30}..."

        # Test basic connectivity
        if redis-cli -u "$REDIS_URL" ping | grep -q "PONG"; then
            print_success "Direct Redis ping successful"

            # Test basic operations
            redis-cli -u "$REDIS_URL" set "isolation_test_$(date +%s)" "test_value" > /dev/null
            if [[ $? -eq 0 ]]; then
                print_success "Direct Redis write operation successful"
            else
                print_error "Direct Redis write operation failed"
            fi

            # Test list operations (Celery uses lists for queues)
            test_key="isolation_test_queue_$(date +%s)"
            redis-cli -u "$REDIS_URL" lpush "$test_key" "test_message" > /dev/null
            if message=$(redis-cli -u "$REDIS_URL" rpop "$test_key"); then
                print_success "Direct Redis queue operations successful"
                echo "   Message retrieved: $message"
            else
                print_error "Direct Redis queue operations failed"
            fi

        else
            print_error "Direct Redis ping failed"
            echo "   REDIS_URL may be incorrect or Redis service is down"
        fi
    else
        print_warning "REDIS_URL environment variable not set"
        echo "   Cannot test direct Redis connectivity"
    fi
else
    print_warning "redis-cli not available for direct testing"
    echo "   Install redis-tools: apt-get install redis-tools"
fi

echo ""

# Test 2: Direct Database Connection (bypassing ORM)
print_header "TEST 2: DIRECT DATABASE CONNECTIVITY"
echo "Testing PostgreSQL connection directly, bypassing application ORM..."

if command -v psql &> /dev/null; then
    if [[ -n "$DATABASE_URL" ]]; then
        echo "Testing database connection..."

        # Test basic connectivity
        if psql "$DATABASE_URL" -c "SELECT 1;" &> /dev/null; then
            print_success "Direct database connection successful"

            # Test table access
            if psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM pg_tables WHERE schemaname = 'public';" &> /dev/null; then
                table_count=$(psql "$DATABASE_URL" -t -c "SELECT COUNT(*) FROM pg_tables WHERE schemaname = 'public';" 2>/dev/null | xargs)
                print_success "Database table access successful ($table_count public tables)"
            else
                print_warning "Could not count tables (permissions or schema issue)"
            fi

            # Test if test_runs table exists
            if psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM test_runs LIMIT 1;" &> /dev/null; then
                run_count=$(psql "$DATABASE_URL" -t -c "SELECT COUNT(*) FROM test_runs;" 2>/dev/null | xargs)
                print_success "test_runs table accessible ($run_count records)"
            else
                print_warning "test_runs table not accessible or doesn't exist"
                echo "   This may cause task execution failures"
            fi

        else
            print_error "Direct database connection failed"
            echo "   DATABASE_URL may be incorrect or database service is down"
        fi
    else
        print_warning "DATABASE_URL environment variable not set"
        echo "   Cannot test direct database connectivity"
    fi
else
    print_warning "psql not available for direct testing"
    echo "   Install postgresql-client: apt-get install postgresql-client"
fi

echo ""

# Test 3: Worker Process Testing (if we're on the worker)
print_header "TEST 3: WORKER PROCESS ISOLATION"
echo "Testing Celery worker functionality directly..."

if command -v python3 &> /dev/null; then
    # Test if we can import the Celery app
    cat << 'EOF' > /tmp/test_celery_import.py
import sys
import os
sys.path.insert(0, '/opt/render/project/src/kith-platform')
try:
    from app.celery_app import celery_app
    print("SUCCESS: Celery app import successful")
    print(f"App name: {celery_app.main}")
    print(f"Task count: {len(celery_app.tasks.keys())}")
    test_tasks = [k for k in celery_app.tasks.keys() if 'test' in k.lower()]
    print(f"Test tasks: {test_tasks}")
except Exception as e:
    print(f"ERROR: Celery app import failed: {e}")
    sys.exit(1)
EOF

    if python3 /tmp/test_celery_import.py; then
        print_success "Worker can import Celery application"

        # Test task registration
        cat << 'EOF' > /tmp/test_task_registration.py
import sys
sys.path.insert(0, '/opt/render/project/src/kith-platform')
try:
    from app.celery_app import celery_app
    target_task = 'app.tasks.test_tasks.run_test_suite'
    if target_task in celery_app.tasks:
        print("SUCCESS: run_test_suite task is registered")
    else:
        print(f"ERROR: run_test_suite task not found")
        print(f"Available tasks: {list(celery_app.tasks.keys())}")
        sys.exit(1)
except Exception as e:
    print(f"ERROR: Task registration check failed: {e}")
    sys.exit(1)
EOF

        if python3 /tmp/test_task_registration.py; then
            print_success "run_test_suite task is properly registered"
        else
            print_error "run_test_suite task is not registered"
            echo "   This will cause 'task not registered' errors"
        fi

    else
        print_error "Worker cannot import Celery application"
        echo "   This indicates a fundamental configuration or dependency issue"
    fi

    # Cleanup
    rm -f /tmp/test_celery_import.py /tmp/test_task_registration.py
else
    print_warning "Python3 not available for worker testing"
fi

echo ""

# Test 4: Network Connectivity Between Components
print_header "TEST 4: NETWORK CONNECTIVITY ISOLATION"
echo "Testing network connectivity between services..."

# Test Redis host connectivity (extract host from REDIS_URL)
if [[ -n "$REDIS_URL" ]]; then
    redis_host=$(echo "$REDIS_URL" | sed -n 's#redis://\([^:/]*\).*#\1#p')
    redis_port=$(echo "$REDIS_URL" | sed -n 's#redis://[^:]*:\([0-9]*\).*#\1#p')
    redis_port=${redis_port:-6379}

    if [[ -n "$redis_host" ]]; then
        echo "Testing connectivity to Redis host: $redis_host:$redis_port"
        if timeout 5 bash -c "</dev/tcp/$redis_host/$redis_port" 2>/dev/null; then
            print_success "Network connectivity to Redis host successful"
        else
            print_error "Cannot establish network connection to Redis host"
            echo "   Host: $redis_host, Port: $redis_port"
            echo "   This indicates network, DNS, or firewall issues"
        fi
    else
        print_warning "Could not parse Redis host from REDIS_URL"
    fi
fi

# Test database host connectivity
if [[ -n "$DATABASE_URL" ]]; then
    db_host=$(echo "$DATABASE_URL" | sed -n 's#postgresql://[^@]*@\([^:/]*\).*#\1#p')
    db_port=$(echo "$DATABASE_URL" | sed -n 's#postgresql://[^@]*@[^:]*:\([0-9]*\).*#\1#p')
    db_port=${db_port:-5432}

    if [[ -n "$db_host" ]]; then
        echo "Testing connectivity to database host: $db_host:$db_port"
        if timeout 5 bash -c "</dev/tcp/$db_host/$db_port" 2>/dev/null; then
            print_success "Network connectivity to database host successful"
        else
            print_error "Cannot establish network connection to database host"
            echo "   Host: $db_host, Port: $db_port"
            echo "   This indicates network, DNS, or firewall issues"
        fi
    else
        print_warning "Could not parse database host from DATABASE_URL"
    fi
fi

echo ""

# Test 5: Process and Resource Isolation
print_header "TEST 5: PROCESS AND RESOURCE ISOLATION"
echo "Testing process health and resource constraints..."

# Check memory usage
if command -v free &> /dev/null; then
    memory_info=$(free -m)
    available_memory=$(echo "$memory_info" | awk '/^Mem:/ {print $7}')
    total_memory=$(echo "$memory_info" | awk '/^Mem:/ {print $2}')

    if [[ $available_memory -lt 100 ]]; then
        print_error "Low available memory: ${available_memory}MB (total: ${total_memory}MB)"
        echo "   This may cause OOM kills and task failures"
    else
        print_success "Sufficient memory available: ${available_memory}MB (total: ${total_memory}MB)"
    fi
fi

# Check disk space
if command -v df &> /dev/null; then
    disk_usage=$(df -h / | tail -1)
    usage_percent=$(echo "$disk_usage" | awk '{print $5}' | sed 's/%//')

    if [[ $usage_percent -gt 90 ]]; then
        print_error "High disk usage: ${usage_percent}%"
        echo "   This may cause application failures"
    else
        print_success "Disk usage acceptable: ${usage_percent}%"
    fi
fi

# Check for zombie processes
zombie_count=$(ps aux | awk '$8 ~ /^Z/ {count++} END {print count+0}')
if [[ $zombie_count -gt 0 ]]; then
    print_warning "Found $zombie_count zombie processes"
    echo "   This may indicate process cleanup issues"
else
    print_success "No zombie processes detected"
fi

echo ""

# Summary and Recommendations
print_header "ISOLATION TEST SUMMARY"

echo ""
echo "📊 COMPONENT STATUS:"
echo "   Redis:    $(if redis-cli -u "$REDIS_URL" ping &>/dev/null; then echo "✅ HEALTHY"; else echo "❌ FAILED"; fi)"
echo "   Database: $(if [[ -n "$DATABASE_URL" ]] && psql "$DATABASE_URL" -c "SELECT 1;" &>/dev/null; then echo "✅ HEALTHY"; else echo "❌ FAILED"; fi)"
echo "   Network:  $(if timeout 2 bash -c "</dev/tcp/8.8.8.8/53" 2>/dev/null; then echo "✅ HEALTHY"; else echo "❌ FAILED"; fi)"
echo "   Resources:$(if [[ $(free -m | awk '/^Mem:/ {print $7}') -gt 100 ]]; then echo "✅ HEALTHY"; else echo "❌ LOW"; fi)"

echo ""
echo "🎯 NEXT STEPS:"
echo "   1. Address any FAILED components above"
echo "   2. Run the full system diagnostic: ./diagnose_system.sh"
echo "   3. Check service logs for specific error messages"
echo "   4. Test actual task execution after fixes"

echo ""
echo "🔧 DEBUGGING COMMANDS:"
echo "   Redis debug:    redis-cli -u \$REDIS_URL monitor"
echo "   Database debug: psql \$DATABASE_URL -c '\\l'"
echo "   Process debug:  ps aux | grep -E '(celery|python|gunicorn)'"
echo "   Network debug:  netstat -tlnp | grep -E '(6379|5432)'"
echo ""