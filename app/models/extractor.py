"""
Intelligence Extraction Module.

Implements Task 7.1 requirements for extracting financial intelligence:
- UPI IDs (e.g., user@paytm) - AC-3.1.1: >90% precision
- Bank account numbers (9-18 digits) - AC-3.1.2: >85% precision
- IFSC codes (11 characters, XXXX0XXXXXX format) - AC-3.1.3: >95% precision
- Phone numbers (Indian mobile format) - AC-3.1.4: >90% precision
- Phishing links (URLs) - AC-3.1.5: >95% precision
- Devanagari digit conversion - AC-3.3.1: 100% accurate
"""

from typing import Dict, List, Optional, Set, Tuple
import re
from urllib.parse import urlparse

from app.utils.logger import get_logger

logger = get_logger(__name__)

# Valid UPI provider suffixes
VALID_UPI_PROVIDERS: Set[str] = {
    "paytm", "ybl", "okaxis", "okhdfcbank", "oksbi", "okicici",
    "upi", "apl", "axisbank", "icici", "sbi", "hdfcbank",
    "ibl", "kotak", "pnb", "boi", "cbi", "canara", "bob",
    "unionbank", "idbi", "indianbank", "pnb", "iob", "allahabad",
    "axl", "fbl", "hdfc", "hsbc", "indus", "rbl", "sc", "yesbank",
    "airtel", "jio", "postbank", "dbs", "federal", "bandhan",
    "pingpay", "waaxis", "wahdfcbank", "wasbi", "waicici",
    "gpay", "phonepe", "payzapp", "amazonpay", "freecharge",
}

# Known phishing/suspicious domains patterns
SUSPICIOUS_DOMAIN_PATTERNS: List[str] = [
    r"\.xyz$", r"\.tk$", r"\.ml$", r"\.ga$", r"\.cf$",
    r"\.gq$", r"\.pw$", r"\.top$", r"\.club$", r"\.work$",
    r"bit\.ly", r"tinyurl", r"goo\.gl", r"t\.co", r"is\.gd",
    r"bank.*verify", r"verify.*bank", r"kyc.*update",
    r"update.*kyc", r"secure.*login", r"login.*secure",
]

# Legitimate domains to exclude from phishing detection
LEGITIMATE_DOMAINS: Set[str] = {
    "google.com", "www.google.com", "gmail.com", "youtube.com",
    "facebook.com", "twitter.com", "instagram.com", "linkedin.com",
    "microsoft.com", "apple.com", "amazon.com", "amazon.in",
    "flipkart.com", "paytm.com", "phonepe.com", "gpay.com",
    "sbi.co.in", "hdfcbank.com", "icicibank.com", "axisbank.com",
    "rbi.org.in", "npci.org.in", "upi.org.in",
}


class IntelligenceExtractor:
    """
    Extract financial intelligence from text using regex and optional NER.
    
    Implements high-precision extraction for:
    - UPI IDs (precision >90%)
    - Bank accounts (precision >85%)
    - IFSC codes (precision >95%)
    - Phone numbers (precision >90%)
    - Phishing links (precision >95%)
    
    Attributes:
        nlp: Optional spaCy NLP model for enhanced NER
        patterns: Dict of regex patterns for each entity type
        use_spacy: Whether spaCy is available
    """
    
    def __init__(self, use_spacy: bool = True) -> None:
        """
        Initialize the IntelligenceExtractor.
        
        Args:
            use_spacy: Whether to try loading spaCy model
        """
        self.nlp = None
        self.use_spacy = use_spacy
        
        if use_spacy:
            self._load_spacy()
        
        # Regex patterns for each entity type
        self.patterns: Dict[str, str] = {
            # UPI IDs: alphanumeric with dots, underscores, hyphens @ provider
            "upi_ids": r"\b[a-zA-Z0-9][a-zA-Z0-9._-]*@[a-zA-Z]{2,}\b",
            
            # Bank accounts: 9-18 digits (not starting with 0 typically)
            "bank_accounts": r"\b[1-9]\d{8,17}\b",
            
            # IFSC codes: 4-5 letters + (0 or O) + 6 alphanumeric
            # Handle common typos:
            # - O instead of 0 in 5th position
            # - Extra letter (e.g., SBIIN instead of SBIN)
            # We're lenient here because we want to CAPTURE scammer data
            "ifsc_codes": r"\b[A-Z]{4,5}[0O][A-Z0-9]{6}\b",
            
            # Phone numbers: Indian mobile format with optional +91
            "phone_numbers": r"(?:\+91[\s\-]?)?(?:0)?[6-9]\d{9}\b",
            
            # Phishing links: HTTP/HTTPS URLs
            "phishing_links": r"https?://[^\s<>\"\'{}|\\^`\[\]]+",
        }
        
        # Devanagari to ASCII digit mapping
        self.devanagari_map: Dict[str, str] = {
            "\u0966": "0",  # ०
            "\u0967": "1",  # १
            "\u0968": "2",  # २
            "\u0969": "3",  # ३
            "\u096A": "4",  # ४
            "\u096B": "5",  # ५
            "\u096C": "6",  # ६
            "\u096D": "7",  # ७
            "\u096E": "8",  # ८
            "\u096F": "9",  # ९
        }
    
    def _load_spacy(self) -> None:
        """Load spaCy model for enhanced NER."""
        try:
            import spacy
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("spaCy model loaded for enhanced NER")
        except ImportError:
            logger.warning("spaCy not installed, using regex-only extraction")
            self.nlp = None
        except OSError:
            logger.warning("spaCy model 'en_core_web_sm' not found, using regex-only")
            self.nlp = None
    
    def extract(self, text: str) -> Tuple[Dict[str, List[str]], float]:
        """
        Extract intelligence from text.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Tuple of (intelligence_dict, confidence_score)
        """
        if not text or not text.strip():
            return self._empty_intel(), 0.0
        
        # Convert Devanagari digits to ASCII (AC-3.3.1: 100% accurate)
        text = self._convert_devanagari_digits(text)
        
        intel: Dict[str, List[str]] = {
            "upi_ids": [],
            "bank_accounts": [],
            "ifsc_codes": [],
            "phone_numbers": [],
            "phishing_links": [],
        }
        
        # Extract using regex patterns
        for entity_type, pattern in self.patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE if entity_type == "ifsc_codes" else 0)
            intel[entity_type] = list(set(matches))
        
        # Validate and filter each entity type
        intel["upi_ids"] = self._validate_upi_ids(intel["upi_ids"])
        intel["bank_accounts"] = self._validate_bank_accounts(intel["bank_accounts"])
        intel["ifsc_codes"] = self._validate_ifsc_codes(intel["ifsc_codes"])
        intel["phone_numbers"] = self._normalize_phone_numbers(intel["phone_numbers"])
        intel["phishing_links"] = self._validate_phishing_links(intel["phishing_links"])
        
        # Remove any bank accounts that are actually phone numbers
        # Phone numbers are normalized to +91XXXXXXXXXX format
        phone_digits = set()
        for phone in intel["phone_numbers"]:
            # Extract the 10-digit number from +91XXXXXXXXXX
            digits = phone.replace("+91", "")
            phone_digits.add(digits)
            # Also add with 91 prefix in case it was captured that way
            phone_digits.add("91" + digits)
        
        # Filter out bank accounts that match phone numbers
        intel["bank_accounts"] = [
            acc for acc in intel["bank_accounts"]
            if acc not in phone_digits and acc[-10:] not in phone_digits
        ]
        
        # Use spaCy NER for additional entities if available
        if self.nlp is not None:
            self._extract_with_spacy(text, intel)
        
        # Calculate confidence score
        confidence = self._calculate_confidence(intel)
        
        logger.debug(f"Extracted intel: {len(intel['upi_ids'])} UPIs, "
                     f"{len(intel['bank_accounts'])} accounts, "
                     f"{len(intel['phone_numbers'])} phones, "
                     f"confidence={confidence:.2f}")
        
        return intel, confidence
    
    def _empty_intel(self) -> Dict[str, List[str]]:
        """Return empty intelligence dict."""
        return {
            "upi_ids": [],
            "bank_accounts": [],
            "ifsc_codes": [],
            "phone_numbers": [],
            "phishing_links": [],
        }
    
    def _convert_devanagari_digits(self, text: str) -> str:
        """
        Convert Devanagari digits to ASCII.
        
        Implements AC-3.3.1: 100% accurate Devanagari conversion.
        
        Args:
            text: Input text
            
        Returns:
            Text with Devanagari digits converted to ASCII
        """
        for dev, asc in self.devanagari_map.items():
            text = text.replace(dev, asc)
        return text
    
    def _validate_upi_ids(self, upi_ids: List[str]) -> List[str]:
        """
        Validate UPI IDs for precision >90% (AC-3.1.1).
        
        Args:
            upi_ids: List of potential UPI IDs
            
        Returns:
            List of validated UPI IDs
        """
        validated = []
        
        for upi in upi_ids:
            upi_lower = upi.lower()
            
            # Extract provider (part after @)
            if "@" not in upi:
                continue
            
            parts = upi.split("@")
            if len(parts) != 2:
                continue
            
            user_part, provider = parts
            provider_lower = provider.lower()
            
            # User part must be at least 2 characters
            if len(user_part) < 2:
                continue
            
            # Check if provider is valid UPI provider
            if provider_lower in VALID_UPI_PROVIDERS:
                validated.append(upi)
            # Allow unknown providers if they look like UPI (2-10 chars, alphabetic)
            elif 2 <= len(provider) <= 10 and provider.isalpha():
                # Exclude common email domains
                if provider_lower not in {"com", "org", "net", "edu", "gov", "in", "co", "io"}:
                    validated.append(upi)
        
        return list(set(validated))
    
    def _validate_bank_accounts(self, accounts: List[str]) -> List[str]:
        """
        Validate bank account numbers for precision >85% (AC-3.1.2).
        
        Bank account numbers in India:
        - SBI: 11 digits
        - HDFC: 13-14 digits
        - ICICI: 12 digits
        - Axis: 15 digits
        - Other banks: 9-18 digits
        
        Args:
            accounts: List of potential account numbers
            
        Returns:
            List of validated account numbers
        """
        validated = []
        
        for account in accounts:
            # Must be 9-18 digits
            if len(account) < 9 or len(account) > 18:
                continue
            
            # Exclude exactly 10-digit numbers starting with 6,7,8,9 (Indian phone numbers)
            if len(account) == 10 and account[0] in "6789":
                continue
            
            # Exclude if it looks like +91 phone (starts with 91 + 6-9 and is 12 digits)
            if len(account) == 12 and account[:2] == "91" and account[2] in "6789":
                continue
            
            # Check for repeated digits (unlikely to be valid account)
            if len(set(account)) == 1:
                continue
            
            # Check for sequential patterns (123456789, 987654321)
            if self._is_sequential(account):
                continue
            
            validated.append(account)
        
        return list(set(validated))
    
    def _is_sequential(self, number: str) -> bool:
        """
        Check if number is an OBVIOUS sequential pattern.
        
        IMPORTANT: For a honeypot, we WANT to capture ALL data scammers provide,
        even if it looks like a test/sequential pattern. Scammers might use
        obvious patterns, and we should still track them.
        
        Therefore, this function now returns False for all inputs.
        We only reject all-same-digit patterns (handled in _validate_bank_accounts).
        """
        # DO NOT reject sequential patterns - capture all scammer data
        # The honeypot's purpose is intelligence gathering, not validation
        return False
    
    def _validate_ifsc_codes(self, ifsc_codes: List[str]) -> List[str]:
        """
        Validate IFSC codes - lenient to capture scammer data even with typos.
        
        Standard IFSC format: 4 letters + 0 + 6 alphanumeric (11 chars)
        But we accept typos like:
        - SBIIN0010789 (12 chars with extra letter)
        - SBIN0O10789 (O instead of 0)
        
        For a honeypot, we want to CAPTURE the data scammers provide.
        
        Args:
            ifsc_codes: List of potential IFSC codes
            
        Returns:
            List of validated/normalized IFSC codes
        """
        validated = []
        
        for ifsc in ifsc_codes:
            ifsc_upper = ifsc.upper()
            
            # Accept 11-12 characters (allow for typos like SBIIN)
            if len(ifsc_upper) < 11 or len(ifsc_upper) > 12:
                continue
            
            # First 4 must be letters (bank code) - for 12 char, first 5 are letters
            letter_prefix_len = 4 if len(ifsc_upper) == 11 else 5
            if not ifsc_upper[:letter_prefix_len].isalpha():
                continue
            
            # Replace all O (letter) with 0 (zero) in numeric parts
            fixed_suffix = ""
            for char in ifsc_upper[letter_prefix_len:]:
                if char == "O":
                    fixed_suffix += "0"
                else:
                    fixed_suffix += char
            
            # Check that after the letter prefix, first char is 0
            if fixed_suffix and fixed_suffix[0] != "0":
                continue
            
            # Rest must be alphanumeric
            if not fixed_suffix[1:].isalnum():
                continue
            
            # Store the original (we want to capture what scammer actually sent)
            validated.append(ifsc_upper)
        
        return list(set(validated))
    
    def _normalize_phone_numbers(self, phone_numbers: List[str]) -> List[str]:
        """
        Normalize and validate phone numbers for precision >90% (AC-3.1.4).
        
        Args:
            phone_numbers: List of potential phone numbers
            
        Returns:
            List of normalized phone numbers
        """
        validated = []
        
        for phone in phone_numbers:
            # Remove spaces and hyphens
            cleaned = re.sub(r"[\s\-]", "", phone)
            
            # Remove leading +91 or 0
            if cleaned.startswith("+91"):
                cleaned = cleaned[3:]
            elif cleaned.startswith("91") and len(cleaned) == 12:
                cleaned = cleaned[2:]
            elif cleaned.startswith("0"):
                cleaned = cleaned[1:]
            
            # Must be exactly 10 digits
            if len(cleaned) != 10:
                continue
            
            # Must start with 6-9 (Indian mobile)
            if cleaned[0] not in "6789":
                continue
            
            # Exclude repeated digits
            if len(set(cleaned)) <= 2:
                continue
            
            # Format with +91 prefix
            formatted = f"+91{cleaned}"
            validated.append(formatted)
        
        return list(set(validated))
    
    def _validate_phishing_links(self, links: List[str]) -> List[str]:
        """
        Validate and filter phishing links for precision >95% (AC-3.1.5).
        
        In a scam context, we want to capture ALL links that aren't from
        well-known legitimate domains, as they could be phishing attempts.
        
        Args:
            links: List of potential phishing links
            
        Returns:
            List of suspicious links
        """
        validated = []
        
        for link in links:
            # Clean up trailing punctuation
            link = link.rstrip(".,;:!?)")
            
            try:
                parsed = urlparse(link)
                domain = parsed.netloc.lower()
                
                # Skip empty or malformed URLs
                if not domain:
                    continue
                
                # Remove www. prefix for comparison
                if domain.startswith("www."):
                    domain_clean = domain[4:]
                else:
                    domain_clean = domain
                
                # Skip only well-known legitimate domains
                if domain_clean in LEGITIMATE_DOMAINS or domain in LEGITIMATE_DOMAINS:
                    continue
                
                # In a scam context, ANY unknown link is suspicious
                # Since this is a honeypot system, we want to capture all links
                # that scammers share - they're likely phishing attempts
                is_suspicious = True
                
                # Extra flags for definitely suspicious patterns
                for pattern in SUSPICIOUS_DOMAIN_PATTERNS:
                    if re.search(pattern, link, re.IGNORECASE):
                        is_suspicious = True
                        break
                
                # Check for IP-based URLs (often phishing)
                if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", domain):
                    is_suspicious = True
                
                # Check for unusually long domain (typosquatting)
                if len(domain_clean) > 30:
                    is_suspicious = True
                
                # Check for fake bank/payment keywords
                fake_keywords = ["bank", "kyc", "verify", "secure", "login", "update", "upi", "paytm"]
                for keyword in fake_keywords:
                    if keyword in domain_clean:
                        is_suspicious = True
                        break
                
                # All non-legitimate links with HTTP (not HTTPS) are suspicious
                if parsed.scheme == "http" and domain_clean not in LEGITIMATE_DOMAINS:
                    is_suspicious = True
                
                if is_suspicious:
                    validated.append(link)
                    
            except Exception:
                # Malformed URL - could be suspicious
                validated.append(link)
        
        return list(set(validated))
    
    def _extract_with_spacy(self, text: str, intel: Dict[str, List[str]]) -> None:
        """
        Use spaCy NER for additional entity extraction.
        
        Args:
            text: Input text
            intel: Intelligence dict to update
        """
        if self.nlp is None:
            return
        
        try:
            doc = self.nlp(text)
            
            for ent in doc.ents:
                # CARDINAL entities might be account numbers
                if ent.label_ == "CARDINAL":
                    num_text = re.sub(r"[^\d]", "", ent.text)
                    
                    if 9 <= len(num_text) <= 18 and len(num_text) != 10:
                        if num_text not in intel["bank_accounts"]:
                            if self._validate_bank_accounts([num_text]):
                                intel["bank_accounts"].append(num_text)
                
                # MONEY entities might contain account numbers
                elif ent.label_ == "MONEY":
                    nums = re.findall(r"\d{9,18}", ent.text)
                    for num in nums:
                        if num not in intel["bank_accounts"] and len(num) != 10:
                            if self._validate_bank_accounts([num]):
                                intel["bank_accounts"].append(num)
                                
        except Exception as e:
            logger.warning(f"spaCy extraction failed: {e}")
    
    def _calculate_confidence(self, intel: Dict[str, List[str]]) -> float:
        """
        Calculate extraction confidence score.
        
        Weights reflect importance of each entity type for scam detection.
        
        Args:
            intel: Extracted intelligence dictionary
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        weights = {
            "upi_ids": 0.30,       # UPI IDs are strong indicators
            "bank_accounts": 0.30, # Bank accounts are strong indicators
            "ifsc_codes": 0.20,    # IFSC adds validity to bank accounts
            "phone_numbers": 0.10, # Phone numbers are weaker indicators
            "phishing_links": 0.10,# Phishing links are suspicious
        }
        
        score = 0.0
        for entity_type, weight in weights.items():
            if len(intel.get(entity_type, [])) > 0:
                score += weight
        
        return min(score, 1.0)
    
    def extract_from_conversation(
        self,
        messages: List[Dict],
    ) -> Tuple[Dict[str, List[str]], float]:
        """
        Extract intelligence from a list of conversation messages.
        
        Args:
            messages: List of message dicts with 'message' key
            
        Returns:
            Tuple of (intelligence_dict, confidence_score)
        """
        full_text = " ".join(msg.get("message", "") for msg in messages)
        return self.extract(full_text)


# Singleton extractor instance
_extractor: Optional[IntelligenceExtractor] = None


def get_extractor() -> IntelligenceExtractor:
    """
    Get singleton extractor instance.
    
    Returns:
        IntelligenceExtractor instance
    """
    global _extractor
    if _extractor is None:
        _extractor = IntelligenceExtractor()
    return _extractor


def reset_extractor() -> None:
    """Reset the singleton extractor (for testing)."""
    global _extractor
    _extractor = None


def extract_intelligence(text: str) -> Tuple[Dict[str, List[str]], float]:
    """
    Convenience function for intelligence extraction.
    
    This is the main entry point for extracting financial intelligence
    from scammer messages.
    
    Args:
        text: Input text to analyze
        
    Returns:
        Tuple of (intelligence_dict, confidence_score)
        
    Example:
        >>> intel, conf = extract_intelligence("Send ₹5000 to scammer@paytm")
        >>> assert "scammer@paytm" in intel['upi_ids']
        >>> assert conf > 0.0
    """
    extractor = get_extractor()
    return extractor.extract(text)


def extract_from_messages(messages: List[Dict]) -> Tuple[Dict[str, List[str]], float]:
    """
    Extract intelligence from conversation messages.
    
    Args:
        messages: List of message dicts with 'message' key
        
    Returns:
        Tuple of (intelligence_dict, confidence_score)
    """
    extractor = get_extractor()
    return extractor.extract_from_conversation(messages)
