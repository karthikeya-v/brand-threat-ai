'use client';

import React from 'react';
import { useKeycloak } from '@/contexts/KeycloakContext';
import { Button } from '@/components/ui/Button';

const KeycloakLogin: React.FC = () => {
  const { authenticated, loading, login, logout, userInfo } = useKeycloak();

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (authenticated) {
    return (
      <div className="max-w-md mx-auto mt-8 p-6 bg-white rounded-lg shadow-md">
        <h2 className="text-2xl font-bold mb-4 text-center">Welcome!</h2>
        <div className="space-y-4">
          {userInfo && (
            <div className="bg-gray-50 p-4 rounded-md">
              <h3 className="font-semibold mb-2">User Information:</h3>
              <p><strong>Name:</strong> {userInfo.name || 'N/A'}</p>
              <p><strong>Email:</strong> {userInfo.email || 'N/A'}</p>
              <p><strong>Username:</strong> {userInfo.preferred_username || 'N/A'}</p>
            </div>
          )}
          <Button
            onClick={logout}
            className="w-full bg-red-600 hover:bg-red-700 text-white"
          >
            Logout
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-md mx-auto mt-8 p-6 bg-white rounded-lg shadow-md">
      <h2 className="text-2xl font-bold mb-6 text-center">Login to ThreatWatch AI</h2>
      <div className="space-y-4">
        <p className="text-gray-600 text-center">
          Please log in to access your threat monitoring dashboard.
        </p>
        <Button
          onClick={login}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white"
        >
          Login with Keycloak
        </Button>
      </div>
    </div>
  );
};

export default KeycloakLogin;