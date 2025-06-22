'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { useApiAuth } from '@/utils/keycloakApi'
import { mentions } from '@/utils/api'
import { Mention } from '@/types'
import { 
  ChatBubbleLeftRightIcon, 
  MagnifyingGlassIcon,
  FunnelIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline'

export default function MentionsPage() {
  const { authenticated } = useApiAuth()
  const [allMentions, setAllMentions] = useState<Mention[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [filter, setFilter] = useState<string>('all')
  const [searchTerm, setSearchTerm] = useState<string>('')

  useEffect(() => {
    const fetchMentions = async () => {
      if (!authenticated) {
        setIsLoading(false)
        return
      }

      try {
        const response = await mentions.getAll()
        if (response.data && Array.isArray(response.data)) {
          setAllMentions(response.data as Mention[])
        }
      } catch (error) {
        console.error('Failed to fetch mentions:', error)
      } finally {
        setIsLoading(false)
      }
    }

    fetchMentions()
  }, [authenticated])

  const handleRefresh = async () => {
    setIsLoading(true)
    try {
      const response = await mentions.getAll()
      if (response.data && Array.isArray(response.data)) {
        setAllMentions(response.data as Mention[])
      }
    } catch (error) {
      console.error('Failed to refresh mentions:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const filteredMentions = allMentions.filter(mention => {
    // Platform filter
    if (filter !== 'all' && mention.platform !== filter) return false
    
    // Search filter
    if (searchTerm && !mention.content.toLowerCase().includes(searchTerm.toLowerCase())) {
      return false
    }
    
    return true
  })

  const getSentimentColor = () => {
    return 'text-gray-600 bg-gray-50'
  }

  const getSentimentLabel = () => {
    return 'Unknown'
  }

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
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Mentions</h1>
          <p className="text-gray-600">Monitor all mentions of your brands across platforms</p>
        </div>
        
        <button 
          onClick={handleRefresh}
          className="bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-md flex items-center space-x-2"
        >
          <ArrowPathIcon className="h-4 w-4" />
          <span>Refresh</span>
        </button>
      </div>

      {/* Search and filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1 relative">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search mentions..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          />
        </div>
        
        <div className="flex items-center space-x-2">
          <FunnelIcon className="h-4 w-4 text-gray-500" />
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="rounded-md border border-gray-300 bg-white px-3 py-2 text-sm"
          >
            <option value="all">All Platforms</option>
            <option value="twitter">Twitter</option>
            <option value="reddit">Reddit</option>
            <option value="facebook">Facebook</option>
            <option value="instagram">Instagram</option>
            <option value="youtube">YouTube</option>
            <option value="news">News</option>
          </select>
        </div>
      </div>

      {/* Mentions list */}
      <div className="space-y-4">
        {filteredMentions.length > 0 ? (
          filteredMentions.map((mention) => (
            <Card key={mention.id} className="hover:shadow-md transition-shadow">
              <CardContent className="p-6">
                <div className="flex justify-between items-start mb-3">
                  <div className="flex items-center space-x-3">
                    <Badge variant="gray" size="sm">
                      {mention.platform}
                    </Badge>
                    <Badge 
                      variant="gray" 
                      size="sm"
                      className={getSentimentColor()}
                    >
                      {getSentimentLabel()}
                    </Badge>
                  </div>
                  <div className="text-sm text-gray-500">
                    {new Date(mention.collected_at).toLocaleDateString()}
                  </div>
                </div>

                <div className="mb-4">
                  <p className="text-gray-900 mb-2">{mention.content}</p>
                  {mention.author && (
                    <p className="text-sm text-gray-600">
                      by <span className="font-medium">{mention.author}</span>
                      {mention.author_followers && (
                        <span className="ml-2">
                          ({mention.author_followers.toLocaleString()} followers)
                        </span>
                      )}
                    </p>
                  )}
                </div>

                <div className="flex justify-between items-center">
                  <div className="flex items-center space-x-4 text-sm text-gray-500">
                    {mention.engagement_count && (
                      <span>{mention.engagement_count} engagements</span>
                    )}
                    <span>Platform: {mention.platform}</span>
                  </div>
                  
                  <div className="flex space-x-2">
                    {mention.url && (
                      <a
                        href={mention.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary-600 hover:text-primary-700 text-sm font-medium"
                      >
                        View Original
                      </a>
                    )}
                    <Badge variant={mention.processed ? 'success' : 'gray'} size="sm">
                      {mention.processed ? 'Processed' : 'Pending'}
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        ) : (
          <Card>
            <CardContent className="text-center py-12">
              <ChatBubbleLeftRightIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No mentions found</h3>
              <p className="text-gray-500 mb-6">
                {searchTerm || filter !== 'all' 
                  ? 'Try adjusting your search or filters'
                  : 'No mentions detected for your brands yet'
                }
              </p>
              {!searchTerm && filter === 'all' && (
                <button 
                  onClick={handleRefresh}
                  className="bg-primary-600 hover:bg-primary-700 text-white px-6 py-3 rounded-md flex items-center space-x-2 mx-auto"
                >
                  <ArrowPathIcon className="h-5 w-5" />
                  <span>Collect Mentions</span>
                </button>
              )}
            </CardContent>
          </Card>
        )}
      </div>

      {/* Platform stats */}
      <Card>
        <CardHeader>
          <CardTitle>Platform Overview</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
            {['twitter', 'reddit', 'facebook', 'instagram', 'youtube', 'news'].map((platform) => {
              const count = allMentions.filter(m => m.platform === platform).length
              return (
                <div key={platform} className="text-center p-3 bg-gray-50 rounded-lg">
                  <p className="text-2xl font-bold text-gray-900">{count}</p>
                  <p className="text-sm text-gray-600 capitalize">{platform}</p>
                </div>
              )
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}