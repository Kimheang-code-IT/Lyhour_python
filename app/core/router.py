"""Page router: map page id (int) to stack index."""
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QWidget

# Page id (from nav) -> stack index. Order of registration = index.
_pages: list[type["QWidget"]] = []
_page_ids: list[int] = []


def register(page_id: int, page_factory: type["QWidget"]) -> None:
    """Register a page: page_id is the nav index, page_factory is the widget class (or a callable that returns QWidget)."""
    while len(_page_ids) <= page_id:
        _page_ids.append(-1)
    idx = len(_pages)
    _pages.append(page_factory)
    _page_ids[page_id] = idx


def get_index(page_id: int) -> int:
    """Return stack index for page_id. Assumes page_id equals registration order 0,1,2,3."""
    if 0 <= page_id < len(_page_ids) and _page_ids[page_id] >= 0:
        return _page_ids[page_id]
    return max(0, page_id) if page_id >= 0 else 0


def get_page_classes() -> list:
    """Return list of page classes/factories in stack order."""
    return list(_pages)


def clear() -> None:
    """Reset router (e.g. for tests)."""
    _pages.clear()
    _page_ids.clear()
