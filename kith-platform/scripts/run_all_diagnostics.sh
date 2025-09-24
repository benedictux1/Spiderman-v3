#!/bin/bash
# Master Diagnostic Script - Runs all diagnostic tools in sequence
# This script orchestrates the complete diagnostic process

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
WEB_SERVICE_URL="${1:-https://kith-platform.onrender.com}"
SCRIPT_DIR="$(dirname "$0")"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
REPORT_FILE="/tmp/diagnostic_report_$TIMESTAMP.txt"

print_banner() {
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║              KITH PLATFORM COMPREHENSIVE DIAGNOSTICS        ║"
    echo "╠══════════════════════════════════════════════════════════════╣"
    echo "║ This script runs all diagnostic tools to identify root      ║"
    echo "║ causes of 503 errors and Celery task execution failures.    ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_header() {
    echo -e "${BLUE}"
    echo "┌─────────────────────────────────────────────────────────────┐"
    echo "│ $1"
    printf "│ %-59s │\n" "$(date)"
    echo "└─────────────────────────────────────────────────────────────┘"
    echo -e "${NC}"
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

run_diagnostic_tool() {
    local tool_name="$1"
    local script_path="$2"
    local description="$3"
    local args="${4:-}"

    echo ""
    print_header "$tool_name: $description"

    if [[ ! -f "$script_path" ]]; then
        print_error "Diagnostic tool not found: $script_path"
        echo "   Please ensure all diagnostic scripts are in place"
        return 1
    fi

    if [[ ! -x "$script_path" ]]; then
        print_warning "Making script executable: $script_path"
        chmod +x "$script_path"
    fi

    echo "Running: $script_path $args"
    echo ""

    # Run the tool and capture output
    if [[ -n "$args" ]]; then
        "$script_path" $args | tee -a "$REPORT_FILE"
    else
        "$script_path" | tee -a "$REPORT_FILE"
    fi

    local exit_code=${PIPESTATUS[0]}

    echo ""
    if [[ $exit_code -eq 0 ]]; then
        print_success "$tool_name completed successfully"
    elif [[ $exit_code -eq 1 ]]; then
        print_warning "$tool_name completed with warnings"
    else
        print_error "$tool_name failed or found critical issues"
    fi

    echo "----------------------------------------" >> "$REPORT_FILE"
    return $exit_code
}

# Main execution
clear
print_banner

echo "🔍 DIAGNOSTIC CONFIGURATION:"
echo "   Web Service URL: $WEB_SERVICE_URL"
echo "   Scripts Directory: $SCRIPT_DIR"
echo "   Report File: $REPORT_FILE"
echo "   Timestamp: $(date)"
echo ""

# Initialize report file
echo "KITH PLATFORM COMPREHENSIVE DIAGNOSTIC REPORT" > "$REPORT_FILE"
echo "Generated: $(date)" >> "$REPORT_FILE"
echo "Web Service URL: $WEB_SERVICE_URL" >> "$REPORT_FILE"
echo "=========================================" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# Phase 1: Component Isolation Testing
run_diagnostic_tool \
    "PHASE 1" \
    "$SCRIPT_DIR/isolation_tests.sh" \
    "Component Isolation Testing"

isolation_exit=$?

# Phase 2: System Integration Testing
run_diagnostic_tool \
    "PHASE 2" \
    "$SCRIPT_DIR/diagnose_system.sh" \
    "System Integration Testing" \
    "$WEB_SERVICE_URL"

system_exit=$?

# Phase 3: Log Analysis
run_diagnostic_tool \
    "PHASE 3" \
    "$SCRIPT_DIR/analyze_logs.sh" \
    "Historical Log Analysis"

logs_exit=$?

# Phase 4: Final Assessment
print_header "PHASE 4: FINAL ASSESSMENT AND RECOMMENDATIONS"

echo ""
echo "📊 DIAGNOSTIC RESULTS SUMMARY:"
echo ""

# Analyze results from each phase
if [[ $isolation_exit -eq 0 ]]; then
    print_success "Component isolation tests: All components healthy"
elif [[ $isolation_exit -eq 1 ]]; then
    print_warning "Component isolation tests: Some components have issues"
else
    print_error "Component isolation tests: Critical component failures"
fi

if [[ $system_exit -eq 0 ]]; then
    print_success "System integration tests: All systems operational"
elif [[ $system_exit -eq 1 ]]; then
    print_warning "System integration tests: Partial system failure"
else
    print_error "System integration tests: Critical system failure"
fi

if [[ $logs_exit -eq 0 ]]; then
    print_success "Log analysis: Clean logs, no major issues"
else
    print_warning "Log analysis: Issues detected in historical logs"
fi

# Overall assessment
echo ""
echo "🎯 OVERALL SYSTEM STATUS:"

if [[ $system_exit -eq 0 ]]; then
    print_success "SYSTEM STATUS: OPERATIONAL"
    echo "   The 503 error issue appears to be resolved."
    echo "   All critical systems are functioning normally."
    echo ""
    echo "   ✅ Next steps:"
    echo "      1. Monitor system for 30 minutes to ensure stability"
    echo "      2. Test actual task execution through the admin UI"
    echo "      3. Set up automated monitoring using the diagnostic endpoints"

elif [[ $isolation_exit -eq 2 || $system_exit -eq 2 ]]; then
    print_error "SYSTEM STATUS: CRITICAL FAILURE"
    echo "   Multiple critical components are failing."
    echo "   Immediate intervention required."
    echo ""
    echo "   🚨 CRITICAL ACTIONS:"
    echo "      1. Check service status: render services list"
    echo "      2. Review recent deployments for breaking changes"
    echo "      3. Verify environment variables are properly set"
    echo "      4. Consider rollback to last known good deployment"

else
    print_warning "SYSTEM STATUS: DEGRADED"
    echo "   Some components are failing but system may be partially operational."
    echo ""
    echo "   ⚠️  IMMEDIATE ACTIONS:"

    # Provide specific recommendations based on failure patterns
    if [[ $isolation_exit -ne 0 ]]; then
        echo "      1. Address component-level failures identified in Phase 1"
    fi

    if [[ $system_exit -ne 0 ]]; then
        echo "      2. Fix system integration issues identified in Phase 2"
        if [[ $system_exit -eq 1 ]]; then
            echo "         - Focus on Redis connectivity and worker health"
        fi
    fi

    echo "      3. Review log analysis findings from Phase 3"
    echo "      4. Re-run diagnostics after each fix"
fi

echo ""
echo "📋 DETAILED REPORT AVAILABLE:"
echo "   Full diagnostic report: $REPORT_FILE"
echo "   View with: cat $REPORT_FILE"
echo "   Or: less $REPORT_FILE"

echo ""
echo "🔄 RE-RUN DIAGNOSTICS:"
echo "   After making fixes: $0 $WEB_SERVICE_URL"

echo ""
echo "🛠️  QUICK REFERENCE COMMANDS:"
echo "   Service status:     render services list"
echo "   Web service logs:   render logs -s kith-platform --tail 100"
echo "   Worker logs:        render logs -s Spiderman-v3-1 --tail 100"
echo "   Environment check:  render env get -s kith-platform"
echo "   Test task manually: curl -X POST $WEB_SERVICE_URL/api/analytics/test-runs \\"
echo "                          -H 'Content-Type: application/json' \\"
echo "                          -d '{\"markers\":[\"unit\"],\"parallel\":false}'"

# Save summary to report
echo "" >> "$REPORT_FILE"
echo "FINAL ASSESSMENT" >> "$REPORT_FILE"
echo "================" >> "$REPORT_FILE"
echo "Isolation Tests Exit Code: $isolation_exit" >> "$REPORT_FILE"
echo "System Tests Exit Code: $system_exit" >> "$REPORT_FILE"
echo "Log Analysis Exit Code: $logs_exit" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

if [[ $system_exit -eq 0 ]]; then
    echo "OVERALL STATUS: OPERATIONAL" >> "$REPORT_FILE"
elif [[ $isolation_exit -eq 2 || $system_exit -eq 2 ]]; then
    echo "OVERALL STATUS: CRITICAL FAILURE" >> "$REPORT_FILE"
else
    echo "OVERALL STATUS: DEGRADED" >> "$REPORT_FILE"
fi

echo "" >> "$REPORT_FILE"
echo "Report generated: $(date)" >> "$REPORT_FILE"

# Final spacing and cleanup
echo ""
print_header "DIAGNOSTIC PROCESS COMPLETE"
echo ""

# Exit with appropriate code based on overall results
if [[ $system_exit -eq 0 ]]; then
    exit 0  # All systems operational
elif [[ $isolation_exit -eq 2 || $system_exit -eq 2 ]]; then
    exit 2  # Critical failure
else
    exit 1  # Degraded but potentially recoverable
fi