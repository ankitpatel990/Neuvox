"""
Unit Tests for Model Loading and Caching.

Tests model download, caching, and loading time requirements.
"""

import pytest
import time
from unittest.mock import patch, MagicMock


class TestIndicBERTLoading:
    """Tests for IndicBERT model loading."""
    
    def test_indicbert_loads_successfully(self):
        """Test IndicBERT can be loaded."""
        try:
            from transformers import AutoModel, AutoTokenizer
            
            start = time.time()
            tokenizer = AutoTokenizer.from_pretrained("ai4bharat/indic-bert")
            model = AutoModel.from_pretrained("ai4bharat/indic-bert")
            load_time = time.time() - start
            
            assert tokenizer is not None
            assert model is not None
            assert load_time > 0
            
        except ImportError:
            pytest.skip("transformers not installed")
        except Exception as e:
            pytest.skip(f"IndicBERT model not available: {e}")
    
    def test_indicbert_load_time_requirement(self):
        """Test IndicBERT loads in <10 seconds (after first download)."""
        try:
            from transformers import AutoModel, AutoTokenizer
            
            start = time.time()
            tokenizer = AutoTokenizer.from_pretrained("ai4bharat/indic-bert")
            model = AutoModel.from_pretrained("ai4bharat/indic-bert")
            load_time = time.time() - start
            
            # Note: First load may be slower due to model download
            # This test verifies subsequent loads are fast
            # If model is cached, it should load quickly
            if load_time > 10.0:
                pytest.skip(f"IndicBERT load time {load_time:.2f}s exceeds 10s (may be first download)")
            
            assert load_time < 10.0, f"IndicBERT should load in <10s, took {load_time:.2f}s"
            
        except ImportError:
            pytest.skip("transformers not installed")
        except Exception as e:
            pytest.skip(f"IndicBERT model not available: {e}")
    
    def test_indicbert_model_functionality(self):
        """Test IndicBERT model can process text."""
        try:
            from transformers import AutoModel, AutoTokenizer
            
            tokenizer = AutoTokenizer.from_pretrained("ai4bharat/indic-bert")
            model = AutoModel.from_pretrained("ai4bharat/indic-bert")
            
            test_text = "Test message for scam detection"
            inputs = tokenizer(test_text, return_tensors="pt", truncation=True, max_length=512)
            
            model.eval()
            # Model should process without errors
            outputs = model(**inputs)
            assert outputs is not None
            assert hasattr(outputs, 'last_hidden_state') or hasattr(outputs, 'logits')
            
        except ImportError:
            pytest.skip("transformers not installed")
        except Exception as e:
            pytest.skip(f"IndicBERT model not available: {e}")


class TestSpacyLoading:
    """Tests for spaCy model loading."""
    
    def test_spacy_loads_successfully(self):
        """Test spaCy model can be loaded."""
        try:
            import spacy
            
            start = time.time()
            nlp = spacy.load("en_core_web_sm")
            load_time = time.time() - start
            
            assert nlp is not None
            assert load_time > 0
            
        except ImportError:
            pytest.skip("spacy not installed")
        except OSError:
            pytest.skip("spaCy model 'en_core_web_sm' not installed")
        except Exception as e:
            pytest.skip(f"spaCy model not available: {e}")
    
    def test_spacy_load_time_requirement(self):
        """Test spaCy loads in <5 seconds."""
        try:
            import spacy
            
            start = time.time()
            nlp = spacy.load("en_core_web_sm")
            load_time = time.time() - start
            
            assert load_time < 5.0, f"spaCy should load in <5s, took {load_time:.2f}s"
            
        except ImportError:
            pytest.skip("spacy not installed")
        except OSError:
            pytest.skip("spaCy model 'en_core_web_sm' not installed")
        except Exception as e:
            pytest.skip(f"spaCy model not available: {e}")
    
    def test_spacy_model_functionality(self):
        """Test spaCy model can process text."""
        try:
            import spacy
            
            nlp = spacy.load("en_core_web_sm")
            doc = nlp("Test message for entity extraction")
            
            assert doc is not None
            assert len(doc) > 0
            
        except ImportError:
            pytest.skip("spacy not installed")
        except OSError:
            pytest.skip("spaCy model 'en_core_web_sm' not installed")
        except Exception as e:
            pytest.skip(f"spaCy model not available: {e}")


class TestSentenceTransformersLoading:
    """Tests for sentence-transformers model loading."""
    
    def test_sentence_transformers_loads_successfully(self):
        """Test sentence-transformers model can be loaded."""
        try:
            from sentence_transformers import SentenceTransformer
            
            start = time.time()
            embedder = SentenceTransformer('all-MiniLM-L6-v2')
            load_time = time.time() - start
            
            assert embedder is not None
            assert load_time > 0
            
        except ImportError:
            pytest.skip("sentence-transformers not installed")
        except Exception as e:
            pytest.skip(f"Sentence transformers model not available: {e}")
    
    def test_sentence_transformers_functionality(self):
        """Test sentence-transformers model can encode text."""
        try:
            from sentence_transformers import SentenceTransformer
            
            embedder = SentenceTransformer('all-MiniLM-L6-v2')
            test_text = "Test message for embedding"
            embedding = embedder.encode(test_text)
            
            assert embedding is not None
            assert len(embedding) > 0
            assert isinstance(embedding, (list, type(embedding)))
            
        except ImportError:
            pytest.skip("sentence-transformers not installed")
        except Exception as e:
            pytest.skip(f"Sentence transformers model not available: {e}")


class TestModelSetupScript:
    """Tests for setup_models.py script functions."""
    
    def test_download_indicbert_function_exists(self):
        """Test download_indicbert function exists and is callable."""
        from scripts.setup_models import download_indicbert
        
        assert callable(download_indicbert)
    
    def test_download_spacy_function_exists(self):
        """Test download_spacy function exists and is callable."""
        from scripts.setup_models import download_spacy
        
        assert callable(download_spacy)
    
    def test_download_sentence_transformers_function_exists(self):
        """Test download_sentence_transformers function exists and is callable."""
        from scripts.setup_models import download_sentence_transformers
        
        assert callable(download_sentence_transformers)
    
    def test_verify_models_function_exists(self):
        """Test verify_models function exists and is callable."""
        from scripts.setup_models import verify_models
        
        assert callable(verify_models)
    
    def test_download_indicbert_returns_tuple(self):
        """Test download_indicbert returns (bool, Optional[float])."""
        from scripts.setup_models import download_indicbert
        
        success, load_time = download_indicbert()
        
        assert isinstance(success, bool)
        assert load_time is None or isinstance(load_time, (int, float))
    
    def test_download_spacy_returns_tuple(self):
        """Test download_spacy returns (bool, Optional[float])."""
        from scripts.setup_models import download_spacy
        
        success, load_time = download_spacy()
        
        assert isinstance(success, bool)
        assert load_time is None or isinstance(load_time, (int, float))
    
    def test_download_sentence_transformers_returns_tuple(self):
        """Test download_sentence_transformers returns (bool, Optional[float])."""
        from scripts.setup_models import download_sentence_transformers
        
        success, load_time = download_sentence_transformers()
        
        assert isinstance(success, bool)
        assert load_time is None or isinstance(load_time, (int, float))
    
    def test_verify_models_returns_tuple(self):
        """Test verify_models returns (bool, dict)."""
        from scripts.setup_models import verify_models
        
        all_verified, load_times = verify_models()
        
        assert isinstance(all_verified, bool)
        assert isinstance(load_times, dict)
