#!/bin/bash

# Web Client Validation Script
# Tests the web client and API connectivity

echo "🧪 Web Client Validation Test"
echo "=============================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
PASSED=0
FAILED=0

# Test 1: Check if containers are running
echo "Test 1: Checking if containers are running..."
if docker-compose ps | grep -q "Up"; then
    echo -e "${GREEN}✅ PASS${NC} - Containers are running"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC} - Containers are not running"
    ((FAILED++))
fi
echo ""

# Test 2: Web client accessibility
echo "Test 2: Testing web client accessibility (http://localhost)..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost/ | grep -q "200"; then
    echo -e "${GREEN}✅ PASS${NC} - Web client is accessible"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC} - Web client is not accessible"
    ((FAILED++))
fi
echo ""

# Test 3: API health check through web client proxy
echo "Test 3: Testing API health check (http://localhost/api/health)..."
HEALTH_RESPONSE=$(curl -s http://localhost/api/health)
if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo -e "${GREEN}✅ PASS${NC} - API health check successful"
    echo "Response: $HEALTH_RESPONSE"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC} - API health check failed"
    echo "Response: $HEALTH_RESPONSE"
    ((FAILED++))
fi
echo ""

# Test 4: Chat endpoint
echo "Test 4: Testing chat endpoint (http://localhost/api/chat)..."
CHAT_RESPONSE=$(curl -s -X POST http://localhost/api/chat \
    -H "Content-Type: application/json" \
    -d '{"user_id":"validation_test","message":"test"}')
if echo "$CHAT_RESPONSE" | grep -q "session_id"; then
    echo -e "${GREEN}✅ PASS${NC} - Chat endpoint working"
    echo "Response: $CHAT_RESPONSE" | cut -c1-100
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC} - Chat endpoint failed"
    echo "Response: $CHAT_RESPONSE"
    ((FAILED++))
fi
echo ""

# Test 5: Traefik dashboard
echo "Test 5: Testing Traefik dashboard (http://localhost:8080)..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/api/overview | grep -q "200"; then
    echo -e "${GREEN}✅ PASS${NC} - Traefik dashboard accessible"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠️  WARN${NC} - Traefik dashboard may not be accessible"
    ((FAILED++))
fi
echo ""

# Summary
echo "=============================="
echo "📊 Test Summary"
echo "=============================="
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    echo ""
    echo "🌐 Access Points:"
    echo "  - Web Client:        http://localhost"
    echo "  - API Health:        http://localhost/api/health"
    echo "  - API Endpoint:      http://localhost:8000"
    echo "  - Traefik Dashboard: http://localhost:8080"
    exit 0
else
    echo -e "${RED}❌ Some tests failed. Check the logs above.${NC}"
    echo ""
    echo "🔧 Debugging commands:"
    echo "  - Check logs:    docker-compose logs -f"
    echo "  - Restart:       docker-compose restart"
    echo "  - Rebuild:       docker-compose up -d --build"
    exit 1
fi
