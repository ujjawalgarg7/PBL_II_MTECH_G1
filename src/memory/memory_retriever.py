from datetime import datetime

from src.memory.short_term_memory import ShortTermMemory
from src.memory.episodic_memory import EpisodicMemory
from src.memory.semantic_memory import SemanticMemory


class MemoryRetriever:
    """
    Retrieve and rank memories from all memory layers.

    MemoryScore:

        Score = alpha*S + beta*R + gamma*I + delta*C

    S = similarity
    R = recency
    I = importance
    C = task consistency
    """

    def __init__(
        self,
        short_term_memory,
        episodic_memory,
        semantic_memory,
        alpha=0.4,
        beta=0.2,
        gamma=0.2,
        delta=0.2,
    ):
        self.short_term_memory = short_term_memory
        self.episodic_memory = episodic_memory
        self.semantic_memory = semantic_memory

        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.delta = delta

        self._validate_weights()

    def _validate_weights(self):
        """Validate MemoryScore weights."""

        weights = [
            self.alpha,
            self.beta,
            self.gamma,
            self.delta,
        ]

        if any(weight < 0 for weight in weights):
            raise ValueError(
                "MemoryScore weights cannot be negative."
            )

        if sum(weights) == 0:
            raise ValueError(
                "At least one MemoryScore weight must be greater than zero."
            )

    @staticmethod
    def _tokenize(text):
        """Convert text into lowercase tokens."""

        if not text:
            return set()

        return {
            token.strip(".,!?():;[]{}\"'")
            for token in str(text).lower().split()
            if token.strip(".,!?():;[]{}\"'")
        }

    def _similarity(self, query, text):
        """
        Calculate simple token-based similarity.

        Returns a value between 0 and 1.
        """

        query_tokens = self._tokenize(query)
        text_tokens = self._tokenize(text)

        if not query_tokens or not text_tokens:
            return 0.0

        common_tokens = query_tokens.intersection(
            text_tokens
        )

        return len(common_tokens) / len(query_tokens)

    @staticmethod
    def _recency(timestamp):
        """
        Calculate recency score.

        Recent memories receive a higher score.
        """

        if not timestamp:
            return 0.0

        try:
            memory_time = datetime.fromisoformat(
                timestamp
            )
        except (ValueError, TypeError):
            return 0.0

        now = (
            datetime.now(memory_time.tzinfo)
            if memory_time.tzinfo
            else datetime.now()
        )

        age_seconds = max(
            0,
            (now - memory_time).total_seconds(),
        )

        return 1.0 / (
            1.0 + age_seconds / 3600
        )

    @staticmethod
    def _importance(memory):
        """Return the importance of a memory."""

        try:
            return float(
                memory.get(
                    "importance",
                    0.5,
                )
            )
        except (
            AttributeError,
            TypeError,
            ValueError,
        ):
            return 0.5

    @staticmethod
    def _consistency(memory, task_id):
        """
        Calculate task consistency.

        A memory belonging to the current task
        receives a score of 1.0.
        """

        if not task_id:
            return 0.0

        memory_task = memory.get(
            "task_id"
        )

        if memory_task == task_id:
            return 1.0

        return 0.0

    def _calculate_score(
        self,
        similarity,
        recency,
        importance,
        consistency,
    ):
        """Calculate the final MemoryScore."""

        return (
            self.alpha * similarity
            + self.beta * recency
            + self.gamma * importance
            + self.delta * consistency
        )

    def _build_result(
        self,
        memory_type,
        content,
        query,
        task_id=None,
    ):
        """Build a ranked retrieval result."""

        if memory_type == "short_term":
            text = str(content)

        elif memory_type == "episodic":
            text = " ".join(
                [
                    str(
                        content.get(
                            "event",
                            "",
                        )
                    ),
                    str(
                        content.get(
                            "reason",
                            "",
                        )
                    ),
                    str(
                        content.get(
                            "task_id",
                            "",
                        )
                    ),
                ]
            )

        else:
            text = " ".join(
                [
                    str(
                        content.get(
                            "key",
                            "",
                        )
                    ),
                    str(
                        content.get(
                            "value",
                            "",
                        )
                    ),
                    str(
                        content.get(
                            "source",
                            "",
                        )
                    ),
                ]
            )

        similarity = self._similarity(
            query,
            text,
        )

        if memory_type == "short_term":
            recency = 1.0
            importance = 0.5
            consistency = 0.0

        else:
            recency = self._recency(
                content.get(
                    "timestamp"
                )
            )

            importance = self._importance(
                content
            )

            consistency = self._consistency(
                content,
                task_id,
            )

        score = self._calculate_score(
            similarity,
            recency,
            importance,
            consistency,
        )

        return {
            "memory_type": memory_type,
            "content": content,
            "similarity": similarity,
            "recency": recency,
            "importance": importance,
            "consistency": consistency,
            "score": score,
        }

    def retrieve(
        self,
        query,
        task_id=None,
    ):
        """
        Retrieve and rank memories from all
        memory layers.
        """

        if not query:
            return []

        results = []

        # Short-term memory
        for item in self.short_term_memory.get_all():
            if (
                self._similarity(
                    query,
                    str(item),
                )
                > 0
            ):
                results.append(
                    self._build_result(
                        "short_term",
                        item,
                        query,
                        task_id,
                    )
                )

        # Episodic memory
        for item in self.episodic_memory.get_all():
            text = " ".join(
                [
                    str(
                        item.get(
                            "event",
                            "",
                        )
                    ),
                    str(
                        item.get(
                            "reason",
                            "",
                        )
                    ),
                    str(
                        item.get(
                            "task_id",
                            "",
                        )
                    ),
                ]
            )

            if (
                self._similarity(
                    query,
                    text,
                )
                > 0
            ):
                results.append(
                    self._build_result(
                        "episodic",
                        item,
                        query,
                        task_id,
                    )
                )

        # Semantic memory
        for item in self.semantic_memory.get_all():
            text = " ".join(
                [
                    str(
                        item.get(
                            "key",
                            "",
                        )
                    ),
                    str(
                        item.get(
                            "value",
                            "",
                        )
                    ),
                    str(
                        item.get(
                            "source",
                            "",
                        )
                    ),
                ]
            )

            if (
                self._similarity(
                    query,
                    text,
                )
                > 0
            ):
                results.append(
                    self._build_result(
                        "semantic",
                        item,
                        query,
                        task_id,
                    )
                )

        return sorted(
            results,
            key=lambda item: item["score"],
            reverse=True,
        )

    def retrieve_short_term(
        self,
        query,
    ):
        """Retrieve short-term memories."""

        return [
            result
            for result in self.retrieve(query)
            if result["memory_type"]
            == "short_term"
        ]

    def retrieve_episodic(
        self,
        query,
    ):
        """Retrieve episodic memories."""

        return [
            result
            for result in self.retrieve(query)
            if result["memory_type"]
            == "episodic"
        ]

    def retrieve_semantic(
        self,
        query,
    ):
        """Retrieve semantic memories."""

        return [
            result
            for result in self.retrieve(query)
            if result["memory_type"]
            == "semantic"
        ]