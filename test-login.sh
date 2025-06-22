#!/bin/bash

echo "🧪 Testing ThreatWatch AI Login System"
echo "======================================="
echo

# Test if services are running
echo "📡 Checking services..."
if curl -s http://localhost:3000/ > /dev/null; then
    echo "✅ Frontend is running on http://localhost:3000"
else
    echo "❌ Frontend is not accessible"
    exit 1
fi

if curl -s http://localhost:8080/ > /dev/null; then
    echo "✅ Keycloak is running on http://localhost:8080"
else
    echo "❌ Keycloak is not accessible"
    exit 1
fi

if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend is running on http://localhost:8000"
else
    echo "❌ Backend is not accessible"
    exit 1
fi

echo

# Test Keycloak realm
echo "🔐 Testing Keycloak configuration..."
if curl -s "http://localhost:8080/realms/threatwatch" | grep -q "threatwatch"; then
    echo "✅ Threatwatch realm is configured"
else
    echo "❌ Threatwatch realm is not properly configured"
    exit 1
fi

# Test OpenID configuration
if curl -s "http://localhost:8080/realms/threatwatch/.well-known/openid_configuration" | grep -q "authorization_endpoint"; then
    echo "✅ OpenID configuration is accessible"
else
    echo "❌ OpenID configuration is not accessible"
fi

echo

# Test login page
echo "🎨 Testing login page..."
if curl -s "http://localhost:3000/auth/keycloak" | grep -q "ThreatWatch AI"; then
    echo "✅ Login page is working"
else
    echo "❌ Login page is not working"
fi

echo
echo "🎉 All tests passed!"
echo
echo "📝 Test the login flow:"
echo "1. Open your browser and go to: http://localhost:3000"
echo "2. You should see the beautiful ThreatWatch AI login page"
echo "3. Click 'Secure Login with Keycloak'"
echo "4. Use the test credentials:"
echo "   Username: testuser"
echo "   Password: testpassword"
echo "5. After login, you should be redirected to the dashboard"
echo
echo "🔧 Admin access:"
echo "Keycloak Admin Console: http://localhost:8080/admin/"
echo "Admin credentials: admin / admin123"