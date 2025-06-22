'use client';

import React from 'react';
import { useKeycloak } from '@/contexts/KeycloakContext';
import { Button } from '@/components/ui/Button';
import { ShieldExclamationIcon, UserCircleIcon, CheckCircleIcon } from '@heroicons/react/24/outline';

const KeycloakLogin: React.FC = () => {
  const { authenticated, loading, login, logout, userInfo } = useKeycloak();

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-4 border-blue-500 border-t-transparent mx-auto mb-4"></div>
          <p className="text-gray-600 text-lg">Initializing secure connection...</p>
        </div>
      </div>
    );
  }

  if (authenticated) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-100 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8">
          <div className="text-center mb-6">
            <div className="mx-auto w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mb-4">
              <CheckCircleIcon className="h-10 w-10 text-green-600" />
            </div>
            <h2 className="text-3xl font-bold text-gray-900 mb-2">Welcome Back!</h2>
            <p className="text-gray-600">You're successfully authenticated</p>
          </div>

          {userInfo && (
            <div className="bg-gradient-to-r from-gray-50 to-gray-100 p-6 rounded-xl mb-6 border border-gray-200">
              <div className="flex items-center mb-4">
                <UserCircleIcon className="h-8 w-8 text-gray-500 mr-3" />
                <h3 className="font-semibold text-lg text-gray-900">Profile Information</h3>
              </div>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium text-gray-500">Name:</span>
                  <span className="text-sm text-gray-900">{userInfo.name || userInfo.preferred_username || 'N/A'}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium text-gray-500">Email:</span>
                  <span className="text-sm text-gray-900">{userInfo.email || 'N/A'}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium text-gray-500">Username:</span>
                  <span className="text-sm text-gray-900">{userInfo.preferred_username || 'N/A'}</span>
                </div>
              </div>
            </div>
          )}

          <div className="space-y-4">
            <Button
              onClick={() => window.location.href = '/dashboard'}
              className="w-full bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white py-3 text-lg font-semibold"
            >
              Go to Dashboard
            </Button>
            <Button
              onClick={logout}
              variant="outline"
              className="w-full border-2 border-red-200 text-red-600 hover:bg-red-50 py-3"
            >
              Logout
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        {/* Logo and Header */}
        <div className="text-center mb-8">
          <div className="mx-auto w-20 h-20 bg-gradient-to-br from-blue-600 to-indigo-700 rounded-2xl flex items-center justify-center mb-6 shadow-lg">
            <ShieldExclamationIcon className="h-10 w-10 text-white" />
          </div>
          <h1 className="text-4xl font-bold text-gray-900 mb-2">ThreatWatch AI</h1>
          <p className="text-lg text-gray-600">Secure Login Portal</p>
        </div>

        {/* Login Card */}
        <div className="bg-white rounded-2xl shadow-xl p-8 border border-gray-100">
          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-3">Welcome Back</h2>
            <p className="text-gray-600">
              Access your threat monitoring dashboard with secure authentication
            </p>
          </div>

          {/* Features List */}
          <div className="mb-8 space-y-3">
            <div className="flex items-center text-sm text-gray-600">
              <div className="w-2 h-2 bg-green-500 rounded-full mr-3"></div>
              Real-time threat monitoring
            </div>
            <div className="flex items-center text-sm text-gray-600">
              <div className="w-2 h-2 bg-blue-500 rounded-full mr-3"></div>
              AI-powered analysis
            </div>
            <div className="flex items-center text-sm text-gray-600">
              <div className="w-2 h-2 bg-purple-500 rounded-full mr-3"></div>
              Secure cloud infrastructure
            </div>
          </div>

          {/* Login Button */}
          <Button
            onClick={login}
            className="w-full bg-gradient-to-r from-blue-600 to-indigo-700 hover:from-blue-700 hover:to-indigo-800 text-white py-4 text-lg font-semibold rounded-xl shadow-lg hover:shadow-xl transition-all duration-200 transform hover:scale-105"
          >
            <div className="flex items-center justify-center">
              <ShieldExclamationIcon className="h-5 w-5 mr-2" />
              Secure Login with Keycloak
            </div>
          </Button>

          {/* Test Credentials Info */}
          <div className="mt-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
            <h4 className="text-sm font-semibold text-gray-700 mb-2">Test Credentials:</h4>
            <div className="text-xs text-gray-600 space-y-1">
              <div>Username: <span className="font-mono bg-gray-200 px-1 rounded">testuser</span></div>
              <div>Password: <span className="font-mono bg-gray-200 px-1 rounded">testpassword</span></div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="text-center mt-8 text-sm text-gray-500">
          <p>Protected by enterprise-grade security</p>
        </div>
      </div>
    </div>
  );
};

export default KeycloakLogin;