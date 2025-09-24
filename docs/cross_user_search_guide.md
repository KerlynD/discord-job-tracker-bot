# Cross-User Search & Privacy Guide

## Overview

The enhanced `/search` command now supports **cross-user analytics** while respecting user privacy. You can ask questions about the entire community's job search activity, like "Who is currently in the Bloomberg process?" and get anonymized results.

## 🔒 Privacy-First Design

### Default Settings
- **Default**: Cross-user search is **ENABLED** for all users
- **Anonymization**: Other users appear as "User_123" in results
- **Your Data**: Your own data always shows as "You" in results

### Opt-Out Protection
Users can disable cross-user sharing at any time using `/security`

## 🎯 Query Types

### Personal Queries (Your Data Only)
These queries only access your personal data:
```
/search How many applications do I have?
/search What's my success rate?
/search Which companies rejected me?
/search What stage am I at with Google?
```

### Cross-User Queries (Community Data)
These queries access community data (privacy-filtered):
```
/search Who is currently in the Bloomberg process?
/search How many people are interviewing at Google?
/search Which companies are most popular in the community?
/search What's the community success rate for tech companies?
/search How many users have offers from FAANG companies?
```

## 🤖 Smart Query Detection

The AI automatically detects cross-user queries based on keywords:
- **"who"** - "Who is in the Google process?"
- **"people"** - "How many people applied to Microsoft?"
- **"users"** - "Which users have offers?"
- **"everyone"** - "What's everyone's favorite season?"
- **"community"** - "What's the community success rate?"
- **"total"** - "Total applications across all users"

## 📊 Example Queries & Responses

### Company-Specific Analytics
**Query**: `/search Who is currently in the Bloomberg process?`

**Response**: 
> Currently, **User_456**, **User_789**, and **You** are in the Bloomberg interview process. User_456 is at the Phone stage, User_789 is at On-site, and you're at the OA stage.

### Aggregate Statistics
**Query**: `/search What's the community success rate for offers?`

**Response**:
> Across all community members who opted in (5 users), there's a **12.5%** offer rate with 3 offers out of 24 total applications. **Google** and **Microsoft** have the highest offer rates in our community.

### Popular Companies
**Query**: `/search Which companies are most popular?`

**Response**:
> The most popular companies in our community are:
> 1. **Google** - 8 applications across 4 users
> 2. **Microsoft** - 6 applications across 3 users  
> 3. **Bloomberg** - 5 applications across 3 users

## 🔒 Privacy Controls with `/security`

### Viewing Your Settings
```
/security
```
Shows your current privacy preferences with toggle buttons.

### Privacy Options

#### ✅ **Cross-User Search Enabled** (Default)
- Your data appears in community analytics
- You're anonymized as "User_YourID" 
- Helps build community insights
- You can see others' anonymized data too

#### ❌ **Cross-User Search Disabled**
- Your data is completely private
- Only you can search your own applications
- You won't see others' data in community queries
- Your applications won't appear in others' searches

### What Data is Shared?

When **enabled**, other users can see:
- ✅ Your company names and application stages
- ✅ Your anonymized identifier ("User_123")
- ✅ Aggregate statistics you contribute to

When **enabled**, other users **CANNOT** see:
- ❌ Your real Discord username
- ❌ Your specific Discord user ID
- ❌ Any personal information
- ❌ Private details beyond job applications

## 🛡️ Security Features

### Data Anonymization
- Real user IDs are masked as "User_123"
- Only the requesting user sees their own data as "You"
- No personal information is ever shared

### Opt-Out Respect
- Users who opt out are completely excluded
- Their data never appears in cross-user queries
- No traces or counts include opted-out users

### Query Validation
- Harmful keywords are blocked
- No database manipulation allowed
- Safe, read-only access to anonymized data

## 📈 Use Cases

### For Job Seekers
- **Benchmark Performance**: See how your success rate compares
- **Company Insights**: Learn which companies others are interviewing with
- **Process Tracking**: Find others in similar interview stages
- **Community Support**: Connect with others interviewing at same companies

### For Study Groups
- **Progress Tracking**: Monitor group application progress
- **Company Popularity**: See trending companies among peers
- **Success Rates**: Understand conversion rates across the group
- **Stage Analysis**: See where people typically get stuck

## 🔄 Migration & Setup

### For Existing Users
- All existing users default to **ENABLED** for cross-user search
- Use `/security` to opt out if desired
- No data is shared until you explicitly search for community data

### For New Users
- New users default to **ENABLED**
- Can change preferences immediately using `/security`
- Privacy settings persist across bot restarts

## 💡 Tips for Effective Queries

### Cross-User Query Phrases
- Start with "Who", "How many people", "Which users"
- Use "community", "everyone", "total", "all users"
- Ask about "others" or "people" specifically

### Personal Query Phrases  
- Use "I", "my", "me" for personal data
- Ask about "my applications", "my success rate"
- Company-specific: "my Google application"

### Mixed Queries
- "How does my success rate compare to the community?"
- "Am I the only one interviewing at this company?"

## 🚀 Future Enhancements

Potential future features (feedback welcome):
- **Role-based filtering**: "Who else is applying for SWE roles?"
- **Timeline analytics**: "What's the average time from application to offer?"
- **Geographic insights**: "Applications by location" (if location data added)
- **Skill-based matching**: "Others with similar tech stacks"

## 🆘 Troubleshooting

### "No community data available"
- Not enough users have opted in to cross-user search
- Encourage others to use `/security` to enable sharing

### "Only showing your data"  
- Your query was detected as personal rather than cross-user
- Try rephrasing with "who", "people", or "community"

### Privacy concerns
- Use `/security` to review and change your preferences
- Remember: data is always anonymized for others
- You control your participation completely

---

*This feature respects user privacy while enabling powerful community insights. Have questions? Use `/search` to ask the AI directly!*
