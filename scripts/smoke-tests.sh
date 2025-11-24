#!/bin/bash
# Smoke tests for Darts application deployment

set -e

NAMESPACE="${NAMESPACE:-darts-app}"
TIMEOUT=60

echo "🧪 Running smoke tests for Darts application..."
echo "Namespace: $NAMESPACE"
echo ""

# Function to check if a service is healthy
check_service_health() {
    local service_name=$1
    local port=$2
    local path=$3
    
    echo "Checking $service_name health..."
    
    timeout $TIMEOUT kubectl run smoke-test-pod \
        --image=curlimages/curl \
        --rm -i --restart=Never \
        -n $NAMESPACE \
        -- curl -f -s "http://${service_name}:${port}${path}" > /dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        echo "✅ $service_name is healthy"
        return 0
    else
        echo "❌ $service_name health check failed"
        return 1
    fi
}

# Function to check if pods are running
check_pods_running() {
    local app_label=$1
    
    echo "Checking if $app_label pods are running..."
    
    local running_pods=$(kubectl get pods -n $NAMESPACE -l app=$app_label \
        --field-selector=status.phase=Running \
        --no-headers 2>/dev/null | wc -l)
    
    if [ "$running_pods" -gt 0 ]; then
        echo "✅ $app_label has $running_pods running pod(s)"
        return 0
    else
        echo "❌ No running pods found for $app_label"
        return 1
    fi
}

# Function to check service exists
check_service_exists() {
    local service_name=$1
    
    echo "Checking if service $service_name exists..."
    
    kubectl get service $service_name -n $NAMESPACE > /dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        echo "✅ Service $service_name exists"
        return 0
    else
        echo "❌ Service $service_name not found"
        return 1
    fi
}

# Test results counter
tests_passed=0
tests_failed=0

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 1: Check namespace exists"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if kubectl get namespace $NAMESPACE > /dev/null 2>&1; then
    echo "✅ Namespace $NAMESPACE exists"
    ((tests_passed++))
else
    echo "❌ Namespace $NAMESPACE not found"
    ((tests_failed++))
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 2: Check if pods are running"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if check_pods_running "darts-app"; then
    ((tests_passed++))
else
    ((tests_failed++))
fi

if check_pods_running "api-gateway"; then
    ((tests_passed++))
else
    ((tests_failed++))
fi

if check_pods_running "postgres"; then
    ((tests_passed++))
else
    ((tests_failed++))
fi

if check_pods_running "rabbitmq"; then
    ((tests_passed++))
else
    ((tests_failed++))
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 3: Check if services exist"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if check_service_exists "darts-app-service"; then
    ((tests_passed++))
else
    ((tests_failed++))
fi

if check_service_exists "api-gateway-service"; then
    ((tests_passed++))
else
    ((tests_failed++))
fi

if check_service_exists "postgres-service"; then
    ((tests_passed++))
else
    ((tests_failed++))
fi

if check_service_exists "rabbitmq-service"; then
    ((tests_passed++))
else
    ((tests_failed++))
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 4: Check service health endpoints"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if check_service_health "darts-app-service" "5000" "/health"; then
    ((tests_passed++))
else
    ((tests_failed++))
fi

if check_service_health "api-gateway-service" "8080" "/health"; then
    ((tests_passed++))
else
    ((tests_failed++))
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 5: Check HPA configuration"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if kubectl get hpa darts-app-hpa -n $NAMESPACE > /dev/null 2>&1; then
    echo "✅ HPA for darts-app is configured"
    ((tests_passed++))
else
    echo "❌ HPA for darts-app not found"
    ((tests_failed++))
fi

if kubectl get hpa api-gateway-hpa -n $NAMESPACE > /dev/null 2>&1; then
    echo "✅ HPA for api-gateway is configured"
    ((tests_passed++))
else
    echo "❌ HPA for api-gateway not found"
    ((tests_failed++))
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
total_tests=$((tests_passed + tests_failed))
echo "Total tests: $total_tests"
echo "✅ Passed: $tests_passed"
echo "❌ Failed: $tests_failed"
echo ""

if [ $tests_failed -eq 0 ]; then
    echo "🎉 All smoke tests passed!"
    exit 0
else
    echo "⚠️  Some tests failed. Check the logs above for details."
    exit 1
fi
