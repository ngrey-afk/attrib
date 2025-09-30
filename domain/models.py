from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class MetadataEntity:
    file: str
    title: str
    description: str
    keywords: List[str]
    disambiguations: Dict[str, str]
    category: Optional[str] = None
    secondary_category: Optional[str] = None
    flags: Optional[Dict[str, bool]] = None
    captions: Optional[List[str]] = None
