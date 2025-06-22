'use client'

import React from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { useKeycloak } from '@/contexts/KeycloakContext'
import { ShieldExclamationIcon } from '@heroicons/react/24/outline'

export default function LoginPage() {
  const router = useRouter()
  const { login, authenticated, loading } = useKeycloak()

  // Redirect if already authenticated
  React.useEffect(() => {
    if (!loading && authenticated) {
      router.push('/dashboard')
    }
  }, [authenticated, loading, router])

  const handleLogin = () => {
    login()
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <div className="flex justify-center">
            <ShieldExclamationIcon className="h-12 w-12 text-primary-600" />
          </div>
          <h2 className="mt-6 text-3xl font-extrabold text-gray-900">
            Sign in to ThreatWatch AI
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            Monitor your brand threats in real-time
          </p>
        </div>

        <Card>
          <div className="space-y-6 text-center">
            <p className="text-gray-600">
              Click the button below to sign in with Keycloak
            </p>

            <Button
              onClick={handleLogin}
              className="w-full"
            >
              Sign in with Keycloak
            </Button>
          </div>
        </Card>
      </div>
    </div>
  )
}