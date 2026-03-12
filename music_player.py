"""
music_player.py
───────────────────────────────────────────────────────────────────────────────
Handles all background music for "Ping: Connection Linked".

  - Scans assets/audio/ for .mp3 files automatically
  - Modes: SHUFFLE (default), LOOP (repeat one), AUTO (sequential)
  - Persists music_track, music_mode, music_volume to player_data.json
  - Exposes a simple API used by main_interface and chat_interface

PUBLIC API
──────────
  MusicPlayer(user_data)          — create & start playback
  player.update()                 — call once per frame to advance tracks
  player.next_track()             — skip to next
  player.prev_track()             — go to previous
  player.set_mode(mode)           — 'SHUFFLE' | 'LOOP' | 'AUTO'
  player.set_volume(0.0-1.0)      — set volume
  player.set_track(index)         — jump to specific track
  player.toggle_pause()           — pause / resume
  player.stop()                   — stop playback entirely
  player.save(user_data)          — persist prefs back to user_data dict
  player.track_name               — display name of current track (no ext)
  player.track_index              — int index into player.tracks
  player.tracks                   — list of full file paths
  player.mode                     — current mode string
  player.volume                   — float 0.0-1.0
  player.paused                   — bool
"""

import pygame
import os
import random
import sys


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


AUDIO_DIR   = resource_path(os.path.join("assets", "audio"))
MODES      = ["SHUFFLE", "LOOP", "AUTO"]
DEFAULT_VOL = 0.6


# ─────────────────────────────────────────────────────────────────────────────

def _scan_tracks():
    """Return sorted list of .mp3 paths from AUDIO_DIR. Empty list if none."""
    if not os.path.exists(AUDIO_DIR):
        print(f"[MUSIC] Audio directory not found: {AUDIO_DIR}")
        return []
    found = sorted(
        os.path.join(AUDIO_DIR, f)
        for f in os.listdir(AUDIO_DIR)
        if f.lower().endswith(".mp3")
    )
    print(f"[MUSIC] Found {len(found)} track(s): {[os.path.basename(p) for p in found]}")
    return found


def _display_name(path):
    """Strip directory and extension for UI display."""
    return os.path.splitext(os.path.basename(path))[0]


# ─────────────────────────────────────────────────────────────────────────────

class MusicPlayer:
    def __init__(self, user_data=None):
        ud = user_data or {}

        self.tracks = _scan_tracks()
        self.mode   = ud.get("music_mode",   "SHUFFLE")
        self.volume = float(ud.get("music_volume", DEFAULT_VOL))
        self.paused = False
        self._play_start_time = 0

        # Restore last track if it still exists, otherwise start fresh
        saved_track = ud.get("music_track", "")
        if saved_track and saved_track in self.tracks:
            self.track_index = self.tracks.index(saved_track)
        else:
            self.track_index = 0

        # Build shuffle order
        self._shuffle_order  = list(range(len(self.tracks)))
        self._shuffle_pos    = 0
        if self.mode == "SHUFFLE" and self.tracks:
            random.shuffle(self._shuffle_order)
            # Put the saved track first in the shuffle so it plays immediately
            if self.track_index in self._shuffle_order:
                self._shuffle_order.remove(self.track_index)
            self._shuffle_order.insert(0, self.track_index)

        # Start playback
        if self.tracks:
            self._load_and_play(self.track_index)
        else:
            print("[MUSIC] No tracks found — music disabled.")

    # ── Playback control ──────────────────────────────────────────────────────

    def _load_and_play(self, index):
        if not self.tracks:
            return
        self.track_index = index % len(self.tracks)
        path = self.tracks[self.track_index]
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(self.volume)
            pygame.mixer.music.play()
            self.paused = False
            self._play_start_time = pygame.time.get_ticks()   # ← ADD THIS
            print(f"[MUSIC] Playing: {_display_name(path)} [{self.mode}]")
        except Exception as e:
            print(f"[MUSIC] Error loading {path}: {e}")

    def update(self):
        if not self.tracks or self.paused:
            return

        # Guard: don't check busy() within 500ms of starting a track
        if pygame.time.get_ticks() - self._play_start_time < 500:   # ← ADD THIS
            return

        if pygame.mixer.music.get_busy():
            return  # still playing

        # Track finished — decide what to play next
        if self.mode == "LOOP":
            self._load_and_play(self.track_index)
        elif self.mode == "AUTO":
            next_idx = (self.track_index + 1) % len(self.tracks)
            self._load_and_play(next_idx)
        else:  # SHUFFLE
            self._shuffle_pos = (self._shuffle_pos + 1) % len(self._shuffle_order)
            if self._shuffle_pos == 0:
                random.shuffle(self._shuffle_order)
            self._load_and_play(self._shuffle_order[self._shuffle_pos])

    def next_track(self):
        """Skip to next track (respects mode for shuffle order)."""
        if not self.tracks:
            return
        if self.mode == "SHUFFLE":
            self._shuffle_pos = (self._shuffle_pos + 1) % len(self._shuffle_order)
            if self._shuffle_pos == 0:
                random.shuffle(self._shuffle_order)
            self._load_and_play(self._shuffle_order[self._shuffle_pos])
        else:
            self._load_and_play(self.track_index + 1)

    def prev_track(self):
        """Go to previous track."""
        if not self.tracks:
            return
        if self.mode == "SHUFFLE":
            self._shuffle_pos = (self._shuffle_pos - 1) % len(self._shuffle_order)
            self._load_and_play(self._shuffle_order[self._shuffle_pos])
        else:
            self._load_and_play(self.track_index - 1)

    def set_track(self, index):
        """Jump to a specific track by index."""
        if not self.tracks:
            return
        self.track_index = index % len(self.tracks)
        # Keep shuffle order consistent: move chosen track to current position
        if self.mode == "SHUFFLE" and self.track_index in self._shuffle_order:
            self._shuffle_order.remove(self.track_index)
            self._shuffle_order.insert(self._shuffle_pos, self.track_index)
        self._load_and_play(self.track_index)

    def set_mode(self, mode):
        """Set playback mode: 'SHUFFLE', 'LOOP', or 'AUTO'."""
        if mode not in MODES:
            return
        self.mode = mode
        if mode == "SHUFFLE":
            # Rebuild shuffle list from current position
            self._shuffle_order = list(range(len(self.tracks)))
            random.shuffle(self._shuffle_order)
            if self.track_index in self._shuffle_order:
                self._shuffle_order.remove(self.track_index)
            self._shuffle_order.insert(0, self.track_index)
            self._shuffle_pos = 0
        print(f"[MUSIC] Mode set to {mode}")

    def set_volume(self, vol):
        """Set volume 0.0–1.0."""
        self.volume = max(0.0, min(1.0, vol))
        pygame.mixer.music.set_volume(self.volume)

    def toggle_pause(self):
        if not self.tracks:
            return
        if self.paused:
            pygame.mixer.music.unpause()
            self.paused = False
        else:
            pygame.mixer.music.pause()
            self.paused = True

    def stop(self):
        pygame.mixer.music.stop()

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def track_name(self):
        if not self.tracks:
            return "NO TRACKS FOUND"
        return _display_name(self.tracks[self.track_index])

    # ── Persistence ───────────────────────────────────────────────────────────

    def save(self, user_data):
        """Write music prefs into user_data dict (caller saves to disk)."""
        user_data["music_mode"]   = self.mode
        user_data["music_volume"] = round(self.volume, 2)
        user_data["music_track"]  = self.tracks[self.track_index] if self.tracks else ""
        return user_data