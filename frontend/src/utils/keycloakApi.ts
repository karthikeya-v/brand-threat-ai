import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface KeycloakLoginData {
  username: string;
  password: string;
}

export interface KeycloakTokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface UserInfo {
  sub: string;
  email: string;
  name?: string;
  preferred_username?: string;
  given_name?: string;
  family_name?: string;
}

class KeycloakAPI {
  private apiClient;

  constructor() {
    this.apiClient = axios.create({
      baseURL: `${API_BASE_URL}/api/auth`,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  setAuthToken(token: string) {
    this.apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  }

  removeAuthToken() {
    delete this.apiClient.defaults.headers.common['Authorization'];
  }

  async login(credentials: KeycloakLoginData): Promise<KeycloakTokenResponse> {
    const response = await this.apiClient.post('/keycloak/login', credentials);
    return response.data;
  }

  async refreshToken(refreshToken: string): Promise<KeycloakTokenResponse> {
    const response = await this.apiClient.post('/keycloak/refresh', {
      refresh_token: refreshToken,
    });
    return response.data;
  }

  async logout(refreshToken: string): Promise<void> {
    await this.apiClient.post('/keycloak/logout', {
      refresh_token: refreshToken,
    });
  }

  async getUserInfo(): Promise<UserInfo> {
    const response = await this.apiClient.get('/keycloak/me');
    return response.data;
  }

  async verifyToken(): Promise<{
    valid: boolean;
    user_id: string;
    username: string;
    email: string;
    exp: number;
  }> {
    const response = await this.apiClient.get('/keycloak/verify');
    return response.data;
  }
}

export const keycloakApi = new KeycloakAPI();