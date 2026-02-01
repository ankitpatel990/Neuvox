"""
PostgreSQL Database Module.

Provides connection management and CRUD operations for:
- Conversations
- Messages
- Extracted Intelligence
"""

from typing import Dict, List, Optional, Any
import os
from contextlib import contextmanager

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Global engine and session factory
engine = None
SessionLocal = None


def init_engine() -> None:
    """
    Initialize SQLAlchemy engine from configuration.
    
    Raises:
        ValueError: If POSTGRES_URL is not configured
    """
    global engine, SessionLocal
    
    if engine is not None:
        return
    
    postgres_url = settings.POSTGRES_URL
    
    if not postgres_url:
        logger.warning("POSTGRES_URL not configured. Database operations will fail.")
        return
    
    try:
        engine = create_engine(
            postgres_url,
            pool_pre_ping=True,  # Verify connections before using
            pool_size=5,
            max_overflow=10,
            echo=False,  # Set to True for SQL debugging
        )
        SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
        logger.info("PostgreSQL engine initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize PostgreSQL engine: {e}")
        raise


def get_db_connection():
    """
    Get PostgreSQL database connection.
    
    Returns:
        Database connection object
        
    Raises:
        ConnectionError: If database connection fails
        ValueError: If POSTGRES_URL is not configured
    """
    if engine is None:
        init_engine()
    
    if engine is None:
        raise ConnectionError("PostgreSQL engine not initialized. Check POSTGRES_URL configuration.")
    
    try:
        return engine.connect()
    except SQLAlchemyError as e:
        logger.error(f"Failed to get database connection: {e}")
        raise ConnectionError(f"Database connection failed: {e}") from e


@contextmanager
def get_db_session():
    """
    Get database session context manager.
    
    Yields:
        SQLAlchemy Session
        
    Example:
        with get_db_session() as session:
            # Use session
            pass
    """
    if SessionLocal is None:
        init_engine()
    
    if SessionLocal is None:
        raise ConnectionError("PostgreSQL session factory not initialized. Check POSTGRES_URL configuration.")
    
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_database() -> None:
    """
    Initialize database with schema.
    
    Creates tables:
    - conversations
    - messages
    - extracted_intelligence
    
    Also creates required indexes.
    
    Raises:
        ConnectionError: If database connection fails
        SQLAlchemyError: If schema creation fails
    """
    if engine is None:
        init_engine()
    
    if engine is None:
        raise ConnectionError("PostgreSQL engine not initialized. Check POSTGRES_URL configuration.")
    
    # Define schema statements in order
    schema_statements = [
        # Create tables first
        """
        CREATE TABLE IF NOT EXISTS conversations (
            id SERIAL PRIMARY KEY,
            session_id VARCHAR(255) UNIQUE NOT NULL,
            language VARCHAR(10) NOT NULL,
            persona VARCHAR(50),
            scam_detected BOOLEAN DEFAULT FALSE,
            confidence FLOAT,
            turn_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            conversation_id INTEGER REFERENCES conversations(id) ON DELETE CASCADE,
            turn_number INTEGER NOT NULL,
            sender VARCHAR(50) NOT NULL,
            message TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS extracted_intelligence (
            id SERIAL PRIMARY KEY,
            conversation_id INTEGER REFERENCES conversations(id) ON DELETE CASCADE,
            upi_ids TEXT[],
            bank_accounts TEXT[],
            ifsc_codes TEXT[],
            phone_numbers TEXT[],
            phishing_links TEXT[],
            extraction_confidence FLOAT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        # Create indexes after tables
        "CREATE INDEX IF NOT EXISTS idx_session_id ON conversations(session_id)",
        "CREATE INDEX IF NOT EXISTS idx_conversation_id ON messages(conversation_id)",
        "CREATE INDEX IF NOT EXISTS idx_created_at ON conversations(created_at)",
        "CREATE INDEX IF NOT EXISTS idx_scam_detected ON conversations(scam_detected)",
    ]
    
    try:
        with engine.begin() as conn:  # Use begin() for automatic transaction management
            for statement in schema_statements:
                statement = statement.strip()
                if statement:
                    try:
                        conn.execute(text(statement))
                    except SQLAlchemyError as e:
                        # Ignore "already exists" errors
                        error_str = str(e).lower()
                        if "already exists" not in error_str and "duplicate" not in error_str:
                            logger.warning(f"Schema creation warning for statement: {e}")
                            # Don't fail on index creation errors if table doesn't exist yet
                            if "does not exist" in error_str and "index" in statement.lower():
                                logger.debug(f"Skipping index creation (table may not exist yet): {e}")
                            else:
                                raise
            # Transaction commits automatically with 'begin()' context manager
        logger.info("Database schema initialized successfully")
    except SQLAlchemyError as e:
        logger.error(f"Failed to initialize database schema: {e}")
        raise


def verify_schema() -> bool:
    """
    Verify that all required tables and indexes exist.
    
    Returns:
        True if schema is complete, False otherwise
    """
    if engine is None:
        return False
    
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        required_tables = ['conversations', 'messages', 'extracted_intelligence']
        missing_tables = [t for t in required_tables if t not in tables]
        
        if missing_tables:
            logger.warning(f"Missing tables: {missing_tables}")
            return False
        
        # Check indexes
        indexes = inspector.get_indexes('conversations')
        index_names = [idx['name'] for idx in indexes]
        required_indexes = ['idx_session_id', 'idx_created_at', 'idx_scam_detected']
        missing_indexes = [idx for idx in required_indexes if idx not in index_names]
        
        if missing_indexes:
            logger.warning(f"Missing indexes on conversations: {missing_indexes}")
        
        return True
    except Exception as e:
        logger.error(f"Failed to verify schema: {e}")
        return False


def save_conversation(session_id: str, conversation_data: Dict[str, Any]) -> int:
    """
    Save conversation to PostgreSQL.
    
    Implements AC-2.3.3: PostgreSQL stores complete logs.
    
    Args:
        session_id: Unique session identifier
        conversation_data: Conversation data including:
            - language: Detected language
            - persona: Active persona name
            - scam_confidence: Detection confidence
            - turn_count: Number of turns
            - messages: List of message dicts
            - extracted_intel: Optional intelligence data
            
    Returns:
        Conversation ID (0 if failed)
    """
    if engine is None:
        init_engine()
    
    if engine is None:
        logger.error("Cannot save conversation: Database not initialized")
        return 0
    
    try:
        with engine.connect() as conn:
            # Check if conversation already exists
            check_sql = text(
                "SELECT id FROM conversations WHERE session_id = :session_id"
            )
            result = conn.execute(check_sql, {"session_id": session_id})
            existing = result.fetchone()
            
            if existing:
                # Update existing conversation
                update_sql = text("""
                    UPDATE conversations
                    SET language = :language,
                        persona = :persona,
                        scam_detected = :scam_detected,
                        confidence = :confidence,
                        turn_count = :turn_count,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE session_id = :session_id
                    RETURNING id
                """)
                result = conn.execute(update_sql, {
                    "session_id": session_id,
                    "language": conversation_data.get("language", "en"),
                    "persona": conversation_data.get("persona"),
                    "scam_detected": conversation_data.get("scam_confidence", 0) >= 0.7,
                    "confidence": conversation_data.get("scam_confidence", 0.0),
                    "turn_count": conversation_data.get("turn_count", 0),
                })
                row = result.fetchone()
                conversation_id = row[0] if row else existing[0]
            else:
                # Insert new conversation
                insert_sql = text("""
                    INSERT INTO conversations 
                    (session_id, language, persona, scam_detected, confidence, turn_count)
                    VALUES (:session_id, :language, :persona, :scam_detected, :confidence, :turn_count)
                    RETURNING id
                """)
                result = conn.execute(insert_sql, {
                    "session_id": session_id,
                    "language": conversation_data.get("language", "en"),
                    "persona": conversation_data.get("persona"),
                    "scam_detected": conversation_data.get("scam_confidence", 0) >= 0.7,
                    "confidence": conversation_data.get("scam_confidence", 0.0),
                    "turn_count": conversation_data.get("turn_count", 0),
                })
                row = result.fetchone()
                conversation_id = row[0] if row else 0
            
            conn.commit()
            
            # Save messages if provided
            messages = conversation_data.get("messages", [])
            if messages and conversation_id > 0:
                save_messages(conversation_id, messages)
            
            # Save intelligence if provided
            extracted_intel = conversation_data.get("extracted_intel", {})
            extraction_confidence = conversation_data.get("extraction_confidence", 0.0)
            if extracted_intel and conversation_id > 0:
                save_intelligence(conversation_id, extracted_intel, extraction_confidence)
            
            logger.info(f"Conversation saved: session_id={session_id}, id={conversation_id}")
            return conversation_id
            
    except SQLAlchemyError as e:
        logger.error(f"Failed to save conversation: {e}")
        return 0


def get_conversation(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve conversation by session ID.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Conversation data including messages, or None if not found
    """
    if engine is None:
        init_engine()
    
    if engine is None:
        logger.error("Cannot get conversation: Database not initialized")
        return None
    
    try:
        with engine.connect() as conn:
            # Get conversation
            conv_sql = text("""
                SELECT id, session_id, language, persona, scam_detected, 
                       confidence, turn_count, created_at, updated_at
                FROM conversations
                WHERE session_id = :session_id
            """)
            result = conn.execute(conv_sql, {"session_id": session_id})
            row = result.fetchone()
            
            if not row:
                return None
            
            conversation_id = row[0]
            
            # Get messages
            msg_sql = text("""
                SELECT turn_number, sender, message, timestamp
                FROM messages
                WHERE conversation_id = :conversation_id
                ORDER BY turn_number
            """)
            msg_result = conn.execute(msg_sql, {"conversation_id": conversation_id})
            messages = [
                {
                    "turn": msg_row[0],
                    "sender": msg_row[1],
                    "message": msg_row[2],
                    "timestamp": msg_row[3].isoformat() if msg_row[3] else None,
                }
                for msg_row in msg_result.fetchall()
            ]
            
            # Get intelligence
            intel_sql = text("""
                SELECT upi_ids, bank_accounts, ifsc_codes, phone_numbers, 
                       phishing_links, extraction_confidence
                FROM extracted_intelligence
                WHERE conversation_id = :conversation_id
                ORDER BY created_at DESC
                LIMIT 1
            """)
            intel_result = conn.execute(intel_sql, {"conversation_id": conversation_id})
            intel_row = intel_result.fetchone()
            
            extracted_intel = {}
            extraction_confidence = 0.0
            if intel_row:
                extracted_intel = {
                    "upi_ids": intel_row[0] or [],
                    "bank_accounts": intel_row[1] or [],
                    "ifsc_codes": intel_row[2] or [],
                    "phone_numbers": intel_row[3] or [],
                    "phishing_links": intel_row[4] or [],
                }
                extraction_confidence = intel_row[5] or 0.0
            
            return {
                "id": row[0],
                "session_id": row[1],
                "language": row[2],
                "persona": row[3],
                "scam_detected": row[4],
                "scam_confidence": row[5],
                "turn_count": row[6],
                "created_at": row[7].isoformat() if row[7] else None,
                "updated_at": row[8].isoformat() if row[8] else None,
                "messages": messages,
                "extracted_intel": extracted_intel,
                "extraction_confidence": extraction_confidence,
            }
            
    except SQLAlchemyError as e:
        logger.error(f"Failed to get conversation: {e}")
        return None


def update_conversation(session_id: str, updates: Dict[str, Any]) -> bool:
    """
    Update existing conversation.
    
    Args:
        session_id: Session identifier
        updates: Fields to update (language, persona, scam_detected, confidence, turn_count)
        
    Returns:
        True if successful, False otherwise
    """
    if engine is None:
        init_engine()
    
    if engine is None:
        logger.error("Cannot update conversation: Database not initialized")
        return False
    
    if not updates:
        return True  # Nothing to update
    
    # Build dynamic update SQL
    allowed_fields = {"language", "persona", "scam_detected", "confidence", "turn_count"}
    update_fields = {k: v for k, v in updates.items() if k in allowed_fields}
    
    if not update_fields:
        logger.warning(f"No valid fields to update: {updates.keys()}")
        return False
    
    try:
        with engine.connect() as conn:
            # Build SET clause
            set_clauses = [f"{field} = :{field}" for field in update_fields]
            set_clauses.append("updated_at = CURRENT_TIMESTAMP")
            set_clause = ", ".join(set_clauses)
            
            update_sql = text(f"""
                UPDATE conversations
                SET {set_clause}
                WHERE session_id = :session_id
            """)
            
            params = {"session_id": session_id, **update_fields}
            result = conn.execute(update_sql, params)
            conn.commit()
            
            if result.rowcount > 0:
                logger.info(f"Conversation updated: session_id={session_id}")
                return True
            else:
                logger.warning(f"No conversation found to update: session_id={session_id}")
                return False
            
    except SQLAlchemyError as e:
        logger.error(f"Failed to update conversation: {e}")
        return False


def save_messages(conversation_id: int, messages: List[Dict[str, Any]]) -> int:
    """
    Save messages to conversation.
    
    Args:
        conversation_id: Parent conversation ID
        messages: List of message dictionaries with turn, sender, message, timestamp
        
    Returns:
        Number of messages saved
    """
    if engine is None:
        init_engine()
    
    if engine is None:
        logger.error("Cannot save messages: Database not initialized")
        return 0
    
    if not messages:
        return 0
    
    try:
        with engine.connect() as conn:
            # Get existing message turn numbers to avoid duplicates
            existing_sql = text("""
                SELECT turn_number FROM messages
                WHERE conversation_id = :conversation_id
            """)
            result = conn.execute(existing_sql, {"conversation_id": conversation_id})
            existing_turns = {row[0] for row in result.fetchall()}
            
            saved_count = 0
            for msg in messages:
                turn = msg.get("turn", 0)
                
                # Skip if this turn already exists
                if turn in existing_turns:
                    continue
                
                insert_sql = text("""
                    INSERT INTO messages (conversation_id, turn_number, sender, message)
                    VALUES (:conversation_id, :turn_number, :sender, :message)
                """)
                conn.execute(insert_sql, {
                    "conversation_id": conversation_id,
                    "turn_number": turn,
                    "sender": msg.get("sender", "unknown"),
                    "message": msg.get("message", ""),
                })
                saved_count += 1
                existing_turns.add(turn)
            
            conn.commit()
            logger.debug(f"Saved {saved_count} messages for conversation {conversation_id}")
            return saved_count
            
    except SQLAlchemyError as e:
        logger.error(f"Failed to save messages: {e}")
        return 0


def save_intelligence(
    conversation_id: int,
    intelligence: Dict[str, List[str]],
    confidence: float,
) -> int:
    """
    Save extracted intelligence to database.
    
    Args:
        conversation_id: Parent conversation ID
        intelligence: Extracted intelligence data with keys:
            - upi_ids, bank_accounts, ifsc_codes, phone_numbers, phishing_links
        confidence: Extraction confidence score
        
    Returns:
        Intelligence record ID (0 if failed)
    """
    if engine is None:
        init_engine()
    
    if engine is None:
        logger.error("Cannot save intelligence: Database not initialized")
        return 0
    
    try:
        with engine.connect() as conn:
            insert_sql = text("""
                INSERT INTO extracted_intelligence 
                (conversation_id, upi_ids, bank_accounts, ifsc_codes, 
                 phone_numbers, phishing_links, extraction_confidence)
                VALUES (:conversation_id, :upi_ids, :bank_accounts, :ifsc_codes,
                        :phone_numbers, :phishing_links, :extraction_confidence)
                RETURNING id
            """)
            
            result = conn.execute(insert_sql, {
                "conversation_id": conversation_id,
                "upi_ids": intelligence.get("upi_ids", []),
                "bank_accounts": intelligence.get("bank_accounts", []),
                "ifsc_codes": intelligence.get("ifsc_codes", []),
                "phone_numbers": intelligence.get("phone_numbers", []),
                "phishing_links": intelligence.get("phishing_links", []),
                "extraction_confidence": confidence,
            })
            
            row = result.fetchone()
            intel_id = row[0] if row else 0
            
            conn.commit()
            logger.info(f"Intelligence saved: conversation_id={conversation_id}, id={intel_id}")
            return intel_id
            
    except SQLAlchemyError as e:
        logger.error(f"Failed to save intelligence: {e}")
        return 0


def get_conversations_by_date(start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """
    Get conversations within date range.
    
    Args:
        start_date: Start date (ISO format: YYYY-MM-DD)
        end_date: End date (ISO format: YYYY-MM-DD)
        
    Returns:
        List of conversation records
    """
    if engine is None:
        init_engine()
    
    if engine is None:
        logger.error("Cannot query conversations: Database not initialized")
        return []
    
    try:
        with engine.connect() as conn:
            query_sql = text("""
                SELECT id, session_id, language, persona, scam_detected,
                       confidence, turn_count, created_at, updated_at
                FROM conversations
                WHERE created_at >= :start_date AND created_at < :end_date
                ORDER BY created_at DESC
            """)
            
            result = conn.execute(query_sql, {
                "start_date": start_date,
                "end_date": end_date,
            })
            
            conversations = []
            for row in result.fetchall():
                conversations.append({
                    "id": row[0],
                    "session_id": row[1],
                    "language": row[2],
                    "persona": row[3],
                    "scam_detected": row[4],
                    "confidence": row[5],
                    "turn_count": row[6],
                    "created_at": row[7].isoformat() if row[7] else None,
                    "updated_at": row[8].isoformat() if row[8] else None,
                })
            
            return conversations
            
    except SQLAlchemyError as e:
        logger.error(f"Failed to get conversations by date: {e}")
        return []


def get_scammer_profiles() -> List[Dict[str, Any]]:
    """
    Get aggregated scammer profiles from extracted intelligence.
    
    Returns:
        List of scammer profile data with aggregated phone numbers, UPI IDs, etc.
    """
    if engine is None:
        init_engine()
    
    if engine is None:
        logger.error("Cannot get scammer profiles: Database not initialized")
        return []
    
    try:
        with engine.connect() as conn:
            # Get all intelligence with conversation data
            query_sql = text("""
                SELECT c.session_id, c.language, c.persona, c.confidence,
                       e.upi_ids, e.bank_accounts, e.ifsc_codes, 
                       e.phone_numbers, e.phishing_links,
                       e.extraction_confidence, c.created_at
                FROM extracted_intelligence e
                JOIN conversations c ON e.conversation_id = c.id
                WHERE c.scam_detected = true
                ORDER BY c.created_at DESC
            """)
            
            result = conn.execute(query_sql)
            
            # Aggregate by phone number or UPI ID
            profiles: Dict[str, Dict[str, Any]] = {}
            
            for row in result.fetchall():
                phone_numbers = row[7] or []
                upi_ids = row[4] or []
                
                # Use first phone number or UPI as profile key
                profile_key = None
                if phone_numbers:
                    profile_key = phone_numbers[0]
                elif upi_ids:
                    profile_key = upi_ids[0]
                
                if not profile_key:
                    continue
                
                if profile_key not in profiles:
                    profiles[profile_key] = {
                        "identifier": profile_key,
                        "phone_numbers": set(),
                        "upi_ids": set(),
                        "bank_accounts": set(),
                        "ifsc_codes": set(),
                        "phishing_links": set(),
                        "languages": set(),
                        "personas_encountered": set(),
                        "session_count": 0,
                        "avg_confidence": 0.0,
                        "confidence_sum": 0.0,
                        "first_seen": row[10],
                        "last_seen": row[10],
                    }
                
                profile = profiles[profile_key]
                profile["phone_numbers"].update(phone_numbers)
                profile["upi_ids"].update(upi_ids)
                profile["bank_accounts"].update(row[5] or [])
                profile["ifsc_codes"].update(row[6] or [])
                profile["phishing_links"].update(row[8] or [])
                profile["languages"].add(row[1])
                if row[2]:
                    profile["personas_encountered"].add(row[2])
                profile["session_count"] += 1
                profile["confidence_sum"] += row[3] or 0.0
                if row[10] and row[10] < profile["first_seen"]:
                    profile["first_seen"] = row[10]
                if row[10] and row[10] > profile["last_seen"]:
                    profile["last_seen"] = row[10]
            
            # Convert sets to lists and calculate averages
            result_profiles = []
            for profile in profiles.values():
                profile["phone_numbers"] = list(profile["phone_numbers"])
                profile["upi_ids"] = list(profile["upi_ids"])
                profile["bank_accounts"] = list(profile["bank_accounts"])
                profile["ifsc_codes"] = list(profile["ifsc_codes"])
                profile["phishing_links"] = list(profile["phishing_links"])
                profile["languages"] = list(profile["languages"])
                profile["personas_encountered"] = list(profile["personas_encountered"])
                profile["avg_confidence"] = (
                    profile["confidence_sum"] / profile["session_count"]
                    if profile["session_count"] > 0 else 0.0
                )
                del profile["confidence_sum"]
                profile["first_seen"] = (
                    profile["first_seen"].isoformat() 
                    if profile["first_seen"] else None
                )
                profile["last_seen"] = (
                    profile["last_seen"].isoformat() 
                    if profile["last_seen"] else None
                )
                result_profiles.append(profile)
            
            return result_profiles
            
    except SQLAlchemyError as e:
        logger.error(f"Failed to get scammer profiles: {e}")
        return []


def delete_conversation(session_id: str) -> bool:
    """
    Delete a conversation and all related data.
    
    Args:
        session_id: Session identifier
        
    Returns:
        True if deleted, False otherwise
    """
    if engine is None:
        init_engine()
    
    if engine is None:
        logger.error("Cannot delete conversation: Database not initialized")
        return False
    
    try:
        with engine.connect() as conn:
            # CASCADE delete will handle messages and intelligence
            delete_sql = text("""
                DELETE FROM conversations
                WHERE session_id = :session_id
            """)
            result = conn.execute(delete_sql, {"session_id": session_id})
            conn.commit()
            
            if result.rowcount > 0:
                logger.info(f"Conversation deleted: session_id={session_id}")
                return True
            return False
            
    except SQLAlchemyError as e:
        logger.error(f"Failed to delete conversation: {e}")
        return False


def get_conversation_stats() -> Dict[str, Any]:
    """
    Get aggregated conversation statistics.
    
    Returns:
        Dictionary with statistics
    """
    if engine is None:
        init_engine()
    
    if engine is None:
        return {"error": "Database not initialized"}
    
    try:
        with engine.connect() as conn:
            stats_sql = text("""
                SELECT 
                    COUNT(*) as total_conversations,
                    SUM(CASE WHEN scam_detected THEN 1 ELSE 0 END) as scam_count,
                    AVG(confidence) as avg_confidence,
                    AVG(turn_count) as avg_turns,
                    COUNT(DISTINCT language) as language_count
                FROM conversations
            """)
            result = conn.execute(stats_sql)
            row = result.fetchone()
            
            if row:
                return {
                    "total_conversations": row[0] or 0,
                    "scam_count": row[1] or 0,
                    "avg_confidence": float(row[2]) if row[2] else 0.0,
                    "avg_turns": float(row[3]) if row[3] else 0.0,
                    "language_count": row[4] or 0,
                }
            
            return {
                "total_conversations": 0,
                "scam_count": 0,
                "avg_confidence": 0.0,
                "avg_turns": 0.0,
                "language_count": 0,
            }
            
    except SQLAlchemyError as e:
        logger.error(f"Failed to get conversation stats: {e}")
        return {"error": str(e)}
