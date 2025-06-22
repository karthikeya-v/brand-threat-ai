'use client'

import React from 'react'
import { useRouter } from 'next/navigation'

export default function LoginPage() {
  const router = useRouter()

  // Redirect to the dedicated Keycloak login page
  React.useEffect(() => {
    router.push('/auth/keycloak')
  }, [router])

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-16 w-16 border-4 border-blue-500 border-t-transparent mx-auto mb-4"></div>
        <p className="text-gray-600 text-lg">Redirecting to secure login...</p>
      </div>
    </div>
  )
}