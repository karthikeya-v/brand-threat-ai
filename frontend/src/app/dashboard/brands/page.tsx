'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { useApiAuth } from '@/utils/keycloakApi'
import { brands } from '@/utils/api'
import { Brand } from '@/types'
import { TagIcon, PlusIcon, CogIcon } from '@heroicons/react/24/outline'

export default function BrandsPage() {
  const { authenticated } = useApiAuth()
  const [userBrands, setUserBrands] = useState<Brand[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const fetchBrands = async () => {
      if (!authenticated) {
        setIsLoading(false)
        return
      }

      try {
        const response = await brands.getAll()
        if (response.data && Array.isArray(response.data)) {
          setUserBrands(response.data as Brand[])
        }
      } catch (error) {
        console.error('Failed to fetch brands:', error)
      } finally {
        setIsLoading(false)
      }
    }

    fetchBrands()
  }, [authenticated])

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-6"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-48 bg-gray-200 rounded-lg"></div>
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
          <h1 className="text-2xl font-bold text-gray-900">Brands</h1>
          <p className="text-gray-600">Manage the brands you're monitoring for threats</p>
        </div>
        
        <button className="bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-md flex items-center space-x-2">
          <PlusIcon className="h-4 w-4" />
          <span>Add Brand</span>
        </button>
      </div>

      {/* Brands grid */}
      {userBrands.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {userBrands.map((brand) => (
            <Card key={brand.id} className="hover:shadow-lg transition-shadow">
              <CardContent className="p-6">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">{brand.name}</h3>
                    <p className="text-sm text-gray-500">
                      {brand.industry || 'No industry set'}
                    </p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Badge variant={brand.is_active ? 'success' : 'gray'} size="sm">
                      {brand.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                    <button className="text-gray-400 hover:text-gray-600">
                      <CogIcon className="h-4 w-4" />
                    </button>
                  </div>
                </div>

                <div className="space-y-3">
                  <div>
                    <p className="text-sm font-medium text-gray-700">Keywords</p>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {brand.keywords && brand.keywords.length > 0 ? (
                        brand.keywords.slice(0, 3).map((keyword, idx) => (
                          <span
                            key={idx}
                            className="inline-flex items-center px-2 py-1 rounded text-xs bg-gray-100 text-gray-800"
                          >
                            {keyword}
                          </span>
                        ))
                      ) : (
                        <span className="text-xs text-gray-500">No keywords set</span>
                      )}
                      {brand.keywords && brand.keywords.length > 3 && (
                        <span className="inline-flex items-center px-2 py-1 rounded text-xs bg-gray-100 text-gray-800">
                          +{brand.keywords.length - 3} more
                        </span>
                      )}
                    </div>
                  </div>

                  {brand.stats && (
                    <div className="grid grid-cols-2 gap-4 pt-3 border-t border-gray-200">
                      <div>
                        <p className="text-xs text-gray-500">Mentions</p>
                        <p className="text-sm font-semibold text-gray-900">
                          {brand.stats.total_mentions}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500">New Threats</p>
                        <p className={`text-sm font-semibold ${
                          brand.stats.new_threats > 0 ? 'text-red-600' : 'text-gray-900'
                        }`}>
                          {brand.stats.new_threats}
                        </p>
                      </div>
                    </div>
                  )}

                  <div className="pt-3 border-t border-gray-200">
                    <div className="flex justify-between items-center">
                      <div>
                        <p className="text-xs text-gray-500">Sentiment Threshold</p>
                        <p className="text-sm font-medium text-gray-700">
                          {brand.sentiment_threshold.toFixed(1)}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500">Viral Threshold</p>
                        <p className="text-sm font-medium text-gray-700">
                          {brand.viral_threshold.toFixed(1)}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="mt-4 flex space-x-2">
                  <button className="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-2 rounded text-sm">
                    Edit
                  </button>
                  <button className="flex-1 bg-primary-50 hover:bg-primary-100 text-primary-700 px-3 py-2 rounded text-sm">
                    View Details
                  </button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="text-center py-12">
            <TagIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No brands configured</h3>
            <p className="text-gray-500 mb-6">
              Get started by adding your first brand to monitor for threats and mentions.
            </p>
            <button className="bg-primary-600 hover:bg-primary-700 text-white px-6 py-3 rounded-md flex items-center space-x-2 mx-auto">
              <PlusIcon className="h-5 w-5" />
              <span>Add Your First Brand</span>
            </button>
          </CardContent>
        </Card>
      )}

      {/* Brand management tips */}
      <Card>
        <CardHeader>
          <CardTitle>Brand Management Tips</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center p-4">
              <TagIcon className="h-8 w-8 text-primary-600 mx-auto mb-2" />
              <h4 className="font-medium text-gray-900 mb-1">Choose Good Keywords</h4>
              <p className="text-sm text-gray-600">
                Include your brand name, product names, and common misspellings
              </p>
            </div>
            <div className="text-center p-4">
              <CogIcon className="h-8 w-8 text-primary-600 mx-auto mb-2" />
              <h4 className="font-medium text-gray-900 mb-1">Set Thresholds</h4>
              <p className="text-sm text-gray-600">
                Adjust sentiment and viral thresholds to match your brand's needs
              </p>
            </div>
            <div className="text-center p-4">
              <PlusIcon className="h-8 w-8 text-primary-600 mx-auto mb-2" />
              <h4 className="font-medium text-gray-900 mb-1">Monitor Competitors</h4>
              <p className="text-sm text-gray-600">
                Add competitor names to stay informed about industry trends
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}