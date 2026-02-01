# API Contract Specification: ScamShield AI
## REST API Endpoints & JSON Schemas

**Version:** 1.0.0  
**Base URL:** `https://api.scamshield.example.com/api/v1`  
**Date:** January 26, 2026  
**Protocol:** HTTPS  
**Content-Type:** application/json

---

## TABLE OF CONTENTS
1. [Authentication](#authentication)
2. [Endpoints](#endpoints)
3. [Request/Response Schemas](#schemas)
4. [Error Handling](#error-handling)
5. [Rate Limiting](#rate-limiting)
6. [Examples](#examples)

---

## AUTHENTICATION

**Phase 1:** No authentication required (competition testing)  
**Phase 2:** Bearer token authentication

```http
Authorization: Bearer {api_key}
```

---

## ENDPOINTS

### Overview

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | /honeypot/engage | Primary scam detection and engagement | No (Phase 1) |
| GET | /honeypot/session/{session_id} | Retrieve conversation history | No (Phase 1) |
| GET | /health | Service health check | No |
| POST | /honeypot/batch | Batch message processing | No (Phase 1) |

---

## 1. POST /honeypot/engage

**Description:** Detect scam messages and engage scammers with AI personas to extract intelligence.

**Endpoint:** `POST /api/v1/honeypot/engage`

### Request

**Headers:**
```http
Content-Type: application/json
Accept: application/json
```

**Body Schema:**
```json
{
  "message": {
    "type": "string",
    "required": true,
    "minLength": 1,
    "maxLength": 5000,
    "description": "The message to analyze for scam detection"
  },
  "session_id": {
    "type": "string",
    "required": false,
    "format": "uuid",
    "description": "Session ID for multi-turn conversations. Auto-generated if not provided."
  },
  "language": {
    "type": "string",
    "required": false,
    "enum": ["auto", "en", "hi"],
    "default": "auto",
    "description": "Message language. 'auto' for automatic detection."
  },
  "mock_scammer_callback": {
    "type": "string",
    "required": false,
    "format": "uri",
    "description": "Competition testing: URL to call with agent responses"
  }
}
```

**Request Example:**
```json
{
  "message": "Congratulations! You have won ₹10 lakh rupees. Share your OTP to claim the prize immediately.",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "language": "auto"
}
```

**Validation Rules:**
- `message`: Must not be empty or only whitespace
- `session_id`: Must be valid UUID v4 format (if provided)
- `language`: Must be one of: "auto", "en", "hi"
- `mock_scammer_callback`: Must be valid HTTP/HTTPS URL (if provided)

---

### Response (Scam Detected)

**Status Code:** `200 OK`

**Body Schema:**
```json
{
  "status": {
    "type": "string",
    "enum": ["success", "error"],
    "description": "Request processing status"
  },
  "scam_detected": {
    "type": "boolean",
    "description": "Whether the message was classified as a scam"
  },
  "confidence": {
    "type": "number",
    "minimum": 0.0,
    "maximum": 1.0,
    "description": "Scam detection confidence score"
  },
  "language_detected": {
    "type": "string",
    "enum": ["en", "hi", "hinglish"],
    "description": "Detected language of the message"
  },
  "session_id": {
    "type": "string",
    "format": "uuid",
    "description": "Session identifier for this conversation"
  },
  "engagement": {
    "type": "object",
    "properties": {
      "agent_response": {
        "type": "string",
        "minLength": 1,
        "maxLength": 500,
        "description": "AI agent's response to the scammer"
      },
      "turn_count": {
        "type": "integer",
        "minimum": 1,
        "maximum": 20,
        "description": "Current conversation turn number"
      },
      "max_turns_reached": {
        "type": "boolean",
        "description": "Whether maximum conversation turns reached"
      },
      "strategy": {
        "type": "string",
        "enum": ["build_trust", "express_confusion", "probe_details"],
        "description": "Current engagement strategy"
      },
      "persona": {
        "type": "string",
        "enum": ["elderly", "eager", "confused"],
        "description": "Active persona type"
      }
    },
    "required": ["agent_response", "turn_count", "max_turns_reached", "strategy"]
  },
  "extracted_intelligence": {
    "type": "object",
    "properties": {
      "upi_ids": {
        "type": "array",
        "items": {"type": "string"},
        "description": "Extracted UPI IDs (e.g., user@paytm)"
      },
      "bank_accounts": {
        "type": "array",
        "items": {"type": "string"},
        "description": "Extracted bank account numbers (9-18 digits)"
      },
      "ifsc_codes": {
        "type": "array",
        "items": {"type": "string"},
        "description": "Extracted IFSC codes (11 chars, format XXXX0XXXXXX)"
      },
      "phone_numbers": {
        "type": "array",
        "items": {"type": "string"},
        "description": "Extracted phone numbers (Indian mobile format)"
      },
      "phishing_links": {
        "type": "array",
        "items": {"type": "string", "format": "uri"},
        "description": "Extracted phishing/suspicious URLs"
      },
      "extraction_confidence": {
        "type": "number",
        "minimum": 0.0,
        "maximum": 1.0,
        "description": "Overall confidence in extracted intelligence"
      }
    },
    "required": ["upi_ids", "bank_accounts", "ifsc_codes", "phone_numbers", "phishing_links", "extraction_confidence"]
  },
  "conversation_history": {
    "type": "array",
    "items": {
      "type": "object",
      "properties": {
        "turn": {
          "type": "integer",
          "minimum": 1,
          "description": "Turn number in conversation"
        },
        "sender": {
          "type": "string",
          "enum": ["scammer", "agent"],
          "description": "Message sender"
        },
        "message": {
          "type": "string",
          "description": "Message content"
        },
        "timestamp": {
          "type": "string",
          "format": "date-time",
          "description": "Message timestamp in ISO-8601 format"
        }
      },
      "required": ["turn", "sender", "message", "timestamp"]
    },
    "description": "Complete conversation history"
  },
  "metadata": {
    "type": "object",
    "properties": {
      "processing_time_ms": {
        "type": "integer",
        "description": "Total processing time in milliseconds"
      },
      "model_version": {
        "type": "string",
        "description": "System version"
      },
      "detection_model": {
        "type": "string",
        "description": "Model used for scam detection"
      },
      "engagement_model": {
        "type": "string",
        "description": "Model used for engagement"
      }
    },
    "required": ["processing_time_ms", "model_version"]
  }
}
```

**Response Example (Scam Detected):**
```json
{
  "status": "success",
  "scam_detected": true,
  "confidence": 0.94,
  "language_detected": "en",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "engagement": {
    "agent_response": "Oh wonderful! I'm so excited! But I'm not very good with technology. Can you please tell me step by step how to claim this prize?",
    "turn_count": 1,
    "max_turns_reached": false,
    "strategy": "build_trust",
    "persona": "elderly"
  },
  "extracted_intelligence": {
    "upi_ids": [],
    "bank_accounts": [],
    "ifsc_codes": [],
    "phone_numbers": [],
    "phishing_links": [],
    "extraction_confidence": 0.0
  },
  "conversation_history": [
    {
      "turn": 1,
      "sender": "scammer",
      "message": "Congratulations! You have won ₹10 lakh rupees. Share your OTP to claim the prize immediately.",
      "timestamp": "2026-01-26T10:30:00.000Z"
    },
    {
      "turn": 1,
      "sender": "agent",
      "message": "Oh wonderful! I'm so excited! But I'm not very good with technology. Can you please tell me step by step how to claim this prize?",
      "timestamp": "2026-01-26T10:30:02.150Z"
    }
  ],
  "metadata": {
    "processing_time_ms": 1850,
    "model_version": "v1.0.0",
    "detection_model": "indic-bert",
    "engagement_model": "groq-llama-3.1-70b"
  }
}
```

---

### Response (Not Scam)

**Status Code:** `200 OK`

**Body Schema:**
```json
{
  "status": {
    "type": "string",
    "enum": ["success"],
    "description": "Request processing status"
  },
  "scam_detected": {
    "type": "boolean",
    "const": false,
    "description": "Message classified as legitimate"
  },
  "confidence": {
    "type": "number",
    "minimum": 0.0,
    "maximum": 1.0,
    "description": "Confidence that message is NOT a scam"
  },
  "language_detected": {
    "type": "string",
    "enum": ["en", "hi", "hinglish"],
    "description": "Detected language"
  },
  "session_id": {
    "type": "string",
    "format": "uuid",
    "description": "Session identifier"
  },
  "message": {
    "type": "string",
    "description": "Human-readable response"
  }
}
```

**Response Example (Not Scam):**
```json
{
  "status": "success",
  "scam_detected": false,
  "confidence": 0.12,
  "language_detected": "en",
  "session_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "message": "No scam detected. Message appears legitimate."
}
```

---

### Response (Hindi Scam Example)

**Response Example:**
```json
{
  "status": "success",
  "scam_detected": true,
  "confidence": 0.96,
  "language_detected": "hi",
  "session_id": "a1b2c3d4-e5f6-4789-a0b1-c2d3e4f5a6b7",
  "engagement": {
    "agent_response": "अरे वाह! बहुत अच्छी बात है। लेकिन मुझे समझ नहीं आ रहा, मैं OTP कैसे भेजूं? मेरा फोन बहुत पुराना है।",
    "turn_count": 1,
    "max_turns_reached": false,
    "strategy": "build_trust",
    "persona": "elderly"
  },
  "extracted_intelligence": {
    "upi_ids": [],
    "bank_accounts": [],
    "ifsc_codes": [],
    "phone_numbers": [],
    "phishing_links": [],
    "extraction_confidence": 0.0
  },
  "conversation_history": [
    {
      "turn": 1,
      "sender": "scammer",
      "message": "आप जीत गए हैं 10 लाख रुपये! अपना OTP शेयर करें।",
      "timestamp": "2026-01-26T10:35:00.000Z"
    },
    {
      "turn": 1,
      "sender": "agent",
      "message": "अरे वाह! बहुत अच्छी बात है। लेकिन मुझे समझ नहीं आ रहा, मैं OTP कैसे भेजूं? मेरा फोन बहुत पुराना है।",
      "timestamp": "2026-01-26T10:35:01.920Z"
    }
  ],
  "metadata": {
    "processing_time_ms": 1720,
    "model_version": "v1.0.0",
    "detection_model": "indic-bert",
    "engagement_model": "groq-llama-3.1-70b"
  }
}
```

---

### Response (Intelligence Extracted)

**Response Example:**
```json
{
  "status": "success",
  "scam_detected": true,
  "confidence": 0.97,
  "language_detected": "en",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "engagement": {
    "agent_response": "Thank you! I will send the money to scammer@paytm right away. Let me try now.",
    "turn_count": 8,
    "max_turns_reached": false,
    "strategy": "probe_details",
    "persona": "eager"
  },
  "extracted_intelligence": {
    "upi_ids": ["scammer@paytm", "fraudster@ybl"],
    "bank_accounts": ["1234567890123"],
    "ifsc_codes": ["SBIN0001234"],
    "phone_numbers": ["+919876543210", "9988776655"],
    "phishing_links": ["http://fake-sbi-bank.com/verify"],
    "extraction_confidence": 0.89
  },
  "conversation_history": [
    {
      "turn": 1,
      "sender": "scammer",
      "message": "You won a prize. Send OTP.",
      "timestamp": "2026-01-26T10:30:00.000Z"
    },
    {
      "turn": 1,
      "sender": "agent",
      "message": "Really? How do I claim it?",
      "timestamp": "2026-01-26T10:30:02.000Z"
    },
    {
      "turn": 2,
      "sender": "scammer",
      "message": "Pay ₹500 processing fee to scammer@paytm and call +919876543210",
      "timestamp": "2026-01-26T10:30:15.000Z"
    },
    {
      "turn": 2,
      "sender": "agent",
      "message": "Which UPI ID should I use? Can you confirm again?",
      "timestamp": "2026-01-26T10:30:17.000Z"
    },
    {
      "turn": 3,
      "sender": "scammer",
      "message": "Use scammer@paytm or fraudster@ybl. Also send to bank account 1234567890123, IFSC SBIN0001234. Visit http://fake-sbi-bank.com/verify",
      "timestamp": "2026-01-26T10:30:30.000Z"
    },
    {
      "turn": 3,
      "sender": "agent",
      "message": "Thank you! I will send the money to scammer@paytm right away.",
      "timestamp": "2026-01-26T10:30:32.000Z"
    }
  ],
  "metadata": {
    "processing_time_ms": 1950,
    "model_version": "v1.0.0",
    "detection_model": "indic-bert",
    "engagement_model": "groq-llama-3.1-70b"
  }
}
```

---

## 2. GET /honeypot/session/{session_id}

**Description:** Retrieve complete conversation history for a session.

**Endpoint:** `GET /api/v1/honeypot/session/{session_id}`

### Request

**Path Parameters:**
```json
{
  "session_id": {
    "type": "string",
    "format": "uuid",
    "required": true,
    "description": "UUID of the session to retrieve"
  }
}
```

**Headers:**
```http
Accept: application/json
```

**Request Example:**
```http
GET /api/v1/honeypot/session/550e8400-e29b-41d4-a716-446655440000
Accept: application/json
```

---

### Response (Success)

**Status Code:** `200 OK`

**Body Schema:**
```json
{
  "session_id": {
    "type": "string",
    "format": "uuid"
  },
  "language": {
    "type": "string",
    "enum": ["en", "hi", "hinglish"]
  },
  "persona": {
    "type": "string",
    "enum": ["elderly", "eager", "confused"]
  },
  "scam_confidence": {
    "type": "number",
    "minimum": 0.0,
    "maximum": 1.0
  },
  "turn_count": {
    "type": "integer",
    "minimum": 0
  },
  "conversation_history": {
    "type": "array",
    "items": {
      "type": "object",
      "properties": {
        "turn": {"type": "integer"},
        "sender": {"type": "string", "enum": ["scammer", "agent"]},
        "message": {"type": "string"},
        "timestamp": {"type": "string", "format": "date-time"}
      }
    }
  },
  "extracted_intelligence": {
    "type": "object",
    "properties": {
      "upi_ids": {"type": "array", "items": {"type": "string"}},
      "bank_accounts": {"type": "array", "items": {"type": "string"}},
      "ifsc_codes": {"type": "array", "items": {"type": "string"}},
      "phone_numbers": {"type": "array", "items": {"type": "string"}},
      "phishing_links": {"type": "array", "items": {"type": "string"}},
      "extraction_confidence": {"type": "number"}
    }
  },
  "created_at": {
    "type": "string",
    "format": "date-time"
  },
  "updated_at": {
    "type": "string",
    "format": "date-time"
  }
}
```

**Response Example:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "language": "en",
  "persona": "elderly",
  "scam_confidence": 0.94,
  "turn_count": 5,
  "conversation_history": [
    {
      "turn": 1,
      "sender": "scammer",
      "message": "You won 10 lakh!",
      "timestamp": "2026-01-26T10:30:00.000Z"
    },
    {
      "turn": 1,
      "sender": "agent",
      "message": "Really? How?",
      "timestamp": "2026-01-26T10:30:02.000Z"
    }
  ],
  "extracted_intelligence": {
    "upi_ids": ["test@paytm"],
    "bank_accounts": [],
    "ifsc_codes": [],
    "phone_numbers": [],
    "phishing_links": [],
    "extraction_confidence": 0.65
  },
  "created_at": "2026-01-26T10:30:00.000Z",
  "updated_at": "2026-01-26T10:35:15.000Z"
}
```

---

### Response (Not Found)

**Status Code:** `404 Not Found`

**Body Schema:**
```json
{
  "status": {
    "type": "string",
    "const": "error"
  },
  "error": {
    "type": "object",
    "properties": {
      "code": {"type": "string", "const": "SESSION_NOT_FOUND"},
      "message": {"type": "string"},
      "session_id": {"type": "string"}
    }
  }
}
```

**Response Example:**
```json
{
  "status": "error",
  "error": {
    "code": "SESSION_NOT_FOUND",
    "message": "No conversation found for the provided session ID",
    "session_id": "invalid-uuid-12345"
  }
}
```

---

## 3. GET /health

**Description:** Service health check for monitoring and load balancing.

**Endpoint:** `GET /api/v1/health`

### Request

**Headers:**
```http
Accept: application/json
```

**Request Example:**
```http
GET /api/v1/health
Accept: application/json
```

---

### Response (Healthy)

**Status Code:** `200 OK`

**Body Schema:**
```json
{
  "status": {
    "type": "string",
    "enum": ["healthy", "degraded", "unhealthy"]
  },
  "version": {
    "type": "string",
    "pattern": "^\\d+\\.\\d+\\.\\d+$",
    "description": "Semantic version"
  },
  "timestamp": {
    "type": "string",
    "format": "date-time"
  },
  "dependencies": {
    "type": "object",
    "properties": {
      "groq_api": {
        "type": "string",
        "enum": ["online", "offline"]
      },
      "postgres": {
        "type": "string",
        "enum": ["online", "offline"]
      },
      "redis": {
        "type": "string",
        "enum": ["online", "offline"]
      },
      "models_loaded": {
        "type": "boolean"
      }
    }
  },
  "uptime_seconds": {
    "type": "integer",
    "minimum": 0
  }
}
```

**Response Example (Healthy):**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-01-26T10:45:30.000Z",
  "dependencies": {
    "groq_api": "online",
    "postgres": "online",
    "redis": "online",
    "models_loaded": true
  },
  "uptime_seconds": 86400
}
```

**Response Example (Degraded):**
```json
{
  "status": "degraded",
  "version": "1.0.0",
  "timestamp": "2026-01-26T10:45:30.000Z",
  "dependencies": {
    "groq_api": "online",
    "postgres": "online",
    "redis": "offline",
    "models_loaded": true
  },
  "uptime_seconds": 86400
}
```

---

### Response (Unhealthy)

**Status Code:** `503 Service Unavailable`

**Body Schema:** Same as healthy response

**Response Example:**
```json
{
  "status": "unhealthy",
  "version": "1.0.0",
  "timestamp": "2026-01-26T10:45:30.000Z",
  "dependencies": {
    "groq_api": "offline",
    "postgres": "offline",
    "redis": "offline",
    "models_loaded": false
  },
  "uptime_seconds": 1200
}
```

---

## 4. POST /honeypot/batch

**Description:** Process multiple messages in batch mode.

**Endpoint:** `POST /api/v1/honeypot/batch`

### Request

**Headers:**
```http
Content-Type: application/json
Accept: application/json
```

**Body Schema:**
```json
{
  "messages": {
    "type": "array",
    "minItems": 1,
    "maxItems": 100,
    "items": {
      "type": "object",
      "properties": {
        "id": {
          "type": "string",
          "description": "Client-provided message ID"
        },
        "message": {
          "type": "string",
          "minLength": 1,
          "maxLength": 5000
        },
        "language": {
          "type": "string",
          "enum": ["auto", "en", "hi"],
          "default": "auto"
        }
      },
      "required": ["id", "message"]
    }
  }
}
```

**Request Example:**
```json
{
  "messages": [
    {
      "id": "msg-001",
      "message": "You won 10 lakh! Send OTP.",
      "language": "auto"
    },
    {
      "id": "msg-002",
      "message": "Hi, how are you doing?",
      "language": "en"
    },
    {
      "id": "msg-003",
      "message": "आप गिरफ्तार हो जाएंगे। पैसे भेजें।",
      "language": "hi"
    }
  ]
}
```

---

### Response

**Status Code:** `200 OK`

**Body Schema:**
```json
{
  "status": {
    "type": "string",
    "const": "success"
  },
  "processed": {
    "type": "integer",
    "description": "Number of messages successfully processed"
  },
  "failed": {
    "type": "integer",
    "description": "Number of messages that failed processing"
  },
  "results": {
    "type": "array",
    "items": {
      "type": "object",
      "properties": {
        "id": {"type": "string"},
        "status": {"type": "string", "enum": ["success", "error"]},
        "scam_detected": {"type": "boolean"},
        "confidence": {"type": "number"},
        "language_detected": {"type": "string"},
        "error": {
          "type": "object",
          "properties": {
            "code": {"type": "string"},
            "message": {"type": "string"}
          }
        }
      }
    }
  },
  "processing_time_ms": {
    "type": "integer"
  }
}
```

**Response Example:**
```json
{
  "status": "success",
  "processed": 3,
  "failed": 0,
  "results": [
    {
      "id": "msg-001",
      "status": "success",
      "scam_detected": true,
      "confidence": 0.95,
      "language_detected": "en"
    },
    {
      "id": "msg-002",
      "status": "success",
      "scam_detected": false,
      "confidence": 0.08,
      "language_detected": "en"
    },
    {
      "id": "msg-003",
      "status": "success",
      "scam_detected": true,
      "confidence": 0.97,
      "language_detected": "hi"
    }
  ],
  "processing_time_ms": 2350
}
```

---

## ERROR HANDLING

### Error Response Schema

All error responses follow this structure:

```json
{
  "status": {
    "type": "string",
    "const": "error"
  },
  "error": {
    "type": "object",
    "properties": {
      "code": {
        "type": "string",
        "description": "Machine-readable error code"
      },
      "message": {
        "type": "string",
        "description": "Human-readable error message"
      },
      "details": {
        "type": "object",
        "description": "Additional error context"
      }
    },
    "required": ["code", "message"]
  }
}
```

### Error Codes

| HTTP Status | Error Code | Description | Resolution |
|-------------|------------|-------------|------------|
| 400 | INVALID_REQUEST | Malformed request body | Check request schema |
| 400 | VALIDATION_ERROR | Field validation failed | Fix invalid fields |
| 400 | MESSAGE_TOO_LONG | Message exceeds 5000 chars | Shorten message |
| 400 | INVALID_SESSION_ID | Session ID format invalid | Provide valid UUID |
| 400 | INVALID_LANGUAGE | Unsupported language code | Use 'auto', 'en', or 'hi' |
| 404 | SESSION_NOT_FOUND | Session does not exist | Check session ID |
| 410 | SESSION_EXPIRED | Session expired (>1 hour old) | Start new session |
| 429 | RATE_LIMIT_EXCEEDED | Too many requests | Wait and retry |
| 500 | INTERNAL_ERROR | Server-side error | Contact support |
| 502 | LLM_API_ERROR | Groq API unavailable | Retry with backoff |
| 503 | SERVICE_UNAVAILABLE | Service temporarily down | Check /health endpoint |

### Error Response Examples

**400 Bad Request - Validation Error:**
```json
{
  "status": "error",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": {
      "field": "message",
      "issue": "Field is required but was not provided"
    }
  }
}
```

**400 Bad Request - Message Too Long:**
```json
{
  "status": "error",
  "error": {
    "code": "MESSAGE_TOO_LONG",
    "message": "Message exceeds maximum length of 5000 characters",
    "details": {
      "max_length": 5000,
      "actual_length": 6543
    }
  }
}
```

**429 Rate Limit Exceeded:**
```json
{
  "status": "error",
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit of 100 requests per minute exceeded",
    "details": {
      "retry_after_seconds": 45,
      "limit": 100,
      "window_seconds": 60
    }
  }
}
```

**500 Internal Server Error:**
```json
{
  "status": "error",
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "An unexpected error occurred while processing your request",
    "details": {
      "request_id": "req_a1b2c3d4e5",
      "timestamp": "2026-01-26T10:50:00.000Z"
    }
  }
}
```

**502 Bad Gateway - LLM API Error:**
```json
{
  "status": "error",
  "error": {
    "code": "LLM_API_ERROR",
    "message": "External LLM service (Groq) is currently unavailable",
    "details": {
      "service": "groq",
      "retry_recommended": true,
      "retry_after_seconds": 30
    }
  }
}
```

---

## RATE LIMITING

**Phase 1 Limits:**
- 100 requests per minute per IP
- 1000 requests per hour per IP
- No authentication required

**Response Headers:**
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1706270400
```

**Rate Limit Exceeded Response:**
```http
HTTP/1.1 429 Too Many Requests
Retry-After: 45
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1706270400

{
  "status": "error",
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Please retry after 45 seconds."
  }
}
```

---

## CURL EXAMPLES

### Example 1: Detect English Scam
```bash
curl -X POST https://api.scamshield.example.com/api/v1/honeypot/engage \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Congratulations! You won 10 lakh rupees. Send OTP to claim.",
    "language": "auto"
  }'
```

### Example 2: Continue Conversation
```bash
curl -X POST https://api.scamshield.example.com/api/v1/honeypot/engage \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Send money to scammer@paytm immediately!",
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "language": "en"
  }'
```

### Example 3: Detect Hindi Scam
```bash
curl -X POST https://api.scamshield.example.com/api/v1/honeypot/engage \
  -H "Content-Type: application/json" \
  -d '{
    "message": "आप गिरफ्तार हो जाएंगे। तुरंत 10000 रुपये भेजें।",
    "language": "hi"
  }'
```

### Example 4: Retrieve Session
```bash
curl -X GET https://api.scamshield.example.com/api/v1/honeypot/session/550e8400-e29b-41d4-a716-446655440000 \
  -H "Accept: application/json"
```

### Example 5: Health Check
```bash
curl -X GET https://api.scamshield.example.com/api/v1/health \
  -H "Accept: application/json"
```

### Example 6: Batch Processing
```bash
curl -X POST https://api.scamshield.example.com/api/v1/honeypot/batch \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"id": "1", "message": "You won a prize!"},
      {"id": "2", "message": "Hi, how are you?"}
    ]
  }'
```

---

## OPENAPI SPECIFICATION

**OpenAPI Version:** 3.0.3

Complete OpenAPI YAML specification available at:
`https://api.scamshield.example.com/openapi.yaml`

```yaml
openapi: 3.0.3
info:
  title: ScamShield AI API
  version: 1.0.0
  description: Agentic Honeypot System for Scam Detection & Intelligence Extraction
servers:
  - url: https://api.scamshield.example.com/api/v1
    description: Production server
paths:
  /honeypot/engage:
    post:
      summary: Detect and engage with scam messages
      operationId: engageHoneypot
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/EngageRequest'
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                oneOf:
                  - $ref: '#/components/schemas/ScamDetectedResponse'
                  - $ref: '#/components/schemas/NotScamResponse'
        '400':
          description: Bad request
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
  /health:
    get:
      summary: Health check
      operationId: healthCheck
      responses:
        '200':
          description: Service is healthy
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HealthResponse'
components:
  schemas:
    EngageRequest:
      type: object
      required:
        - message
      properties:
        message:
          type: string
          minLength: 1
          maxLength: 5000
        session_id:
          type: string
          format: uuid
        language:
          type: string
          enum: [auto, en, hi]
          default: auto
```

---

**Document Status:** Production Ready  
**Next Steps:** Implement API endpoints as per this contract  
**Testing:** Refer to EVAL_SPEC.md for API testing framework
