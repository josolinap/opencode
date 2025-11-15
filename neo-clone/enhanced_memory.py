"""
Enhanced memory and context management for Neo-Clone
Provides vector similarity, conversation summarization, and smart context pruning
"""

import json
import os
import time
import math
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime, timedelta
import threading
import logging

logger = logging.getLogger(__name__)


@dataclass
class ConversationSummary:
    """Summary of a conversation segment"""

    start_time: float
    end_time: float
    message_count: int
    key_topics: List[str]
    user_intent: str
    outcome: str
    importance_score: float = 0.5


@dataclass
class ContextVector:
    """Vector representation of context for similarity matching"""

    text: str
    vector: List[float]
    timestamp: float
    message_type: str  # user, assistant, system
    session_id: str
    relevance_score: float = 1.0


class VectorMemory:
    """Simple vector similarity for context retrieval"""

    def __init__(self, vector_size: int = 384):
        self.vector_size = vector_size
        self.vectors: List[ContextVector] = []
        self._lock = threading.Lock()

    def _text_to_vector(self, text: str) -> List[float]:
        """Convert text to simple vector representation"""
        # Simple TF-IDF-like vectorization
        words = text.lower().split()
        word_counts = {}

        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1

        # Create fixed-size vector
        vector = [0.0] * self.vector_size

        for i, word in enumerate(words[: self.vector_size]):
            # Simple hash-based embedding
            word_hash = sum(ord(c) for c in word) % self.vector_size
            vector[word_hash] = word_counts.get(word, 0) / len(words)

        # Normalize vector
        magnitude = math.sqrt(sum(x * x for x in vector))
        if magnitude > 0:
            vector = [x / magnitude for x in vector]

        return vector

    def add_context(self, text: str, message_type: str, session_id: str):
        """Add context vector"""
        vector = self._text_to_vector(text)

        context_vector = ContextVector(
            text=text,
            vector=vector,
            timestamp=time.time(),
            message_type=message_type,
            session_id=session_id,
        )

        with self._lock:
            self.vectors.append(context_vector)

            # Keep only recent vectors (last 1000)
            if len(self.vectors) > 1000:
                self.vectors = self.vectors[-1000:]

    def find_similar(
        self, query: str, limit: int = 5, min_similarity: float = 0.3
    ) -> List[ContextVector]:
        """Find similar context vectors"""
        query_vector = self._text_to_vector(query)

        with self._lock:
            similarities = []

            for context_vec in self.vectors:
                # Calculate cosine similarity
                similarity = self._cosine_similarity(query_vector, context_vec.vector)

                # Apply time decay (older contexts less relevant)
                time_decay = math.exp(
                    -(time.time() - context_vec.timestamp) / 3600
                )  # 1 hour half-life
                final_similarity = similarity * time_decay * context_vec.relevance_score

                if final_similarity >= min_similarity:
                    similarities.append((final_similarity, context_vec))

            # Sort by similarity and return top results
            similarities.sort(key=lambda x: x[0], reverse=True)
            return [context for _, context in similarities[:limit]]

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    def cleanup_old_vectors(self, max_age_hours: int = 24):
        """Remove old vectors"""
        cutoff_time = time.time() - (max_age_hours * 3600)

        with self._lock:
            original_count = len(self.vectors)
            self.vectors = [v for v in self.vectors if v.timestamp > cutoff_time]
            removed_count = original_count - len(self.vectors)

            if removed_count > 0:
                logger.debug(f"Cleaned up {removed_count} old context vectors")


class ConversationSummarizer:
    """Summarizes conversations to manage context length"""

    def __init__(self):
        self.summaries: List[ConversationSummary] = []
        self._lock = threading.Lock()

    def summarize_messages(
        self, messages: List[Dict[str, Any]], session_id: str
    ) -> ConversationSummary:
        """Summarize a segment of messages"""
        if not messages:
            return ConversationSummary(
                start_time=time.time(),
                end_time=time.time(),
                message_count=0,
                key_topics=[],
                user_intent="unknown",
                outcome="no_messages",
            )

        # Extract key information
        user_messages = [m for m in messages if m.get("role") == "user"]
        assistant_messages = [m for m in messages if m.get("role") == "assistant"]

        # Simple topic extraction (keyword-based)
        all_text = " ".join([m.get("content", "") for m in messages]).lower()
        topic_keywords = [
            "code",
            "data",
            "analysis",
            "help",
            "error",
            "question",
            "task",
        ]
        key_topics = [topic for topic in topic_keywords if topic in all_text]

        # Determine user intent
        intent = self._classify_intent(user_messages)

        # Determine outcome
        outcome = self._classify_outcome(assistant_messages)

        # Calculate importance score
        importance = self._calculate_importance(messages, key_topics)

        summary = ConversationSummary(
            start_time=messages[0].get("timestamp", time.time())
            if messages
            else time.time(),
            end_time=messages[-1].get("timestamp", time.time())
            if messages
            else time.time(),
            message_count=len(messages),
            key_topics=key_topics,
            user_intent=intent,
            outcome=outcome,
            importance_score=importance,
        )

        with self._lock:
            self.summaries.append(summary)

            # Keep only recent summaries (last 100)
            if len(self.summaries) > 100:
                self.summaries = self.summaries[-100:]

        return summary

    def _classify_intent(self, user_messages: List[Dict[str, Any]]) -> str:
        """Classify user intent from messages"""
        if not user_messages:
            return "unknown"

        text = " ".join([m.get("content", "") for m in user_messages]).lower()

        # Simple keyword-based intent classification
        intent_patterns = {
            "question": ["what", "how", "why", "when", "where", "who", "?"],
            "command": ["generate", "create", "analyze", "search", "find"],
            "help": ["help", "stuck", "error", "problem"],
            "conversation": ["hello", "hi", "thanks", "bye", "goodbye"],
            "task": ["do", "make", "implement", "write", "code"],
        }

        intent_scores = {}
        for intent, keywords in intent_patterns.items():
            score = sum(1 for keyword in keywords if keyword in text)
            intent_scores[intent] = score

        return (
            max(intent_scores.items(), key=lambda x: x[1])[0]
            if intent_scores
            else "unknown"
        )

    def _classify_outcome(self, assistant_messages: List[Dict[str, Any]]) -> str:
        """Classify conversation outcome"""
        if not assistant_messages:
            return "no_response"

        text = " ".join([m.get("content", "") for m in assistant_messages]).lower()

        if any(word in text for word in ["error", "failed", "sorry", "can't"]):
            return "failed"
        elif any(word in text for word in ["success", "done", "complete", "finished"]):
            return "successful"
        elif any(word in text for word in ["?", "unclear", "clarify"]):
            return "clarification_needed"
        else:
            return "informational"

    def _calculate_importance(
        self, messages: List[Dict[str, Any]], key_topics: List[str]
    ) -> float:
        """Calculate importance score of conversation segment"""
        # Base importance on message count and topics
        message_score = min(len(messages) / 10, 1.0)  # Normalize to 0-1
        topic_score = min(len(key_topics) / 3, 1.0)  # Normalize to 0-1

        # Check for error indicators (higher importance)
        text = " ".join([m.get("content", "") for m in messages]).lower()
        error_score = (
            0.2 if any(word in text for word in ["error", "failed", "bug"]) else 0.0
        )

        # Combine scores
        importance = message_score * 0.4 + topic_score * 0.4 + error_score * 0.2
        return min(importance, 1.0)

    def get_relevant_summaries(
        self, current_session: str, limit: int = 5
    ) -> List[ConversationSummary]:
        """Get most relevant summaries for current context"""
        with self._lock:
            # Sort by importance and recency
            scored_summaries = []
            current_time = time.time()

            for summary in self.summaries:
                # Calculate relevance score
                time_decay = math.exp(
                    -(current_time - summary.end_time) / 7200
                )  # 2 hour half-life
                relevance = summary.importance_score * time_decay

                scored_summaries.append((relevance, summary))

            scored_summaries.sort(key=lambda x: x[0], reverse=True)
            return [summary for _, summary in scored_summaries[:limit]]


class SmartContextManager:
    """Intelligent context management with pruning and optimization"""

    def __init__(self, max_context_tokens: int = 8000, max_history: int = 50):
        self.max_context_tokens = max_context_tokens
        self.max_history = max_history
        self.vector_memory = VectorMemory()
        self.summarizer = ConversationSummarizer()
        self._lock = threading.Lock()

        # Context windows
        self.immediate_context = []  # Last few messages
        self.recent_context = []  # Last hour
        self.summarized_context = []  # Important older context

    def add_message(
        self, role: str, content: str, session_id: str, metadata: Optional[Dict] = None
    ):
        """Add message with intelligent context management"""
        message = {
            "role": role,
            "content": content,
            "timestamp": time.time(),
            "session_id": session_id,
            "metadata": metadata or {},
        }

        with self._lock:
            # Add to immediate context
            self.immediate_context.append(message)

            # Add to vector memory for similarity search
            self.vector_memory.add_context(content, role, session_id)

            # Manage context size
            self._prune_context()

    def _prune_context(self):
        """Intelligently prune context to stay within limits"""
        # Estimate token count (rough approximation: 1 token ≈ 4 characters)
        total_chars = sum(len(m.get("content", "")) for m in self.immediate_context)
        estimated_tokens = total_chars / 4

        if estimated_tokens <= self.max_context_tokens:
            return

        # If over limit, summarize older messages
        messages_to_summarize = []
        messages_to_keep = []

        # Keep most recent messages within limit
        current_tokens = 0
        for message in reversed(self.immediate_context):
            message_tokens = len(message.get("content", "")) / 4

            if (
                current_tokens + message_tokens <= self.max_context_tokens * 0.7
            ):  # Keep 70% for immediate
                messages_to_keep.insert(0, message)
                current_tokens += message_tokens
            else:
                messages_to_summarize.insert(0, message)

        # Summarize older messages
        if messages_to_summarize:
            session_id = messages_to_summarize[0].get("session_id", "unknown")
            summary = self.summarizer.summarize_messages(
                messages_to_summarize, session_id
            )

            # Add to summarized context
            self.summarized_context.append(
                {"type": "summary", "summary": summary, "timestamp": time.time()}
            )

        # Update immediate context
        self.immediate_context = list(reversed(messages_to_keep))

        # Keep only recent summaries
        cutoff_time = time.time() - 3600  # 1 hour
        self.summarized_context = [
            s for s in self.summarized_context if s["timestamp"] > cutoff_time
        ]

        # Keep only in immediate context
        if len(self.immediate_context) > self.max_history:
            self.immediate_context = self.immediate_context[-self.max_history :]

    def get_context_for_llm(self, query: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get optimized context for LLM consumption"""
        with self._lock:
            context_messages = []

            # Add system message
            context_messages.append(
                {
                    "role": "system",
                    "content": "You are Neo-Clone, an advanced AI assistant with memory and context awareness.",
                }
            )

            # Add relevant summaries first
            if self.summarized_context:
                for summary_ctx in self.summarized_context[-3:]:  # Last 3 summaries
                    summary = summary_ctx["summary"]
                    summary_text = (
                        f"Previous conversation summary ({summary.message_count} messages): "
                        f"Topics: {', '.join(summary.key_topics)}. "
                        f"Intent: {summary.user_intent}. "
                        f"Outcome: {summary.outcome}."
                    )

                    context_messages.append({"role": "system", "content": summary_text})

            # Add relevant context from vector search if query provided
            if query:
                similar_contexts = self.vector_memory.find_similar(query, limit=3)
                for ctx in similar_contexts:
                    if ctx.message_type == "user":
                        context_messages.append(
                            {
                                "role": "system",
                                "content": f"Related previous user message: {ctx.text[:100]}...",
                            }
                        )

            # Add immediate context
            for msg in self.immediate_context:
                context_messages.append(
                    {"role": msg.get("role", "user"), "content": msg.get("content", "")}
                )

            return context_messages

    def search_context(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search through all context"""
        with self._lock:
            results = []

            # Search immediate context
            for msg in self.immediate_context:
                if query.lower() in msg.get("content", "").lower():
                    results.append(
                        {"type": "message", "message": msg, "relevance": 1.0}
                    )

            # Search vector memory
            similar_contexts = self.vector_memory.find_similar(
                query, limit=limit - len(results)
            )
            for ctx in similar_contexts:
                results.append(
                    {
                        "type": "vector_match",
                        "text": ctx.text,
                        "relevance": 0.8,  # Slightly lower than exact matches
                        "timestamp": ctx.timestamp,
                    }
                )

            # Sort by relevance and timestamp
            results.sort(
                key=lambda x: (x["relevance"], x.get("timestamp", 0)), reverse=True
            )

            return results[:limit]

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        with self._lock:
            return {
                "immediate_messages": len(self.immediate_context),
                "summarized_contexts": len(self.summarized_context),
                "vector_count": len(self.vector_memory.vectors),
                "estimated_tokens": sum(
                    len(m.get("content", "")) for m in self.immediate_context
                )
                / 4,
                "max_tokens": self.max_context_tokens,
                "utilization": min(
                    sum(len(m.get("content", "")) for m in self.immediate_context)
                    / 4
                    / self.max_context_tokens,
                    1.0,
                ),
            }

    def cleanup(self):
        """Cleanup old memory data"""
        self.vector_memory.cleanup_old_vectors()

        # Clean old summaries
        cutoff_time = time.time() - 86400  # 24 hours
        original_count = len(self.summarizer.summaries)
        self.summarizer.summaries = [
            s for s in self.summarizer.summaries if s.end_time > cutoff_time
        ]

        if len(self.summarizer.summaries) < original_count:
            logger.debug(
                f"Cleaned up {original_count - len(self.summarizer.summaries)} old summaries"
            )


# Global enhanced memory manager
enhanced_memory = SmartContextManager()
