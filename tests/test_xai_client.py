"""
Unit tests for xAI API client.

Run with: pytest tests/test_xai_client.py
"""
import pytest
import json
from unittest.mock import Mock, patch

from api.xai_client import XAIClient


@pytest.fixture
def xai_client():
    """Create a test xAI client with dummy API key."""
    return XAIClient(api_key="test_key_123")


class TestXAIClientParsing:
    """Test API response parsing."""

    def test_parse_valid_json_response(self, xai_client):
        """Test parsing a valid JSON response."""
        mock_response = {
            "choices": [{
                "message": {
                    "content": json.dumps([{
                        "cleaned_text": "Cleaned note text",
                        "category": "General",
                        "date": "2025-01-01",
                        "timestamp": "12:00:00",
                        "confidence_score": 0.95,
                        "clarifying_question": None
                    }])
                }
            }]
        }

        parsed = xai_client._parse_response(mock_response)

        assert len(parsed) == 1
        assert parsed[0]["cleaned_text"] == "Cleaned note text"
        assert parsed[0]["category"] == "General"
        assert parsed[0]["confidence_score"] == 0.95

    def test_parse_json_in_markdown_block(self, xai_client):
        """Test parsing JSON wrapped in markdown code blocks."""
        json_content = [{
            "cleaned_text": "Test note",
            "category": "General",
            "date": "2025-01-01",
            "timestamp": "12:00:00"
        }]

        mock_response = {
            "choices": [{
                "message": {
                    "content": f"```json\n{json.dumps(json_content)}\n```"
                }
            }]
        }

        parsed = xai_client._parse_response(mock_response)

        assert len(parsed) == 1
        assert parsed[0]["cleaned_text"] == "Test note"

    def test_parse_dict_converts_to_list(self, xai_client):
        """Test that a single dict response is converted to a list."""
        mock_response = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "cleaned_text": "Single note",
                        "category": "General",
                        "date": "2025-01-01",
                        "timestamp": "12:00:00"
                    })
                }
            }]
        }

        parsed = xai_client._parse_response(mock_response)

        assert isinstance(parsed, list)
        assert len(parsed) == 1

    def test_parse_invalid_category_defaults_to_general(self, xai_client):
        """Test that invalid categories default to 'General'."""
        mock_response = {
            "choices": [{
                "message": {
                    "content": json.dumps([{
                        "cleaned_text": "Test note",
                        "category": "InvalidCategory",
                        "date": "2025-01-01",
                        "timestamp": "12:00:00"
                    }])
                }
            }]
        }

        parsed = xai_client._parse_response(mock_response)

        assert parsed[0]["category"] == "General"

    def test_parse_missing_confidence_defaults(self, xai_client):
        """Test that missing confidence score gets default value."""
        mock_response = {
            "choices": [{
                "message": {
                    "content": json.dumps([{
                        "cleaned_text": "Test note",
                        "category": "General",
                        "date": "2025-01-01",
                        "timestamp": "12:00:00"
                    }])
                }
            }]
        }

        parsed = xai_client._parse_response(mock_response)

        assert "confidence_score" in parsed[0]
        assert parsed[0]["confidence_score"] == 0.75  # Default

    def test_parse_confidence_score_clamped(self, xai_client):
        """Test that confidence scores are clamped to 0-1 range."""
        mock_response = {
            "choices": [{
                "message": {
                    "content": json.dumps([{
                        "cleaned_text": "Test note",
                        "category": "General",
                        "date": "2025-01-01",
                        "timestamp": "12:00:00",
                        "confidence_score": 1.5  # Over 1.0
                    }])
                }
            }]
        }

        parsed = xai_client._parse_response(mock_response)

        assert parsed[0]["confidence_score"] == 1.0

    def test_parse_multiple_notes(self, xai_client):
        """Test parsing multiple notes in response."""
        mock_response = {
            "choices": [{
                "message": {
                    "content": json.dumps([
                        {
                            "cleaned_text": "Note 1",
                            "category": "General",
                            "date": "2025-01-01",
                            "timestamp": "10:00:00"
                        },
                        {
                            "cleaned_text": "Note 2",
                            "category": "Pricing",
                            "date": "2025-01-01",
                            "timestamp": "11:00:00"
                        }
                    ])
                }
            }]
        }

        parsed = xai_client._parse_response(mock_response)

        assert len(parsed) == 2
        assert parsed[0]["cleaned_text"] == "Note 1"
        assert parsed[1]["category"] == "Pricing"

    def test_parse_invalid_json_raises_error(self, xai_client):
        """Test that invalid JSON raises ValueError."""
        mock_response = {
            "choices": [{
                "message": {
                    "content": "This is not valid JSON"
                }
            }]
        }

        with pytest.raises(ValueError, match="Invalid API response format"):
            xai_client._parse_response(mock_response)

    def test_parse_missing_required_fields_raises_error(self, xai_client):
        """Test that missing required fields raises ValueError."""
        mock_response = {
            "choices": [{
                "message": {
                    "content": json.dumps([{
                        "cleaned_text": "Test note",
                        # Missing category, date, timestamp
                    }])
                }
            }]
        }

        with pytest.raises(ValueError, match="Missing required fields"):
            xai_client._parse_response(mock_response)


class TestXAIClientBuildPrompt:
    """Test prompt building."""

    def test_build_prompt_includes_categories(self, xai_client):
        """Test that prompt includes all categories."""
        prompt = xai_client._build_prompt("Test notes")

        # Check that some known categories are in the prompt
        assert "General" in prompt
        assert "Pricing" in prompt
        assert "Schedule" in prompt
        assert "Action Items" in prompt

    def test_build_prompt_includes_instructions(self, xai_client):
        """Test that prompt includes key instructions."""
        prompt = xai_client._build_prompt("Test notes")

        assert "clean" in prompt.lower()
        assert "categorize" in prompt.lower()
        assert "JSON" in prompt or "json" in prompt


class TestXAIClientConfiguration:
    """Test client configuration."""

    def test_init_without_api_key_raises_error(self):
        """Test that initialization without API key raises error."""
        with patch('api.xai_client.XAI_API_KEY', None):
            with pytest.raises(ValueError, match="XAI_API_KEY not configured"):
                XAIClient(api_key=None)

    def test_init_with_api_key(self):
        """Test initialization with API key."""
        client = XAIClient(api_key="test_key")
        assert client.api_key == "test_key"

    def test_default_settings(self, xai_client):
        """Test that default settings are configured."""
        assert xai_client.max_retries == 3
        assert xai_client.timeout == 30
        assert len(xai_client.retry_delays) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
