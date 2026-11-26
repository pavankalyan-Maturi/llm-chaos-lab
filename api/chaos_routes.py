"""/chaos admin endpoint. Requires the X-Chaos-Token header.

During a blind game day, the person diagnosing must not call GET /chaos.
"""

from __future__ import annotations

import hmac

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

from api.settings import Settings, get_settings
from chaos.flags import REGISTRY, STORE


def require_token(
    x_chaos_token: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> None:
    if x_chaos_token is None or not hmac.compare_digest(x_chaos_token, settings.chaos_token):
        raise HTTPException(status_code=401, detail="bad or missing X-Chaos-Token")


router = APIRouter(prefix="/chaos", tags=["chaos"], dependencies=[Depends(require_token)])


class FlagUpdate(BaseModel):
    flags: dict[str, str]


@router.get("")
def list_flags() -> dict:
    return {
        "registered": {f: {"area": r.area, "description": r.description} for f, r in REGISTRY.items()},
        "values": STORE.snapshot(),
        "active": STORE.active(),
    }


@router.post("")
def set_flags(update: FlagUpdate) -> dict:
    unknown = [f for f in update.flags if f not in REGISTRY]
    if unknown:
        raise HTTPException(status_code=400, detail=f"unregistered flags: {unknown}")
    for flag, val in update.flags.items():
        STORE.set(flag, val)
    return {"active": STORE.active()}


@router.delete("")
def reset_flags() -> dict:
    STORE.clear()
    return {"active": STORE.active()}
