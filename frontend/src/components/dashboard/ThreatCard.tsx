'use client'

import React from 'react'
import Link from 'next/link'
import { Threat } from '@/types'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { 
  formatRelativeTime, 
  getSeverityColor, 
  getThreatTypeColor,
  getPlatformColor,
  getSentimentLabel,
  getViralPotentialLabel,
  truncateText
} from '@/utils/helpers'
import {
  ExclamationTriangleIcon,
  FireIcon,
  ChatBubbleLeftIcon,
  ArrowTopRightOnSquareIcon
} from '@heroicons/react/24/outline'

interface ThreatCardProps {
  threat: Threat
  onStatusChange?: (threatId: string, status: string) => void
}

export function ThreatCard({ threat, onStatusChange }: ThreatCardProps) {
  const severityColor = getSeverityColor(threat.severity_score)
  const threatTypeColor = getThreatTypeColor(threat.threat_type)
  const platformColor = getPlatformColor(threat.mention.platform)
  
  const handleStatusChange = (status: string) => {
    if (onStatusChange) {
      onStatusChange(threat.id, status)
    }
  }

  return (
    <Card className="hover:shadow-md transition-shadow duration-200">
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="flex items-center space-x-3">
            <div className="flex-shrink-0">
              {threat.severity_score > 0.7 ? (
                <ExclamationTriangleIcon className="h-6 w-6 text-red-500" />
              ) : threat.viral_potential > 0.7 ? (
                <FireIcon className="h-6 w-6 text-orange-500" />
              ) : (
                <ChatBubbleLeftIcon className="h-6 w-6 text-blue-500" />
              )}
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                {threat.brand_name}
              </h3>
              <p className="text-sm text-gray-500">
                {formatRelativeTime(threat.created_at)}
              </p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <Badge className={severityColor}>
              {Math.round(threat.severity_score * 100)}% Severity
            </Badge>
            {threat.ai_refined && (
              <Badge variant="secondary" size="sm">
                AI Refined
              </Badge>
            )}
          </div>
        </div>

        {/* Threat details */}
        <div className="space-y-3">
          <div className="flex items-center space-x-4">
            <Badge className={threatTypeColor}>
              {threat.threat_type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
            </Badge>
            <Badge className={platformColor}>
              {threat.mention.platform}
            </Badge>
          </div>

          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="font-medium text-gray-700">Sentiment:</span>
              <span className="ml-2 text-gray-600">
                {getSentimentLabel(threat.sentiment_score)}
              </span>
            </div>
            <div>
              <span className="font-medium text-gray-700">Viral Risk:</span>
              <span className="ml-2 text-gray-600">
                {getViralPotentialLabel(threat.viral_potential)}
              </span>
            </div>
          </div>

          {/* Mention content */}
          <div className="bg-gray-50 rounded-lg p-3">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">
                {threat.mention.author || 'Unknown Author'}
              </span>
              {threat.mention.url && (
                <a
                  href={threat.mention.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary-600 hover:text-primary-800"
                >
                  <ArrowTopRightOnSquareIcon className="h-4 w-4" />
                </a>
              )}
            </div>
            <p className="text-sm text-gray-900">
              {truncateText(threat.mention.content, 200)}
            </p>
          </div>

          {/* AI Summary */}
          {threat.summary && (
            <div className="bg-blue-50 rounded-lg p-3">
              <h4 className="text-sm font-medium text-blue-900 mb-1">AI Analysis</h4>
              <p className="text-sm text-blue-800">{threat.summary}</p>
            </div>
          )}

          {/* Suggested responses */}
          {threat.suggested_responses && threat.suggested_responses.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2">Suggested Responses</h4>
              <div className="space-y-1">
                {threat.suggested_responses.slice(0, 2).map((response, index) => (
                  <p key={index} className="text-sm text-gray-600 bg-gray-50 rounded p-2">
                    {response}
                  </p>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center justify-between pt-4 border-t border-gray-200">
          <div className="flex items-center space-x-2">
            {threat.status === 'new' && (
              <>
                <Button
                  size="sm"
                  onClick={() => handleStatusChange('reviewing')}
                >
                  Review
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => handleStatusChange('dismissed')}
                >
                  Dismiss
                </Button>
              </>
            )}
            {threat.status === 'reviewing' && (
              <>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => handleStatusChange('resolved')}
                >
                  Resolve
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => handleStatusChange('new')}
                >
                  Back to New
                </Button>
              </>
            )}
          </div>
          
          <Link
            href={`/dashboard/threats/${threat.id}`}
            className="text-primary-600 hover:text-primary-800 text-sm font-medium"
          >
            View Details →
          </Link>
        </div>
      </div>
    </Card>
  )
}