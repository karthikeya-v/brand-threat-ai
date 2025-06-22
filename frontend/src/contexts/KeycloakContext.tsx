'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import Keycloak from 'keycloak-js';

interface KeycloakContextType {
  keycloak: Keycloak | null;
  authenticated: boolean;
  loading: boolean;
  login: () => void;
  logout: () => void;
  token: string | null;
  userInfo: any;
}

const KeycloakContext = createContext<KeycloakContextType | undefined>(undefined);

export const useKeycloak = () => {
  const context = useContext(KeycloakContext);
  if (!context) {
    throw new Error('useKeycloak must be used within a KeycloakProvider');
  }
  return context;
};

interface KeycloakProviderProps {
  children: React.ReactNode;
}

export const KeycloakProvider: React.FC<KeycloakProviderProps> = ({ children }) => {
  const [keycloak, setKeycloak] = useState<Keycloak | null>(null);
  const [authenticated, setAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState<string | null>(null);
  const [userInfo, setUserInfo] = useState<any>(null);

  useEffect(() => {
    const initKeycloak = async () => {
      try {
        const keycloakConfig = {
          url: process.env.NEXT_PUBLIC_KEYCLOAK_URL || 'http://localhost:8080',
          realm: process.env.NEXT_PUBLIC_KEYCLOAK_REALM || 'threatwatch',
          clientId: process.env.NEXT_PUBLIC_KEYCLOAK_CLIENT_ID || 'threatwatch-frontend',
        };

        console.log('Initializing Keycloak with config:', keycloakConfig);

        const keycloakInstance = new Keycloak(keycloakConfig);
        
        const authenticated = await keycloakInstance.init({
          onLoad: 'check-sso',
          silentCheckSsoRedirectUri: window.location.origin + '/silent-check-sso.html',
          pkceMethod: 'S256',
          checkLoginIframe: false,
          flow: 'standard'
        });

        console.log('Keycloak initialization result:', { authenticated });

        setKeycloak(keycloakInstance);
        setAuthenticated(authenticated);
        
        if (authenticated) {
          setToken(keycloakInstance.token || null);
          
          // Load user info
          try {
            const userInfo = await keycloakInstance.loadUserInfo();
            setUserInfo(userInfo);
          } catch (error) {
            console.error('Failed to load user info:', error);
          }

          // Setup token refresh
          keycloakInstance.onTokenExpired = () => {
            keycloakInstance.updateToken(30).then((refreshed) => {
              if (refreshed) {
                setToken(keycloakInstance.token || null);
              }
            }).catch((error) => {
              console.error('Failed to refresh token:', error);
              keycloakInstance.logout();
            });
          };
        }
      } catch (error) {
        console.error('Keycloak initialization failed:', error);
        console.error('Error details:', error);
      } finally {
        console.log('Setting loading to false');
        setLoading(false);
      }
    };

    initKeycloak();
  }, []);

  const login = () => {
    if (keycloak) {
      keycloak.login();
    }
  };

  const logout = () => {
    if (keycloak) {
      keycloak.logout();
    }
  };

  const value: KeycloakContextType = {
    keycloak,
    authenticated,
    loading,
    login,
    logout,
    token,
    userInfo,
  };

  return (
    <KeycloakContext.Provider value={value}>
      {children}
    </KeycloakContext.Provider>
  );
};