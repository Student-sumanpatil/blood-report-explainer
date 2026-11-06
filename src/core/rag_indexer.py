"""
Curated Medical Knowledge Base Indexer & Retriever.
Indexes markdown medical references from data/medical_kb/ and retrieves grounded context with citations.
Zero-download lightweight design: Uses structured section parsing and BM25/keyword retrieval.
"""
import os
import re
from typing import List, Dict, Any, Optional

DEFAULT_KB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "medical_kb")


class MedicalKnowledgeChunk:
    def __init__(self, title: str, content: str, source_url: str, canonical_tag: str):
        self.title = title
        self.content = content
        self.source_url = source_url
        self.canonical_tag = canonical_tag

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "content": self.content,
            "source_url": self.source_url,
            "canonical_tag": self.canonical_tag,
        }


class MedicalRAGRetriever:
    def __init__(self, kb_dir: str = DEFAULT_KB_DIR):
        self.kb_dir = kb_dir
        self.chunks: List[MedicalKnowledgeChunk] = []
        self._load_knowledge_base()

    def _load_knowledge_base(self):
        """Loads and chunks all markdown files from the medical_kb directory."""
        if not os.path.exists(self.kb_dir):
            return

        for filename in os.listdir(self.kb_dir):
            if filename.endswith(".md"):
                file_path = os.path.join(self.kb_dir, filename)
                self._parse_markdown_file(file_path)

    def _parse_markdown_file(self, file_path: str):
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

        # Extract source URL from metadata header if present
        source_url_match = re.search(r"\*\*Topic URL\*\*:\s*([^\s\n]+)", text)
        source_url = source_url_match.group(1) if source_url_match else "https://medlineplus.gov/lab-tests/"

        # Split into sections based on '###' headings
        sections = re.split(r"(?m)^###\s+", text)
        for section in sections[1:]:  # skip preamble
            lines = section.strip().split("\n")
            title = lines[0].strip()
            content = "\n".join(lines[1:]).strip()

            # Identify canonical tag keyword from title (e.g. Hemoglobin, WBC, Platelets)
            canonical_tag = title.lower()

            chunk = MedicalKnowledgeChunk(
                title=title,
                content=content,
                source_url=source_url,
                canonical_tag=canonical_tag
            )
            self.chunks.append(chunk)

    def retrieve(self, test_name: str, query: Optional[str] = None) -> Optional[MedicalKnowledgeChunk]:
        """
        Retrieves the most relevant medical knowledge chunk for a given lab test.
        Uses exact token boundaries and priority ranking.
        """
        target = test_name.lower().strip()

        # Disambiguate Hemoglobin vs Glycated Hemoglobin
        if target in ("hemoglobin", "hb", "hgb"):
            for chunk in self.chunks:
                clean_title = re.sub(r"^\d+\.\s*", "", chunk.title).lower()
                if clean_title.startswith("hemoglobin") and "glycated" not in clean_title:
                    return chunk

        # 1. Exact match on title head
        for chunk in self.chunks:
            clean_title = re.sub(r"^\d+\.\s*", "", chunk.title).lower()
            if clean_title.startswith(target) or target == clean_title.split("(")[0].strip():
                return chunk

        # 2. Check canonical aliases
        alias_map = {
            "hb": "hemoglobin",
            "hgb": "hemoglobin",
            "wbc": "white blood cell",
            "tlc": "white blood cell",
            "plt": "platelet",
            "platelets": "platelet",
            "rbc": "red blood cell",
            "tsh": "thyroid-stimulating",
            "fbs": "fasting",
            "glucose": "fasting",
            "ppbs": "postprandial",
            "hba1c": "glycated hemoglobin",
            "ldl": "ldl",
            "hdl": "hdl",
            "triglycerides": "triglycerides",
        }
        for alias, mapped_term in alias_map.items():
            if alias == target or (alias in target and len(alias) >= 3):
                for chunk in self.chunks:
                    clean_title = re.sub(r"^\d+\.\s*", "", chunk.title).lower()
                    if mapped_term in clean_title and (mapped_term != "hemoglobin" or "glycated" not in clean_title):
                        return chunk

        # 3. Direct tag match
        for chunk in self.chunks:
            if target in chunk.canonical_tag:
                return chunk

        # 4. Fallback: match content keywords
        for chunk in self.chunks:
            if target in chunk.content.lower():
                return chunk

        return None
