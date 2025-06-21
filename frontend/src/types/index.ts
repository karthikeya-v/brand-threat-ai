export interface User {
  id: string;
  email: string;
  company_name?: string;
  tier: 'starter' | 'professional' | 'enterprise';
  is_active: boolean;
  created_at: string;
}

export interface Brand {
  id: string;
  name: string;
  keywords: string[];
  competitors: string[];
  industry?: string;
  sentiment_threshold: number;
  viral_threshold: number;
  is_active: boolean;
  created_at: string;
  stats?: BrandStats;
}

export interface BrandStats {
  total_mentions: number;
  new_threats: number;
  high_severity_threats: number;
  avg_sentiment: number;
}

export interface Mention {
  id: string;
  brand_id: string;
  brand_name: string;
  platform: string;
  platform_id?: string;
  url?: string;
  title?: string;
  content: string;
  author?: string;
  author_followers: number;
  engagement_count: number;
  published_at?: string;
  collected_at: string;
  processed: boolean;
}

export interface Threat {
  id: string;
  brand_id: string;
  brand_name: string;
  mention_id: string;
  threat_type: string;
  severity_score: number;
  viral_potential: number;
  sentiment_score: number;
  confidence: number;
  ai_refined: boolean;
  status: 'new' | 'reviewing' | 'resolved' | 'dismissed';
  summary?: string;
  suggested_responses: string[];
  assigned_to?: string;
  created_at: string;
  updated_at: string;
  mention: {
    id: string;
    platform: string;
    content: string;
    author?: string;
    author_followers: number;
    engagement_count: number;
    url?: string;
    published_at?: string;
  };
}

export interface ThreatStats {
  total_threats: number;
  new_threats: number;
  in_progress_threats: number;
  resolved_threats: number;
  high_severity_count: number;
  avg_severity: number;
}

export interface OverviewStats {
  total_brands: number;
  total_mentions: number;
  total_threats: number;
  high_severity_threats: number;
  avg_sentiment: number;
  threat_resolution_rate: number;
}

export interface SentimentTrend {
  date: string;
  avg_sentiment: number;
  mention_count: number;
  threat_count: number;
}

export interface ThreatBreakdown {
  threat_type: string;
  count: number;
  avg_severity: number;
  percentage: number;
}

export interface PlatformPerformance {
  platform: string;
  mention_count: number;
  threat_count: number;
  avg_sentiment: number;
  engagement_rate: number;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface ApiError {
  detail: string;
}

export type ThreatSeverity = 'low' | 'medium' | 'high' | 'critical';
export type PlatformType = 'twitter' | 'reddit' | 'news' | 'youtube' | 'facebook' | 'instagram';
export type ThreatType = 'severe_negative' | 'crisis_potential' | 'competitor_attack' | 'product_issue' | 'service_complaint' | 'negative_sentiment' | 'neutral_mention';