from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Generator, Iterable, List, Optional, Tuple

import json
import math

from utils.data_utils import EdgeList, Edge


@dataclass
class FakeNewsNetLoadConfig:
    root: Path
    alpha: float = 0.05  # weight mapping: p = 1 - exp(-alpha * count)
    news_limit: Optional[int] = None
    tweets_limit_per_news: Optional[int] = None


def _iter_news_dirs(root: Path) -> Generator[Path, None, None]:
    """
    Yield news item directories under FakeNewsNet root.
    Expected structure like: root/{politifact,gossipcop}/{fake,real}/*
    We consider any directory containing a 'tweets' subdirectory.
    """
    for domain in ("politifact", "gossipcop"):
        for label in ("fake", "real"):
            base = root / domain / label
            if not base.exists():
                continue
            for news_dir in base.iterdir():
                if not news_dir.is_dir():
                    continue
                if (news_dir / "tweets").exists():
                    yield news_dir


def _iter_tweet_jsons(news_dir: Path) -> Generator[dict, None, None]:
    tweets_dir = news_dir / "tweets"
    if not tweets_dir.exists():
        return
    # Common patterns: each tweet as a separate .json file, or a .jsonl file
    for p in tweets_dir.rglob("*.json"):
        try:
            with p.open("r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    yield data
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            yield item
        except Exception:
            # Try treating as JSONL
            try:
                with p.open("r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            obj = json.loads(line)
                            if isinstance(obj, dict):
                                yield obj
                        except Exception:
                            continue
            except Exception:
                continue


def _get_int(value: object) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(str(value))
    except Exception:
        return None


def _extract_edges_from_tweet(tweet: dict) -> List[Tuple[int, int, float]]:
    edges: List[Tuple[int, int, float]] = []
    user_id = None
    u = tweet.get("user")
    if isinstance(u, dict):
        user_id = _get_int(u.get("id") or u.get("id_str"))
    if user_id is None:
        user_id = _get_int(tweet.get("user_id") or tweet.get("user_id_str"))
    if user_id is None:
        return edges

    # Retweet edge: user -> original author
    rt = tweet.get("retweeted_status")
    if isinstance(rt, dict):
        rt_user = rt.get("user")
        if isinstance(rt_user, dict):
            orig = _get_int(rt_user.get("id") or rt_user.get("id_str"))
            if orig is not None:
                edges.append((user_id, orig, 1.0))

    # Reply edge: user -> replied-to user
    reply_to = _get_int(tweet.get("in_reply_to_user_id") or tweet.get("in_reply_to_user_id_str"))
    if reply_to is not None:
        edges.append((user_id, reply_to, 1.0))

    # Mentions: user -> mentioned user(s)
    entities = tweet.get("entities")
    if isinstance(entities, dict):
        mentions = entities.get("user_mentions")
        if isinstance(mentions, list):
            for m in mentions:
                if isinstance(m, dict):
                    mid = _get_int(m.get("id") or m.get("id_str"))
                    if mid is not None:
                        edges.append((user_id, mid, 0.5))  # mention weighted lower than retweet/reply

    return edges


def load_fakenewsnet_edges(cfg: FakeNewsNetLoadConfig) -> EdgeList:
    # Aggregate counts per directed pair
    pair_to_count: Dict[Tuple[int, int], float] = {}
    news_seen = 0

    for news_dir in _iter_news_dirs(cfg.root):
        if cfg.news_limit is not None and news_seen >= cfg.news_limit:
            break
        news_seen += 1

        tweets_seen = 0
        for tw in _iter_tweet_jsons(news_dir):
            if cfg.tweets_limit_per_news is not None and tweets_seen >= cfg.tweets_limit_per_news:
                break
            tweets_seen += 1
            for u, v, w in _extract_edges_from_tweet(tw):
                key = (u, v)
                pair_to_count[key] = pair_to_count.get(key, 0.0) + float(w)

    # Map counts to probabilities
    edges: List[Edge] = []
    for (u, v), c in pair_to_count.items():
        p = 1.0 - math.exp(-cfg.alpha * float(c))
        p = max(1e-4, min(0.95, p))
        edges.append((u, v, p))

    return EdgeList(edges=edges)
