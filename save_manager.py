"""
save_manager.py
Handles reading and writing of save slots (1-10) to JSON.

Save file location: assets/saves/slot_<N>.json
"""

import json
import os
import sys
from datetime import datetime

def get_save_path(relative_path):
    """ Gets the real folder where the .exe is sitting to save data safely. """
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.abspath(".")
    return os.path.join(base_dir, relative_path)

SAVE_DIR = get_save_path(os.path.join("assets", "saves"))
SLOT_COUNT = 10

# Keys to strip from displayed_messages rows before saving —
# large or redundant fields that can be reconstructed.
_STRIP_KEYS = {'_CHAPTER', '_CHAPTER_IDX'}

# JSON-safe types — anything else gets coerced to str
_SAFE_TYPES = (str, int, float, bool, type(None))


def _slot_path(slot: int) -> str:
    return os.path.join(SAVE_DIR, f"slot_{slot}.json")


def _ensure_dir():
    os.makedirs(SAVE_DIR, exist_ok=True)


def _clean_row(row: dict) -> dict:
    """Strip non-serialisable / redundant keys and coerce values to JSON-safe types."""
    out = {}
    for k, v in row.items():
        if k in _STRIP_KEYS:
            continue
        if isinstance(v, _SAFE_TYPES):
            out[k] = v
        else:
            out[k] = str(v)
    return out


# ─────────────────────────────────────────────────────────────────────────────
#  Public API
# ─────────────────────────────────────────────────────────────────────────────

def save_slot(slot: int, chat_manager, preview_msg: str = "") -> bool:
    """
    Write current game state to slot N.

    Stored fields
    -------------
    slot             : int   — slot number
    timestamp        : str   — human-readable save time
    current_chapter  : int   — which chapter file is currently loaded
    script_index     : int   — row index within the current chapter
    displayed_messages: list — full content of every displayed message row
    ignored_ids      : list  — IDs permanently skipped by branch choices
    unlocked_private : list  — unlocked private sub-channel names
    preview_msg      : str   — last chat message, shown on the save card
    personnel_db     : dict  — live NPC statuses at save time
    """
    _ensure_dir()
    assert 1 <= slot <= SLOT_COUNT, f"Slot must be 1-{SLOT_COUNT}"

    # Serialise displayed_messages in full — no ID lookups needed on load
    displayed_rows = [_clean_row(r) for r in chat_manager.displayed_messages]

    # Also keep a list of IDs for the save-card stats display (backwards compat)
    displayed_ids = []
    for row in chat_manager.displayed_messages:
        rid = str(row.get('ID', '')).strip()
        if rid.endswith('.0'):
            rid = rid[:-2]
        if rid:
            displayed_ids.append(rid)

    unlocked = sorted(list(getattr(chat_manager, 'unlocked_private_channels', set())))

    payload = {
        "slot":              slot,
        "timestamp":         datetime.now().strftime("%Y-%m-%d  %H:%M"),
        "current_chapter":   getattr(chat_manager, 'current_chapter', 0),
        "script_index":      chat_manager.script_index,
        "displayed_messages": displayed_rows,
        "displayed_ids":     displayed_ids,   # kept for save-card stats only
        "ignored_ids":       sorted(list(chat_manager.ignored_ids)),
        "unlocked_private":  unlocked,
        "preview_msg":       preview_msg,
        "personnel_db":      dict(chat_manager.personnel_db),
    }

    try:
        with open(_slot_path(slot), 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        print(f"[SAVE] Slot {slot} written — chapter {payload['current_chapter']}, "
              f"index {payload['script_index']}, "
              f"{len(displayed_rows)} messages, "
              f"{len(chat_manager.ignored_ids)} ignored IDs.")
        return True
    except Exception as e:
        print(f"[SAVE] Failed writing slot {slot}: {e}")
        return False


def load_slot(slot: int, chat_manager) -> bool:
    """
    Restore game state from slot N into a live ChatManager.
    Returns True on success, False if slot is empty or corrupt.

    Because displayed_messages is stored in full, this works regardless of
    which chapter is currently loaded in full_script — no ID lookup needed.
    After this returns, the caller should call:
        chat_manager.restore_from_save(...)
    to swap in the correct chapter file.  We store the data on a temporary
    namespace so chat_interface.py can pick it up.
    """
    assert 1 <= slot <= SLOT_COUNT
    path = _slot_path(slot)

    if not os.path.exists(path):
        print(f"[LOAD] Slot {slot} is empty.")
        return False

    try:
        with open(path, 'r', encoding='utf-8') as f:
            payload = json.load(f)
    except Exception as e:
        print(f"[LOAD] Failed reading slot {slot}: {e}")
        return False

    # ── Restore ignored_ids ───────────────────────────────────────────────────
    chat_manager.ignored_ids = set(str(i) for i in payload.get("ignored_ids", []))

    # ── Restore script_index and chapter ─────────────────────────────────────
    chat_manager.script_index    = int(payload.get("script_index", 0))
    chat_manager.current_chapter = int(payload.get("current_chapter", 0))

    # ── Restore displayed_messages directly from saved content ───────────────
    # No full_script lookup needed — the full row data is in the save file.
    raw_msgs = payload.get("displayed_messages", [])

    # Backwards-compat: old saves only stored displayed_ids, not full rows.
    # In that case fall back to ID-based lookup (will only work for chapter 0).
    if raw_msgs:
        chat_manager.displayed_messages = raw_msgs
    else:
        _legacy_restore_by_ids(payload, chat_manager)

    # ── Restore unlocked private channels ────────────────────────────────────
    unlocked = payload.get("unlocked_private", [])
    if not hasattr(chat_manager, 'unlocked_private_channels'):
        chat_manager.unlocked_private_channels = set()
    chat_manager.unlocked_private_channels = set(unlocked)

    # ── Restore personnel statuses ────────────────────────────────────────────
    saved_personnel = payload.get("personnel_db", {})
    if saved_personnel:
        if not hasattr(chat_manager, 'personnel_db'):
            chat_manager.personnel_db = {}
        chat_manager.personnel_db.update(saved_personnel)

    # ── Reset transient state ─────────────────────────────────────────────────
    chat_manager.is_waiting         = False
    chat_manager.waiting_for_choice = False
    chat_manager.pending_choices    = []
    chat_manager.last_advance_time  = 0
    chat_manager._all_chapters_done = False

    print(f"[LOAD] Slot {slot} restored — chapter {chat_manager.current_chapter}, "
          f"index {chat_manager.script_index}, "
          f"{len(chat_manager.displayed_messages)} messages.")
    return True


def _legacy_restore_by_ids(payload: dict, chat_manager) -> None:
    """Fallback for old saves that only stored row IDs."""
    id_to_row = {}
    for row in chat_manager.full_script:
        rid = str(row.get('ID', '')).strip()
        if rid.endswith('.0'):
            rid = rid[:-2]
        if rid:
            id_to_row[rid] = row

    chat_manager.displayed_messages = []
    for rid in payload.get("displayed_ids", []):
        row = id_to_row.get(str(rid))
        if row:
            dr = dict(row)
            dr['MESSAGE']   = chat_manager._substitute(str(row.get('MESSAGE', '')))
            dr['CHARACTER'] = chat_manager._substitute(str(row.get('CHARACTER', '')))
            chat_manager.displayed_messages.append(dr)


def read_slot_meta(slot: int) -> dict | None:
    """Return save metadata for a slot without loading full state. None = empty."""
    path = _slot_path(slot)
    if not os.path.exists(path):
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def delete_slot(slot: int) -> bool:
    path = _slot_path(slot)
    if os.path.exists(path):
        os.remove(path)
        return True
    return False


def all_slot_metas() -> list[dict | None]:
    """Return list of 10 meta dicts (index 0 = slot 1). None = empty slot."""
    return [read_slot_meta(s) for s in range(1, SLOT_COUNT + 1)]