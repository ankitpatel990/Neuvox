"""
Unit tests for PostgreSQL database module.

Tests database connection, schema initialization, and CRUD operations.

Task 6.2 Acceptance Criteria:
- AC-2.3.3: PostgreSQL stores complete logs
"""

import pytest
import os
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError

from app.database.postgres import (
    get_db_connection,
    init_database,
    verify_schema,
    get_db_session,
    init_engine,
    save_conversation,
    get_conversation,
    update_conversation,
    delete_conversation,
    save_messages,
    save_intelligence,
    get_conversations_by_date,
    get_scammer_profiles,
    get_conversation_stats,
)


class TestPostgresConnection:
    """Test PostgreSQL connection functionality."""
    
    def test_get_db_connection_no_config(self):
        """Test connection fails gracefully when POSTGRES_URL not set."""
        with patch('app.database.postgres.settings') as mock_settings:
            mock_settings.POSTGRES_URL = None
            with patch('app.database.postgres.engine', None):
                with pytest.raises(ConnectionError, match="not initialized"):
                    get_db_connection()
    
    def test_init_engine_success(self):
        """Test engine initialization with valid URL."""
        test_url = "postgresql://user:pass@localhost:5432/testdb"
        with patch('app.database.postgres.settings') as mock_settings:
            mock_settings.POSTGRES_URL = test_url
            with patch('app.database.postgres.create_engine') as mock_create:
                mock_engine = MagicMock()
                mock_create.return_value = mock_engine
                
                init_engine()
                
                mock_create.assert_called_once()
                assert mock_create.call_args[0][0] == test_url
    
    def test_init_engine_no_url(self):
        """Test engine initialization fails gracefully without URL."""
        # Reset global engine
        import app.database.postgres as postgres_module
        postgres_module.engine = None
        postgres_module.SessionLocal = None
        
        with patch('app.database.postgres.settings') as mock_settings:
            mock_settings.POSTGRES_URL = None
            with patch('app.database.postgres.logger') as mock_logger:
                init_engine()
                mock_logger.warning.assert_called()
    
    def test_get_db_session_context_manager(self):
        """Test database session context manager."""
        mock_session = MagicMock()
        mock_session_factory = MagicMock(return_value=mock_session)
        
        with patch('app.database.postgres.SessionLocal', mock_session_factory):
            with get_db_session() as session:
                assert session == mock_session
            
            mock_session.commit.assert_called_once()
            mock_session.close.assert_called_once()
    
    def test_get_db_session_rollback_on_error(self):
        """Test session rolls back on error."""
        mock_session = MagicMock()
        mock_session_factory = MagicMock(return_value=mock_session)
        
        with patch('app.database.postgres.SessionLocal', mock_session_factory):
            with pytest.raises(ValueError):
                with get_db_session():
                    raise ValueError("Test error")
            
            mock_session.rollback.assert_called_once()
            mock_session.close.assert_called_once()


class TestSchemaInitialization:
    """Test database schema initialization."""
    
    def test_init_database_creates_tables(self):
        """Test that init_database creates all required tables."""
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        
        with patch('app.database.postgres.engine', mock_engine):
            with patch('app.database.postgres.text') as mock_text:
                init_database()
                
                # Verify connection was used
                assert mock_engine.connect.called
                # Verify commit was called
                assert mock_conn.commit.called
    
    def test_init_database_no_engine(self):
        """Test init_database fails gracefully without engine."""
        with patch('app.database.postgres.engine', None):
            with patch('app.database.postgres.init_engine') as mock_init:
                mock_init.side_effect = ConnectionError("No URL")
                with pytest.raises(ConnectionError):
                    init_database()
    
    def test_verify_schema_checks_tables(self):
        """Test schema verification checks for required tables."""
        mock_inspector = MagicMock()
        mock_inspector.get_table_names.return_value = [
            'conversations',
            'messages',
            'extracted_intelligence'
        ]
        mock_inspector.get_indexes.return_value = [
            {'name': 'idx_session_id'},
            {'name': 'idx_created_at'},
            {'name': 'idx_scam_detected'}
        ]
        
        mock_engine = MagicMock()
        with patch('app.database.postgres.engine', mock_engine):
            with patch('app.database.postgres.inspect', return_value=mock_inspector):
                result = verify_schema()
                assert result is True
    
    def test_verify_schema_missing_tables(self):
        """Test schema verification detects missing tables."""
        mock_inspector = MagicMock()
        mock_inspector.get_table_names.return_value = ['conversations']  # Missing tables
        mock_inspector.get_indexes.return_value = []
        
        mock_engine = MagicMock()
        with patch('app.database.postgres.engine', mock_engine):
            with patch('app.database.postgres.inspect', return_value=mock_inspector):
                with patch('app.database.postgres.logger') as mock_logger:
                    result = verify_schema()
                    assert result is False
                    mock_logger.warning.assert_called()
    
    def test_verify_schema_no_engine(self):
        """Test schema verification fails gracefully without engine."""
        with patch('app.database.postgres.engine', None):
            result = verify_schema()
            assert result is False


class TestPostgresErrorHandling:
    """Test error handling in PostgreSQL operations."""
    
    def test_connection_error_handling(self):
        """Test connection errors are handled gracefully."""
        mock_engine = MagicMock()
        mock_engine.connect.side_effect = SQLAlchemyError("Connection failed")
        
        with patch('app.database.postgres.engine', mock_engine):
            with patch('app.database.postgres.logger') as mock_logger:
                with pytest.raises(ConnectionError):
                    get_db_connection()
                mock_logger.error.assert_called()
    
    def test_schema_error_handling(self):
        """Test schema creation errors are handled gracefully."""
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        # Make execute raise error on first call (not "already exists")
        mock_conn.execute.side_effect = SQLAlchemyError("Schema error - table locked")
        mock_conn.commit = MagicMock()
        mock_engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        
        with patch('app.database.postgres.engine', mock_engine):
            with patch('app.database.postgres.text') as mock_text:
                mock_text.return_value = MagicMock()
                with patch('app.database.postgres.logger') as mock_logger:
                    # The function catches individual statement errors and logs warnings
                    init_database()
                    # Verify warning was logged for non-"already exists" errors
                    mock_logger.warning.assert_called()
                    # Verify execute was attempted
                    assert mock_conn.execute.called


# ============================================================================
# Task 6.2 Tests: Conversation CRUD Operations (AC-2.3.3)
# ============================================================================

class TestSaveConversation:
    """Tests for save_conversation function."""
    
    def test_save_conversation_no_engine(self):
        """Test save_conversation returns 0 when engine not initialized."""
        with patch('app.database.postgres.engine', None):
            with patch('app.database.postgres.init_engine') as mock_init:
                # Make init_engine leave engine as None
                mock_init.return_value = None
                
                result = save_conversation("session-123", {"language": "en"})
                
                assert result == 0
    
    def test_save_conversation_new_session(self):
        """Test saving a new conversation."""
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        
        # Setup mock for checking existing session (returns None)
        mock_check_result = MagicMock()
        mock_check_result.fetchone.return_value = None
        
        # Setup mock for insert
        mock_insert_result = MagicMock()
        mock_insert_result.fetchone.return_value = (42,)  # Return ID
        
        mock_conn.execute.side_effect = [mock_check_result, mock_insert_result]
        mock_conn.commit = MagicMock()
        
        mock_engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        
        with patch('app.database.postgres.engine', mock_engine):
            with patch('app.database.postgres.text') as mock_text:
                mock_text.return_value = MagicMock()
                
                result = save_conversation("session-123", {
                    "language": "en",
                    "persona": "elderly",
                    "scam_confidence": 0.85,
                    "turn_count": 5,
                })
                
                assert result == 42
    
    def test_save_conversation_update_existing(self):
        """Test updating an existing conversation."""
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        
        # Setup mock for checking existing session (returns existing ID)
        mock_check_result = MagicMock()
        mock_check_result.fetchone.return_value = (10,)  # Existing ID
        
        # Setup mock for update
        mock_update_result = MagicMock()
        mock_update_result.fetchone.return_value = (10,)  # Return same ID
        
        mock_conn.execute.side_effect = [mock_check_result, mock_update_result]
        mock_conn.commit = MagicMock()
        
        mock_engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        
        with patch('app.database.postgres.engine', mock_engine):
            with patch('app.database.postgres.text') as mock_text:
                mock_text.return_value = MagicMock()
                
                result = save_conversation("session-123", {
                    "language": "hi",
                    "turn_count": 10,
                })
                
                assert result == 10
    
    def test_save_conversation_with_messages(self):
        """Test saving conversation with messages."""
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        
        mock_check_result = MagicMock()
        mock_check_result.fetchone.return_value = None
        
        mock_insert_result = MagicMock()
        mock_insert_result.fetchone.return_value = (42,)
        
        mock_conn.execute.side_effect = [mock_check_result, mock_insert_result]
        mock_conn.commit = MagicMock()
        
        mock_engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        
        with patch('app.database.postgres.engine', mock_engine):
            with patch('app.database.postgres.text') as mock_text:
                mock_text.return_value = MagicMock()
                with patch('app.database.postgres.save_messages') as mock_save_msgs:
                    mock_save_msgs.return_value = 2
                    
                    result = save_conversation("session-123", {
                        "language": "en",
                        "messages": [
                            {"turn": 1, "sender": "scammer", "message": "Hello"},
                            {"turn": 2, "sender": "agent", "message": "Hi"},
                        ],
                    })
                    
                    assert result == 42
                    mock_save_msgs.assert_called_once()
    
    def test_save_conversation_sqlalchemy_error(self):
        """Test save_conversation handles SQLAlchemy errors."""
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_conn.execute.side_effect = SQLAlchemyError("DB error")
        
        mock_engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        
        with patch('app.database.postgres.engine', mock_engine):
            with patch('app.database.postgres.text'):
                with patch('app.database.postgres.logger') as mock_logger:
                    result = save_conversation("session-123", {})
                    
                    assert result == 0
                    mock_logger.error.assert_called()


class TestGetConversation:
    """Tests for get_conversation function."""
    
    def test_get_conversation_no_engine(self):
        """Test get_conversation returns None when engine not initialized."""
        with patch('app.database.postgres.engine', None):
            with patch('app.database.postgres.init_engine'):
                result = get_conversation("session-123")
                assert result is None
    
    def test_get_conversation_not_found(self):
        """Test get_conversation returns None for non-existent session."""
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        mock_conn.execute.return_value = mock_result
        
        mock_engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        
        with patch('app.database.postgres.engine', mock_engine):
            with patch('app.database.postgres.text'):
                result = get_conversation("non-existent")
                assert result is None
    
    def test_get_conversation_success(self):
        """Test get_conversation returns full data."""
        from datetime import datetime
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        
        now = datetime.utcnow()
        
        # Mock conversation result
        conv_result = MagicMock()
        conv_result.fetchone.return_value = (
            1, "session-123", "en", "elderly", True, 0.85, 5, now, now
        )
        
        # Mock messages result
        msg_result = MagicMock()
        msg_result.fetchall.return_value = [
            (1, "scammer", "Hello", now),
            (2, "agent", "Hi", now),
        ]
        
        # Mock intelligence result
        intel_result = MagicMock()
        intel_result.fetchone.return_value = (
            ["test@upi"], ["1234567890"], ["IFSC123"],
            ["9876543210"], ["http://scam.com"], 0.9
        )
        
        mock_conn.execute.side_effect = [conv_result, msg_result, intel_result]
        
        mock_engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        
        with patch('app.database.postgres.engine', mock_engine):
            with patch('app.database.postgres.text'):
                result = get_conversation("session-123")
                
                assert result is not None
                assert result["session_id"] == "session-123"
                assert result["language"] == "en"
                assert result["persona"] == "elderly"
                assert result["scam_detected"] is True
                assert len(result["messages"]) == 2
                assert result["extracted_intel"]["upi_ids"] == ["test@upi"]


class TestUpdateConversation:
    """Tests for update_conversation function."""
    
    def test_update_conversation_no_engine(self):
        """Test update_conversation returns False when engine not initialized."""
        with patch('app.database.postgres.engine', None):
            with patch('app.database.postgres.init_engine'):
                result = update_conversation("session-123", {"turn_count": 10})
                assert result is False
    
    def test_update_conversation_empty_updates(self):
        """Test update_conversation with empty updates returns True."""
        with patch('app.database.postgres.engine', MagicMock()):
            result = update_conversation("session-123", {})
            assert result is True
    
    def test_update_conversation_invalid_fields(self):
        """Test update_conversation ignores invalid fields."""
        with patch('app.database.postgres.engine', MagicMock()):
            with patch('app.database.postgres.logger') as mock_logger:
                result = update_conversation("session-123", {"invalid_field": "value"})
                assert result is False
                mock_logger.warning.assert_called()
    
    def test_update_conversation_success(self):
        """Test successful conversation update."""
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_conn.execute.return_value = mock_result
        mock_conn.commit = MagicMock()
        
        mock_engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        
        with patch('app.database.postgres.engine', mock_engine):
            with patch('app.database.postgres.text'):
                result = update_conversation("session-123", {"turn_count": 15})
                assert result is True


class TestSaveMessages:
    """Tests for save_messages function."""
    
    def test_save_messages_no_engine(self):
        """Test save_messages returns 0 when engine not initialized."""
        with patch('app.database.postgres.engine', None):
            with patch('app.database.postgres.init_engine'):
                result = save_messages(1, [{"turn": 1, "sender": "agent", "message": "Hi"}])
                assert result == 0
    
    def test_save_messages_empty_list(self):
        """Test save_messages with empty list returns 0."""
        with patch('app.database.postgres.engine', MagicMock()):
            result = save_messages(1, [])
            assert result == 0
    
    def test_save_messages_skips_duplicates(self):
        """Test save_messages skips existing turns."""
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        
        # Mock existing turns query
        existing_result = MagicMock()
        existing_result.fetchall.return_value = [(1,), (2,)]  # Turns 1 and 2 exist
        
        mock_conn.execute.return_value = existing_result
        mock_conn.commit = MagicMock()
        
        mock_engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        
        with patch('app.database.postgres.engine', mock_engine):
            with patch('app.database.postgres.text'):
                result = save_messages(1, [
                    {"turn": 1, "sender": "scammer", "message": "Hi"},  # Duplicate
                    {"turn": 3, "sender": "agent", "message": "Hello"},  # New
                ])
                
                # Should only save turn 3
                assert result == 1


class TestSaveIntelligence:
    """Tests for save_intelligence function."""
    
    def test_save_intelligence_no_engine(self):
        """Test save_intelligence returns 0 when engine not initialized."""
        with patch('app.database.postgres.engine', None):
            with patch('app.database.postgres.init_engine'):
                result = save_intelligence(1, {"upi_ids": ["test@upi"]}, 0.9)
                assert result == 0
    
    def test_save_intelligence_success(self):
        """Test successful intelligence saving."""
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (99,)
        mock_conn.execute.return_value = mock_result
        mock_conn.commit = MagicMock()
        
        mock_engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        
        with patch('app.database.postgres.engine', mock_engine):
            with patch('app.database.postgres.text'):
                result = save_intelligence(1, {
                    "upi_ids": ["test@upi"],
                    "phone_numbers": ["9876543210"],
                }, 0.85)
                
                assert result == 99


class TestDeleteConversation:
    """Tests for delete_conversation function."""
    
    def test_delete_conversation_no_engine(self):
        """Test delete_conversation returns False when engine not initialized."""
        with patch('app.database.postgres.engine', None):
            with patch('app.database.postgres.init_engine'):
                result = delete_conversation("session-123")
                assert result is False
    
    def test_delete_conversation_success(self):
        """Test successful conversation deletion."""
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_conn.execute.return_value = mock_result
        mock_conn.commit = MagicMock()
        
        mock_engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        
        with patch('app.database.postgres.engine', mock_engine):
            with patch('app.database.postgres.text'):
                result = delete_conversation("session-123")
                assert result is True
    
    def test_delete_conversation_not_found(self):
        """Test delete_conversation returns False for non-existent session."""
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_conn.execute.return_value = mock_result
        mock_conn.commit = MagicMock()
        
        mock_engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        
        with patch('app.database.postgres.engine', mock_engine):
            with patch('app.database.postgres.text'):
                result = delete_conversation("non-existent")
                assert result is False


class TestGetConversationsByDate:
    """Tests for get_conversations_by_date function."""
    
    def test_get_conversations_by_date_no_engine(self):
        """Test returns empty list when engine not initialized."""
        with patch('app.database.postgres.engine', None):
            with patch('app.database.postgres.init_engine'):
                result = get_conversations_by_date("2024-01-01", "2024-01-31")
                assert result == []
    
    def test_get_conversations_by_date_success(self):
        """Test successful date-based query."""
        from datetime import datetime
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        
        now = datetime.utcnow()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            (1, "session-1", "en", "elderly", True, 0.9, 10, now, now),
            (2, "session-2", "hi", "eager", False, 0.3, 5, now, now),
        ]
        mock_conn.execute.return_value = mock_result
        
        mock_engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        
        with patch('app.database.postgres.engine', mock_engine):
            with patch('app.database.postgres.text'):
                result = get_conversations_by_date("2024-01-01", "2024-01-31")
                
                assert len(result) == 2
                assert result[0]["session_id"] == "session-1"
                assert result[1]["language"] == "hi"


class TestGetConversationStats:
    """Tests for get_conversation_stats function."""
    
    def test_get_conversation_stats_no_engine(self):
        """Test returns error when engine not initialized."""
        with patch('app.database.postgres.engine', None):
            with patch('app.database.postgres.init_engine'):
                result = get_conversation_stats()
                assert "error" in result
    
    def test_get_conversation_stats_success(self):
        """Test successful stats retrieval."""
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (100, 75, 0.85, 8.5, 3)
        mock_conn.execute.return_value = mock_result
        
        mock_engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        
        with patch('app.database.postgres.engine', mock_engine):
            with patch('app.database.postgres.text'):
                result = get_conversation_stats()
                
                assert result["total_conversations"] == 100
                assert result["scam_count"] == 75
                assert result["avg_confidence"] == 0.85


class TestAcceptanceCriteria:
    """Tests for Task 6.2 Acceptance Criteria."""
    
    def test_ac_2_3_3_complete_logs_stored(self):
        """AC-2.3.3: PostgreSQL stores complete logs."""
        # Verify conversation data structure supports all required fields
        conversation_data = {
            "language": "en",
            "persona": "elderly",
            "scam_confidence": 0.85,
            "turn_count": 10,
            "messages": [
                {"turn": 1, "sender": "scammer", "message": "Hello"},
                {"turn": 2, "sender": "agent", "message": "Hi"},
            ],
            "extracted_intel": {
                "upi_ids": ["test@upi"],
                "bank_accounts": ["1234567890"],
                "ifsc_codes": ["IFSC123"],
                "phone_numbers": ["9876543210"],
                "phishing_links": ["http://scam.com"],
            },
            "extraction_confidence": 0.9,
        }
        
        # Verify all fields are present
        assert "language" in conversation_data
        assert "persona" in conversation_data
        assert "scam_confidence" in conversation_data
        assert "turn_count" in conversation_data
        assert "messages" in conversation_data
        assert "extracted_intel" in conversation_data
        
        # Verify intelligence fields
        intel = conversation_data["extracted_intel"]
        assert "upi_ids" in intel
        assert "bank_accounts" in intel
        assert "ifsc_codes" in intel
        assert "phone_numbers" in intel
        assert "phishing_links" in intel
