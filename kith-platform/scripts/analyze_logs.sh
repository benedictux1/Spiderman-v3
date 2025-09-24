#!/bin/bash
# Comprehensive Log Analysis Script
# Analyzes logs from both web service and worker to identify patterns and root causes

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
WEB_SERVICE="kith-platform"
WORKER_SERVICE="Spiderman-v3-1"
LOG_LINES=500

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

analyze_pattern() {
    local logs="$1"
    local pattern="$2"
    local description="$3"
    local severity="${4:-INFO}"

    count=$(echo "$logs" | grep -i "$pattern" | wc -l)

    if [[ $count -gt 0 ]]; then
        case $severity in
            "ERROR")
                print_error "$description: $count occurrences"
                ;;
            "WARNING")
                print_warning "$description: $count occurrences"
                ;;
            *)
                echo "   $description: $count occurrences"
                ;;
        esac

        # Show recent examples (max 3)
        echo "$logs" | grep -i "$pattern" | tail -3 | while read -r line; do
            echo "      $(echo "$line" | cut -c1-100)..."
        done
    fi
}

print_header "COMPREHENSIVE LOG ANALYSIS"
echo "Timestamp: $(date)"
echo "Analyzing logs from:"
echo "  Web Service:    $WEB_SERVICE"
echo "  Worker Service: $WORKER_SERVICE"
echo "  Log Lines:      $LOG_LINES each"
echo ""

# Fetch logs
echo "Fetching logs..."
web_logs=$(render logs -s "$WEB_SERVICE" --tail $LOG_LINES 2>/dev/null)
worker_logs=$(render logs -s "$WORKER_SERVICE" --tail $LOG_LINES 2>/dev/null)

if [[ -z "$web_logs" ]]; then
    print_error "Could not fetch web service logs"
    echo "   Check: render auth status and service name"
    web_logs=""
fi

if [[ -z "$worker_logs" ]]; then
    print_error "Could not fetch worker service logs"
    echo "   Check: render auth status and service name"
    worker_logs=""
fi

echo ""

# Analysis 1: Critical Errors
print_header "CRITICAL ERROR ANALYSIS"

echo ""
echo "🔥 Web Service Critical Errors:"
analyze_pattern "$web_logs" "CRITICAL\|FATAL" "Critical/Fatal errors" "ERROR"
analyze_pattern "$web_logs" "500 Internal Server Error" "HTTP 500 errors" "ERROR"
analyze_pattern "$web_logs" "503 Service Unavailable" "HTTP 503 errors" "ERROR"
analyze_pattern "$web_logs" "send_task.*failed\|Failed to enqueue" "Task dispatch failures" "ERROR"
analyze_pattern "$web_logs" "Exception\|Traceback" "Python exceptions" "ERROR"

echo ""
echo "🔥 Worker Critical Errors:"
analyze_pattern "$worker_logs" "CRITICAL\|FATAL" "Critical/Fatal errors" "ERROR"
analyze_pattern "$worker_logs" "ERROR\|Exception" "General errors" "ERROR"
analyze_pattern "$worker_logs" "Traceback" "Python tracebacks" "ERROR"
analyze_pattern "$worker_logs" "Task.*failed\|FAILURE" "Task execution failures" "ERROR"

# Analysis 2: Connection Issues
echo ""
print_header "CONNECTION ANALYSIS"

echo ""
echo "🔌 Redis Connection Issues:"
analyze_pattern "$web_logs" "redis.*connection\|redis.*error\|broker.*error" "Web service Redis issues" "ERROR"
analyze_pattern "$worker_logs" "redis.*connection\|redis.*error\|broker.*error" "Worker Redis issues" "ERROR"
analyze_pattern "$web_logs" "Connection refused.*6379\|timeout.*6379" "Redis connection refused" "ERROR"
analyze_pattern "$worker_logs" "Connection refused.*6379\|timeout.*6379" "Worker Redis connection refused" "ERROR"

echo ""
echo "🗃️ Database Connection Issues:"
analyze_pattern "$web_logs" "database.*connection\|postgresql.*error\|sqlalchemy.*error" "Web service DB issues" "ERROR"
analyze_pattern "$worker_logs" "database.*connection\|postgresql.*error\|sqlalchemy.*error" "Worker DB issues" "ERROR"
analyze_pattern "$web_logs" "Connection refused.*5432\|timeout.*5432" "Database connection refused" "ERROR"
analyze_pattern "$worker_logs" "Connection refused.*5432\|timeout.*5432" "Worker DB connection refused" "ERROR"

# Analysis 3: Task Processing
echo ""
print_header "TASK PROCESSING ANALYSIS"

echo ""
echo "📋 Task Registration and Discovery:"
analyze_pattern "$worker_logs" "Connected to redis\|ready\|mingle" "Worker startup success" "INFO"
analyze_pattern "$worker_logs" "Received task.*run_test_suite" "Test task received" "INFO"
analyze_pattern "$worker_logs" "Task.*run_test_suite.*succeeded" "Test task success" "INFO"
analyze_pattern "$worker_logs" "autodiscover_tasks\|include.*tasks" "Task discovery events" "INFO"
analyze_pattern "$worker_logs" "registered" "Task registration events" "INFO"

echo ""
echo "⚠️ Task Processing Issues:"
analyze_pattern "$web_logs" "test runner task not registered" "Task not registered errors" "ERROR"
analyze_pattern "$worker_logs" "task.*not.*registered\|unknown task" "Unknown task errors" "ERROR"
analyze_pattern "$worker_logs" "task.*timeout\|SoftTimeLimitExceeded" "Task timeout issues" "WARNING"
analyze_pattern "$worker_logs" "task.*revoked\|task.*terminated" "Task termination" "WARNING"

# Analysis 4: Resource and Performance
echo ""
print_header "RESOURCE AND PERFORMANCE ANALYSIS"

echo ""
echo "💾 Memory and Resource Issues:"
analyze_pattern "$web_logs" "out of memory\|oom\|killed" "OOM issues (web)" "ERROR"
analyze_pattern "$worker_logs" "out of memory\|oom\|killed" "OOM issues (worker)" "ERROR"
analyze_pattern "$worker_logs" "memory.*limit\|resource.*limit" "Resource limit hits" "WARNING"
analyze_pattern "$web_logs" "high memory\|memory usage" "Memory warnings (web)" "WARNING"
analyze_pattern "$worker_logs" "high memory\|memory usage" "Memory warnings (worker)" "WARNING"

echo ""
echo "🐌 Performance Issues:"
analyze_pattern "$web_logs" "slow\|timeout\|taking.*long" "Performance warnings (web)" "WARNING"
analyze_pattern "$worker_logs" "slow\|timeout\|taking.*long" "Performance warnings (worker)" "WARNING"
analyze_pattern "$worker_logs" "task.*seconds\|execution.*time" "Task duration info" "INFO"

# Analysis 5: Environment and Configuration
echo ""
print_header "CONFIGURATION ANALYSIS"

echo ""
echo "🔧 Environment Variable Issues:"
analyze_pattern "$web_logs" "REDIS_URL.*not.*set\|environment.*variable.*not" "Missing env vars (web)" "ERROR"
analyze_pattern "$worker_logs" "REDIS_URL.*not.*set\|environment.*variable.*not" "Missing env vars (worker)" "ERROR"
analyze_pattern "$web_logs" "\\\${{.*}}\|not.*resolved" "Unresolved env vars (web)" "ERROR"
analyze_pattern "$worker_logs" "\\\${{.*}}\|not.*resolved" "Unresolved env vars (worker)" "ERROR"

echo ""
echo "⚙️ Configuration Issues:"
analyze_pattern "$web_logs" "configuration.*error\|config.*invalid" "Config errors (web)" "ERROR"
analyze_pattern "$worker_logs" "configuration.*error\|config.*invalid" "Config errors (worker)" "ERROR"
analyze_pattern "$worker_logs" "broker.*url\|result.*backend" "Broker configuration" "INFO"

# Analysis 6: Recent Activity Patterns
echo ""
print_header "RECENT ACTIVITY ANALYSIS"

echo ""
echo "📊 Recent Activity Summary (last 50 log lines):"

# Recent web service activity
recent_web=$(echo "$web_logs" | tail -50)
web_requests=$(echo "$recent_web" | grep -E "POST|GET|PUT|DELETE" | wc -l)
web_errors=$(echo "$recent_web" | grep -E "ERROR|CRITICAL|500|503" | wc -l)

echo "   Web Service (recent 50 lines):"
echo "     HTTP Requests: $web_requests"
echo "     Errors: $web_errors"

# Recent worker activity
recent_worker=$(echo "$worker_logs" | tail -50)
worker_tasks=$(echo "$recent_worker" | grep -E "Received task|Task.*succeeded|Task.*failed" | wc -l)
worker_errors=$(echo "$recent_worker" | grep -E "ERROR|CRITICAL|FAILURE|Exception" | wc -l)

echo "   Worker Service (recent 50 lines):"
echo "     Task Events: $worker_tasks"
echo "     Errors: $worker_errors"

# Analysis 7: Timeline Analysis
echo ""
print_header "TIMELINE ANALYSIS"

echo ""
echo "🕒 Recent Error Timeline (last 10 errors from each service):"

echo ""
echo "Web Service Errors:"
echo "$web_logs" | grep -E "ERROR|CRITICAL|500|503" | tail -10 | while read -r line; do
    timestamp=$(echo "$line" | grep -o '\[.*\]' | head -1)
    error_type=$(echo "$line" | grep -oE "(ERROR|CRITICAL|500|503|Exception)")
    echo "   $timestamp: $error_type"
done

echo ""
echo "Worker Errors:"
echo "$worker_logs" | grep -E "ERROR|CRITICAL|FAILURE|Exception" | tail -10 | while read -r line; do
    timestamp=$(echo "$line" | grep -o '\[.*\]' | head -1)
    error_type=$(echo "$line" | grep -oE "(ERROR|CRITICAL|FAILURE|Exception)")
    echo "   $timestamp: $error_type"
done

# Analysis 8: Success Indicators
echo ""
print_header "SUCCESS INDICATORS"

echo ""
echo "✅ Positive Indicators:"
analyze_pattern "$worker_logs" "ready.*consume" "Worker ready to consume" "INFO"
analyze_pattern "$worker_logs" "Connected to redis" "Redis connection established" "INFO"
analyze_pattern "$worker_logs" "Task.*succeeded" "Successful task completions" "INFO"
analyze_pattern "$web_logs" "200.*OK\|202.*Accepted" "Successful HTTP responses" "INFO"
analyze_pattern "$web_logs" "Task started with ID" "Successful task dispatch" "INFO"

# Summary and Recommendations
echo ""
print_header "LOG ANALYSIS SUMMARY"

# Calculate overall health score
total_errors=$(echo "$web_logs $worker_logs" | grep -cE "ERROR|CRITICAL|FATAL|Exception|500|503")
total_warnings=$(echo "$web_logs $worker_logs" | grep -cE "WARNING|WARN|timeout|slow")
total_success=$(echo "$web_logs $worker_logs" | grep -cE "succeeded|200 OK|Connected|ready")

echo ""
echo "📈 HEALTH METRICS:"
echo "   Total Errors:   $total_errors"
echo "   Total Warnings: $total_warnings"
echo "   Success Events: $total_success"

# Determine overall health
if [[ $total_errors -gt 20 ]]; then
    print_error "SYSTEM STATUS: CRITICAL (High error count)"
elif [[ $total_errors -gt 5 ]]; then
    print_warning "SYSTEM STATUS: DEGRADED (Moderate errors)"
elif [[ $total_success -gt 10 ]]; then
    print_success "SYSTEM STATUS: HEALTHY (Good success rate)"
else
    print_warning "SYSTEM STATUS: UNKNOWN (Insufficient data)"
fi

echo ""
echo "🎯 KEY FINDINGS:"

# Identify top issues
if echo "$web_logs" | grep -q "redis.*connection\|redis.*error"; then
    print_error "Redis connectivity issues detected in web service"
fi

if echo "$worker_logs" | grep -q "Task.*not.*registered\|unknown task"; then
    print_error "Task registration issues detected in worker"
fi

if echo "$web_logs $worker_logs" | grep -q "out of memory\|oom\|killed"; then
    print_error "Memory/OOM issues detected"
fi

if echo "$web_logs" | grep -q "503.*Service Unavailable"; then
    print_error "503 Service Unavailable errors confirmed"
fi

echo ""
echo "🔧 IMMEDIATE ACTIONS NEEDED:"

# Provide specific recommendations based on findings
if echo "$web_logs" | grep -q "redis.*error\|redis.*connection"; then
    echo "   1. Fix Redis connectivity issues on web service"
    echo "      Command: render env get -s $WEB_SERVICE | grep REDIS_URL"
fi

if echo "$worker_logs" | grep -q "Task.*not.*registered"; then
    echo "   2. Fix task registration on worker"
    echo "      Command: render logs -s $WORKER_SERVICE | grep -i register"
fi

if [[ $total_errors -gt 10 ]]; then
    echo "   3. Investigate high error rate"
    echo "      Command: render logs -s $WEB_SERVICE --tail 100 | grep ERROR"
fi

echo ""
echo "📋 MONITORING COMMANDS:"
echo "   Real-time web logs:    render logs -s $WEB_SERVICE -f"
echo "   Real-time worker logs: render logs -s $WORKER_SERVICE -f"
echo "   Service status:        render services list"
echo "   Recent deployments:    render deploys list -s $WEB_SERVICE"

echo ""
echo "🔄 NEXT STEPS:"
echo "   1. Address critical issues identified above"
echo "   2. Run system diagnostic: ./diagnose_system.sh"
echo "   3. Test fixes with isolation tests: ./isolation_tests.sh"
echo "   4. Monitor logs for 10-15 minutes after fixes"
echo ""