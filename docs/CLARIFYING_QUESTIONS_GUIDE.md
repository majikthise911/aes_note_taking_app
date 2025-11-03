# Clarifying Questions Feature Guide

## Overview
The app now intelligently asks clarifying questions when the AI is uncertain about how to categorize your notes!

## How It Works

### 1. **Note Entry (Same as Before)**
```
You: "Reviewed Primoris bid at 61.2 cents/W. Engineering team needs
      to review structural design. Budget looks tight."
```

### 2. **AI Processing (New Intelligence)**
The AI now:
- Cleans and formats your note
- Categorizes it
- **Assigns a confidence score (0.0 - 1.0)**
- **Generates a clarifying question if uncertain**

Example AI Response:
```json
{
  "cleaned_text": "• Reviewed Primoris bid\n  - Cost: 61.2 cents/W\n• Action Items\n  - Engineering team review needed for structural design\n  - Budget appears constrained",
  "category": "Budget & Cost Analysis",
  "confidence_score": 0.65,
  "clarifying_question": "This note mentions both budget and engineering review. Which aspect is more critical: A) Cost analysis and budget concerns B) Technical/engineering review?"
}
```

### 3. **Approval View (Enhanced)**

#### High Confidence Notes (≥80%)
- Shows: 🎯 **Confidence: 95%** in green
- No questions asked
- Quick approval process

#### Medium Confidence Notes (60-79%)
- Shows: ⚠️ **Confidence: 65%** in yellow
- Displays clarifying question
- You can:
  - Adjust the category based on the question
  - Edit the note
  - Approve as-is

#### Low Confidence Notes (<60%)
- Shows: ❓ **Confidence: 45%** in red
- Strongly suggests reviewing categorization
- Clarifying question helps you make the right choice

## Confidence Score Meanings

| Score | Meaning | Action |
|-------|---------|--------|
| 90-100% | Very confident | Auto-approve safe |
| 70-89% | Confident | Quick review recommended |
| 50-69% | Uncertain | Review category carefully |
| 0-49% | Low confidence | Definitely review & adjust |

## Example Scenarios

### Scenario 1: Clear Categorization
```
Input: "Met with vendor to discuss panel pricing"
Confidence: 92%
Question: None (too clear!)
Category: Budget & Cost Analysis ✓
```

### Scenario 2: Ambiguous Note
```
Input: "Discussed engineering timelines and budget constraints with PM"
Confidence: 68%
Question: "This note mentions both schedule and budget. Which is the primary focus: A) Project timeline and schedule B) Budget and cost management?"
Category: Schedule & Timeline (you can change based on question)
```

### Scenario 3: Multi-Topic Note
```
Input: "Safety inspection flagged structural issues. Need to reallocate budget for fixes. Meeting tomorrow to discuss timeline."
Confidence: 52%
Question: "This note covers safety, budget, and schedule. What's the main concern: A) Safety & Compliance B) Budget reallocation C) Schedule adjustment?"
Category: Safety & Compliance (AI's best guess - you decide!)
```

## Benefits

1. **Faster for Clear Notes**: High-confidence notes zip through approval
2. **Smarter for Ambiguous Notes**: Questions help you categorize correctly
3. **No Interruptions During Entry**: Questions appear during approval, not while typing
4. **You're Always in Control**: Questions are suggestions - you decide!

## Database Persistence

Your confidence scores and questions are stored in the database:
```sql
notes table:
  - confidence_score: REAL (0.0 to 1.0)
  - clarifying_question: TEXT (nullable)
```

This allows you to:
- Track which notes needed clarification
- Analyze categorization patterns
- Improve the system over time

## Tips

1. **Trust High Scores**: Notes with 85%+ confidence are usually spot-on
2. **Review Medium Scores**: 60-80% means "probably right, but double-check"
3. **Read Questions**: They often highlight what made categorization tricky
4. **Adjust Freely**: The AI is helping you, not deciding for you

## Future Enhancements

Potential improvements:
- Learn from your corrections to improve future confidence scores
- Show category alternatives with their scores
- Filter approval queue by confidence level
- Analytics on categorization accuracy
