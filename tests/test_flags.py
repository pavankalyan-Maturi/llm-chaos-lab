import pytest

from chaos import flags
from chaos.flags import Fault, FlagStore


def test_no_faults_registered_in_scaffold():
    assert flags.REGISTRY == {}
    assert flags.STORE.active() == []


@pytest.mark.parametrize(
    "name", ["FAULT_RETRIEVAL_HNSW_POSTFILTER", "FAULT_GATEWAY_X", "FAULT_MCP_RUG_PULL_2"]
)
def test_valid_names(name):
    flags.validate_name(name)


@pytest.mark.parametrize(
    "name", ["RETRIEVAL_X", "FAULT_retrieval_x", "FAULT_NOPE_X", "FAULT_GATEWAY_", "FAULT_GATEWAY"]
)
def test_invalid_names(name):
    with pytest.raises(ValueError):
        flags.validate_name(name)


@pytest.fixture
def temp_fault(monkeypatch):
    monkeypatch.setattr(flags, "REGISTRY", {})
    monkeypatch.delenv("FAULT_OBS_TEST", raising=False)
    return flags.register(Fault("FAULT_OBS_TEST", "test fault"))


def test_env_then_override(temp_fault, monkeypatch):
    store = FlagStore()
    assert not store.is_enabled("FAULT_OBS_TEST")
    monkeypatch.setenv("FAULT_OBS_TEST", "1")
    assert store.is_enabled("FAULT_OBS_TEST")
    store.set("FAULT_OBS_TEST", "0")
    assert not store.is_enabled("FAULT_OBS_TEST")
    store.clear()
    assert store.active() == ["FAULT_OBS_TEST"]


def test_unregistered_flag_raises(temp_fault):
    with pytest.raises(KeyError):
        FlagStore().value("FAULT_OBS_OTHER")


def test_duplicate_registration(temp_fault):
    with pytest.raises(ValueError):
        flags.register(Fault("FAULT_OBS_TEST", "again"))
