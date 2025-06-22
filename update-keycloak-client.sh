#!/bin/bash

echo "Updating Keycloak client configuration..."

# Get admin token
ADMIN_TOKEN=$(curl -s -X POST http://localhost:8080/realms/master/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin" \
  -d "password=admin123" \
  -d "grant_type=password" \
  -d "client_id=admin-cli" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$ADMIN_TOKEN" ]; then
    echo "Failed to get admin token"
    exit 1
fi

# Get frontend client ID
CLIENT_ID=$(curl -s -X GET "http://localhost:8080/admin/realms/threatwatch/clients?clientId=threatwatch-frontend" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | grep -o '"id":"[^"]*' | cut -d'"' -f4)

if [ -z "$CLIENT_ID" ]; then
    echo "Frontend client not found"
    exit 1
fi

echo "Updating frontend client configuration..."

# Update frontend client with correct CORS settings
curl -s -X PUT "http://localhost:8080/admin/realms/threatwatch/clients/$CLIENT_ID" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "'$CLIENT_ID'",
    "clientId": "threatwatch-frontend",
    "enabled": true,
    "publicClient": true,
    "redirectUris": [
      "http://localhost:3000/*",
      "http://localhost:3000/auth/keycloak/*",
      "http://localhost:3000/dashboard/*"
    ],
    "webOrigins": [
      "http://localhost:3000",
      "+"
    ],
    "standardFlowEnabled": true,
    "implicitFlowEnabled": false,
    "directAccessGrantsEnabled": true,
    "attributes": {
      "pkce.code.challenge.method": "S256"
    }
  }'

echo "Frontend client updated successfully!"
echo ""
echo "You can test the login at: http://localhost:3000/auth/keycloak"
echo "Test credentials:"
echo "Username: testuser"
echo "Password: testpassword"