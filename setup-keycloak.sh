#!/bin/bash

echo "Setting up Keycloak realm and client..."

# Wait for Keycloak to be ready
echo "Waiting for Keycloak to be ready..."
until curl -sf http://localhost:8080/health/ready; do
    echo "Waiting for Keycloak..."
    sleep 5
done

echo "Keycloak is ready. Setting up realm..."

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

echo "Got admin token. Creating realm..."

# Create threatwatch realm
curl -s -X POST http://localhost:8080/admin/realms \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "realm": "threatwatch",
    "enabled": true,
    "displayName": "ThreatWatch AI",
    "loginWithEmailAllowed": true,
    "registrationAllowed": true,
    "resetPasswordAllowed": true
  }'

echo "Creating frontend client..."

# Create frontend client
curl -s -X POST http://localhost:8080/admin/realms/threatwatch/clients \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "clientId": "threatwatch-frontend",
    "enabled": true,
    "publicClient": true,
    "redirectUris": ["http://localhost:3000/*"],
    "webOrigins": ["http://localhost:3000"],
    "standardFlowEnabled": true,
    "implicitFlowEnabled": false,
    "directAccessGrantsEnabled": true
  }'

echo "Creating backend client..."

# Create backend client
curl -s -X POST http://localhost:8080/admin/realms/threatwatch/clients \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "clientId": "threatwatch-backend",
    "enabled": true,
    "publicClient": false,
    "serviceAccountsEnabled": true,
    "standardFlowEnabled": true,
    "directAccessGrantsEnabled": true,
    "secret": "your-client-secret"
  }'

echo "Creating test user..."

# Create a test user
curl -s -X POST http://localhost:8080/admin/realms/threatwatch/users \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@threatwatch.ai",
    "firstName": "Test",
    "lastName": "User",
    "enabled": true,
    "emailVerified": true
  }'

# Get user ID
USER_ID=$(curl -s -X GET "http://localhost:8080/admin/realms/threatwatch/users?username=testuser" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | grep -o '"id":"[^"]*' | cut -d'"' -f4)

if [ ! -z "$USER_ID" ]; then
    echo "Setting password for test user..."
    # Set password for test user
    curl -s -X PUT "http://localhost:8080/admin/realms/threatwatch/users/$USER_ID/reset-password" \
      -H "Authorization: Bearer $ADMIN_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "type": "password",
        "value": "testpassword",
        "temporary": false
      }'
fi

echo "Keycloak setup complete!"
echo "You can now login with:"
echo "Username: testuser"
echo "Password: testpassword"
echo ""
echo "Keycloak Admin Console: http://localhost:8080/admin/"
echo "Admin credentials: admin / admin123"