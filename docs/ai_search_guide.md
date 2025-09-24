# AI-Powered Search Feature Guide

## Overview

The `/search` command uses Google's Gemini AI to let you query your job application data using natural language. Instead of learning specific filters and commands, you can ask questions like you would to a human assistant.

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Get Gemini API Key
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add it to your `.env` file:
```
GEMINI_API_KEY=your_api_key_here
```

### 3. Test Installation
```bash
python scripts/test_gemini.py
```

## Usage Examples

### Basic Queries
- `/search How many applications do I have?`
- `/search Which companies rejected me?`
- `/search What's my success rate?`

### Company-Specific Queries
- `/search How many Bloomberg interviews am I in?`
- `/search What stage am I at with Google?`
- `/search Which companies ghosted me?`

### Time-Based Analysis
- `/search How many applications did I submit this month?`
- `/search What's my most active season?`
- `/search Which applications are getting old?`

### Stage Analysis
- `/search How many people are in onsite interviews?`
- `/search What percentage of my applications reach the phone stage?`
- `/search How many offers do I have?`

### Advanced Insights
- `/search What's my conversion rate from OA to phone?`
- `/search Which season has the highest success rate?`
- `/search What companies should I follow up with?`

## Features

### 🎯 Natural Language Understanding
- Ask questions in plain English
- No need to remember specific command syntax
- Handles various phrasings of the same question

### 📊 Smart Analytics
- Calculates percentages and conversion rates
- Identifies trends and patterns
- Provides contextual insights

### 🔒 Data Privacy & Safety
- Your data stays secure (only metadata sent to AI)
- Input validation prevents harmful queries
- Graceful error handling

### ⚡ Real-Time Analysis
- Always uses your current data
- Includes all application stages and seasons
- Respects your data structure

## Data Context

The AI has access to:
- **Company names** and **job roles**
- **Application stages**: Applied, OA, Phone, On-site, Offer, Rejected, Ghosted
- **Seasons**: Summer, Fall, Winter, Full time
- **Timestamps**: When you applied and last updated
- **Statistics**: Counts by stage, success rates, etc.

## Limitations

- Requires internet connection for AI processing
- API calls cost money (minimal for personal use)
- Cannot modify data, only query it
- Limited to data in your job tracker database

## Troubleshooting

### "AI search is not available"
- Check that `GEMINI_API_KEY` is set in your `.env` file
- Verify the API key is valid
- Run `python scripts/test_gemini.py` to diagnose

### "Query contains potentially harmful keyword"
- Rephrase your question to avoid SQL-like keywords
- Use natural language instead of technical terms

### Unexpected or incorrect responses
- Be more specific in your question
- Check that your application data is correct
- Try rephrasing the query

## Cost Considerations

- Gemini API pricing is very affordable for personal use
- Each query costs fractions of a penny
- Consider setting up billing alerts if concerned

## Privacy Notes

- Only your application metadata is sent to Google's API
- No personal information like emails or addresses
- Data is used only for generating your response
- Consider this when deciding to use the feature

## Example Conversation

**User**: `/search How many onsite Bloomberg interviews are currently happening`

**Bot**: 🔍 **Search Results**
Based on your applications, you currently have **2 Bloomberg** applications in the "On-site" stage. These represent active onsite interview processes that are ongoing.

**Query**: *How many onsite Bloomberg interviews are currently happening*
*Powered by Gemini AI*

---

**User**: `/search What's my conversion rate from phone to onsite?`

**Bot**: 🔍 **Search Results**
Looking at your application pipeline, you have a **66.7%** conversion rate from phone interviews to onsite interviews. Out of 6 phone interviews completed, 4 progressed to the onsite stage. This is a strong conversion rate showing good interview performance!

**Query**: *What's my conversion rate from phone to onsite?*
*Powered by Gemini AI*
