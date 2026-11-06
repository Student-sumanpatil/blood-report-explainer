"""
Unit tests for the Curated RAG Retriever.
"""
from src.core.rag_indexer import MedicalRAGRetriever


def test_rag_retrieves_cbc():
    retriever = MedicalRAGRetriever()
    chunk = retriever.retrieve("Hemoglobin")
    assert chunk is not None
    assert "Hemoglobin" in chunk.title
    assert "medlineplus.gov" in chunk.source_url
    assert "oxygen" in chunk.content.lower()


def test_rag_retrieves_lipid():
    retriever = MedicalRAGRetriever()
    chunk = retriever.retrieve("Total Cholesterol")
    assert chunk is not None
    assert "Cholesterol" in chunk.title
    assert "200" in chunk.content


def test_rag_retrieves_thyroid():
    retriever = MedicalRAGRetriever()
    chunk = retriever.retrieve("TSH")
    assert chunk is not None
    assert "Thyroid-Stimulating Hormone" in chunk.title
    assert "pituitary" in chunk.content.lower()
