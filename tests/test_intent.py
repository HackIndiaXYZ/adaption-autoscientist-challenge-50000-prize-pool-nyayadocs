"""
Test cases for intent classification system
"""
import pytest
import sys
import os

# Add parent directory to path to import main
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import classify_intent, rule_based_extraction, INTENT_MAP


class TestIntentClassification:
    """Test intent classification functionality"""
    
    def test_bail_application_intent(self):
        """Test bail application intent detection"""
        message = "I need to apply for bail for my brother who is in custody"
        intent_key = classify_intent(message)
        intent = INTENT_MAP[intent_key]
        assert intent == "bail_application", f"Expected 'bail_application', got '{intent}'"
    
    def test_surety_bond_intent(self):
        """Test surety bond intent detection"""
        message = "I want to become a surety for my friend's bail"
        intent_key = classify_intent(message)
        intent = INTENT_MAP[intent_key]
        assert intent == "surety_bond", f"Expected 'surety_bond', got '{intent}'"
    
    def test_case_status_intent(self):
        """Test case status check intent detection"""
        message = "What is the status of FIR number 123/2024?"
        intent_key = classify_intent(message)
        intent = INTENT_MAP[intent_key]
        assert intent == "case_status", f"Expected 'case_status', got '{intent}'"
    
    def test_legal_aid_intent(self):
        """Test legal aid request intent detection"""
        message = "I need a lawyer but cannot afford one"
        intent_key = classify_intent(message)
        intent = INTENT_MAP[intent_key]
        assert intent == "legal_aid", f"Expected 'legal_aid', got '{intent}'"
    
    def test_rule_based_extraction_with_entities(self):
        """Test full rule-based extraction with entities"""
        message = "FIR No. 456/2024 at City Police Station, accused John Doe, section 420"
        result = rule_based_extraction(message, "en")
        
        assert result["intent"] is not None
        assert result["fir_number"] == "456/2024"
        assert result["police_station"] is not None
        assert result["section_charged"] == "420"
        assert result["language_of_message"] == "en"
    
    def test_multilingual_intent_hindi(self):
        """Test intent classification for Hindi message"""
        message = "मुझे जमानत के लिए आवेदन करना है"
        result = rule_based_extraction(message, "hi")
        
        assert result["intent"] in ["bail_application", "legal_aid", "general_inquiry"]
        assert result["language_of_message"] == "hi"


class TestIntentKeywords:
    """Test intent keyword matching"""
    
    def test_bail_keywords(self):
        """Test bail-related keywords"""
        bail_messages = [
            "I need bail for my father",
            "How to apply for anticipatory bail?",
            "Bail application help needed"
        ]
        
        for message in bail_messages:
            intent_key = classify_intent(message)
            intent = INTENT_MAP[intent_key]
            assert intent == "bail_application", \
                f"Message '{message}' should be classified as bail_application, got '{intent}'"
    
    def test_surety_keywords(self):
        """Test surety-related keywords"""
        surety_messages = [
            "I want to be a surety",
            "How to provide surety bond?",
            "Surety requirements for bail"
        ]
        
        for message in surety_messages:
            intent_key = classify_intent(message)
            intent = INTENT_MAP[intent_key]
            assert intent == "surety_bond", \
                f"Message '{message}' should be classified as surety_bond, got '{intent}'"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
