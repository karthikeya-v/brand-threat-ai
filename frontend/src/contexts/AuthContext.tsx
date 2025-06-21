'use client'

import React, { createContext, useContext, useReducer, useEffect } from 'react'
import { User } from '@/types'
import { auth, apiClient } from '@/utils/api'

interface AuthState {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
}

interface AuthContextType extends AuthState {
  login: (email: string, password: string) => Promise<{ success: boolean; error?: string }>
  register: (email: string, password: string, companyName?: string) => Promise<{ success: boolean; error?: string }>
  logout: () => void
  refreshUser: () => Promise<void>
}

type AuthAction =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_USER'; payload: User | null }
  | { type: 'LOGOUT' }

const initialState: AuthState = {
  user: null,
  isLoading: true,
  isAuthenticated: false,
}

function authReducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload }
    case 'SET_USER':
      return {
        ...state,
        user: action.payload,
        isAuthenticated: !!action.payload,
        isLoading: false,
      }
    case 'LOGOUT':
      return {
        ...state,
        user: null,
        isAuthenticated: false,
        isLoading: false,
      }
    default:
      return state
  }
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(authReducer, initialState)

  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('auth_token')
      
      if (token) {
        apiClient.setToken(token)
        try {
          const response = await auth.getCurrentUser()
          if (response.data) {
            dispatch({ type: 'SET_USER', payload: response.data })
          } else {
            localStorage.removeItem('auth_token')
            dispatch({ type: 'SET_LOADING', payload: false })
          }
        } catch (error) {
          localStorage.removeItem('auth_token')
          dispatch({ type: 'SET_LOADING', payload: false })
        }
      } else {
        dispatch({ type: 'SET_LOADING', payload: false })
      }
    }

    initAuth()
  }, [])

  const login = async (email: string, password: string) => {
    dispatch({ type: 'SET_LOADING', payload: true })
    
    try {
      const response = await auth.login(email, password)
      
      if (response.data) {
        const { access_token, user } = response.data
        apiClient.setToken(access_token)
        dispatch({ type: 'SET_USER', payload: user })
        return { success: true }
      } else {
        dispatch({ type: 'SET_LOADING', payload: false })
        return { success: false, error: response.error || 'Login failed' }
      }
    } catch (error) {
      dispatch({ type: 'SET_LOADING', payload: false })
      return { success: false, error: 'Network error' }
    }
  }

  const register = async (email: string, password: string, companyName?: string) => {
    dispatch({ type: 'SET_LOADING', payload: true })
    
    try {
      const response = await auth.register(email, password, companyName)
      
      if (response.data) {
        const { access_token, user } = response.data
        apiClient.setToken(access_token)
        dispatch({ type: 'SET_USER', payload: user })
        return { success: true }
      } else {
        dispatch({ type: 'SET_LOADING', payload: false })
        return { success: false, error: response.error || 'Registration failed' }
      }
    } catch (error) {
      dispatch({ type: 'SET_LOADING', payload: false })
      return { success: false, error: 'Network error' }
    }
  }

  const logout = () => {
    auth.logout()
    dispatch({ type: 'LOGOUT' })
  }

  const refreshUser = async () => {
    try {
      const response = await auth.getCurrentUser()
      if (response.data) {
        dispatch({ type: 'SET_USER', payload: response.data })
      }
    } catch (error) {
      console.error('Failed to refresh user:', error)
    }
  }

  const value: AuthContextType = {
    ...state,
    login,
    register,
    logout,
    refreshUser,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}