'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { ThreatCard } from '@/components/dashboard/ThreatCard'
import ProtectedRoute from '@/components/auth/ProtectedRoute'
import { threats, analytics, brands } from '@/utils/api'
import { Threat, OverviewStats, Brand } from '@/types'
import {
  ShieldExclamationIcon,
  ChatBubbleLeftRightIcon,
  ExclamationTriangleIcon,
  TagIcon
} from '@heroicons/react/24/outline'

export default function DashboardPage() {
  const [overviewStats, setOverviewStats] = useState<OverviewStats | null>(null)
  const [recentThreats, setRecentThreats] = useState<Threat[]>([])
  const [userBrands, setUserBrands] = useState<Brand[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const [statsResponse, threatsResponse, brandsResponse] = await Promise.all([
          analytics.getOverview({ days: 7 }),
          threats.getAll({ limit: 6 }),
          brands.getAll()
        ])

        if (statsResponse.data && Object.keys(statsResponse.data).length > 0) {
          setOverviewStats(statsResponse.data as OverviewStats)
        }

        if (threatsResponse.data && Array.isArray(threatsResponse.data)) {
          setRecentThreats(threatsResponse.data as Threat[])
        }

        if (brandsResponse.data && Array.isArray(brandsResponse.data)) {
          setUserBrands(brandsResponse.data as Brand[])
        }
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error)
      } finally {
        setIsLoading(false)
      }
    }

    fetchDashboardData()
  }, [])

  const handleThreatStatusChange = async (threatId: string, status: string) => {
    try {
      await threats.updateStatus(threatId, status)
      // Refresh threats
      const response = await threats.getAll({ limit: 6 })
      if (response.data && Array.isArray(response.data)) {
        setRecentThreats(response.data as Threat[])
      }
    } catch (error) {
      console.error('Failed to update threat status:', error)
    }
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-6"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-32 bg-gray-200 rounded-lg"></div>
            ))}
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="h-96 bg-gray-200 rounded-lg"></div>
            <div className="h-96 bg-gray-200 rounded-lg"></div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <ProtectedRoute>
      <div className="space-y-6">
        {/* Page header */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600">Monitor your brand threats in real-time</p>
        </div>

      {/* Stats overview */}
      {overviewStats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card>
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <TagIcon className="h-6 w-6 text-primary-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Brands</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {overviewStats.total_brands}
                </p>
              </div>
            </div>
          </Card>

          <Card>
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <ChatBubbleLeftRightIcon className="h-6 w-6 text-blue-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Mentions</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {overviewStats.total_mentions}
                </p>
              </div>
            </div>
          </Card>

          <Card>
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <ShieldExclamationIcon className="h-6 w-6 text-orange-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Total Threats</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {overviewStats.total_threats}
                </p>
              </div>
            </div>
          </Card>

          <Card>
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <ExclamationTriangleIcon className="h-6 w-6 text-red-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">High Severity</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {overviewStats.high_severity_threats}
                </p>
              </div>
            </div>
          </Card>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent threats */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Threats</CardTitle>
          </CardHeader>
          <CardContent>
            {recentThreats.length > 0 ? (
              <div className="space-y-4">
                {recentThreats.slice(0, 3).map((threat) => (
                  <ThreatCard
                    key={threat.id}
                    threat={threat}
                    onStatusChange={handleThreatStatusChange}
                  />
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <ShieldExclamationIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500">No threats detected recently</p>
                <p className="text-sm text-gray-400">This is good news for your brand!</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Brand overview */}
        <Card>
          <CardHeader>
            <CardTitle>Your Brands</CardTitle>
          </CardHeader>
          <CardContent>
            {userBrands.length > 0 ? (
              <div className="space-y-4">
                {userBrands.map((brand) => (
                  <div
                    key={brand.id}
                    className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
                  >
                    <div>
                      <h4 className="font-medium text-gray-900">{brand.name}</h4>
                      <p className="text-sm text-gray-500">
                        {brand.keywords.length} keywords • {brand.industry || 'No industry set'}
                      </p>
                      {brand.stats && (
                        <div className="flex items-center space-x-4 mt-2">
                          <span className="text-sm text-gray-600">
                            {brand.stats.total_mentions} mentions
                          </span>
                          {brand.stats.new_threats > 0 && (
                            <Badge variant="warning" size="sm">
                              {brand.stats.new_threats} new threats
                            </Badge>
                          )}
                        </div>
                      )}
                    </div>
                    <div className="flex items-center space-x-2">
                      <Badge variant={brand.is_active ? 'success' : 'gray'} size="sm">
                        {brand.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <TagIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500">No brands configured</p>
                <p className="text-sm text-gray-400">Add your first brand to start monitoring</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
    </ProtectedRoute>
  )
}