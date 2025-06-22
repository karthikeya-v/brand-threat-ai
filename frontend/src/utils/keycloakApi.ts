'use client';

import { useEffect } from 'react';
import { useKeycloak } from '@/contexts/KeycloakContext';
import { apiClient } from './api';

// Hook to integrate Keycloak token with API client
export const useApiAuth = () => {
  const { token, authenticated } = useKeycloak();

  useEffect(() => {
    if (authenticated && token) {
      // Set up the token provider for the API client
      apiClient.setTokenProvider(() => token);
    } else {
      // Clear token when not authenticated
      apiClient.clearToken();
    }
  }, [token, authenticated]);

  return { authenticated, token };
};