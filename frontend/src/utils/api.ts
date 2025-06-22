const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  status: number;
}

class ApiClient {
  private baseURL: string;
  private token: string | null = null;
  private getToken: (() => string | null) | null = null;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
    
    // Load token from localStorage on client side (fallback)
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('auth_token');
    }
  }

  setTokenProvider(getToken: () => string | null) {
    this.getToken = getToken;
  }

  setToken(token: string) {
    this.token = token;
    if (typeof window !== 'undefined') {
      localStorage.setItem('auth_token', token);
    }
  }

  clearToken() {
    this.token = null;
    this.getToken = null;
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token');
    }
  }

  private getCurrentToken(): string | null {
    // First try the token provider (Keycloak)
    if (this.getToken) {
      return this.getToken();
    }
    // Fallback to stored token
    return this.token;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseURL}${endpoint}`;
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...((options.headers as Record<string, string>) || {}),
    };

    const currentToken = this.getCurrentToken();
    if (currentToken) {
      headers.Authorization = `Bearer ${currentToken}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      const status = response.status;
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        return {
          error: errorData.detail || `HTTP ${status}`,
          status,
        };
      }

      const data = await response.json();
      return { data, status };
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : 'Network error',
        status: 0,
      };
    }
  }

  async get<T>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  async post<T>(endpoint: string, data?: any): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async put<T>(endpoint: string, data?: any): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async delete<T>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }

  // Form data for file uploads or form submissions
  async postForm<T>(endpoint: string, formData: FormData): Promise<ApiResponse<T>> {
    const url = `${this.baseURL}${endpoint}`;
    
    const headers: Record<string, string> = {};
    const currentToken = this.getCurrentToken();
    if (currentToken) {
      headers.Authorization = `Bearer ${currentToken}`;
    }

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers,
        body: formData,
      });

      const status = response.status;
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        return {
          error: errorData.detail || `HTTP ${status}`,
          status,
        };
      }

      const data = await response.json();
      return { data, status };
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : 'Network error',
        status: 0,
      };
    }
  }
}

export const apiClient = new ApiClient(API_BASE_URL);

// Authentication helpers
export const auth = {
  async login(email: string, password: string) {
    const formData = new FormData();
    formData.append('username', email);
    formData.append('password', password);
    
    return apiClient.postForm<any>('/api/auth/login', formData);
  },

  async register(email: string, password: string, companyName?: string) {
    return apiClient.post('/api/auth/register', {
      email,
      password,
      company_name: companyName,
    });
  },

  async getCurrentUser() {
    return apiClient.get('/api/auth/me');
  },

  async refreshToken() {
    return apiClient.post('/api/auth/refresh');
  },

  logout() {
    apiClient.clearToken();
  },
};

// Brand API helpers
export const brands = {
  async getAll() {
    return apiClient.get('/api/brands');
  },

  async getById(id: string) {
    return apiClient.get(`/api/brands/${id}`);
  },

  async create(brandData: any) {
    return apiClient.post('/api/brands', brandData);
  },

  async update(id: string, brandData: any) {
    return apiClient.put(`/api/brands/${id}`, brandData);
  },

  async delete(id: string) {
    return apiClient.delete(`/api/brands/${id}`);
  },

  async test(id: string) {
    return apiClient.post(`/api/brands/${id}/test`);
  },
};

// Threat API helpers
export const threats = {
  async getAll(params?: {
    brand_id?: string;
    status?: string;
    severity_min?: number;
    days?: number;
    limit?: number;
  }) {
    const queryParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          queryParams.append(key, value.toString());
        }
      });
    }
    
    const endpoint = `/api/threats${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return apiClient.get(endpoint);
  },

  async getById(id: string) {
    return apiClient.get(`/api/threats/${id}`);
  },

  async getStats(params?: { brand_id?: string; days?: number }) {
    const queryParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          queryParams.append(key, value.toString());
        }
      });
    }
    
    const endpoint = `/api/threats/stats${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return apiClient.get(endpoint);
  },

  async updateStatus(id: string, status: string, assigned_to?: string) {
    return apiClient.put(`/api/threats/${id}/status`, {
      status,
      assigned_to,
    });
  },

  async submitResponse(id: string, action: string, message: string) {
    return apiClient.post(`/api/threats/${id}/response`, {
      action,
      message,
    });
  },

  async assign(id: string, userId?: string) {
    return apiClient.put(`/api/threats/${id}/assign`, {
      user_id: userId,
    });
  },
};

// Mentions API helpers
export const mentions = {
  async getAll(params?: {
    brand_id?: string;
    platform?: string;
    days?: number;
    limit?: number;
    processed?: boolean;
  }) {
    const queryParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          queryParams.append(key, value.toString());
        }
      });
    }
    
    const endpoint = `/api/mentions${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return apiClient.get(endpoint);
  },

  async getById(id: string) {
    return apiClient.get(`/api/mentions/${id}`);
  },

  async triggerCollection(brandId?: string) {
    return apiClient.post('/api/mentions/collect', brandId ? { brand_id: brandId } : {});
  },

  async getPlatformStatus() {
    return apiClient.get('/api/mentions/platforms/status');
  },
};

// Analytics API helpers
export const analytics = {
  async getOverview(params?: { brand_id?: string; days?: number }) {
    const queryParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          queryParams.append(key, value.toString());
        }
      });
    }
    
    const endpoint = `/api/analytics/overview${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return apiClient.get(endpoint);
  },

  async getSentimentTrends(params?: { brand_id?: string; days?: number }) {
    const queryParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          queryParams.append(key, value.toString());
        }
      });
    }
    
    const endpoint = `/api/analytics/sentiment-trends${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return apiClient.get(endpoint);
  },

  async getThreatBreakdown(params?: { brand_id?: string; days?: number }) {
    const queryParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          queryParams.append(key, value.toString());
        }
      });
    }
    
    const endpoint = `/api/analytics/threat-breakdown${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return apiClient.get(endpoint);
  },

  async getPlatformPerformance(params?: { brand_id?: string; days?: number }) {
    const queryParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          queryParams.append(key, value.toString());
        }
      });
    }
    
    const endpoint = `/api/analytics/platform-performance${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return apiClient.get(endpoint);
  },
};