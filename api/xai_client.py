"""
xAI API client for note processing with Grok.
"""
import json
import requests
from datetime import datetime
from typing import List, Dict, Optional
from time import sleep

from config.settings import (
    XAI_API_KEY,
    XAI_API_URL,
    XAI_MODEL,
    API_MAX_RETRIES,
    API_RETRY_DELAYS,
    API_TIMEOUT,
)
from config.categories import get_categories_list, validate_category
from utils.logger import logger


class XAIClient:
    """
    Client for interacting with xAI's Grok API.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize xAI client.

        Args:
            api_key: xAI API key (defaults to settings)
        """
        self.api_key = api_key or XAI_API_KEY
        self.api_url = XAI_API_URL
        self.model = XAI_MODEL
        self.max_retries = API_MAX_RETRIES
        self.retry_delays = API_RETRY_DELAYS
        self.timeout = API_TIMEOUT

        if not self.api_key:
            raise ValueError("XAI_API_KEY not configured")

    def _build_prompt(self, raw_notes: str) -> str:
        """
        Build the complete prompt for the API.

        Args:
            raw_notes: Raw note text from user

        Returns:
            Formatted prompt string
        """
        categories = get_categories_list()
        categories_str = ", ".join(categories)

        system_message = f"""You are a professional note-taking assistant. Your task is to:
1. Clean the provided raw notes for grammar, structure, and clarity
2. Categorize each note under ONE of the predefined categories
3. Preserve the original meaning and technical details
4. Format the cleaned text with proper bullet points and structure
5. Assign a confidence score (0.0-1.0) for your categorization
6. Generate a clarifying question if confidence is below 0.8
7. Return valid JSON format

Predefined categories: {categories_str}

CRITICAL: "Action Items" Category Rules
The "Action Items" category is ONLY for discrete, assignable tasks with clear ownership. Use this category ONLY when the note contains:
✅ Specific assignee/owner (e.g., "AES to", "Pre to", "JC to", "John needs to", "Team must")
✅ Clear action verb (schedule, complete, submit, review, send, follow up, etc.)
✅ Definite task or deliverable

Examples of Action Items:
- "AES to schedule meeting with engineering team by EOW"
- "Pre to submit revised drawings by Friday"
- "JC needs to follow up with vendor on pricing"
- "Need to schedule site visit with structural engineer"
- "Team must complete geotech report by Q3"

Examples that are NOT Action Items (use appropriate category instead):
- "Discussed engineering timelines" → Schedule or Engineering
- "Budget looks tight" → Pricing or Risk Register
- "Meeting scheduled for next week" → Schedule or relevant technical category
- "Review needed for structural design" → Structural (unless it says WHO needs to review)
- "Vendor submitted pricing" → Pricing or Contracting

If a note is general information, status updates, or observations without a specific assigned task, use the appropriate technical category (Schedule, Pricing, Engineering, etc.) NOT "Action Items".

FORMATTING REQUIREMENTS:
- Organize information into clear bullet points using "•" or "-"
- Group related information under topic headings when appropriate
- Maintain proper indentation for sub-points (use 2-4 spaces)
- Keep bullets aligned and readable
- Use line breaks between different topics or sections
- Avoid creating walls of text - break content into digestible chunks

Example of good formatting:
"• Main topic 1
  - Sub-point with details
  - Another sub-point
• Main topic 2
  - Related detail
  - Additional information"

CONFIDENCE SCORE GUIDELINES:
- 0.9-1.0: Very confident - clear categorization, unambiguous content
- 0.7-0.89: Confident - good categorization, minor ambiguity
- 0.5-0.69: Uncertain - could fit multiple categories
- 0.0-0.49: Low confidence - unclear or spans multiple domains

CLARIFYING QUESTIONS:
- Only provide if confidence < 0.8
- Ask specific multiple-choice questions to clarify categorization
- Format: "This note mentions [X] and [Y]. Which aspect is more important: A) [X focus] B) [Y focus]?"
- Keep questions concise and actionable

CRITICAL: When to Create Multiple Notes vs Keep as One

GUIDING PRINCIPLE: Notes from the same meeting/call/discussion should stay together, even if they cover multiple technical topics.

KEEP AS ONE NOTE when:
- All information is from the same meeting/call/discussion
- Multiple bullet points about related work (even across different technical areas)
- Context from one date/timeframe with various updates
- A collection of updates that naturally go together
- Date-stamped observations that share context

Example 1 - KEEP AS ONE NOTE:
"2025-08-06 Morning Call - Primoris Review:
• Pricing: 61.2 cents/W competitive with internal 73.4 cents/W
• Schedule: Need to schedule internal estimating call on Redonda
• Technical: Construction spares at 0.4%, module washing excluded
• Follow-up: Verify geotech data, add contingency if needed"
→ ONE NOTE (one meeting, multiple topics)
Category: Choose the PRIMARY focus (probably "Pricing" or "General")

Example 2 - KEEP AS ONE NOTE:
"Met with vendor about project status. Discussed pricing at 61.2 cents/W. Reviewed structural design concerns. Budget approved pending engineering review. AES to follow up on drawings by Friday."
→ ONE NOTE (single meeting with multiple agenda items)

Example 3 - TWO NOTES (different contexts):
"Morning meeting: Budget approved at 61.2 cents/W. AES to schedule follow-up.

---

Afternoon call with engineering: Structural design needs major revision. PRE to provide updated drawings."
→ TWO NOTES (different meetings/calls)

ONLY SPLIT INTO MULTIPLE NOTES when:
- Clearly different meetings/calls/discussions
- Explicit separators: "---", "Later that day:", "Afternoon meeting:", etc.
- Notes from obviously different dates/contexts
- User explicitly indicates separation with line breaks + context change

NEVER SPLIT:
- Individual bullet points from same context
- Sentences within same paragraph
- Related updates from same source/time

CATEGORIZATION with Multiple Topics:
- Choose the PRIMARY/DOMINANT category
- If a meeting covers budget (60%) and schedule (40%), choose "Pricing"
- Don't create separate notes just because multiple categories mentioned
- Use best judgment for the MAIN focus

Return format (JSON array):
[
  {{
    "cleaned_text": "Properly formatted note with bullet points and structure",
    "category": "Primary Category Name",
    "confidence_score": 0.85,
    "clarifying_question": "Optional question if confidence < 0.8, otherwise null",
    "date": "{datetime.now().strftime('%Y-%m-%d')}",
    "timestamp": "{datetime.now().strftime('%H:%M:%S')}"
  }}
]

Default to FEWER, MORE COMPREHENSIVE notes rather than many small fragments.
Prefer 1-3 notes per user submission, not 10-20 fragments.
"""
        return system_message

    def _make_request(self, raw_notes: str) -> Dict:
        """
        Make API request with retry logic.

        Args:
            raw_notes: Raw note text

        Returns:
            API response dictionary

        Raises:
            requests.RequestException: If all retries fail
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        system_prompt = self._build_prompt(raw_notes)

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Raw Notes:\n{raw_notes}"},
            ],
            "temperature": 0.3,  # Lower temperature for more consistent output
        }

        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    self.api_url,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                return response.json()

            except requests.RequestException as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    delay = self.retry_delays[attempt]
                    sleep(delay)
                    continue
                else:
                    break

        raise last_error

    def _parse_response(self, response: Dict) -> List[Dict]:
        """
        Parse API response and extract cleaned notes.

        Args:
            response: API response dictionary

        Returns:
            List of cleaned note dictionaries

        Raises:
            ValueError: If response format is invalid
        """
        try:
            # Extract content from response
            content = response["choices"][0]["message"]["content"]

            # Try to parse as JSON
            # The API might return the JSON in markdown code blocks
            if "```json" in content:
                # Extract JSON from markdown code block
                start = content.find("```json") + 7
                end = content.find("```", start)
                content = content[start:end].strip()
            elif "```" in content:
                # Generic code block
                start = content.find("```") + 3
                end = content.find("```", start)
                content = content[start:end].strip()

            parsed = json.loads(content)

            # Ensure it's a list
            if isinstance(parsed, dict):
                parsed = [parsed]

            # Validate each note has required fields and valid category
            for note in parsed:
                # Check required fields
                required_fields = ["cleaned_text", "category", "date", "timestamp"]
                if not all(key in note for key in required_fields):
                    raise ValueError("Missing required fields in API response")

                # Validate and set defaults for optional fields
                if "confidence_score" not in note or note["confidence_score"] is None:
                    note["confidence_score"] = 0.75  # Default moderate confidence

                if "clarifying_question" not in note:
                    note["clarifying_question"] = None

                # Ensure confidence_score is a float between 0 and 1
                try:
                    note["confidence_score"] = float(note["confidence_score"])
                    note["confidence_score"] = max(0.0, min(1.0, note["confidence_score"]))
                except (ValueError, TypeError):
                    logger.warning(f"Invalid confidence score, defaulting to 0.75")
                    note["confidence_score"] = 0.75

                # Validate category and default to "General" if invalid
                if not validate_category(note["category"]):
                    logger.warning(
                        f"Invalid category '{note['category']}' returned by API. "
                        f"Defaulting to 'General'."
                    )
                    note["category"] = "General"

            return parsed

        except (KeyError, json.JSONDecodeError, ValueError) as e:
            raise ValueError(f"Invalid API response format: {e}")

    def process_notes(self, raw_notes: str) -> List[Dict]:
        """
        Process raw notes through the xAI API.

        Args:
            raw_notes: Raw note text from user

        Returns:
            List of dictionaries with cleaned notes:
            [
                {
                    "cleaned_text": str,
                    "category": str,
                    "date": str (YYYY-MM-DD),
                    "timestamp": str (HH:MM:SS)
                },
                ...
            ]

        Raises:
            requests.RequestException: If API request fails after retries
            ValueError: If response format is invalid
        """
        response = self._make_request(raw_notes)
        cleaned_notes = self._parse_response(response)
        return cleaned_notes

    def test_connection(self) -> bool:
        """
        Test API connection.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.process_notes("Test connection")
            return True
        except Exception:
            return False
