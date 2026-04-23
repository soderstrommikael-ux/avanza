"""
test_readonly_avanza.py — Tests for ReadOnlyAvanza wrapper.

Verifies:
  1. Approved read methods are accessible.
  2. Write / mutate methods are blocked.
  3. Return values are plain JSON-safe types (no custom objects).
  4. Direct attribute assignment is blocked.
  5. The underlying client cannot be accessed through the wrapper.

No real credentials are used — a mock client stands in for Avanza.
"""

import pytest
from unittest.mock import MagicMock

from readonly_avanza import ReadOnlyAvanza


@pytest.fixture
def mock_client():
    client = MagicMock()
    client.get_overview.return_value = {"totalOwnCapital": 100000, "accounts": []}
    client.get_accounts_positions.return_value = {"withOrderbook": [], "withoutOrderbook": []}
    client.get_watchlists.return_value = [{"id": "123", "name": "My watchlist", "orderbooks": []}]
    return client

@pytest.fixture
def ro(mock_client):
    return ReadOnlyAvanza(mock_client)


class TestReadMethodsExposed:
    def test_get_overview_exists(self, ro):
        assert callable(getattr(ro, "get_overview", None))

    def test_get_positions_exists(self, ro):
        assert callable(getattr(ro, "get_positions", None))

    def test_get_watchlists_exists(self, ro):
        assert callable(getattr(ro, "get_watchlists", None))

    def test_get_overview_returns_dict(self, ro):
        result = ro.get_overview()
        assert isinstance(result, dict)

    def test_get_positions_returns_dict(self, ro):
        result = ro.get_positions()
        assert isinstance(result, dict)

    def test_get_watchlists_returns_list(self, ro):
        result = ro.get_watchlists()
        assert isinstance(result, list)


WRITE_METHODS = [
    "place_order", "place_order_buy_fund", "place_order_sell_fund",
    "place_stop_loss_order", "edit_order", "delete_order",
    "delete_stop_loss_order", "add_to_watchlist", "remove_from_watchlist",
    "create_monthly_saving", "delete_monthly_saving", "pause_monthly_saving",
    "resume_monthly_saving", "set_price_alert", "delete_price_alert",
]

class TestWriteMethodsBlocked:
    @pytest.mark.parametrize("method_name", WRITE_METHODS)
    def test_write_method_raises(self, ro, method_name):
        with pytest.raises(AttributeError):
            getattr(ro, method_name)

    def test_hasattr_returns_false_for_place_order(self, ro):
        assert not hasattr(ro, "place_order")

    def test_hasattr_returns_false_for_delete_order(self, ro):
        assert not hasattr(ro, "delete_order")

    def test_hasattr_returns_false_for_edit_order(self, ro):
        assert not hasattr(ro, "edit_order")


class TestJsonSafeReturns:
    def _is_json_safe(self, obj):
        if isinstance(obj, (str, int, float, bool, type(None))):
            return True
        if isinstance(obj, dict):
            return all(isinstance(k, str) and self._is_json_safe(v) for k, v in obj.items())
        if isinstance(obj, list):
            return all(self._is_json_safe(v) for v in obj)
        return False

    def test_overview_is_json_safe(self, ro):
        assert self._is_json_safe(ro.get_overview())

    def test_positions_is_json_safe(self, ro):
        assert self._is_json_safe(ro.get_positions())

    def test_watchlists_is_json_safe(self, ro):
        assert self._is_json_safe(ro.get_watchlists())


class TestImmutability:
    def test_cannot_set_attribute(self, ro):
        with pytest.raises(AttributeError):
            ro.some_new_attr = "value"

    def test_cannot_overwrite_read_method(self, ro):
        with pytest.raises(AttributeError):
            ro.get_overview = lambda: {}


class TestClientNotExposed:
    def test_client_attribute_blocked(self, ro):
        with pytest.raises(AttributeError):
            _ = ro._client

    def test_no_raw_client_shortcut(self, ro):
        for attr in ("client", "avanza", "_avanza", "wrapped"):
            assert not hasattr(ro, attr)
