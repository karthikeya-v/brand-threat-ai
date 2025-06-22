'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useKeycloak } from '@/contexts/KeycloakContext'

export default function HomePage() {
  const router = useRouter()
  const { authenticated, loading } = useKeycloak()

  useEffect(() => {
    if (!loading) {
      if (authenticated) {
        router.push('/dashboard')
      } else {
        router.push('/auth/keycloak')
      }
    }
  }, [authenticated, loading, router])

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
        <p className="mt-4 text-gray-600">Loading ThreatWatch AI...</p>
      </div>
    </div>
  )
}