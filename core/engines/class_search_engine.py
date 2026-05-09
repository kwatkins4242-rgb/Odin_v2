class MemorySearch:
    """
    MemorySearch.search("what was my last project?") -> [
        {
            "content": "We discussed the auto shop project yesterday...",
            "layer": "longterm",
            "score": 0.92,
            "metadata": {...}
        },
        ...
    ]
    """

    def __init__(self) -> None:
        # Instantiate only if layer is available; otherwise stubbed.
        self.scorer: Optional[RelevanceScorer] = RelevanceScorer() if RelevanceScorer else None
        self.longterm: Optional[LongTermMemory] = LongTermMemory() if LongTermMemory else None
        self.kg: Optional[KnowledgeGraph] = KnowledgeGraph() if KnowledgeGraph else None
        self.summarizer: Optional[SummaryEngine] = SummaryEngine() if SummaryEngine else None

    # ----------------------------------------------------------------------- #
    # Public API
    # ----------------------------------------------------------------------- #
    async def search(
        self,
        query: str,
        top_k: int = 5,
        layers: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search across memory layers and return top_k results.

        Each dict has keys:
            content, layer, score, metadata
        """
        if not query or not query.strip():
            return []

        target_layers = set(layers) if layers else ALL_LAYERS
        if not target_layers.issubset(ALL_LAYERS):
            logger.warning("Unknown layer names ignored: %s", target_layers - ALL_LAYERS)
            target_layers &= ALL_LAYERS

        results: List[Dict[str, Any]] = []

        # Search each layer in parallel
        tasks = []
        if "longterm" in target_layers and self.longterm:
            tasks.append(self._search_longterm(query))
        if "knowledge" in target_layers and self.kg:
            tasks.append(self._search_knowledge_graph(query))
        if "summaries" in target_layers and self.summarizer:
            tasks.append(self._search_summaries(query))

        from asyncio import gather
        gathered = await gather(*tasks, return_exceptions=True)
        for g in gathered:
            if isinstance(g, Exception):
                logger.error("Layer search failed: %s", g, exc_info=True)
            else:
                results.extend(g or [])

        # Rank globally and deduplicate
        results.sort(key=lambda r: r["score"], reverse=True)
        deduped = self._deduplicate(results)
        return deduped[:top_k]

    def search_sync(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Synchronous wrapper around long-term memory only."""
        if not self.longterm or not self.scorer:
            return []
        results = self._search_longterm_sync(query)
        results.sort(key=lambda r: r["score"], reverse=True)
        return results[:top_k]

    def search_by_emotion(
        self,
        emotion: str,
        min_intensity: float = 0.0,
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        """Return memories matching a specific emotion above a minimum intensity."""
        if not self.longterm:
            return []

        raw = self.longterm.read_by_emotion(emotion, min_intensity)
        if not raw:
            return []

        now = time.time()
        scored: List[Dict[str, Any]] = []

        for m in raw:
            intensity = m.get("intensity", 0.2)
            ts = m.get("timestamp")
            if ts is None:
                # Fallback to ISO created_at
                ts = _to_epoch(m.get("created_at", ""))

            age_days = max(0, (now - ts) / 86400)
            recency = max(0.0, 1 - age_days / 30)
            score = round(intensity * 0.7 + recency * 0.3, 4)

            scored.append(
                {
                    "content": m["content"],
                    "layer": "longterm",
                    "score": score,
                    "emotion": emotion,
                    "intensity": intensity,
                    "metadata": {
                        "id": m.get("id"),
                        "category": m.get("category"),
                        "tags": m.get("tags", []),
                    },
                }
            )

        scored.sort(key=lambda r: r["score"], reverse=True)
        return scored[:top_k]

    def get_emotional_context(self, query: str) -> Dict[str, Any]:
        """
        Detect emotion in query and fetch relevant memories.
        Used by odin-core to decide response style.
        """
        try:
            from layers.layer2_longterm.extractor import classify_emotion
        except ImportError:
            classify_emotion = None

        if not classify_emotion:
            return {"detected_emotion": "neutral", "intensity": 0.0, "related_memories": [], "tone_hint": "balanced"}

        emo = classify_emotion(query)
        emotion = emo["emotion"]
        intensity = emo["intensity"]

        memories = []
        if emotion != "neutral" and intensity >= 0.4:
            memories = self.search_by_emotion(emotion, min_intensity=0.3, top_k=5)

        return {
            "detected_emotion": emotion,
            "intensity": intensity,
            "related_memories": memories,
            "tone_hint": _TONE_HINTS.get(emotion, "balanced"),
        }

    # ----------------------------------------------------------------------- #
    # Internal layer searchers
    # ----------------------------------------------------------------------- #
    async def _search_longterm(self, query: str) -> List[Dict[str, Any]]:
        """Async search for long-term memories."""
        return await asyncio.get_running_loop().run_in_executor(None, self._search_longterm_sync, query)

    def _search_longterm_sync(self, query: str) -> List[Dict[str, Any]]:
        if not self.longterm or not self.scorer:
            return []

        mems = self.longterm.get_all()
        if not mems:
            return []

        scored = self.scorer.score_batch(query, mems)
        results = []
        for m in scored:
            if m["_score"] <= 0:
                continue
            results.append(
                {
                    "content": m["content"],
                    "layer": "longterm",
                    "score": m["_score"],
                    "metadata": {
                        "id": m.get("id"),
                        "category": m.get("category"),
                        "tags": m.get("tags", []),
                        "confidence": m.get("confidence"),
                        "reinforcement": m.get("reinforcement_count", 1),
                        "created_at": m.get("created_at"),
                    },
                }
            )
        return results

    def _search_knowledge_graph(self, query: str) -> List[Dict[str, Any]]:
        if not self.kg or not self.scorer:
            return []

        results = []
        query_lower = query.lower()

        for node_id in list(self.kg.graph.nodes):
            node = self.kg.graph.nodes[node_id]
            label = node.get("label", "")
            ntype = node.get("node_type", "concept")

            fake = {
                "content": label,
                "category": ntype,
                "tags": [label.lower()],
                "confidence": 0.9,
                "reinforcement_count": self.kg.graph.degree(node_id),
            }
            score = self.scorer.score(query, fake)
            if score <= 0.1:
                continue

            neighbors = self.kg.get_neighbors(node_id, depth=1)[:3]
            neighbor_str = ", ".join(f"{n['relation']} {n['label']}" for n in neighbors)

            results.append(
                {
                    "content": f"{label}" + (f" ({neighbor_str})" if neighbor_str else ""),
                    "layer": "knowledge",
                    "score": score,
                    "metadata": {
                        "node_id": node_id,
                        "node_type": ntype,
                        "connections": self.kg.graph.degree(node_id),
                    },
                }
            )
        return results

    def _search_summaries(self, query: str) -> List[Dict[str, Any]]:
        if not self.summarizer or not self.scorer:
            return []

        summaries = self.summarizer.get_recent_summaries(days=14)
        if not summaries:
            return []

        results = []
        for summary in summaries:
            parts = []
            if summary.get("headline"):
                parts.append(summary["headline"])
            if summary.get("full_summary"):
                parts.append(summary["full_summary"][:300])
            for t in summary.get("key_takeaways", []):
                parts.append(t)

            content = " ".join(parts).strip()
            if not content:
                continue

            fake = {
                "content": content,
                "category": "event",
                "tags": summary.get("topics", []),
                "confidence": 1.0,
                "reinforcement_count": 1,
                "last_reinforced": summary.get("generated_at", ""),
            }
            score = self.scorer.score(query, fake)
            if score <= 0.1:
                continue

            results.append(
                {
                    "content": f"[{summary.get('date', 'unknown')}] {summary.get('headline', content[:100])}",
                    "layer": "summaries",
                    "score": score,
                    "metadata": {
                        "date": summary.get("date"),
                        "topics": summary.get("topics", []),
                        "mood": summary.get("mood_energy", ""),
                    },
                }
            )
        return results

    # ----------------------------------------------------------------------- #
    # Deduplication
    # ----------------------------------------------------------------------- #
    @staticmethod
    def _deduplicate(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen: Set[str] = set()
        unique = []
        for r in results:
            fp = _fingerprint(r["content"])
            if fp not in seen:
                unique.append(r)
                seen.add(fp)
        return unique


# --------------------------------------------------------------------------- #
# Utilities
# --------------------------------------------------------------------------- #
def _to_epoch(iso: str) -> float:
    """Convert ISO string → unix epoch seconds; fallback to 0."""
    if not iso:
        return 0.0
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp()
    except Exception:
        return 0.0
