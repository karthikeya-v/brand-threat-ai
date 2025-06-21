import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from app.models.mention import Mention
from app.models.brand import Brand


@dataclass
class ThreatAnalysis:
    sentiment_score: float
    viral_potential: float
    threat_type: str
    severity_score: float
    confidence: float
    ai_refined: bool
    summary: Optional[str] = None
    suggested_responses: Optional[List[str]] = None


class ThreatAnalyzer:
    """Fast, rule-based threat analysis with selective AI refinement"""
    
    def __init__(self):
        self.vader_analyzer = SentimentIntensityAnalyzer()
        
        # Threat classification patterns
        self.threat_patterns = {
            "severe_negative": [
                r'\b(hate|worst|terrible|awful|horrible|disgusting|scam|fraud)\b',
                r'\b(never\s+again|boycott|warning|avoid|stay\s+away)\b',
                r'\b(lawsuit|sue|legal\s+action|report|complaint)\b'
            ],
            "crisis_potential": [
                r'\b(viral|trending|everyone\s+needs\s+to\s+know|share\s+this)\b',
                r'\b(breaking|urgent|alert|scandal|exposed)\b',
                r'\b(going\s+viral|blowing\s+up|spreading\s+fast)\b'
            ],
            "competitor_attack": [
                r'\b(better\s+than|superior\s+to|alternative\s+to)\b',
                r'\b(switch\s+to|choose\s+instead|rather\s+use)\b',
                r'\b(compared\s+to|versus|vs\.?)\b'
            ],
            "product_issue": [
                r'\b(defect|broken|bug|error|problem|issue|fault)\b',
                r'\b(not\s+working|stopped\s+working|malfunction)\b',
                r'\b(quality\s+control|manufacturing\s+defect)\b'
            ],
            "service_complaint": [
                r'\b(customer\s+service|support|help|assistance)\b',
                r'\b(rude|unhelpful|incompetent|slow\s+response)\b',
                r'\b(waited|hold|callback|ignored)\b'
            ]
        }
        
        # Viral indicators
        self.viral_indicators = [
            r'\b(share|retweet|rt|repost|spread\s+the\s+word)\b',
            r'\b(everyone\s+should\s+know|tell\s+your\s+friends)\b',
            r'\b(going\s+viral|viral|trending|blowing\s+up)\b',
            r'\b(thread|story\s+time|buckle\s+up)\b'
        ]
        
        # Engagement multipliers by platform
        self.platform_multipliers = {
            "twitter": 1.2,
            "reddit": 1.0,
            "facebook": 0.8,
            "instagram": 0.9,
            "youtube": 1.5,
            "tiktok": 1.8,
            "news": 2.0
        }

    def analyze_mention(self, mention: Mention, brand: Brand) -> ThreatAnalysis:
        """Main analysis method - fast rule-based analysis"""
        
        # 1. Sentiment analysis using TextBlob + VADER
        sentiment = self._calculate_sentiment(mention.content)
        
        # 2. Viral potential scoring
        viral_score = self._calculate_viral_potential(mention, brand)
        
        # 3. Threat classification
        threat_type = self._classify_threat_type(mention, sentiment, brand)
        
        # 4. Overall severity calculation
        severity = self._calculate_severity(sentiment, viral_score, threat_type, mention)
        
        # 5. Confidence calculation
        confidence = self._calculate_confidence(sentiment, viral_score, mention)
        
        return ThreatAnalysis(
            sentiment_score=sentiment,
            viral_potential=viral_score,
            threat_type=threat_type,
            severity_score=severity,
            confidence=confidence,
            ai_refined=False
        )

    def _calculate_sentiment(self, text: str) -> float:
        """Combine TextBlob and VADER for better accuracy"""
        
        # TextBlob sentiment
        blob = TextBlob(text)
        textblob_sentiment = blob.sentiment.polarity
        
        # VADER sentiment
        vader_scores = self.vader_analyzer.polarity_scores(text)
        vader_sentiment = vader_scores['compound']
        
        # Weighted average (VADER is better for social media)
        combined_sentiment = (textblob_sentiment * 0.3) + (vader_sentiment * 0.7)
        
        return max(-1.0, min(1.0, combined_sentiment))

    def _calculate_viral_potential(self, mention: Mention, brand: Brand) -> float:
        """Score viral potential based on author influence, engagement, platform"""
        
        viral_score = 0.0
        
        # Author influence (follower count)
        if mention.author_followers:
            if mention.author_followers > 100000:
                viral_score += 0.4
            elif mention.author_followers > 10000:
                viral_score += 0.3
            elif mention.author_followers > 1000:
                viral_score += 0.2
            else:
                viral_score += 0.1
        
        # Engagement metrics
        if mention.engagement_count:
            if mention.engagement_count > 1000:
                viral_score += 0.3
            elif mention.engagement_count > 100:
                viral_score += 0.2
            elif mention.engagement_count > 10:
                viral_score += 0.1
        
        # Platform multiplier
        platform_multiplier = self.platform_multipliers.get(mention.platform.lower(), 1.0)
        viral_score *= platform_multiplier
        
        # Content viral indicators
        content_lower = mention.content.lower()
        viral_indicator_count = sum(
            1 for pattern in self.viral_indicators
            if re.search(pattern, content_lower, re.IGNORECASE)
        )
        viral_score += min(0.3, viral_indicator_count * 0.1)
        
        return max(0.0, min(1.0, viral_score))

    def _classify_threat_type(self, mention: Mention, sentiment: float, brand: Brand) -> str:
        """Rule-based threat classification using keywords and patterns"""
        
        content_lower = mention.content.lower()
        
        # Check for each threat type
        threat_scores = {}
        
        for threat_type, patterns in self.threat_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, content_lower, re.IGNORECASE))
                score += matches
            threat_scores[threat_type] = score
        
        # Find the highest scoring threat type
        if not any(threat_scores.values()):
            # No specific patterns found, classify by sentiment
            if sentiment < -0.6:
                return "severe_negative"
            elif sentiment < -0.3:
                return "negative_sentiment"
            else:
                return "neutral_mention"
        
        return max(threat_scores.items(), key=lambda x: x[1])[0]

    def _calculate_severity(self, sentiment: float, viral_score: float, threat_type: str, mention: Mention) -> float:
        """Calculate overall threat severity score"""
        
        # Base severity from sentiment
        sentiment_severity = abs(sentiment) if sentiment < 0 else 0
        
        # Threat type weights
        threat_weights = {
            "severe_negative": 0.9,
            "crisis_potential": 0.8,
            "competitor_attack": 0.6,
            "product_issue": 0.7,
            "service_complaint": 0.5,
            "negative_sentiment": 0.4,
            "neutral_mention": 0.1
        }
        
        threat_weight = threat_weights.get(threat_type, 0.3)
        
        # Combine factors
        severity = (
            sentiment_severity * 0.4 +
            viral_score * 0.3 +
            threat_weight * 0.3
        )
        
        # Platform influence
        if mention.platform in ["news", "youtube", "tiktok"]:
            severity *= 1.2
        
        return max(0.0, min(1.0, severity))

    def _calculate_confidence(self, sentiment: float, viral_score: float, mention: Mention) -> float:
        """Calculate analysis confidence based on available data"""
        
        confidence = 0.5  # Base confidence
        
        # More confidence with stronger sentiment
        if abs(sentiment) > 0.5:
            confidence += 0.2
        
        # More confidence with engagement data
        if mention.engagement_count and mention.engagement_count > 0:
            confidence += 0.15
        
        # More confidence with author data
        if mention.author_followers and mention.author_followers > 0:
            confidence += 0.15
        
        # Content length factor
        if len(mention.content) > 100:
            confidence += 0.1
        
        return max(0.0, min(1.0, confidence))

    def needs_ai_refinement(self, analysis: ThreatAnalysis, mention: Mention) -> bool:
        """Decide when to use expensive AI processing (only ~5% of cases)"""
        
        return (
            analysis.severity_score > 0.7 or  # High severity threats
            analysis.sentiment_score < -0.6 or  # Very negative sentiment
            analysis.viral_potential > 0.8 or  # High viral potential
            self._has_complex_context(mention) or  # Sarcasm, context needed
            analysis.confidence < 0.6  # Low confidence in analysis
        )

    def _has_complex_context(self, mention: Mention) -> bool:
        """Detect mentions that might need AI for context understanding"""
        
        content_lower = mention.content.lower()
        
        # Sarcasm indicators
        sarcasm_indicators = [
            r'\b(sure|yeah\s+right|oh\s+great|fantastic|wonderful)\b.*\b(not|never)\b',
            r'\b(thanks\s+for\s+nothing|appreciate\s+it|real\s+helpful)\b',
            r'[!]{2,}|[?]{2,}|\b(wow|amazing|incredible)\b.*[!]{1,}'
        ]
        
        for pattern in sarcasm_indicators:
            if re.search(pattern, content_lower, re.IGNORECASE):
                return True
        
        # Complex comparisons or context
        complex_patterns = [
            r'\b(compared\s+to|unlike|however|but|although|while)\b',
            r'\b(used\s+to\s+be|was\s+better|has\s+changed)\b',
            r'\b(depends|context|situation|circumstances)\b'
        ]
        
        for pattern in complex_patterns:
            if re.search(pattern, content_lower, re.IGNORECASE):
                return True
        
        return False

    def generate_response_suggestions(self, analysis: ThreatAnalysis, mention: Mention, brand: Brand) -> List[str]:
        """Generate response suggestions based on threat analysis"""
        
        suggestions = []
        
        if analysis.threat_type == "severe_negative":
            suggestions.extend([
                f"Reach out directly to address concerns: 'Hi {mention.author}, we're sorry to hear about your experience. Please DM us so we can make this right.'",
                "Issue public apology if warranted",
                "Escalate to crisis management team"
            ])
        
        elif analysis.threat_type == "product_issue":
            suggestions.extend([
                "Acknowledge the issue and provide timeline for fix",
                "Offer immediate workaround if available",
                "Direct to customer support for individual assistance"
            ])
        
        elif analysis.threat_type == "service_complaint":
            suggestions.extend([
                "Apologize for poor service experience",
                "Offer to connect with customer service manager",
                "Provide direct contact information"
            ])
        
        elif analysis.threat_type == "competitor_attack":
            suggestions.extend([
                "Highlight unique value propositions",
                "Share customer testimonials",
                "Avoid direct confrontation, focus on benefits"
            ])
        
        # High viral potential suggestions
        if analysis.viral_potential > 0.7:
            suggestions.append("Monitor closely for escalation")
            suggestions.append("Prepare proactive statement if needed")
        
        return suggestions[:3]  # Limit to top 3 suggestions