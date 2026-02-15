# Requirements Document: Bharatam AI

## Project Overview

**Bharatam AI** is a conversational AI assistant that helps Indian citizens discover government welfare schemes they're eligible for. The system addresses the accessibility gap in government information by providing personalized, conversational guidance in English and Hindi.

**Hackathon MVP Scope:** Text-based conversational interface with AI-enhanced natural language understanding, rule-based eligibility determination, and semantic search over a curated dataset of 8 government schemes.

---

## Problem Statement

Millions of eligible Indian citizens miss out on government benefits because:
- Scheme information is scattered across complex websites and PDFs
- Eligibility criteria are difficult to understand
- Language barriers prevent access
- No personalized guidance exists

---

## Solution

A conversational AI assistant that:
1. Asks simple questions to understand user needs
2. Extracts information from natural language (AI-powered)
3. Determines eligibility using rule-based logic
4. Uses semantic search to find relevant schemes
5. Explains recommendations in plain language
6. Provides actionable next steps

---

## User Stories

### 1. Natural Conversation
**As a user**, I want to provide my information in natural language, so that I don't have to answer rigid questions one by one.

**Acceptance Criteria:**
- System accepts free-form text input
- AI extracts structured data (age, state, education, income, etc.)
- Falls back to guided questions if AI confidence is low
- Supports mixed Hindi-English input

### 2. Eligibility Determination
**As a user**, I want to know which schemes I'm eligible for based on my situation, so that I can apply for relevant benefits.

**Acceptance Criteria:**
- System evaluates all schemes against user profile
- Filters based on age, state, education, income, category, gender, occupation
- Returns all applicable schemes ranked by relevance
- Provides clear eligibility explanations

### 3. Personalized Explanations
**As a user**, I want to understand why I'm eligible in simple language, so that I can trust the recommendation.

**Acceptance Criteria:**
- AI generates conversational explanations (with template fallback)
- Uses non-technical language
- References specific user attributes that match requirements
- Available in English and Hindi

### 4. Scheme Discovery
**As a user**, I want to search for schemes by topic or need, so that I can explore available options.

**Acceptance Criteria:**
- Semantic search using FAISS vector database
- Filters by state, category, age
- Returns relevant schemes with similarity scores
- Fast response time (<100ms)

### 5. Actionable Guidance
**As a user**, I want clear next steps on how to apply, so that I can complete the application process.

**Acceptance Criteria:**
- Lists required documents
- Provides application portal URL
- Shows deadlines if applicable
- Highlights common mistakes to avoid

---

## Functional Requirements

### FR1: Conversation Management
- Start/end conversation sessions
- Maintain session state (30-minute timeout)
- Track conversation history
- Support language switching (English/Hindi)

### FR2: Natural Language Understanding (AI-Enhanced)
- Extract entities from free-form text
- Confidence scoring (threshold: 0.6)
- Automatic fallback to rule-based extraction
- Handle partial information

### FR3: Eligibility Engine (Rule-Based)
- Deterministic matching on all criteria
- Rank schemes by number of matching criteria
- Generate human-readable explanations
- Handle missing information gracefully

### FR4: Knowledge Base (RAG System)
- FAISS vector database for semantic search
- Sentence-transformers for embeddings
- Metadata filtering (state, category, age)
- Index persistence (save/load)

### FR5: API Endpoints
- Conversation: start, message, get state, end
- Schemes: list, get, search, check eligibility, stats
- AI status: check if AI features are enabled

### FR6: Web Interface
- Modern, responsive chat UI
- Real-time conversation
- Language switching
- Scheme display with categories
- Mobile-friendly design

---

## Non-Functional Requirements

### NFR1: Performance
- Response time: <5 seconds (with AI), <1 second (without AI)
- Search time: <100ms per query
- Support concurrent users

### NFR2: Reliability
- System works perfectly without AI (automatic fallback)
- No crashes on AI failure
- Graceful error handling
- 100% uptime for core features

### NFR3: Security
- No storage of PII beyond active session
- Session data deleted on conversation end
- No authentication required
- API key stored securely in environment variables

### NFR4: Usability
- Simple, intuitive interface
- Clear error messages
- Consistent terminology
- Accessible design

### NFR5: Maintainability
- Clean code structure
- Comprehensive documentation
- Unit tests for core functionality
- Modular architecture

---

## Technical Constraints

### Must Have:
- Python 3.10+
- FastAPI for backend
- FAISS for vector search
- Sentence-transformers for embeddings
- OpenAI API for AI features (optional)

### Nice to Have:
- Redis for session persistence (future)
- Voice interface (future)
- Additional regional languages (future)
- Property-based testing (future)

---

## Success Criteria

### Minimum Viable Product (MVP):
1. ✅ Working conversation flow
2. ✅ Rule-based eligibility determination
3. ✅ Semantic search over 8 schemes
4. ✅ AI-enhanced NLU (optional, with fallback)
5. ✅ Web interface
6. ✅ English and Hindi support
7. ✅ Comprehensive documentation

### Demonstration Goals:
1. Show natural language understanding
2. Compare AI vs rule-based flow
3. Demonstrate mixed language support
4. Show graceful AI fallback
5. Prove meaningful use of AI

---

## Out of Scope (Future Enhancements)

- Voice interface (STT/TTS)
- Regional languages beyond Hindi
- Large-scale scheme database (100+)
- Redis-based session persistence
- Advanced caching
- Mobile app
- User authentication
- Scheme application tracking

---

## Glossary

- **NLU**: Natural Language Understanding
- **RAG**: Retrieval-Augmented Generation
- **FAISS**: Facebook AI Similarity Search
- **PII**: Personally Identifiable Information
- **MVP**: Minimum Viable Product
- **STT**: Speech-to-Text
- **TTS**: Text-to-Speech

---

**Document Status:** Final  
**Last Updated:** February 2026  
**Version:** 1.0 (Hackathon MVP)
