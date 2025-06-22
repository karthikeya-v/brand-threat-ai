'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { ThreatCard } from '@/components/dashboard/ThreatCard'
import { useApiAuth } from '@/utils/keycloakApi'
import { threats } from '@/utils/api'
import { Threat } from '@/types'
import { ShieldExclamationIcon } from '@heroicons/react/24/outline'

export default function ThreatsPage() {
  const { authenticated } = useApiAuth()
  const [allThreats, setAllThreats] = useState<Threat[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [filter, setFilter] = useState<string>('all')

  useEffect(() => {
    const fetchThreats = async () => {
      if (!authenticated) {
        setIsLoading(false)
        return
      }

      try {
        const response = await threats.getAll()
        if (response.data && Array.isArray(response.data)) {
          setAllThreats(response.data as Threat[])
        }
      } catch (error) {
        console.error('Failed to fetch threats:', error)
      } finally {
        setIsLoading(false)
      }
    }

    fetchThreats()
  }, [authenticated])

  const handleThreatStatusChange = async (threatId: string, status: string) => {
    try {
      await threats.updateStatus(threatId, status)
      // Refresh threats
      const response = await threats.getAll()
      if (response.data && Array.isArray(response.data)) {
        setAllThreats(response.data as Threat[])
      }
    } catch (error) {
      console.error('Failed to update threat status:', error)
    }
  }

  const filteredThreats = allThreats.filter(threat => {
    if (filter === 'all') return true
    if (filter === 'new') return threat.status === 'new'
    if (filter === 'investigating') return threat.status === 'investigating'
    if (filter === 'resolved') return threat.status === 'resolved'
    if (filter === 'high-severity') return threat.severity_score > 0.7
    return true
  })

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-6"></div>
          <div className="space-y-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-32 bg-gray-200 rounded-lg"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Threats</h1>
        <p className="text-gray-600">Monitor and manage security threats to your brands</p>
      </div>

      {/* Filter tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { key: 'all', label: 'All Threats', count: allThreats.length },
            { key: 'new', label: 'New', count: allThreats.filter(t => t.status === 'new').length },
            { key: 'investigating', label: 'Investigating', count: allThreats.filter(t => t.status === 'investigating').length },
            { key: 'high-severity', label: 'High Severity', count: allThreats.filter(t => t.severity_score > 0.7).length },
            { key: 'resolved', label: 'Resolved', count: allThreats.filter(t => t.status === 'resolved').length },
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => setFilter(tab.key)}
              className={`${
                filter === tab.key
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              } whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm flex items-center space-x-2`}
            >
              <span>{tab.label}</span>
              <Badge variant={filter === tab.key ? 'primary' : 'gray'} size="sm">
                {tab.count}
              </Badge>
            </button>
          ))}
        </nav>
      </div>

      {/* Threats list */}
      <div className="space-y-4">
        {filteredThreats.length > 0 ? (
          filteredThreats.map((threat) => (
            <ThreatCard
              key={threat.id}
              threat={threat}
              onStatusChange={handleThreatStatusChange}
              expanded={true}
            />
          ))
        ) : (
          <Card>
            <CardContent className="text-center py-12">
              <ShieldExclamationIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500 text-lg">No threats found</p>
              <p className="text-sm text-gray-400">
                {filter === 'all' 
                  ? 'No threats detected for your brands yet'
                  : `No ${filter.replace('-', ' ')} threats found`
                }
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}