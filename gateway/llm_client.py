"""LLM client interface plus a deterministic stub.

The stub lets every CPU-side lab run with no GPU and no API key. It produces
realistic timing (time to first token, inter-token latency), token counts and
SSE-style streaming, so gateway and streaming behavior can be observed. Swap in
an OpenAI-compatible client pointing at vLLM on a rented GPU for serving labs.
"""

from __future__ import annotations

import asyncio
import hashlib
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Message:
    role: str
    content: str


@dataclass(frozen=True)
class Usage:
    prompt_tokens: int
    completion_tokens: int

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


@dataclass(frozen=True)
class Completion:
    text: str
    model: str
    usage: Usage
    finish_reason: str = "stop"


@dataclass(frozen=True)
class StubConfig:
    model: str = "stub-1"
    ttft_s: float = 0.05
    itl_s: float = 0.01
    max_tokens: int = 64
    # USD per 1M tokens; lets cost attribution be tested end to end.
    price_in_per_m: float = 0.0
    price_out_per_m: float = 0.0


class LLMClient(Protocol):
    model: str

    async def complete(self, messages: list[Message], max_tokens: int | None = None) -> Completion: ...

    def stream(self, messages: list[Message], max_tokens: int | None = None) -> AsyncIterator[str]: ...


def count_tokens(text: str) -> int:
    """Whitespace token count. Good enough for a stub; never use for billing."""
    return len(text.split())


def _words_for(messages: list[Message], n: int) -> list[str]:
    seed = "\n".join(f"{m.role}:{m.content}" for m in messages).encode()
    digest = hashlib.sha256(seed).hexdigest()
    return [f"tok{digest[(i * 2) % len(digest) : (i * 2) % len(digest) + 2]}" for i in range(n)]


class StubLLMClient:
    """Deterministic: the same messages always give the same output."""

    def __init__(self, config: StubConfig | None = None) -> None:
        self.config = config or StubConfig()
        self.model = self.config.model

    def _n(self, max_tokens: int | None) -> int:
        n = self.config.max_tokens if max_tokens is None else max_tokens
        if n < 1:
            raise ValueError("max_tokens must be >= 1")
        return n

    async def complete(self, messages: list[Message], max_tokens: int | None = None) -> Completion:
        n = self._n(max_tokens)
        words = _words_for(messages, n)
        await asyncio.sleep(self.config.ttft_s + self.config.itl_s * (n - 1))
        prompt_tokens = sum(count_tokens(m.content) for m in messages)
        return Completion(
            text=" ".join(words),
            model=self.model,
            usage=Usage(prompt_tokens=prompt_tokens, completion_tokens=n),
        )

    async def stream(self, messages: list[Message], max_tokens: int | None = None) -> AsyncIterator[str]:
        n = self._n(max_tokens)
        for i, word in enumerate(_words_for(messages, n)):
            await asyncio.sleep(self.config.ttft_s if i == 0 else self.config.itl_s)
            yield word if i == 0 else " " + word

    def cost_usd(self, usage: Usage) -> float:
        return (
            usage.prompt_tokens * self.config.price_in_per_m
            + usage.completion_tokens * self.config.price_out_per_m
        ) / 1_000_000
