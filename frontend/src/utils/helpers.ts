import { ThreatSeverity, ThreatType } from '@/types';

export function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (diffInSeconds < 60) {
    return 'just now';
  } else if (diffInSeconds < 3600) {
    const minutes = Math.floor(diffInSeconds / 60);
    return `${minutes} minute${minutes === 1 ? '' : 's'} ago`;
  } else if (diffInSeconds < 86400) {
    const hours = Math.floor(diffInSeconds / 3600);
    return `${hours} hour${hours === 1 ? '' : 's'} ago`;
  } else if (diffInSeconds < 604800) {
    const days = Math.floor(diffInSeconds / 86400);
    return `${days} day${days === 1 ? '' : 's'} ago`;
  } else {
    return formatDate(dateString);
  }
}

export function getSeverityLevel(score: number): ThreatSeverity {
  if (score >= 0.8) return 'critical';
  if (score >= 0.6) return 'high';
  if (score >= 0.4) return 'medium';
  return 'low';
}

export function getSeverityColor(severity: ThreatSeverity | number): string {
  const level = typeof severity === 'number' ? getSeverityLevel(severity) : severity;
  
  switch (level) {
    case 'critical':
      return 'text-red-600 bg-red-100';
    case 'high':
      return 'text-orange-600 bg-orange-100';
    case 'medium':
      return 'text-yellow-600 bg-yellow-100';
    case 'low':
      return 'text-green-600 bg-green-100';
    default:
      return 'text-gray-600 bg-gray-100';
  }
}

export function getThreatTypeDisplay(type: string): string {
  const typeMap: Record<string, string> = {
    severe_negative: 'Severe Negative',
    crisis_potential: 'Crisis Potential',
    competitor_attack: 'Competitor Attack',
    product_issue: 'Product Issue',
    service_complaint: 'Service Complaint',
    negative_sentiment: 'Negative Sentiment',
    neutral_mention: 'Neutral Mention',
  };
  
  return typeMap[type] || type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

export function getThreatTypeColor(type: string): string {
  const colorMap: Record<string, string> = {
    severe_negative: 'text-red-600 bg-red-100',
    crisis_potential: 'text-purple-600 bg-purple-100',
    competitor_attack: 'text-blue-600 bg-blue-100',
    product_issue: 'text-orange-600 bg-orange-100',
    service_complaint: 'text-yellow-600 bg-yellow-100',
    negative_sentiment: 'text-red-500 bg-red-50',
    neutral_mention: 'text-gray-600 bg-gray-100',
  };
  
  return colorMap[type] || 'text-gray-600 bg-gray-100';
}

export function getPlatformColor(platform: string): string {
  const colorMap: Record<string, string> = {
    twitter: 'text-blue-500 bg-blue-100',
    reddit: 'text-orange-500 bg-orange-100',
    news: 'text-purple-500 bg-purple-100',
    youtube: 'text-red-500 bg-red-100',
    facebook: 'text-blue-600 bg-blue-100',
    instagram: 'text-pink-500 bg-pink-100',
  };
  
  return colorMap[platform.toLowerCase()] || 'text-gray-500 bg-gray-100';
}

export function formatNumber(num: number): string {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M';
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K';
  }
  return num.toString();
}

export function formatPercentage(value: number, decimals: number = 1): string {
  return `${(value * 100).toFixed(decimals)}%`;
}

export function getSentimentColor(score: number): string {
  if (score > 0.2) return 'text-green-600 bg-green-100';
  if (score > -0.2) return 'text-gray-600 bg-gray-100';
  if (score > -0.6) return 'text-yellow-600 bg-yellow-100';
  return 'text-red-600 bg-red-100';
}

export function getSentimentLabel(score: number): string {
  if (score > 0.5) return 'Very Positive';
  if (score > 0.2) return 'Positive';
  if (score > -0.2) return 'Neutral';
  if (score > -0.6) return 'Negative';
  return 'Very Negative';
}

export function getViralPotentialColor(score: number): string {
  if (score > 0.7) return 'text-red-600 bg-red-100';
  if (score > 0.5) return 'text-orange-600 bg-orange-100';
  if (score > 0.3) return 'text-yellow-600 bg-yellow-100';
  return 'text-green-600 bg-green-100';
}

export function getViralPotentialLabel(score: number): string {
  if (score > 0.8) return 'Very High';
  if (score > 0.6) return 'High';
  if (score > 0.4) return 'Medium';
  if (score > 0.2) return 'Low';
  return 'Very Low';
}

export function getStatusColor(status: string): string {
  const statusMap: Record<string, string> = {
    new: 'text-blue-600 bg-blue-100',
    reviewing: 'text-yellow-600 bg-yellow-100',
    resolved: 'text-green-600 bg-green-100',
    dismissed: 'text-gray-600 bg-gray-100',
  };
  
  return statusMap[status] || 'text-gray-600 bg-gray-100';
}

export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength).trim() + '...';
}

export function extractHashtags(text: string): string[] {
  const hashtagRegex = /#[\w]+/g;
  return text.match(hashtagRegex) || [];
}

export function extractMentions(text: string): string[] {
  const mentionRegex = /@[\w]+/g;
  return text.match(mentionRegex) || [];
}

export function classNames(...classes: (string | undefined | null | false)[]): string {
  return classes.filter(Boolean).join(' ');
}

export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout;
  
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}

export function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

export function generateAvatarColor(name: string): string {
  const colors = [
    'bg-red-500',
    'bg-orange-500',
    'bg-yellow-500',
    'bg-green-500',
    'bg-blue-500',
    'bg-indigo-500',
    'bg-purple-500',
    'bg-pink-500',
  ];
  
  const index = name.charCodeAt(0) % colors.length;
  return colors[index];
}

export function getInitials(name: string): string {
  return name
    .split(' ')
    .map(word => word.charAt(0))
    .join('')
    .toUpperCase()
    .substring(0, 2);
}