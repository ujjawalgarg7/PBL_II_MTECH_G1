"""Backward-compatible import for the canonical memory retriever.

The implementation lives in :mod:`src.memory.memory_retriever` so every
consumer uses one retrieval and ranking algorithm.
"""

from src.memory.memory_retriever import MemoryRetriever

__all__ = ["MemoryRetriever"]
