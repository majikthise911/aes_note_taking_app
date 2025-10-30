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
5. Return valid JSON format

Predefined categories: {categories_str}

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

Return format (JSON array):
[
  {{
    "cleaned_text": "Properly formatted note with bullet points and structure",
    "category": "Category Name",
    "date": "{datetime.now().strftime('%Y-%m-%d')}",
    "timestamp": "{datetime.now().strftime('%H:%M:%S')}"
  }}
]

If multiple distinct notes are provided, return multiple JSON objects in the array.
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
                if not all(
                    key in note
                    for key in ["cleaned_text", "category", "date", "timestamp"]
                ):
                    raise ValueError("Missing required fields in API response")

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
