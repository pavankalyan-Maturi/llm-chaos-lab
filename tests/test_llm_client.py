import pytest

from gateway.llm_client import Message, StubConfig, StubLLMClient

FAST = StubConfig(ttft_s=0.0, itl_s=0.0, price_in_per_m=1.0, price_out_per_m=2.0)
MSGS = [Message("system", "you are terse"), Message("user", "what is two plus two")]


async def test_complete_is_deterministic():
    llm = StubLLMClient(FAST)
    a = await llm.complete(MSGS, max_tokens=8)
    b = await llm.complete(MSGS, max_tokens=8)
    assert a == b
    assert a.usage.completion_tokens == 8
    assert len(a.text.split()) == 8


async def test_prompt_tokens_counted():
    out = await StubLLMClient(FAST).complete(MSGS, max_tokens=1)
    assert out.usage.prompt_tokens == 3 + 5
    assert out.usage.total_tokens == 9


async def test_different_prompts_differ():
    llm = StubLLMClient(FAST)
    a = await llm.complete([Message("user", "a")], max_tokens=4)
    b = await llm.complete([Message("user", "b")], max_tokens=4)
    assert a.text != b.text


async def test_stream_matches_complete():
    llm = StubLLMClient(FAST)
    chunks = [c async for c in llm.stream(MSGS, max_tokens=5)]
    assert len(chunks) == 5
    assert "".join(chunks) == (await llm.complete(MSGS, max_tokens=5)).text


async def test_rejects_zero_tokens():
    with pytest.raises(ValueError):
        await StubLLMClient(FAST).complete(MSGS, max_tokens=0)


async def test_cost():
    llm = StubLLMClient(FAST)
    out = await llm.complete(MSGS, max_tokens=10)
    assert llm.cost_usd(out.usage) == pytest.approx((8 * 1.0 + 10 * 2.0) / 1e6)
