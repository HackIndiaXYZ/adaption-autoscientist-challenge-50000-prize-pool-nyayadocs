"""
Adaptive Learning Module for NyayaSetu AI Agent
Uses nyaysetu_legal_aid.csv to continuously improve model predictions
"""

import csv
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AdaptiveLearningEngine:
    """
    Loads adaptive dataset and provides correction/improvement suggestions
    based on historical feedback and corrections
    """
    
    def __init__(self, csv_path: str = "data/nyayasetu_legal_aid.csv"):
        self.csv_path = Path(csv_path)
        self.dataset = []
        self.intent_corrections = {}
        self.language_corrections = {}
        self.confidence_threshold = 0.85
        self.load_dataset()
        
    def load_dataset(self):
        """Load adaptive dataset with feedback and corrections"""
        if not self.csv_path.exists():
            logger.warning(f"Adaptive dataset not found at {self.csv_path}")
            return
            
        try:
            df = pd.read_csv(self.csv_path)
            self.dataset = df.to_dict('records')
            
            # Build correction lookup tables
            self._build_correction_tables()
            
            logger.info(f"✅ Loaded {len(self.dataset)} adaptive records")
            logger.info(f"   Intent corrections: {len(self.intent_corrections)}")
            logger.info(f"   Language corrections: {len(self.language_corrections)}")
            
        except Exception as e:
            logger.error(f"Failed to load adaptive dataset: {e}")
    
    def _build_correction_tables(self):
        """Build lookup tables for common corrections"""
        for record in self.dataset:
            # Track intent corrections
            if record.get('correction_applied') == 'yes':
                prompt = record.get('prompt', '')[:200]  # First 200 chars as key
                intent = record.get('intent')
                confidence_after = float(record.get('confidence_after', 0))
                
                if confidence_after > self.confidence_threshold:
                    self.intent_corrections[prompt] = intent
            
            # Track language detection improvements
            language_code = record.get('language_code')
            if language_code and record.get('confidence_after', 0) > 0.9:
                prompt = record.get('prompt', '')[:100]
                self.language_corrections[prompt] = language_code
    
    def suggest_intent_correction(self, message: str, predicted_intent: str, 
                                 confidence: float) -> Optional[Dict]:
        """
        Suggests intent correction based on historical data
        
        Returns: {
            "suggested_intent": str,
            "reason": str,
            "confidence": float
        } or None
        """
        # Check if low confidence and we have a similar corrected example
        if confidence < self.confidence_threshold:
            message_prefix = message[:200]
            
            if message_prefix in self.intent_corrections:
                suggested = self.intent_corrections[message_prefix]
                
                if suggested != predicted_intent:
                    return {
                        "suggested_intent": suggested,
                        "reason": "Historical correction from adaptive dataset",
                        "confidence": 0.95,
                        "source": "adaptive_learning"
                    }
        
        return None
    
    def get_similar_examples(self, intent: str, language: str, limit: int = 5) -> List[Dict]:
        """
        Retrieves similar high-quality examples from adaptive dataset
        for few-shot learning
        """
        examples = []
        
        for record in self.dataset:
            if (record.get('intent') == intent and 
                record.get('language_code') == language and
                float(record.get('confidence_after', 0)) > 0.9 and
                int(record.get('feedback_rating', 0)) >= 4):
                
                examples.append({
                    "prompt": record.get('prompt'),
                    "completion": record.get('completion'),
                    "confidence": record.get('confidence_after'),
                    "rating": record.get('feedback_rating')
                })
                
                if len(examples) >= limit:
                    break
        
        return examples
    
    def get_improvement_stats(self) -> Dict:
        """Returns statistics about dataset improvements"""
        if not self.dataset:
            return {}
        
        df = pd.DataFrame(self.dataset)
        
        stats = {
            "total_records": len(self.dataset),
            "corrected_records": len(df[df['correction_applied'] == 'yes']),
            "avg_confidence_before": df['confidence_before'].astype(float).mean(),
            "avg_confidence_after": df['confidence_after'].astype(float).mean(),
            "confidence_gain": df['confidence_after'].astype(float).mean() - 
                             df['confidence_before'].astype(float).mean(),
            "high_quality_records": len(df[df['feedback_rating'].astype(int) >= 4]),
            "languages_covered": df['language_code'].nunique(),
            "intents_covered": df['intent'].nunique()
        }
        
        return stats
    
    def log_interaction(self, message: str, predicted_intent: str, 
                       predicted_language: str, confidence: float,
                       feedback: Optional[Dict] = None):
        """
        Logs new interaction for future adaptive learning
        Appends to the dataset file
        """
        record = {
            "prompt": message,
            "predicted_intent": predicted_intent,
            "predicted_language": predicted_language,
            "confidence": confidence,
            "feedback": json.dumps(feedback) if feedback else None,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Append to interactions log
        log_file = Path("data/adaptive_interactions.jsonl")
        log_file.parent.mkdir(exist_ok=True)
        
        with log_file.open('a', encoding='utf-8') as f:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    
    def get_quality_insights(self, intent: str = None, language: str = None) -> Dict:
        """
        Provides insights about data quality for specific intent/language
        """
        if not self.dataset:
            return {}
        
        df = pd.DataFrame(self.dataset)
        
        if intent:
            df = df[df['intent'] == intent]
        if language:
            df = df[df['language_code'] == language]
        
        if len(df) == 0:
            return {"error": "No data for specified filters"}
        
        return {
            "record_count": len(df),
            "avg_confidence": df['confidence_after'].astype(float).mean(),
            "avg_rating": df['feedback_rating'].astype(int).mean(),
            "correction_rate": len(df[df['correction_applied'] == 'yes']) / len(df),
            "high_quality_percentage": len(df[df['feedback_rating'].astype(int) >= 4]) / len(df) * 100
        }


def integrate_adaptive_learning_with_main():
    """
    Integration code to add to main.py
    """
    integration_code = '''
# Add to top of main.py
from adaptive_learning import AdaptiveLearningEngine

# Initialize adaptive learning engine
adaptive_engine = AdaptiveLearningEngine("data/nyayasetu_legal_aid.csv")

# In your classify_with_groq or LLMService.classify_message function:
def enhanced_classify_message(message: str, language: str) -> dict:
    # Original classification
    result = original_classify_message(message, language)
    
    # Check for adaptive correction
    correction = adaptive_engine.suggest_intent_correction(
        message, 
        result['intent'], 
        result.get('confidence', 0.5)
    )
    
    if correction:
        logger.info(f"Adaptive correction: {result['intent']} → {correction['suggested_intent']}")
        result['intent'] = correction['suggested_intent']
        result['confidence'] = correction['confidence']
        result['correction_source'] = 'adaptive_learning'
    
    # Log interaction for future learning
    adaptive_engine.log_interaction(
        message, 
        result['intent'], 
        language, 
        result.get('confidence', 0.5)
    )
    
    return result

# Add endpoint to get adaptive stats
@app.get("/api/adaptive-stats")
async def get_adaptive_stats():
    return JSONResponse(adaptive_engine.get_improvement_stats())

# Add endpoint for quality insights
@app.get("/api/quality-insights/{intent}")
async def get_quality_insights(intent: str, language: str = None):
    return JSONResponse(adaptive_engine.get_quality_insights(intent, language))
'''
    
    return integration_code


if __name__ == "__main__":
    # Test the adaptive learning engine
    engine = AdaptiveLearningEngine()
    
    print("=" * 70)
    print("🧠 ADAPTIVE LEARNING ENGINE - Test")
    print("=" * 70)
    print()
    
    # Show improvement stats
    stats = engine.get_improvement_stats()
    print("📊 Improvement Statistics:")
    for key, value in stats.items():
        print(f"   {key}: {value:.3f}" if isinstance(value, float) else f"   {key}: {value}")
    print()
    
    # Show quality insights for bail_enquiry
    print("📈 Quality Insights for 'bail_enquiry' intent:")
    insights = engine.get_quality_insights(intent="bail_enquiry")
    for key, value in insights.items():
        print(f"   {key}: {value:.3f}" if isinstance(value, float) else f"   {key}: {value}")
    print()
    
    # Get similar examples
    examples = engine.get_similar_examples("bail_enquiry", "hi", limit=3)
    print(f"✅ Found {len(examples)} high-quality examples for 'bail_enquiry' in Hindi")
    print()
    
    print("=" * 70)
    print("✨ Adaptive Learning Engine is ready!")
    print("=" * 70)
