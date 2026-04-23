"""
readonly_avanza.py — Strict read-only wrapper around the Avanza client.

Exposes only safe read methods. Write/mutate methods are NOT accessible.
Designed for use by OpenClaw (or any automated agent) where accidental
order placement or account mutation must be impossible.

Usage:
    from avanza import Avanza
    from readonly_avanza import ReadOnlyAvanza

    client = Avanza(credentials={...})  # you own the auth
    ro = ReadOnlyAvanza(client)

    overview   = ro.get_overview()    # dict
    positions  = ro.get_positions()   # dict
    watchlists = ro.get_watchlists()  # list of dicts
"""

from __future__ import annotations

from typing import Any, Dict, List


def _to_json_safe(obj: Any) -> Any:
    """Recursively convert an object to plain JSON-safe Python types."""
    if isinstance(obj, dict):
        return {k: _to_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_json_safe(v) for v in obj]
    # Pydantic / dataclass models expose __dict__ or model_dump
    if hasattr(obj, "model_dump"):
        return _to_json_safe(obj.model_dump())
    if hasattr(obj, "__dict__"):
        return _to_json_safe(vars(obj))
    # Scalars that are JSON-safe
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    # Fallback: stringify anything else (e.g. Decimal, date)
    return str(obj)


class ReadOnlyAvanza:
    """
    A strict read-only façade over the Avanza client.

    Only the three approved read methods are exposed.
    No write, mutate, order, or delete methods are accessible.
    All return values are plain JSON-safe dicts/lists.
    """

    # The three public names this wrapper exposes.
    # __getattr__ is only invoked when normal attribute lookup fails, so
    # these explicit methods take priority. The allowlist is used solely
    # to produce a helpful error message for any other attribute access.
    _ALLOWED_METHODS = frozenset({"get_overview", "get_positions", "get_watchlists"})

    def __init__(self, client: Any) -> None:
        # Store the underlying client in a name-mangled attribute so it
        # cannot be trivially accessed as `wrapper._client`.
        object.__setattr__(self, "_ReadOnlyAvanza__client", client)

    # ------------------------------------------------------------------
    # Attribute guard — prevent any access not in the allowlist
    # ------------------------------------------------------------------

    def __getattr__(self, name: str) -> Any:
        # This is only reached for attributes not found via normal lookup
        # (i.e. NOT get_overview / get_positions / get_watchlists, which are
        # defined explicitly below and always resolve before __getattr__).
        raise AttributeError(
            f"'{type(self).__name__}' does not expose '{name}'. "
            "Only these read methods are available: "
            + ", ".join(sorted(self._ALLOWED_METHODS))
        )

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError(
            f"'{type(self).__name__}' is read-only and does not support attribute assignment."
        )

    # ------------------------------------------------------------------
    # Explicit read methods
    # ------------------------------------------------------------------

    def get_overview(self) -> Dict[str, Any]:
        """Return account overview as a plain dict."""
        client = object.__getattribute__(self, "_ReadOnlyAvanza__client")
        return _to_json_safe(client.get_overview())

    def get_positions(self) -> Dict[str, Any]:
        """Return current positions as a plain dict.

        Delegates to client.get_accounts_positions() — the only positions
        method on the underlying Avanza client.
        """
        client = object.__getattribute__(self, "_ReadOnlyAvanza__client")
        return _to_json_safe(client.get_accounts_positions())

    def get_watchlists(self) -> List[Dict[str, Any]]:
        """Return watchlists as a plain list of dicts."""
        client = object.__getattribute__(self, "_ReadOnlyAvanza__client")
        return _to_json_safe(client.get_watchlists())
