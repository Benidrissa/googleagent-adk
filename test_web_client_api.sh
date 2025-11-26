#!/bin/bash
# Comprehensive Web Client API Test
# Tests all endpoints and features through the web client nginx proxy

echo "=== Testing Web Client API Integration ==="
echo ""

# Test 1: Health Check
echo "1. Health Check:"
curl -s http://localhost:3000/api/health | python3 -m json.tool
echo ""

# Test 2: New Patient Registration (French)
echo "2. New Patient Registration (French):"
SESSION=$(curl -s -X POST http://localhost:3000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"integration_test","message":"Bonjour, je mappelle Aminata, jai 28 ans, mon téléphone est +226 70 11 22 33, mes dernières règles étaient le 15 octobre 2025, je suis à Ouagadougou, Burkina Faso"}' \
  | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['session_id']); print('Response:', data['response'][:150] + '...')")
echo ""

# Test 3: Multi-turn Conversation
echo "3. Multi-turn Conversation - Ask about ANC schedule:"
curl -s -X POST http://localhost:3000/api/chat \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"integration_test\",\"session_id\":\"$SESSION\",\"message\":\"Quand est ma prochaine visite prénatale?\"}" \
  | python3 -c "import sys, json; data=json.load(sys.stdin); print('Response length:', len(data['response']), 'chars'); print('Preview:', data['response'][:200] + '...')"
echo ""

# Test 4: Emergency Detection
echo "4. Emergency Detection (bleeding):"
curl -s -X POST http://localhost:3000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"emergency_test","message":"Help! I am bleeding heavily and have severe pain"}' \
  | python3 -c "import sys, json; data=json.load(sys.stdin); print('EMERGENCY RESPONSE:'); print(data['response'][:300] + '...')"
echo ""

# Test 5: Patient Recall
echo "5. Patient Recall (returning patient):"
curl -s -X POST http://localhost:3000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"recall_test","message":"Mon numéro est +226 70 11 22 33"}' \
  | python3 -c "import sys, json; data=json.load(sys.stdin); print('Recall test:'); print(data['response'][:200] + '...')"
echo ""

echo "=== All Tests Complete ==="
