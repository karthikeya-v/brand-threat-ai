import openai
from typing import Optional, List, Dict
import json
import logging

from app.core.config import settings
from app.models.mention import Mention
from app.models.brand import Brand
from app.services.threat_analyzer import ThreatAnalysis

logger = logging.getLogger(__name__)


class AIRefiner:
    """Use DeepSeek R1 via OpenRouter for complex analysis only"""
    
    def __init__(self):
        if not settings.OPENROUTER_API_KEY:
            logger.warning("OpenRouter API key not configured - AI refinement disabled")
            self.enabled = False
        else:
            self.client = openai.OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=settings.OPENROUTER_API_KEY
            )
            self.enabled = True

    async def refine_threat_analysis(
        self, 
        mention: Mention, 
        brand: Brand,
        initial_analysis: ThreatAnalysis
    ) -> ThreatAnalysis:
        """Refine analysis using DeepSeek R1 for complex cases"""
        
        if not self.enabled:
            logger.warning("AI refinement requested but not enabled")
            return initial_analysis
        
        try:
            prompt = self._build_refinement_prompt(mention, brand, initial_analysis)
            
            response = self.client.chat.completions.create(
                model="deepseek/deepseek-r1",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400,
                temperature=0.1
            )
            
            refined_analysis = self._parse_ai_response(
                response.choices[0].message.content, 
                initial_analysis
            )
            
            logger.info(f"AI refinement completed for mention {mention.id}")
            return refined_analysis
            
        except Exception as e:
            logger.error(f"AI refinement failed: {str(e)}")
            return initial_analysis

    def _build_refinement_prompt(self, mention: Mention, brand: Brand, analysis: ThreatAnalysis) -> str:
        """Build prompt for AI refinement"""
        
        prompt = f"""You are a brand threat analysis expert. Analyze this social media mention for potential threats to the brand.

BRAND: {brand.name}
INDUSTRY: {brand.industry or 'Unknown'}
KEYWORDS: {', '.join(brand.keywords)}

MENTION:
Platform: {mention.platform}
Author: {mention.author} ({mention.author_followers or 'Unknown'} followers)
Content: "{mention.content}"
Engagement: {mention.engagement_count or 0} interactions

INITIAL ANALYSIS:
- Sentiment Score: {analysis.sentiment_score:.2f} (-1 to 1)
- Viral Potential: {analysis.viral_potential:.2f} (0 to 1)
- Threat Type: {analysis.threat_type}
- Severity: {analysis.severity_score:.2f} (0 to 1)
- Confidence: {analysis.confidence:.2f} (0 to 1)

Please refine this analysis considering:
1. Context, sarcasm, or hidden meaning
2. Brand-specific implications
3. Industry context
4. Potential for escalation

Respond in JSON format:
{{
    "refined_sentiment": float (-1 to 1),
    "refined_viral_potential": float (0 to 1),
    "refined_threat_type": string,
    "refined_severity": float (0 to 1),
    "confidence": float (0 to 1),
    "summary": "Brief explanation of the threat",
    "suggested_responses": ["response 1", "response 2", "response 3"]
}}"""

        return prompt

    def _parse_ai_response(self, response_text: str, initial_analysis: ThreatAnalysis) -> ThreatAnalysis:
        """Parse AI response and create refined analysis"""
        
        try:
            # Try to extract JSON from response
            if '```json' in response_text:
                json_start = response_text.find('```json') + 7
                json_end = response_text.find('```', json_start)
                json_text = response_text[json_start:json_end].strip()
            elif '{' in response_text and '}' in response_text:
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                json_text = response_text[json_start:json_end]
            else:
                raise ValueError("No JSON found in response")
            
            data = json.loads(json_text)
            
            # Create refined analysis
            return ThreatAnalysis(
                sentiment_score=self._safe_float(data.get('refined_sentiment'), initial_analysis.sentiment_score),
                viral_potential=self._safe_float(data.get('refined_viral_potential'), initial_analysis.viral_potential),
                threat_type=data.get('refined_threat_type', initial_analysis.threat_type),
                severity_score=self._safe_float(data.get('refined_severity'), initial_analysis.severity_score),
                confidence=self._safe_float(data.get('confidence'), initial_analysis.confidence),
                ai_refined=True,
                summary=data.get('summary'),
                suggested_responses=data.get('suggested_responses', [])
            )
            
        except Exception as e:
            logger.error(f"Failed to parse AI response: {str(e)}")
            # Return initial analysis with AI refined flag
            return ThreatAnalysis(
                sentiment_score=initial_analysis.sentiment_score,
                viral_potential=initial_analysis.viral_potential,
                threat_type=initial_analysis.threat_type,
                severity_score=initial_analysis.severity_score,
                confidence=initial_analysis.confidence,
                ai_refined=True,
                summary="AI refinement attempted but parsing failed",
                suggested_responses=[]
            )

    def _safe_float(self, value, default: float) -> float:
        """Safely convert value to float with bounds checking"""
        try:
            result = float(value)
            # Ensure bounds
            if 'sentiment' in str(value):
                return max(-1.0, min(1.0, result))
            else:
                return max(0.0, min(1.0, result))
        except (ValueError, TypeError):
            return default

    async def analyze_trend_context(self, mentions: List[Mention], brand: Brand) -> Dict:
        """Analyze multiple mentions for trending context"""
        
        if not self.enabled or len(mentions) < 3:
            return {}
        
        try:
            content_summary = "\n".join([
                f"- {m.platform}: {m.content[:100]}..." 
                for m in mentions[:10]
            ])
            
            prompt = f"""Analyze these recent mentions of {brand.name} for trending topics or emerging threats:

{content_summary}

Identify:
1. Common themes or issues
2. Escalation patterns
3. Potential crisis indicators
4. Recommended monitoring focus

Respond in JSON format with trend_summary, risk_level (low/medium/high), and recommendations."""

            response = self.client.chat.completions.create(
                model="deepseek/deepseek-r1",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.1
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Trend analysis failed: {str(e)}")
            return {}