'use client';

import KeycloakLogin from '@/components/auth/KeycloakLogin';

export default function KeycloakAuthPage() {
  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="container mx-auto px-4">
        <KeycloakLogin />
      </div>
    </div>
  );
}