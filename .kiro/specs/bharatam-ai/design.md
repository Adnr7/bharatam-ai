# Design Document: Bharatam AI

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         User Interface                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Web Browser (HTML/CSS/JavaScript)                   │  │
│  │  - Chat interface                                    │  │
│  │  - Language selector                                 │  │
│  │  - Scheme display                                    │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────┘
                             │ HTTP/REST
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  API Layer (app/api/)                                │  │
│  │  - Conversation endpoints                            │  │
│  │  - Scheme endpoints                                  │  │
│  │  - AI status endpoint                                │  │
│  └──────────────────────────────────────────────────────┘  │
│                             │                                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  AI Enhancement Layer (OPTIONAL)                     │  │
│  │  - Natural Language Understanding                    │  │
│  │  - Explanation Generation                            │  │
│  │  - Confidence Scoring                                │  │
│  │  - Automatic Fallback                                │  │
│  └──────────────────────────────────────────────────────┘  │
│                             │                                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Service Layer (app/services/)                       │  │
│  │  ┌────────────────┬────────────────┬───────────────┐ │  │
│  │  │ Conversation   │ Eligibility    │ Knowledge     │ │  │
│  │  │ Engine         │ Engine         │ Base (RAG)    │ │  │
│  │  │ (Rule-based)   │ (Rule-based)   │ (FAISS)       │ │  │
│  │  └────────────────┴────────────────┴───────────────┘ │  │
│  └──────────────────────────────────────────────────────┘  │
│                             │                                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Data Models (app/models/)                           │  │
│  │  - UserProfile                                       │  │
│  │  - Scheme                                            │  │
│  │  - ConversationState                                 │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                      Data Storage                            │
│  ┌──────────────────┬──────────────────┬─────────────────┐ │
│  │ In-Memory        │ JSON Files       │ FAISS Index     │ │
│  │ Sessions         │ (schemes.json)   │ (embeddings)    │ │
│  └──────────────────┴──────────────────┴─────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Design

### 1. AI Enhancement Layer (EXPERIMENTAL)

**Purpose:** Optional thin layer that adds natural language understanding and generation without replacing core logic.

**Components:**
- `AIAssistant` class in `app/services/ai_assistant.py`

**Key Methods:**
```python
extract_user_info(message: str, language: str) -> (Dict, float)
  # Extracts structured data from free-form text
  # Returns: (extracted_data, confidence_score)
  # Confidence threshold: 0.6

generate_explanation(scheme, is_eligible, criteria, ...) -> str
  # Generates personalized explanation from deterministic results
  # Returns: Natural language explanation or None

is_available() -> bool
  # Checks if AI features are enabled (API key present)
```

**Safety Features:**
- Confidence scoring (0.0 to 1.0)
- Automatic fallback to rule-based logic
- Timeout protection (5 seconds)
- Comprehensive error handling
- No impact on core eligibility logic

**Integration:**
```python
# In conversation API
if ai_assistant.is_available():
    extracted, confidence = ai_assistant.extract_user_info(message)
    if confidence >= 0.6:
        use_ai_data(extracted)
    else:
        use_rule_based_extraction(message)
else:
    use_rule_based_extraction(message)
```

---

### 2. Conversation Engine

**Purpose:** Manages conversation flow and state.

**Components:**
- `ConversationEngine` class in `app/services/conversation.py`

**Key Methods:**
```python
start_conversation(language: str) -> ConversationState
  # Creates new session with unique ID
  # Returns: ConversationState with greeting

get_next_question(state: ConversationState) -> Optional[str]
  # Determines next question based on missing information
  # Priority: age → state → education → income → category → gender → occupation

is_information_complete(state: ConversationState) -> bool
  # Checks if minimum required info collected (age, state)

update_user_profile(state, field, value) -> None
  # Updates user profile field
```

**Session Management:**
- In-memory storage (Dict[session_id, ConversationState])
- 30-minute timeout
- Automatic cleanup of expired sessions

**Conversation Stages:**
1. `greeting` - Initial welcome message
2. `info_collection` - Gathering user information
3. `eligibility` - Determining eligible schemes
4. `guidance` - Providing application guidance

---

### 3. Eligibility Engine

**Purpose:** Deterministic rule-based eligibility determination.

**Components:**
- `EligibilityEngine` class in `app/services/eligibility.py`

**Key Methods:**
```python
check_single_scheme(user: UserProfile, scheme: Scheme) -> EligibilityResult
  # Checks eligibility for one scheme
  # Returns: EligibilityResult with explanation

determine_eligibility(user: UserProfile, schemes: List[Scheme]) -> List[EligibilityResult]
  # Checks all schemes, returns eligible ones ranked by relevance

generate_eligibility_explanation(scheme, is_eligible, criteria, ...) -> str
  # Generates human-readable explanation
```

**Matching Logic:**
```python
# For each criterion:
if criterion_required and user_value_missing:
    is_eligible = False
    missing_criteria.append(reason)
elif criterion_required and not matches(user_value, scheme_requirement):
    is_eligible = False
    missing_criteria.append(reason)
else:
    matching_criteria.append(reason)

# Confidence = matching_criteria / total_criteria
```

**Ranking:**
- Schemes ranked by number of matching criteria
- More matches = higher relevance

---

### 4. Knowledge Base (RAG System)

**Purpose:** Semantic search over government schemes.

**Components:**
- `KnowledgeBase` class in `app/services/knowledge_base.py`

**Key Methods:**
```python
index_schemes(schemes: List[Scheme]) -> None
  # Generates embeddings and builds FAISS index

retrieve_schemes(query: str, top_k: int, filters: Dict) -> List[Tuple[Scheme, float]]
  # Semantic search with optional filtering
  # Returns: List of (scheme, similarity_score)

save_index() / load_index() -> None / bool
  # Persist/load index to/from disk
```

**Technology:**
- **Model:** sentence-transformers/paraphrase-MiniLM-L3-v2
- **Embedding Dimension:** 384
- **Index Type:** FAISS IndexFlatL2
- **Search Time:** <100ms per query

**Searchable Text:**
```python
searchable_text = f"{scheme.name} {scheme.description} Benefits: {scheme.benefits}"
```

---

### 5. Data Models

**UserProfile:**
```python
class UserProfile:
    age: Optional[int]
    state: Optional[str]
    education_level: Optional[str]
    income_range: Optional[str]
    category: Optional[str]
    gender: Optional[str]
    occupation: Optional[str]
```

**Scheme:**
```python
class Scheme:
    id: str
    name: str
    description: str
    benefits: str
    eligibility: EligibilityCriteria
    documents_required: List[str]
    application_process: str
    official_website: str
    name_translations: Dict[str, str]
```

**EligibilityCriteria:**
```python
class EligibilityCriteria:
    min_age: Optional[int]
    max_age: Optional[int]
    states: Optional[List[str]]
    education_levels: Optional[List[str]]
    income_max: Optional[int]
    categories: Optional[List[str]]
    gender: Optional[str]
    occupations: Optional[List[str]]
```

**ConversationState:**
```python
class ConversationState:
    session_id: str
    language: str
    user_profile: UserProfile
    current_stage: str
    conversation_history: List[Message]
    asked_questions: List[str]
    created_at: datetime
    last_activity: datetime
```

---

## API Design

### Conversation Endpoints

**POST /conversation/start**
```json
Request: {"language": "en"}
Response: {
  "session_id": "uuid",
  "language": "en",
  "greeting": "Hello! I'm Bharatam AI..."
}
```

**POST /conversation/{session_id}/message**
```json
Request: {"message": "I'm 25 from Maharashtra"}
Response: {
  "session_id": "uuid",
  "response": "Great! What is your education level?",
  "next_question": "What is your education level?",
  "stage": "info_collection",
  "information_complete": false,
  "eligible_schemes": null
}
```

**GET /conversation/{session_id}**
```json
Response: {
  "session_id": "uuid",
  "language": "en",
  "current_stage": "info_collection",
  "messages_count": 5,
  "information_complete": false,
  "missing_fields": ["education_level", "income_range"],
  "user_profile": {...}
}
```

**DELETE /conversation/{session_id}**
```
Response: 204 No Content
```

**GET /conversation/ai/status**
```json
Response: {
  "enabled": true,
  "model": "gpt-3.5-turbo",
  "features": {
    "entity_extraction": true,
    "explanation_generation": true,
    "conversational_response": true
  }
}
```

### Scheme Endpoints

**GET /schemes/**
```json
Response: {
  "schemes": [...],
  "total": 8
}
```

**GET /schemes/{scheme_id}**
```json
Response: {
  "id": "pmkvy",
  "name": "Pradhan Mantri Kaushal Vikas Yojana",
  ...
}
```

**POST /schemes/search**
```json
Request: {
  "query": "skill development",
  "top_k": 5,
  "filters": {"state": "Maharashtra"}
}
Response: {
  "results": [
    {
      "scheme": {...},
      "similarity_score": 0.85
    }
  ]
}
```

---

## Data Flow

### Conversation Flow (With AI)

```
1. User: "I'm 25 from Maharashtra, graduated"
   ↓
2. AI extracts: {age: 25, state: "Maharashtra", education: "graduate"}
   Confidence: 0.95
   ↓
3. Update user profile with extracted data
   ↓
4. Check if information complete (age + state minimum)
   ↓
5. If complete: Run eligibility engine (rule-based)
   ↓
6. Get eligible schemes (deterministic results)
   ↓
7. AI generates personalized explanation
   ↓
8. Return response to user
```

### Conversation Flow (Without AI / Fallback)

```
1. User: "25"
   ↓
2. Rule-based extraction: age = 25
   ↓
3. Update user profile
   ↓
4. Check missing information
   ↓
5. Get next question: "Which state do you live in?"
   ↓
6. Return question to user
   ↓
7. Repeat until information complete
   ↓
8. Run eligibility engine
   ↓
9. Generate template explanation
   ↓
10. Return response to user
```

---

## Technology Stack

### Backend
- **Framework:** FastAPI 0.115.0
- **Language:** Python 3.10+
- **Validation:** Pydantic 2.10.0
- **Server:** Uvicorn 0.32.0

### AI/ML
- **LLM:** OpenAI GPT-3.5-turbo (optional)
- **Embeddings:** sentence-transformers 5.2.2
- **Vector DB:** FAISS 1.13.2

### Frontend
- **HTML5** - Structure
- **CSS3** - Styling with animations
- **Vanilla JavaScript** - API integration

### Testing
- **Framework:** pytest 7.4.3
- **Async:** pytest-asyncio 0.21.1
- **Property Testing:** hypothesis 6.92.1 (future)

### Data
- **Format:** JSON
- **Storage:** File-based (schemes.json)
- **Sessions:** In-memory (Dict)

---

## Security Considerations

### Data Privacy
- No PII stored beyond active session
- Sessions deleted after 30 minutes
- No authentication required
- No user tracking

### API Security
- OpenAI API key stored in environment variables
- No API key exposed to frontend
- Timeout protection on AI calls
- Rate limiting (future)

### Input Validation
- Pydantic models for all inputs
- Age validation (1-120)
- State name validation
- Enum validation for categories

---

## Performance Optimization

### Response Time
- AI extraction: 1-2 seconds (with 5s timeout)
- Rule-based extraction: <100ms
- Eligibility check: <50ms
- Semantic search: <100ms
- Total: <5 seconds (with AI), <1 second (without)

### Caching (Future)
- Redis for session persistence
- Cached embeddings
- Cached eligibility results

### Scalability (Future)
- Horizontal scaling with load balancer
- Database for schemes (PostgreSQL)
- Message queue for async processing

---

## Error Handling

### AI Failures
```python
try:
    extracted, confidence = ai_assistant.extract_user_info(message)
    if confidence >= 0.6:
        use_ai_data(extracted)
    else:
        fallback_to_rule_based()
except Exception as e:
    logger.error(f"AI extraction failed: {e}")
    fallback_to_rule_based()
```

### API Errors
- 404: Session not found
- 500: Internal server error
- Timeout: Automatic fallback
- Invalid input: Validation error with details

### User-Facing Errors
- Friendly error messages
- No technical details exposed
- Suggestions for recovery
- Automatic retry on transient failures

---

## Testing Strategy

### Unit Tests
- Data models (20 tests)
- Data loader (9 tests)
- Eligibility engine (15 tests)
- Conversation engine (43 tests)
- Knowledge base (25 tests)

### Integration Tests (Future)
- API endpoints
- End-to-end conversation flow
- AI integration with fallback

### Property-Based Tests (Future)
- Eligibility logic properties
- Conversation state transitions
- Data validation properties

---

## Deployment

### Local Development
```bash
python -m uvicorn app.main:app --reload
```

### Production (Future)
- Docker containerization
- Kubernetes orchestration
- CI/CD pipeline
- Monitoring and logging

---

## Future Enhancements

### Phase 2: Voice Interface
- Speech-to-text (Whisper)
- Text-to-speech (Google TTS)
- Audio compression for low bandwidth

### Phase 3: Scale
- 100+ schemes
- Redis session persistence
- PostgreSQL database
- Advanced caching

### Phase 4: Mobile
- React Native app
- Offline mode
- Push notifications

### Phase 5: Advanced AI
- Fine-tuned models
- Multi-turn dialogue
- Personalized recommendations
- Sentiment analysis

---

**Document Status:** Final  
**Last Updated:** February 2026  
**Version:** 1.0 (Hackathon MVP)
