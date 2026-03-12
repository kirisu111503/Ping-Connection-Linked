import pygame
import sys
import pandas as pd
import os
import json
from profile import run_profile
from save_page import run_save_page
from load_page import run_load_page
from main_interface import run_settings

# --- CONFIGURATION & COLORS ---
INTERNAL_WIDTH = 1000
INTERNAL_HEIGHT = 600
COLOR_BG = (10, 10, 15)
COLOR_TEXT = (200, 255, 200)
COLOR_PANEL_BG = (18, 18, 25)
COLOR_LINE = (40, 40, 60)
COLOR_MUTED = (80, 100, 80)
COLOR_ACCENT = (0, 255, 0)
COLOR_LOCKED = (255, 100, 100)
COLOR_CARD_BG = (22, 28, 22)
COLOR_CARD_BORDER = (0, 200, 0)
COLOR_BTN_BG = (0, 60, 0)
COLOR_BTN_HOVER = (0, 100, 0)

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# The channel name that uses the private-unlock system.
PRIVATE_CHANNEL = "#PRIVATE"

def apply_theme(user_data):
    """Updates global fonts and colors based on user preferences."""
    global COLOR_TEXT, COLOR_MUTED, COLOR_ACCENT
    global COLOR_CARD_BORDER, COLOR_BTN_BG, COLOR_BTN_HOVER
    global COLOR_CARD_BG
    
    if not user_data:
        return
        
    color_choice = user_data.get("theme_color", "GREEN")
    
    color_map = {
        "GREEN":   {"accent": (0, 255, 0),     "text": (200, 255, 200), "muted": (80, 100, 80),   "border": (0, 200, 0),     "btn_bg": (0, 60, 0),     "btn_hov": (0, 100, 0),   "card_bg": (18, 28, 18)},
        "AMBER":   {"accent": (255, 176, 0),   "text": (255, 230, 150), "muted": (160, 110, 0),   "border": (200, 140, 0),   "btn_bg": (60, 40, 0),    "btn_hov": (100, 70, 0),  "card_bg": (28, 22, 12)},
        "CYAN":    {"accent": (0, 255, 255),   "text": (200, 255, 255), "muted": (0, 160, 160),   "border": (0, 200, 200),   "btn_bg": (0, 60, 60),    "btn_hov": (0, 100, 100), "card_bg": (12, 26, 28)},
        "RED":     {"accent": (255, 50, 50),   "text": (255, 200, 200), "muted": (180, 50, 50),   "border": (200, 0, 0),     "btn_bg": (60, 0, 0),     "btn_hov": (100, 0, 0),   "card_bg": (28, 14, 14)},
        "BLUE":    {"accent": (100, 150, 255), "text": (200, 220, 255), "muted": (50, 100, 200),  "border": (50, 100, 200),  "btn_bg": (0, 20, 60),    "btn_hov": (0, 50, 100),  "card_bg": (14, 18, 28)},
        "MAGENTA": {"accent": (255, 0, 255),   "text": (255, 200, 255), "muted": (160, 0, 160),   "border": (200, 0, 200),   "btn_bg": (60, 0, 60),    "btn_hov": (100, 0, 100), "card_bg": (26, 14, 26)},
        "WHITE":   {"accent": (220, 220, 220), "text": (255, 255, 255), "muted": (140, 140, 140), "border": (180, 180, 180), "btn_bg": (50, 50, 50),   "btn_hov": (90, 90, 90),  "card_bg": (24, 24, 28)}
    }
    
    if color_choice in color_map:
        c = color_map[color_choice]
        COLOR_ACCENT      = c["accent"]
        COLOR_TEXT        = c["text"]
        COLOR_MUTED       = c["muted"]
        COLOR_CARD_BORDER = c["border"]
        COLOR_BTN_BG      = c["btn_bg"]
        COLOR_BTN_HOVER   = c["btn_hov"]
        COLOR_CARD_BG     = c["card_bg"]

# --- HELPER FUNCTIONS ---
STORY_DIR = resource_path(os.path.join("assets", "scripts", "story"))

def discover_chapters() -> list[str]:
    """Return sorted list of chapter filenames (e.g. ['0.xlsx','1.xlsx','2.xlsx'])."""
    if not os.path.exists(STORY_DIR):
        print(f"ERROR: Story directory not found: {STORY_DIR}")
        return []
    files = sorted(
        f for f in os.listdir(STORY_DIR)
        if f.endswith('.xlsx') and not f.startswith('~$')
    )
    print(f"[CHAPTER] Discovered {len(files)} chapter(s): {files}")
    return files


def load_chapter(filename: str, chapter_idx: int, mark_read: bool = False) -> list:
    """
    Load a single chapter xlsx into a list of row dicts.

    Parameters
    ----------
    filename    : e.g. '0.xlsx'
    chapter_idx : integer index (0-based) used for sorting/tracking
    mark_read   : if True, every row is pre-marked IS_READ=1 (instant replay)
    """
    path = os.path.join(STORY_DIR, filename)
    try:
        df = pd.read_excel(path)
        if 'is_typing'   not in df.columns: df['is_typing']   = 0
        if 'SUB-CHANNEL' not in df.columns: df['SUB-CHANNEL'] = 'general'
        if 'IS_READ'     not in df.columns: df['IS_READ']      = 0
        if 'IS_CHOSEN'   not in df.columns: df['IS_CHOSEN']    = 0

        records = df.fillna('').to_dict('records')
        for row in records:
            ch = str(row.get('CHANNEL', '')).strip()
            if ch and not ch.startswith('#'):
                row['CHANNEL'] = '#' + ch
            row['_CHAPTER']     = filename
            row['_CHAPTER_IDX'] = chapter_idx
            if mark_read:
                row['IS_READ'] = 1
        print(f"[CHAPTER] Loaded {len(records)} rows from {filename}"
              f"{' (pre-read)' if mark_read else ''}")
        return records
    except Exception as e:
        print(f"[CHAPTER] ERROR loading {filename}: {e}")
        return []


def load_script():
    """Legacy wrapper — loads only chapter 0 for a fresh game start."""
    chapters = discover_chapters()
    if not chapters:
        return []
    return load_chapter(chapters[0], chapter_idx=0)

def load_npc_data():
    path = resource_path(os.path.join("assets", "scripts", "NPC.xlsx"))
    try:
        df = pd.read_excel(path)
        return df.fillna('').to_dict('records')
    except Exception as e:
        print(f"ERROR LOADING NPC DATA: {e}")
        return []

def load_server_data():
    path = resource_path(os.path.join("assets", "scripts", "server.json"))
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        channel_tree = {}
        for channel in data.get("alice_network", []):
            ch_name = channel.get("channel_name", "")
            subs = [sub.get("name", "") for sub in channel.get("sub_channels", [])]
            channel_tree[ch_name] = subs
        return channel_tree
    except Exception as e:
        print(f"ERROR LOADING SERVER JSON: {e}")
        return {"#public-hub": ["general"]}

def draw_panel(surface, rect, title, font):
    pygame.draw.rect(surface, COLOR_PANEL_BG, rect)
    pygame.draw.rect(surface, COLOR_LINE, rect, 2)
    title_rect = pygame.Rect(rect.x, rect.y, rect.width, 30)
    pygame.draw.rect(surface, COLOR_LINE, title_rect)
    title_surf = font.render(title, True, COLOR_TEXT)
    surface.blit(title_surf, (rect.x + 10, rect.y + 5))

def render_wrapped_text(surface, text, font, color, x, y, max_width=None, draw=True):
    if isinstance(x, pygame.Rect):
        rect      = x
        cur_y_in  = y
        x         = rect.x + 10
        y         = cur_y_in
        max_width = rect.width - 20

    words = text.split() 
    line  = []
    cur_y = y

    for word in words:
        test_line  = ' '.join(line + [word])
        test_width, _ = font.size(test_line)
        if test_width > max_width:
            if not line:
                if draw and surface:
                    surface.blit(font.render(word, True, color), (x, cur_y))
                cur_y += font.get_linesize()
            else:
                if draw and surface:
                    surface.blit(font.render(' '.join(line), True, color), (x, cur_y))
                line  = [word]
                cur_y += font.get_linesize()
        else:
            line.append(word)

    if line:
        if draw and surface:
            surface.blit(font.render(' '.join(line), True, color), (x, cur_y))
        cur_y += font.get_linesize()

    return cur_y + 15


# --- NARRATOR OVERLAY ---
class NarratorOverlay:
    """
    Full-screen semi-transparent overlay that displays NARRATOR / inner-monologue
    text without adding anything to the chat feed.
    """

    FADE_IN_MS   = 350
    FADE_OUT_MS  = 300
    HOLD_MIN_MS  = 600
    BOX_ALPHA    = 210

    def __init__(self):
        self.visible  = False
        self.done     = False
        self.text     = ""
        self.speaker  = ""

        self._state       = 'idle'
        self._state_start = 0
        self._alpha       = 0

        self.auto_dismiss_ms = 0

    def show(self, text: str, speaker: str = "", auto_dismiss_ms: int = 0):
        self.text            = text
        self.speaker         = speaker
        self.auto_dismiss_ms = auto_dismiss_ms
        self.visible         = True
        self.done            = False
        self._state          = 'fade_in'
        self._state_start    = pygame.time.get_ticks()
        self._alpha          = 0

    def dismiss(self):
        if self._state in ('fade_in', 'hold'):
            self._state       = 'fade_out'
            self._state_start = pygame.time.get_ticks()

    def force_close(self):
        self._alpha  = 0
        self.visible = False
        self.done    = True
        self._state  = 'idle'

    def update(self, now: int):
        if not self.visible:
            return

        elapsed = now - self._state_start

        if self._state == 'fade_in':
            self._alpha = min(255, int(255 * elapsed / max(1, self.FADE_IN_MS)))
            if elapsed >= self.FADE_IN_MS:
                self._state       = 'hold'
                self._state_start = now

        elif self._state == 'hold':
            self._alpha = 255
            if self.auto_dismiss_ms > 0:
                if elapsed >= max(self.HOLD_MIN_MS, self.auto_dismiss_ms):
                    self.dismiss()

        elif self._state == 'fade_out':
            self._alpha = max(0, int(255 * (1.0 - elapsed / max(1, self.FADE_OUT_MS))))
            if elapsed >= self.FADE_OUT_MS:
                self._alpha  = 0
                self.visible = False
                self.done    = True
                self._state  = 'idle'

    def handle_click(self) -> bool:
        if not self.visible:
            return False
        if self._state in ('fade_in', 'hold'):
            self.dismiss()
            return True
        return False

    def draw(self, canvas, font_title, font_body, now: int):
        if not self.visible or self._alpha == 0:
            return

        vignette = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT), pygame.SRCALPHA)
        vignette.fill((0, 0, 0, int(0.72 * self._alpha)))
        canvas.blit(vignette, (0, 0))

        box_w   = int(INTERNAL_WIDTH * 0.62)
        box_pad = 36
        line_h  = font_body.get_linesize()

        words     = self.text.split()
        lines     = []
        cur_line  = []
        max_text_w = box_w - box_pad * 2
        for word in words:
            test = ' '.join(cur_line + [word])
            if font_body.size(test)[0] > max_text_w and cur_line:
                lines.append(' '.join(cur_line))
                cur_line = [word]
            else:
                cur_line.append(word)
        if cur_line:
            lines.append(' '.join(cur_line))

        speaker_h    = (font_title.get_linesize() + 8) if self.speaker else 0
        text_block_h = len(lines) * line_h
        box_h        = speaker_h + text_block_h + box_pad * 2

        box_x = (INTERNAL_WIDTH  - box_w) // 2
        box_y = (INTERNAL_HEIGHT - box_h) // 2

        box_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        box_col  = (*COLOR_CARD_BG, int(self.BOX_ALPHA * self._alpha / 255))
        pygame.draw.rect(box_surf, box_col, (0, 0, box_w, box_h), border_radius=10)
        canvas.blit(box_surf, (box_x, box_y))

        pulse     = 0.75 + 0.25 * abs((now % 2000) / 1000.0 - 1.0)
        bdr_alpha = int(self._alpha * pulse)
        bdr_col   = tuple(int(c * bdr_alpha / 255) for c in COLOR_ACCENT)
        pygame.draw.rect(canvas, bdr_col,
                         pygame.Rect(box_x, box_y, box_w, box_h), 2, border_radius=10)

        corner_sz = 6
        for cx_, cy_ in [(box_x, box_y), (box_x + box_w - corner_sz, box_y),
                         (box_x, box_y + box_h - corner_sz),
                         (box_x + box_w - corner_sz, box_y + box_h - corner_sz)]:
            pygame.draw.rect(canvas, COLOR_ACCENT, (cx_, cy_, corner_sz, corner_sz))

        pygame.draw.line(canvas, COLOR_LINE,
                         (box_x + 16, box_y + box_pad // 2 + speaker_h - 4),
                         (box_x + box_w - 16, box_y + box_pad // 2 + speaker_h - 4))

        text_y = box_y + box_pad
        if self.speaker:
            spk_surf = font_title.render(f"[ {self.speaker.upper()} ]", True, COLOR_ACCENT)
            spk_x    = box_x + (box_w - spk_surf.get_width()) // 2
            canvas.blit(spk_surf, (spk_x, text_y))
            text_y  += font_title.get_linesize() + 8

        for line in lines:
            line_surf = font_body.render(line, True, COLOR_TEXT)
            lx        = box_x + (box_w - line_surf.get_width()) // 2
            canvas.blit(line_surf, (lx, text_y))
            text_y   += line_h

        if self._state == 'hold' and self.auto_dismiss_ms == 0:
            blink_on = (now // 500) % 2 == 0
            if blink_on:
                hint = FONT_SMALL_REF.render("[ click to continue ]", True, COLOR_MUTED) \
                       if FONT_SMALL_REF else None
                if hint:
                    canvas.blit(hint, (box_x + box_w - hint.get_width() - 12,
                                       box_y + box_h - hint.get_height() - 10))

# Module-level reference updated by run_chat so NarratorOverlay.draw() can use it
FONT_SMALL_REF = None


# --- NPC PROFILE CARD ---
class NpcProfileCard:
    """A small popup card showing basic NPC info when clicking a name in the personnel panel."""

    CARD_W = 215
    CARD_H = 295
    PIC_SIZE = 56
    BTN_H = 28

    def __init__(self):
        self.visible = False
        self.npc_name = ""
        self.npc_info = {}
        self.card_rect = pygame.Rect(0, 0, self.CARD_W, self.CARD_H)
        self.btn_rect  = pygame.Rect(0, 0, self.CARD_W - 20, self.BTN_H)
        self.profile_requested = None

        self._avatar_cache = {}
        self._current_avatar = self._make_placeholder_avatar(self.PIC_SIZE)

    def _make_placeholder_avatar(self, size):
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(surf, (30, 50, 30), (size // 2, size // 2), size // 2)
        pygame.draw.circle(surf, COLOR_CARD_BORDER, (size // 2, size // 2), size // 2, 2)
        head_r = size // 5
        cx = size // 2
        head_y = size // 3
        pygame.draw.circle(surf, (100, 160, 100), (cx, head_y), head_r)
        body_rect = pygame.Rect(cx - head_r - 2, head_y + head_r, (head_r + 2) * 2, head_r + 6)
        pygame.draw.ellipse(surf, (80, 130, 80), body_rect)
        return surf

    def show(self, npc_name, npc_info, anchor_pos):
        self.visible = True
        self.npc_name = npc_name
        self.npc_info = npc_info

        cx, cy = anchor_pos
        card_x = cx - self.CARD_W - 8
        card_y = cy - self.CARD_H // 2
        card_x = max(0, min(card_x, INTERNAL_WIDTH  - self.CARD_W))
        card_y = max(0, min(card_y, INTERNAL_HEIGHT - self.CARD_H))

        self.card_rect = pygame.Rect(card_x, card_y, self.CARD_W, self.CARD_H)
        self.btn_rect  = pygame.Rect(
            card_x + 10,
            card_y + self.CARD_H - self.BTN_H - 10,
            self.CARD_W - 20,
            self.BTN_H
        )

        profile_id = str(npc_info.get('PROFILE_ID', '')).strip()
        if profile_id and profile_id != '':
            if profile_id in self._avatar_cache:
                self._current_avatar = self._avatar_cache[profile_id]
            else:
                img_path = resource_path(os.path.join("assets", "images", f"{profile_id}.png"))
                print(f"[DEBUG] PROFILE_ID={repr(profile_id)}, path={img_path}, exists={os.path.exists(img_path)}")
                print(f"[DEBUG] Full npc_info keys: {list(npc_info.keys())}")
                try:
                    raw = pygame.image.load(img_path).convert_alpha()
                    scaled = pygame.transform.smoothscale(raw, (self.PIC_SIZE, self.PIC_SIZE))
                    result = pygame.Surface((self.PIC_SIZE, self.PIC_SIZE), pygame.SRCALPHA)
                    result.fill((0, 0, 0, 0))
                    cx_m = self.PIC_SIZE // 2
                    cy_m = self.PIC_SIZE // 2
                    r_m  = self.PIC_SIZE // 2
                    for py in range(self.PIC_SIZE):
                        for px in range(self.PIC_SIZE):
                            if (px - cx_m) ** 2 + (py - cy_m) ** 2 <= r_m ** 2:
                                result.set_at((px, py), scaled.get_at((px, py)))
                    pygame.draw.circle(result, COLOR_CARD_BORDER, (cx_m, cy_m), r_m, 2)
                    self._avatar_cache[profile_id] = result
                    self._current_avatar = result
                except Exception as e:
                    print(f"[PROFILE PIC] Could not load {img_path}: {e}")
                    self._current_avatar = self._make_placeholder_avatar(self.PIC_SIZE)
        else:
            self._current_avatar = self._make_placeholder_avatar(self.PIC_SIZE)

    def hide(self):
        self.visible = False
        self.profile_requested = None

    def handle_click(self, pos):
        if not self.visible:
            return False
        if self.btn_rect.collidepoint(pos):
            self.profile_requested = self.npc_name
            return True
        if self.card_rect.collidepoint(pos):
            return True
        self.hide()
        return False

    def draw(self, canvas, font_label, font_value, font_btn, mouse_pos):
        if not self.visible:
            return

        shadow = pygame.Rect(self.card_rect.x + 3, self.card_rect.y + 3,
                             self.CARD_W, self.CARD_H)
        pygame.draw.rect(canvas, (5, 10, 5), shadow, border_radius=8)
        pygame.draw.rect(canvas, COLOR_CARD_BG, self.card_rect, border_radius=8)
        pygame.draw.rect(canvas, COLOR_CARD_BORDER, self.card_rect, 2, border_radius=8)

        hdr = pygame.Rect(self.card_rect.x, self.card_rect.y, self.CARD_W, 26)
        pygame.draw.rect(canvas, COLOR_BTN_BG, hdr,
                         border_top_left_radius=8, border_top_right_radius=8)
        hdr_surf = font_label.render("[ PROFILE ]", True, COLOR_ACCENT)
        canvas.blit(hdr_surf, (hdr.x + 8, hdr.y + 4))

        x_surf = font_value.render("✕", True, COLOR_MUTED)
        canvas.blit(x_surf, (hdr.right - 18, hdr.y + 4))

        pic_x = self.card_rect.x + (self.CARD_W - self.PIC_SIZE) // 2
        pic_y = self.card_rect.y + 32
        canvas.blit(self._current_avatar, (pic_x, pic_y))

        name_surf = font_label.render(self.npc_name, True, COLOR_ACCENT)
        name_x = self.card_rect.x + (self.CARD_W - name_surf.get_width()) // 2
        canvas.blit(name_surf, (name_x, pic_y + self.PIC_SIZE + 4))

        fields = [
            ("NAME",  self.npc_info.get('FULLNAME', '???')),
            ("AGE",   self.npc_info.get('AGE',      '???')),
            ("SEX",   self.npc_info.get('SEX',      '???')),
            ("ROLE",  self.npc_info.get('ROLE',     '???')),
        ]
        row_y = pic_y + self.PIC_SIZE + 22
        for label, value in fields:
            lbl_surf = font_value.render(f"{label}: ", True, COLOR_MUTED)
            val_surf = font_value.render(str(value), True, COLOR_TEXT)
            canvas.blit(lbl_surf, (self.card_rect.x + 10, row_y))
            canvas.blit(val_surf, (self.card_rect.x + 10 + lbl_surf.get_width(), row_y))
            row_y += font_value.get_linesize() + 2

        bio_text = str(self.npc_info.get('BIO', ''))
        if bio_text and bio_text not in ('', '???'):
            row_y += 4
            pygame.draw.line(canvas, COLOR_LINE,
                             (self.card_rect.x + 8, row_y),
                             (self.card_rect.right - 8, row_y))
            row_y += 5
            bio_lbl = font_value.render("BIO:", True, COLOR_MUTED)
            canvas.blit(bio_lbl, (self.card_rect.x + 10, row_y))
            row_y += font_value.get_linesize() + 1
            max_bio_w = self.CARD_W - 20
            words = bio_text.split()
            line_words = []
            for word in words:
                test = ' '.join(line_words + [word])
                if font_value.size(test)[0] > max_bio_w and line_words:
                    bio_line_surf = font_value.render(' '.join(line_words), True, (150, 190, 150))
                    canvas.blit(bio_line_surf, (self.card_rect.x + 10, row_y))
                    row_y += font_value.get_linesize()
                    line_words = [word]
                else:
                    line_words.append(word)
            if line_words:
                bio_line_surf = font_value.render(' '.join(line_words), True, (150, 190, 150))
                canvas.blit(bio_line_surf, (self.card_rect.x + 10, row_y))

        btn_color = COLOR_BTN_HOVER if self.btn_rect.collidepoint(mouse_pos) else COLOR_BTN_BG
        pygame.draw.rect(canvas, btn_color, self.btn_rect, border_radius=4)
        pygame.draw.rect(canvas, COLOR_CARD_BORDER, self.btn_rect, 1, border_radius=4)
        btn_text = font_btn.render("[ VIEW FULL PROFILE ]", True, COLOR_ACCENT)
        bx = self.btn_rect.x + (self.btn_rect.width  - btn_text.get_width())  // 2
        by = self.btn_rect.y + (self.btn_rect.height - btn_text.get_height()) // 2
        canvas.blit(btn_text, (bx, by))


# --- CHAT LOGIC MANAGER ---
class ChatManager:
    def __init__(self, script_data, personnel_db, username="", name=""):
        self.full_script  = script_data
        self.personnel_db = personnel_db
        self.username     = username
        self.name         = name
        self.displayed_messages = []
        self.script_index = 0

        # Typing animation state
        self.is_waiting        = False
        self.typing_timer      = 0
        self.typing_duration   = 0
        self.current_typer     = ""
        self.typing_channel    = ""
        self.typing_subchannel = ""

        self.advance_delay     = 800
        self.last_advance_time = 0

        # ── Choice / branching state ──────────────────────────────────────────
        self.waiting_for_choice = False
        self.pending_choices    = []
        self.choice_made        = False

        # ── Narrator state ────────────────────────────────────────────────────
        self.is_narrator_active = False
        self._narrator_row_done = False

        # Build an ID → list-index lookup for fast JUMP_TO resolution
        self._id_index: dict = {}
        self._rebuild_id_index()

        # IDs to permanently skip
        self.ignored_ids: set = set()

        # ── AUTO / SKIP mode state ────────────────────────────────────────────
        self.auto_mode  = False
        self.skip_mode  = False
        self.auto_delay = 1200
        self.skip_delay = 80

        # ── Click-to-advance flag (normal mode) ───────────────────────────────
        self._click_pending = False

        # ── Choice history — snapshots taken just before each choice ──────────
        self._choice_snapshots = []
        self._all_chapters_done = False  # set True when last chapter is exhausted

        # ── Private channel unlock tracking ───────────────────────────────────
        self.unlocked_private_channels: set = set()

        # ── Chapter tracking ──────────────────────────────────────────────────
        # chapter_files : full sorted list discovered on disk
        # current_chapter: index into chapter_files of the chapter now loaded
        self.chapter_files:   list = []
        self.current_chapter: int  = 0

        self._fast_forward_read_messages()

        # Seed unlocked channels from already-replayed history
        self._refresh_unlocked_private_channels()

    # ── Private channel unlock helpers ───────────────────────────────────────

    def _refresh_unlocked_private_channels(self):
        """
        Scans displayed_messages and adds any PRIVATE sub-channels that have
        at least one message to the unlocked set.  Safe to call every frame —
        it only ever adds to the set, never removes.
        """
        for msg in self.displayed_messages:
            ch  = str(msg.get('CHANNEL', '')).strip()
            sub = str(msg.get('SUB-CHANNEL', '')).strip().lstrip('@')
            if ch == PRIVATE_CHANNEL and sub:
                self.unlocked_private_channels.add(sub)

    def is_private_sub_visible(self, sub_name: str) -> bool:
        """Returns True if the given PRIVATE sub-channel should appear in the nav."""
        return sub_name in self.unlocked_private_channels

    # ── Chapter management ────────────────────────────────────────────────────

    @property
    def is_chapter_complete(self) -> bool:
        """True when current chapter is exhausted and a next one should be loaded."""
        if self._all_chapters_done:
            return False
        return self.script_index >= len(self.full_script)

    def _rebuild_id_index(self):
        """Rebuild the ID→index lookup from the current full_script."""
        self._id_index = {}
        for i, row in enumerate(self.full_script):
            row_id = str(row.get('ID', '')).strip()
            if row_id.endswith('.0'):
                row_id = row_id[:-2]
            if row_id:
                self._id_index[row_id] = i

    def load_next_chapter(self) -> bool:
        """
        REPLACE full_script with the next chapter only — O(1) RAM.
        displayed_messages is preserved (history stays visible).
        Returns True if a new chapter was loaded.
        """
        if self._all_chapters_done:
            return False
        next_idx = self.current_chapter + 1
        if not self.chapter_files or next_idx >= len(self.chapter_files):
            self._all_chapters_done = True
            print("[CHAPTER] No more chapters.")
            return False

        filename = self.chapter_files[next_idx]
        new_rows = load_chapter(filename, chapter_idx=next_idx, mark_read=False)
        if not new_rows:
            return False

        # Swap in the new chapter — discard the old one from RAM
        self.full_script     = new_rows
        self.script_index    = 0
        self.current_chapter = next_idx
        self._rebuild_id_index()
        self.ignored_ids     = set()   # fresh ignore state for new chapter
        self._choice_snapshots = []    # rewind only within a chapter
        print(f"[CHAPTER] Loaded chapter {next_idx}: {filename} "
              f"({len(new_rows)} rows)")
        return True

    def _replay_chapter_into_history(self, filename: str, chapter_idx: int,
                                      saved_ignored: set, saved_chosen: dict):
        """
        Replay a past chapter directly into displayed_messages WITHOUT keeping
        its rows in full_script.  Only message rows with IS_READ=1 (or forced)
        are committed; branching is reconstructed from saved_chosen.

        saved_ignored : set of IDs that were ignored in this chapter
        saved_chosen  : dict { row_id : True } for CHOICES rows that were picked
        """
        rows = load_chapter(filename, chapter_idx=chapter_idx, mark_read=True)
        for row in rows:
            row_id = str(row.get('ID', '')).strip()
            if row_id.endswith('.0'):
                row_id = row_id[:-2]
            if row_id and row_id in saved_ignored:
                continue
            msg   = str(row.get('MESSAGE', '')).strip()
            rtype = str(row.get('TYPE',    '')).strip().upper()
            char  = str(row.get('CHARACTER', '')).strip()
            status = str(row.get('STATUS', '')).strip().upper()
            if char and status:
                _ck = self._substitute(char)
                if _ck and not _ck.startswith('@'):
                    _ck = '@' + _ck
                self.personnel_db[_ck] = status
            if rtype in ('CHOICE', 'CHOOSE', 'CHOICES'):
                # Only show the chosen option
                if row_id and row_id in saved_chosen and msg:
                    display_row = dict(row)
                    display_row['MESSAGE']   = self._substitute(msg)
                    display_row['CHARACTER'] = self._substitute(char)
                    _ch  = str(display_row.get('CHANNEL', '')).strip()
                    if _ch and not _ch.startswith('#'):
                        _ch = '#' + _ch
                    display_row['CHANNEL']     = _ch
                    display_row['SUB-CHANNEL'] = str(display_row.get('SUB-CHANNEL', '')).strip().lstrip('@')
                    self.displayed_messages.append(display_row)
                continue
            if rtype in ('NARRATOR',):
                continue
            if msg:
                display_row = dict(row)
                display_row['MESSAGE']   = self._substitute(msg)
                display_row['CHARACTER'] = self._substitute(char)
                _ch  = str(display_row.get('CHANNEL', '')).strip()
                if _ch and not _ch.startswith('#'):
                    _ch = '#' + _ch
                display_row['CHANNEL']     = _ch
                display_row['SUB-CHANNEL'] = str(display_row.get('SUB-CHANNEL', '')).strip().lstrip('@')
                self.displayed_messages.append(display_row)

    def restore_from_save(self, saved_chapter: int, saved_script_index: int,
                           saved_displayed: list, saved_ignored: set,
                           saved_chosen_per_chapter: dict):
        """
        Called after a save-load.  Only the target chapter is loaded into RAM.
        Past chapter messages come from saved_displayed directly.

        saved_chosen_per_chapter: { chapter_idx: set_of_chosen_row_ids }
        """
        if not self.chapter_files:
            return

        # Restore displayed history straight from save — no re-processing needed
        self.displayed_messages = saved_displayed
        self.ignored_ids        = saved_ignored

        # Load only the current chapter into full_script
        filename  = self.chapter_files[saved_chapter]
        new_rows  = load_chapter(filename, chapter_idx=saved_chapter, mark_read=False)
        self.full_script     = new_rows
        self.script_index    = saved_script_index
        self.current_chapter = saved_chapter
        self._rebuild_id_index()
        self._refresh_unlocked_private_channels()
        print(f"[CHAPTER] Restored to chapter {saved_chapter} "
              f"at row {saved_script_index}")

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _resolve_id(self, row_id: str) -> int | None:
        row_id = str(row_id).strip()
        if row_id.endswith('.0'):
            row_id = row_id[:-2]
        return self._id_index.get(row_id)

    def _parse_ignore_list(self, raw: str) -> set:
        raw = str(raw).strip().strip('{}[]()').strip()
        if not raw or raw in ('', 'nan'):
            return set()
        ids = set()
        for part in raw.split(','):
            part = part.strip()
            if part.endswith('.0'):
                part = part[:-2]
            if part:
                ids.add(part)
        return ids

    def _add_ignored(self, new_ids: set):
        queue = new_ids - self.ignored_ids
        while queue:
            self.ignored_ids |= queue
            next_queue = set()
            for rid in queue:
                idx = self._id_index.get(rid)
                if idx is not None:
                    row = self.full_script[idx]
                    chained = self._parse_ignore_list(str(row.get('IGNORE', '')))
                    next_queue |= chained - self.ignored_ids
            queue = next_queue

    def _substitute(self, text: str) -> str:
        text = text.replace('{USERNAME}', f'@{self.username}')
        text = text.replace('{NAME}', self.name)
        return text

    def _commit_row(self, idx: int):
        row = self.full_script[idx]
        row['IS_READ'] = 1
        msg = str(row.get('MESSAGE', '')).strip()
        if msg:
            display_row = dict(row)
            display_row['MESSAGE']   = self._substitute(msg)
            display_row['CHARACTER'] = self._substitute(str(row.get('CHARACTER', '')))
            # Normalise CHANNEL so visible_msgs filter matches current_channel
            _ch = str(display_row.get('CHANNEL', '')).strip()
            if _ch and not _ch.startswith('#'):
                _ch = '#' + _ch
            display_row['CHANNEL'] = _ch
            # Normalise SUB-CHANNEL
            _sub = str(display_row.get('SUB-CHANNEL', '')).strip().lstrip('@')
            display_row['SUB-CHANNEL'] = _sub
            self.displayed_messages.append(display_row)
            # Immediately unlock the private sub-channel if applicable
            if _ch == PRIVATE_CHANNEL and _sub:
                self.unlocked_private_channels.add(_sub.lstrip('@'))

    def _collect_choices(self) -> list:
        choices = []
        i = self.script_index
        while i < len(self.full_script):
            row = self.full_script[i]
            if str(row.get('TYPE', '')).strip().upper() in ('CHOICE', 'CHOOSE', 'CHOICES'):
                choices.append((i, row))
                i += 1
            else:
                break
        return choices

    def _jump_to(self, row_id: str):
        target = self._resolve_id(row_id)
        if target is not None:
            self.script_index = target
        else:
            print(f"[JUMP] Warning: ID '{row_id}' not found in script.")
            self.script_index += 1

    # ── Fast-forward already-read rows on load ────────────────────────────────

    def _fast_forward_read_messages(self):
        while self.script_index < len(self.full_script):
            row = self.full_script[self.script_index]
            try:
                is_read = int(row.get('IS_READ', 0))
            except (ValueError, TypeError):
                is_read = 0

            if is_read != 1:
                row_id_ff = str(row.get('ID', '')).strip()
                if row_id_ff.endswith('.0'):
                    row_id_ff = row_id_ff[:-2]
                if row_id_ff and row_id_ff in self.ignored_ids:
                    self.script_index += 1
                    continue
                break

            char   = str(row.get('CHARACTER', '')).strip()
            status = str(row.get('STATUS',    '')).strip().upper()
            msg    = str(row.get('MESSAGE',   '')).strip()
            rtype  = str(row.get('TYPE',      '')).strip().upper()

            if char and status:
                _ff_char_key = self._substitute(char)
                if _ff_char_key and not _ff_char_key.startswith('@'):
                    _ff_char_key = '@' + _ff_char_key
                self.personnel_db[_ff_char_key] = status

            if rtype in ('CHOICE', 'CHOOSE', 'CHOICES'):
                ignore_raw = str(row.get('IGNORE', '')).strip()
                if ignore_raw:
                    initial = self._parse_ignore_list(ignore_raw)
                    if initial:
                        self._add_ignored(initial)
                try:
                    is_chosen = int(row.get('IS_CHOSEN', 0))
                except (ValueError, TypeError):
                    is_chosen = 0
                if is_chosen == 1 and msg:
                    display_row = dict(row)
                    display_row['MESSAGE']   = self._substitute(msg)
                    display_row['CHARACTER'] = self._substitute(char)
                    _ff_ch2 = str(display_row.get('CHANNEL', '')).strip()
                    if _ff_ch2 and not _ff_ch2.startswith('#'):
                        _ff_ch2 = '#' + _ff_ch2
                    display_row['CHANNEL'] = _ff_ch2
                    display_row['SUB-CHANNEL'] = str(display_row.get('SUB-CHANNEL', '')).strip().lstrip('@')
                    self.displayed_messages.append(display_row)
                self.script_index += 1
                continue

            if rtype == 'NARRATOR':
                ignore_raw = str(row.get('IGNORE', '')).strip()
                if ignore_raw:
                    initial = self._parse_ignore_list(ignore_raw)
                    if initial:
                        self._add_ignored(initial)
                self.script_index += 1
                continue

            if msg:
                display_row = dict(row)
                display_row['MESSAGE']   = self._substitute(msg)
                display_row['CHARACTER'] = self._substitute(char)
                # Normalise CHANNEL so visible_msgs filter matches current_channel
                _ff_ch = str(display_row.get('CHANNEL', '')).strip()
                if _ff_ch and not _ff_ch.startswith('#'):
                    _ff_ch = '#' + _ff_ch
                display_row['CHANNEL'] = _ff_ch
                display_row['SUB-CHANNEL'] = str(display_row.get('SUB-CHANNEL', '')).strip().lstrip('@')
                self.displayed_messages.append(display_row)

            self.script_index += 1

        self.last_advance_time = pygame.time.get_ticks()

    # ── Narrator resume ───────────────────────────────────────────────────────

    def resume_from_narrator(self):
        if not self.is_narrator_active:
            return
        row = self.full_script[self.script_index]
        row['IS_READ'] = 1

        ignore_raw = str(row.get('IGNORE', '')).strip()
        if ignore_raw:
            initial = self._parse_ignore_list(ignore_raw)
            if initial:
                self._add_ignored(initial)

        jump_to = str(row.get('JUMP_TO', '')).strip()
        if jump_to.endswith('.0'):
            jump_to = jump_to[:-2]
        self.script_index += 1
        if jump_to:
            self._jump_to(jump_to)
        self.is_narrator_active = False
        self.last_advance_time  = pygame.time.get_ticks()

    # ── Toggle helpers (called by UI) ─────────────────────────────────────────

    def toggle_auto(self):
        self.auto_mode = not self.auto_mode
        if self.auto_mode:
            self.skip_mode = False
            if self.is_waiting:
                self._commit_row(self.script_index)
                jump_to = str(self.full_script[self.script_index].get('JUMP_TO', '')).strip()
                if jump_to.endswith('.0'):
                    jump_to = jump_to[:-2]
                self.script_index += 1
                if jump_to:
                    self._jump_to(jump_to)
                self.is_waiting = False
            self.last_advance_time = pygame.time.get_ticks()

    def toggle_skip(self):
        self.skip_mode = not self.skip_mode
        if self.skip_mode:
            self.auto_mode = False
            if self.is_waiting:
                self._commit_row(self.script_index)
                jump_to = str(self.full_script[self.script_index].get('JUMP_TO', '')).strip()
                if jump_to.endswith('.0'):
                    jump_to = jump_to[:-2]
                self.script_index += 1
                if jump_to:
                    self._jump_to(jump_to)
                self.is_waiting = False
            self.last_advance_time = pygame.time.get_ticks()

    # ── Called by the UI when the player clicks the chat panel (normal mode) ──

    def advance_on_click(self):
        if self.auto_mode or self.skip_mode:
            return
        if self.waiting_for_choice:
            return
        if self.is_narrator_active:
            return
        self._click_pending = True

    # ── Called by the UI when the player clicks a choice button ──────────────

    def select_choice(self, choice_index: int):
        if not self.waiting_for_choice or choice_index >= len(self.pending_choices):
            return

        list_idx, chosen_row = self.pending_choices[choice_index]

        for li, _ in self.pending_choices:
            self.full_script[li]['IS_READ'] = 1
        self.full_script[list_idx]['IS_CHOSEN'] = 1

        display_row = dict(chosen_row)
        display_row['MESSAGE']   = self._substitute(str(chosen_row.get('MESSAGE', '')))
        display_row['CHARACTER'] = self._substitute(str(chosen_row.get('CHARACTER', '')))
        # Normalise CHANNEL so visible_msgs filter matches current_channel
        _sc_ch = str(display_row.get('CHANNEL', '')).strip()
        if _sc_ch and not _sc_ch.startswith('#'):
            _sc_ch = '#' + _sc_ch
        display_row['CHANNEL']     = _sc_ch
        display_row['SUB-CHANNEL'] = str(display_row.get('SUB-CHANNEL', '')).strip().lstrip('@')
        self.displayed_messages.append(display_row)

        # Unlock private channel if this choice message lands in one
        ch  = _sc_ch
        sub = display_row['SUB-CHANNEL']
        if ch == PRIVATE_CHANNEL and sub:
            self.unlocked_private_channels.add(sub.lstrip('@'))

        jump_to = str(chosen_row.get('JUMP_TO', '')).strip()
        if jump_to.endswith('.0'):
            jump_to = jump_to[:-2]

        ignore_raw = str(chosen_row.get('IGNORE', '')).strip()
        initial = self._parse_ignore_list(ignore_raw)
        if initial:
            self._add_ignored(initial)

        self.pending_choices    = []
        self.waiting_for_choice = False
        self.last_advance_time  = pygame.time.get_ticks()

        if jump_to:
            self._jump_to(jump_to)
        else:
            self.script_index = list_idx + 1

    # ── Rewind to the last choice point ──────────────────────────────────────

    def rewind_choice(self) -> bool:
        """
        Restore state to just before the last choice was presented.
        Returns True if a rewind was performed, False if no history exists.
        """
        if not self._choice_snapshots:
            return False

        snap = self._choice_snapshots.pop()

        # Restore script rows to their pre-choice state
        for idx, row_state in snap['pending_row_states'].items():
            self.full_script[idx].update(row_state)
            self.full_script[idx]['IS_READ']   = 0
            self.full_script[idx]['IS_CHOSEN'] = 0

        # Restore all tracked state
        self.script_index              = snap['script_index']
        self.displayed_messages        = snap['displayed_messages']
        self.ignored_ids               = snap['ignored_ids']
        self.personnel_db              = snap['personnel_db']
        self.unlocked_private_channels = snap['unlocked_private_channels']
        self.current_chapter           = snap.get('current_chapter', self.current_chapter)

        # Clear any active choice/wait state
        self.waiting_for_choice = False
        self.pending_choices    = []
        self.is_waiting         = False
        self.is_narrator_active = False
        self._click_pending     = False
        self.last_advance_time  = pygame.time.get_ticks()
        return True

    # ── Main update — called every frame ─────────────────────────────────────

    def update(self, current_channel: str = '', current_subchannel: str = ''):
        now = pygame.time.get_ticks()

        # Yield while a narrator overlay is active — run_chat() owns that flow
        if self.is_narrator_active:
            self._click_pending = False
            return

        # Pause for player choices
        if self.waiting_for_choice:
            self._click_pending = False
            return

        # Determine effective delays based on current mode
        if self.skip_mode:
            effective_advance_delay = self.skip_delay
        elif self.auto_mode:
            effective_advance_delay = self.auto_delay
        else:
            effective_advance_delay = self.advance_delay

        # Handle active typing animation
        if self.is_waiting:
            if self.skip_mode:
                elapsed_needed = 0
            elif self.auto_mode:
                elapsed_needed = min(self.typing_duration, 600)
            else:
                elapsed_needed = 0 if self._click_pending else self.typing_duration

            if now - self.typing_timer >= elapsed_needed:
                self._click_pending = False
                self._commit_row(self.script_index)

                jump_to = str(self.full_script[self.script_index].get('JUMP_TO', '')).strip()
                if jump_to.endswith('.0'):
                    jump_to = jump_to[:-2]

                self.script_index += 1
                if jump_to:
                    self._jump_to(jump_to)

                self.is_waiting        = False
                self.last_advance_time = now
            return

        # Normal mode: only advance on player click.
        # AUTO / SKIP: advance on timer.
        if not self.auto_mode and not self.skip_mode:
            if not self._click_pending:
                return
            self._click_pending = False
        else:
            if now - self.last_advance_time < effective_advance_delay:
                return

        if self.script_index >= len(self.full_script):
            return

        row = self.full_script[self.script_index]

        # ── Pre-unlock private sub-channels ──────────────────────────────────
        # As soon as the script reaches a row destined for #PRIVATE, reveal
        # that sub-channel in the nav so the player can navigate to it.
        # This MUST happen before the channel-guard gate below; otherwise the
        # channel stays hidden and the player can never get there.
        _pre_ch  = str(row.get('CHANNEL',     '')).strip()
        _pre_sub = str(row.get('SUB-CHANNEL', '')).strip().lstrip('@')
        if _pre_ch and not _pre_ch.startswith('#'):
            _pre_ch = '#' + _pre_ch
        if _pre_ch == PRIVATE_CHANNEL and _pre_sub:
            self.unlocked_private_channels.add(_pre_sub)

        # Wait until player is viewing the channel this row belongs to
        row_ch  = _pre_ch
        row_sub = _pre_sub if _pre_sub else 'general'
        if row_ch and (row_ch != current_channel or row_sub != current_subchannel):
            self._click_pending = False
            return

        char    = str(row.get('CHARACTER', '')).strip()
        status  = str(row.get('STATUS',    '')).strip().upper()
        msg     = str(row.get('MESSAGE',   '')).strip()
        rtype   = str(row.get('TYPE',      '')).strip().upper()
        jump_to = str(row.get('JUMP_TO',   '')).strip()
        if jump_to.endswith('.0'):
            jump_to = jump_to[:-2]

        # ── Skip ignored rows silently ───────────────────────────────────────
        row_id = str(row.get('ID', '')).strip()
        if row_id.endswith('.0'):
            row_id = row_id[:-2]
        if row_id and row_id in self.ignored_ids:
            cascade = self._parse_ignore_list(str(row.get('IGNORE', '')))
            if cascade:
                self._add_ignored(cascade)
            self.full_script[self.script_index]['IS_READ'] = 1
            self.script_index += 1
            self.last_advance_time = now
            return

        # Update live status — normalise key to always carry @ prefix
        if char and status:
            _char_key = self._substitute(char)
            if _char_key and not _char_key.startswith('@'):
                _char_key = '@' + _char_key
            self.personnel_db[_char_key] = status

        # ── NARRATOR row — pause script and signal overlay ───────────────────
        if rtype == 'NARRATOR':
            ignore_raw = str(row.get('IGNORE', '')).strip()
            if ignore_raw:
                initial = self._parse_ignore_list(ignore_raw)
                if initial:
                    self._add_ignored(initial)
            self.is_narrator_active = True
            return

        # ── CHOICE block — snapshot state then pause ──────────────────────────
        if rtype in ('CHOICE', 'CHOOSE', 'CHOICES'):
            self.pending_choices    = self._collect_choices()
            self.waiting_for_choice = True
            # Snapshot full game state (including unlock set) for rewind support
            self._choice_snapshots.append({
                'script_index':              self.script_index,
                'displayed_messages':        [dict(m) for m in self.displayed_messages],
                'ignored_ids':               set(self.ignored_ids),
                'personnel_db':              dict(self.personnel_db),
                'unlocked_private_channels': set(self.unlocked_private_channels),
                'current_chapter':           self.current_chapter,
                'pending_row_states':        {i: dict(self.full_script[i]) for i, _ in self.pending_choices},
            })
            return

        # ── Empty row — skip ─────────────────────────────────────────────────
        if not msg:
            self.full_script[self.script_index]['IS_READ'] = 1
            self.script_index += 1
            if jump_to:
                self._jump_to(jump_to)
            self.last_advance_time = now
            return

        # ── Typing animation ─────────────────────────────────────────────────
        if int(row.get('is_typing', 0)) == 1:
            if self.skip_mode:
                self._commit_row(self.script_index)
                self.script_index += 1
                if jump_to:
                    self._jump_to(jump_to)
                self.last_advance_time = now
            else:
                self.is_waiting        = True
                self.current_typer     = self._substitute(char)
                self.typing_channel    = str(row.get('CHANNEL',     ''))
                self.typing_subchannel = str(row.get('SUB-CHANNEL', 'general')).strip().lstrip('@')
                self.typing_timer      = now
                self.typing_duration   = max(1000, len(msg) * 50)

        # ── Normal message ────────────────────────────────────────────────────
        else:
            self._commit_row(self.script_index)
            self.script_index += 1
            if jump_to:
                self._jump_to(jump_to)
            self.last_advance_time = now

    def save_to_excel(self):
        """No-op: story xlsx files are read-only. Progress saved via save_manager."""
        pass

def _get_nav_click(mouse_pos, left_panel, channel_tree, nav_scroll, unlocked_private_channels):
    """
    Returns (channel, sub_channel) for the item clicked in the nav panel,
    or (None, None).

    IMPORTANT: the y_off arithmetic here must be a perfect mirror of the
    draw loop in run_chat so that click targets and rendered items stay in
    sync.  Both loops:
      - build visible_subs the same way (filter locked private subs)
      - skip the channel header entirely when visible_subs is empty
      - advance y_off by 26 per channel header, 24 per sub-channel
    """
    nav_area_top = left_panel.y + 35
    nav_area_h   = left_panel.height - 45
    nav_area_w   = left_panel.width - 18

    clip_rect = pygame.Rect(left_panel.x + 5, nav_area_top, nav_area_w, nav_area_h)
    if not clip_rect.collidepoint(mouse_pos):
        return None, None

    mouse_v_x = mouse_pos[0] - (left_panel.x + 5)
    mouse_v_y = mouse_pos[1] - nav_area_top + nav_scroll

    y_off = 5
    for ch, subs in channel_tree.items():
        # Build visible_subs exactly as the draw loop does
        visible_subs = [
            s for s in subs
            if ch != PRIVATE_CHANNEL or s in unlocked_private_channels
        ]
        # If a PRIVATE channel has no visible subs, its header is not drawn
        if not visible_subs and ch == PRIVATE_CHANNEL:
            continue

        # Channel header row (not clickable, just advances y_off)
        y_off += 26

        for sub in visible_subs:
            sub_rect_v = pygame.Rect(0, y_off, nav_area_w, 22)
            if sub_rect_v.collidepoint((mouse_v_x, mouse_v_y)):
                return ch, sub
            y_off += 24

    return None, None


def _get_personnel_click(mouse_pos, right_panel, all_users, personnel_scroll, pers_area_h):
    """Returns the user dict that was clicked in the personnel panel, or None."""
    pers_area_top = right_panel.y + 35
    pers_area_w   = right_panel.width - 18

    clip_rect = pygame.Rect(right_panel.x + 5, pers_area_top, pers_area_w, pers_area_h)
    if not clip_rect.collidepoint(mouse_pos):
        return None, None

    mouse_v_x = mouse_pos[0] - (right_panel.x + 5)
    mouse_v_y = mouse_pos[1] - pers_area_top + personnel_scroll

    for i, user in enumerate(all_users):
        row_rect = pygame.Rect(0, 5 + i * 30, pers_area_w, 28)
        if row_rect.collidepoint((mouse_v_x, mouse_v_y)):
            screen_y = mouse_pos[1]
            anchor   = (right_panel.x + 5, screen_y)
            return user, anchor

    return None, None


# --- MAIN INTERFACE LOOP ---
def run_chat(screen, canvas, clock, current_window_size, user_data, is_fullscreen, preloaded_cm=None, music_player=None):
    
    apply_theme(user_data)
    font_choice = user_data.get("theme_font", "Consolas") if user_data else "Consolas"
    
    try:
        FONT_PANEL  = pygame.font.SysFont(font_choice, 18, bold=True)
        FONT_TEXT   = pygame.font.SysFont(font_choice, 18)
        FONT_NAV    = pygame.font.SysFont(font_choice, 16)
        FONT_SMALL  = pygame.font.SysFont(font_choice, 13)
        FONT_NARRATOR_TITLE = pygame.font.SysFont(font_choice, 17, bold=True)
        FONT_NARRATOR_BODY  = pygame.font.SysFont(font_choice, 20)
    except Exception:
        FONT_PANEL  = pygame.font.SysFont("Consolas", 18, bold=True)
        FONT_TEXT   = pygame.font.SysFont("Consolas", 18)
        FONT_NAV    = pygame.font.SysFont("Consolas", 16)
        FONT_SMALL  = pygame.font.SysFont("Consolas", 13)
        FONT_NARRATOR_TITLE = pygame.font.SysFont("Consolas", 17, bold=True)
        FONT_NARRATOR_BODY  = pygame.font.SysFont("Consolas", 20)

    # Give NarratorOverlay.draw() access to FONT_SMALL without passing it every call
    global FONT_SMALL_REF
    FONT_SMALL_REF = FONT_SMALL

    # BACK sits between LOAD and SKIP
    nav_items = ["SAVE", "LOAD", "BACK", "SKIP", "AUTO", "SETTINGS"]

    # --- Load NPC data ---
    npc_data_list = load_npc_data()
    npc_lookup = {}
    for npc in npc_data_list:
        username = str(npc.get('USERNAME', '')).strip()
        if username:
            npc_lookup[username] = npc
            npc_lookup[username.lstrip('@')] = npc

    personnel_db = {}
    for npc in npc_data_list:
        username = str(npc.get('USERNAME', '')).strip()
        if username:
            personnel_db[username] = str(npc.get('STATUS', 'OFFLINE')).upper()

    # ── Discover all chapters once at startup ────────────────────────────────
    _all_chapter_files = discover_chapters()

    if preloaded_cm is not None:
        # ── Restore from save ─────────────────────────────────────────────────
        # load_slot already populated: displayed_messages, script_index,
        # current_chapter, ignored_ids, unlocked_private_channels, personnel_db.
        # We just need to load the correct chapter file into full_script.
        _saved_chapter = getattr(preloaded_cm, 'current_chapter', 0)
        _lc_file = _all_chapter_files[_saved_chapter]                    if _all_chapter_files and _saved_chapter < len(_all_chapter_files)                    else (_all_chapter_files[0] if _all_chapter_files else None)
        _ch_rows = load_chapter(_lc_file, _saved_chapter) if _lc_file else []

        chat_manager = ChatManager(_ch_rows, personnel_db,
                                   username=user_data.get('username', ''),
                                   name=user_data.get('name', ''))
        chat_manager.chapter_files   = _all_chapter_files
        chat_manager.current_chapter = _saved_chapter
        # Clamp script_index in case chapter length changed between saves
        chat_manager.script_index    = min(
            getattr(preloaded_cm, 'script_index', 0), len(_ch_rows))
        # Restore all saved runtime state directly
        chat_manager.displayed_messages        = preloaded_cm.displayed_messages
        chat_manager.ignored_ids               = getattr(preloaded_cm, 'ignored_ids', set())
        chat_manager.unlocked_private_channels = getattr(preloaded_cm,
                                                          'unlocked_private_channels', set())
        chat_manager._all_chapters_done        = False
        chat_manager.is_waiting                = False
        chat_manager.waiting_for_choice        = False
        chat_manager.pending_choices           = []
        chat_manager.is_narrator_active        = False
        if hasattr(preloaded_cm, 'personnel_db') and preloaded_cm.personnel_db:
            chat_manager.personnel_db.update(preloaded_cm.personnel_db)
        chat_manager._refresh_unlocked_private_channels()
    else:
        # ── Fresh game: load chapter 0 only ──────────────────────────────────
        _ch0 = load_chapter(_all_chapter_files[0], 0) if _all_chapter_files else []
        chat_manager = ChatManager(_ch0, personnel_db,
                                   username=user_data.get('username', ''),
                                   name=user_data.get('name', ''))
        chat_manager.chapter_files   = _all_chapter_files
        chat_manager.current_chapter = 0
        chat_manager.waiting_for_choice = False
        chat_manager.pending_choices    = []
        chat_manager.is_narrator_active = False
        chat_manager.is_waiting         = False

    channel_tree = load_server_data()

    # Default to the first non-private channel so the player never starts on a
    # locked private sub-channel.
    current_channel    = ''
    current_subchannel = ''
    for ch, subs in channel_tree.items():
        if ch != PRIVATE_CHANNEL and subs:
            current_channel    = ch
            current_subchannel = subs[0]
            break
    if not current_channel and channel_tree:
        current_channel    = list(channel_tree.keys())[0]
        current_subchannel = channel_tree[current_channel][0] if channel_tree[current_channel] else ''

    SCROLL_SPEED = 30
    scroll_states = {}

    # Nav panel scroll
    nav_scroll             = 0
    nav_max_scroll         = 0
    dragging_nav_scroll    = False
    drag_start_nav_mouse_y = 0
    drag_start_nav_offset  = 0
    n_thumb_rect           = pygame.Rect(0, 0, 0, 0)
    n_thumb_h              = 20

    # Chat panel scroll
    prev_msg_count     = 0
    dragging_scrollbar = False
    drag_start_mouse_y = 0
    drag_start_offset  = 0
    max_scroll         = 0
    thumb_rect         = pygame.Rect(0, 0, 0, 0)
    thumb_h            = 20

    # Personnel panel scroll
    personnel_scroll        = 0
    pers_max_scroll         = 0
    pers_area_h             = 0
    p_thumb_h               = 20
    dragging_pers_scroll    = False
    drag_start_pers_mouse_y = 0
    drag_start_pers_offset  = 0
    p_thumb_rect            = pygame.Rect(0, 0, 0, 0)

    # NPC profile card
    profile_card = NpcProfileCard()

    # Small avatar cache for the in-conversation NPC header strip
    _conv_avatar_cache = {}
    CONV_AVATAR_SIZE   = 36

    def _get_conv_avatar(profile_id: str):
        """Load and cache a circle-cropped avatar for the conversation header."""
        if profile_id in _conv_avatar_cache:
            return _conv_avatar_cache[profile_id]
        img_path = resource_path(os.path.join("assets", "images", f"{profile_id}.png"))
        size = CONV_AVATAR_SIZE
        try:
            raw    = pygame.image.load(img_path).convert_alpha()
            scaled = pygame.transform.smoothscale(raw, (size, size))
            result = pygame.Surface((size, size), pygame.SRCALPHA)
            result.fill((0, 0, 0, 0))
            cx_m, cy_m, r_m = size // 2, size // 2, size // 2
            for py_ in range(size):
                for px_ in range(size):
                    if (px_ - cx_m) ** 2 + (py_ - cy_m) ** 2 <= r_m ** 2:
                        result.set_at((px_, py_), scaled.get_at((px_, py_)))
            pygame.draw.circle(result, COLOR_CARD_BORDER, (cx_m, cy_m), r_m, 1)
        except Exception:
            result = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.circle(result, (30, 50, 30), (size // 2, size // 2), size // 2)
            pygame.draw.circle(result, COLOR_CARD_BORDER, (size // 2, size // 2), size // 2, 1)
        _conv_avatar_cache[profile_id] = result
        return result

    # Narrator overlay
    narrator_overlay = NarratorOverlay()

    # Save flash feedback
    save_flash_until = 0

    # Unread notification tracking
    unread_channels    = set()
    channel_msg_counts = {}

    # Persistent choice button rects and cached layout data
    choice_rects      = []
    choice_lines      = []
    choice_heights    = []
    last_choice_count = -1
    nav_item_rects    = {}

    def get_scroll():
        return scroll_states.get((current_channel, current_subchannel), 0)

    def set_scroll(val):
        scroll_states[(current_channel, current_subchannel)] = val

    running = True
    while running:
        canvas.fill(COLOR_BG)
        now = pygame.time.get_ticks()

        # ── Refresh unlock set every frame (cheap scan, set only grows) ───────
        chat_manager._refresh_unlocked_private_channels()

        # ── Narrator overlay lifecycle ─────────────────────────────────────────
        if chat_manager.is_narrator_active and not narrator_overlay.visible and not narrator_overlay.done:
            row     = chat_manager.full_script[chat_manager.script_index]
            nar_msg = chat_manager._substitute(str(row.get('MESSAGE', '')).strip())
            speaker = chat_manager._substitute(str(row.get('CHARACTER', '')).strip())
            if chat_manager.skip_mode:
                auto_ms = 1
            elif chat_manager.auto_mode:
                auto_ms = max(2000, len(nar_msg) * 45)
            else:
                auto_ms = 0
            narrator_overlay.show(nar_msg, speaker, auto_ms)

        if chat_manager.skip_mode and narrator_overlay.visible:
            narrator_overlay.force_close()

        narrator_overlay.update(now)

        if narrator_overlay.done and chat_manager.is_narrator_active:
            narrator_overlay.done = False
            chat_manager.resume_from_narrator()

        # ── Chapter completion check ──────────────────────────────────────────
        # When the current chapter is exhausted, automatically load the next.
        if chat_manager.is_chapter_complete:
            if chat_manager.load_next_chapter():
                # Re-seed the ID index was done inside load_next_chapter.
                # Fast-forward any pre-read rows at the start of the new chapter
                # (there won't be any for a fresh chapter, but handles edge cases).
                chat_manager._fast_forward_read_messages()
                prev_msg_count = -1   # force chat redraw

        # ── Normal story update ────────────────────────────────────────────────
        chat_manager.update(current_channel, current_subchannel)

        if music_player:
            music_player.update()

        # Detect new messages in non-active channels while in AUTO mode
        if chat_manager.auto_mode:
            for msg in chat_manager.displayed_messages:
                ch  = str(msg.get('CHANNEL', ''))
                sub = str(msg.get('SUB-CHANNEL', ''))
                key = (ch, sub)
                prev_count = channel_msg_counts.get(key, 0)
                count = sum(
                    1 for m in chat_manager.displayed_messages
                    if str(m.get('CHANNEL', '')) == ch and str(m.get('SUB-CHANNEL', '')) == sub
                )
                if count > prev_count:
                    channel_msg_counts[key] = count
                    if (ch, sub) != (current_channel, current_subchannel):
                        unread_channels.add(key)

        mouse_x, mouse_y = pygame.mouse.get_pos()
        scale_x = INTERNAL_WIDTH  / current_window_size[0]
        scale_y = INTERNAL_HEIGHT / current_window_size[1]
        scaled_mouse_pos = (int(mouse_x * scale_x), int(mouse_y * scale_y))

        left_panel   = pygame.Rect(10,  50, 200, 540)
        center_panel = pygame.Rect(220, 50, 500, 540)
        right_panel  = pygame.Rect(730, 50, 260, 540)

        # Build personnel list — deduplicate by bare name (@ stripped, lowercase)
        player_name = f"@{user_data['username']}"
        _skip = {player_name, player_name.lstrip('@'), '{USERNAME}', '@{USERNAME}'}
        _seen_names = {}
        for name, status in chat_manager.personnel_db.items():
            if name in _skip:
                continue
            # Normalise to @name for display; use bare name as dedup key
            display_name = name if name.startswith('@') else '@' + name
            bare = display_name.lstrip('@').lower()
            # Prefer the @-prefixed entry; only overwrite if we don't have one yet
            if bare not in _seen_names or not _seen_names[bare]['name'].startswith('@'):
                _seen_names[bare] = {"name": display_name, "status": status}
        all_users = list(_seen_names.values())
        all_users.append({"name": player_name, "status": "ONLINE (You)"})

        def sort_personnel(user):
            weight = 0 if 'ONLINE' in user['status'].upper() else 1
            return (weight, user['name'].lower())
        all_users.sort(key=sort_personnel)

        # ── Determine whether choices belong to the currently viewed channel ──
        _choice_channel    = ''
        _choice_subchannel = ''
        if chat_manager.waiting_for_choice and chat_manager.pending_choices:
            _, _first_choice_row = chat_manager.pending_choices[0]
            _raw_ch = str(_first_choice_row.get('CHANNEL', '')).strip()
            if _raw_ch and not _raw_ch.startswith('#'):
                _raw_ch = '#' + _raw_ch
            _choice_channel    = _raw_ch
            _choice_subchannel = str(_first_choice_row.get('SUB-CHANNEL', 'general')).strip().lstrip('@')

        choices_visible_here = (
            chat_manager.waiting_for_choice
            and _choice_channel    == current_channel
            and _choice_subchannel == current_subchannel
        )

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                chat_manager.save_to_excel() 
                running = False

            elif event.type == pygame.VIDEORESIZE and not is_fullscreen:
                current_window_size = (event.w, event.h)
                screen = pygame.display.set_mode(current_window_size, pygame.RESIZABLE)

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if narrator_overlay.visible:
                        narrator_overlay.dismiss()
                    elif profile_card.visible:
                        profile_card.hide()
                    else:
                        if chat_manager.auto_mode:
                            chat_manager.auto_mode = False
                        if chat_manager.skip_mode:
                            chat_manager.skip_mode = False

                elif choices_visible_here and event.key in (
                        pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4,
                        pygame.K_KP1, pygame.K_KP2, pygame.K_KP3, pygame.K_KP4):
                    key_map = {pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2, pygame.K_4: 3,
                               pygame.K_KP1: 0, pygame.K_KP2: 1, pygame.K_KP3: 2, pygame.K_KP4: 3}
                    ci = key_map[event.key]
                    if ci < len(chat_manager.pending_choices):
                        chat_manager.select_choice(ci)
                        choice_rects      = []
                        choice_lines      = []
                        choice_heights    = []
                        last_choice_count = -1
                        set_scroll(0)

                elif event.key == pygame.K_F11:
                    is_fullscreen = not is_fullscreen
                    if is_fullscreen:
                        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                        current_window_size = screen.get_size()
                    else:
                        current_window_size = (INTERNAL_WIDTH, INTERNAL_HEIGHT)
                        screen = pygame.display.set_mode(current_window_size, pygame.RESIZABLE)

            elif event.type == pygame.MOUSEWHEEL:
                if not narrator_overlay.visible:
                    if center_panel.collidepoint(scaled_mouse_pos):
                        new_off = get_scroll() + event.y * SCROLL_SPEED
                        set_scroll(max(0, new_off))
                    elif right_panel.collidepoint(scaled_mouse_pos):
                        personnel_scroll -= event.y * SCROLL_SPEED 
                        personnel_scroll = max(0, min(personnel_scroll, pers_max_scroll))
                    elif left_panel.collidepoint(scaled_mouse_pos):
                        nav_scroll -= event.y * SCROLL_SPEED
                        nav_scroll = max(0, min(nav_scroll, nav_max_scroll))

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:

                    # ── Narrator overlay captures ALL clicks while visible ─────
                    if narrator_overlay.visible:
                        narrator_overlay.handle_click()
                        continue

                    # --- NAV BAR clicks ---
                    save_rect     = nav_item_rects.get('SAVE',     pygame.Rect(0,0,0,0))
                    load_rect     = nav_item_rects.get('LOAD',     pygame.Rect(0,0,0,0))
                    back_rect     = nav_item_rects.get('BACK',     pygame.Rect(0,0,0,0))
                    skip_rect     = nav_item_rects.get('SKIP',     pygame.Rect(0,0,0,0))
                    auto_rect     = nav_item_rects.get('AUTO',     pygame.Rect(0,0,0,0))
                    settings_rect = nav_item_rects.get('SETTINGS', pygame.Rect(0,0,0,0))

                    if save_rect.collidepoint(scaled_mouse_pos):
                        result = run_save_page(screen, canvas, clock,
                                               current_window_size, chat_manager,
                                               is_fullscreen)
                        if isinstance(result, tuple) and result[0] == 'saved':
                            save_flash_until = pygame.time.get_ticks() + 1500

                    elif load_rect.collidepoint(scaled_mouse_pos):
                        result = run_load_page(screen, canvas, clock,
                                               current_window_size, chat_manager,
                                               is_fullscreen)
                        if isinstance(result, tuple) and result[0] == 'loaded':
                            # load_slot already wrote displayed_messages, script_index,
                            # current_chapter, ignored_ids, personnel_db onto chat_manager.
                            # Now swap full_script to the correct chapter file.
                            _lc_idx  = getattr(chat_manager, 'current_chapter', 0)
                            _lc_file = chat_manager.chapter_files[_lc_idx]                                        if chat_manager.chapter_files else None
                            if _lc_file:
                                _lc_rows = load_chapter(_lc_file, _lc_idx, mark_read=False)
                                chat_manager.full_script  = _lc_rows
                                chat_manager._rebuild_id_index()
                            # script_index was restored by load_slot — validate it
                            chat_manager.script_index = min(
                                chat_manager.script_index,
                                len(chat_manager.full_script))
                            chat_manager._all_chapters_done = False
                            chat_manager.auto_mode          = False
                            chat_manager.skip_mode          = False
                            chat_manager.is_narrator_active = False
                            chat_manager.waiting_for_choice = False
                            chat_manager.pending_choices    = []
                            chat_manager._choice_snapshots  = []
                            narrator_overlay.force_close()
                            chat_manager._refresh_unlocked_private_channels()
                            prev_msg_count = -1
                            scroll_states  = {}

                    elif back_rect.collidepoint(scaled_mouse_pos):
                        # Only rewind when there is history to go back to
                        if chat_manager._choice_snapshots:
                            if chat_manager.rewind_choice():
                                choice_rects      = []
                                choice_lines      = []
                                choice_heights    = []
                                last_choice_count = -1
                                narrator_overlay.force_close()
                                prev_msg_count = -1

                    elif skip_rect.collidepoint(scaled_mouse_pos):
                        chat_manager.toggle_skip()
                        if chat_manager.skip_mode and narrator_overlay.visible:
                            narrator_overlay.force_close()

                    elif auto_rect.collidepoint(scaled_mouse_pos):
                        chat_manager.toggle_auto()

                    elif settings_rect.collidepoint(scaled_mouse_pos):
                        was_auto = chat_manager.auto_mode
                        was_skip = chat_manager.skip_mode
                        chat_manager.auto_mode = False
                        chat_manager.skip_mode = False
                        settings_result = run_settings(user_data, is_fullscreen=is_fullscreen, music_player=music_player)
                        if isinstance(settings_result, tuple):
                            updated, is_fullscreen = settings_result
                        else:
                            updated = settings_result
                        if isinstance(updated, dict):
                            user_data = updated
                        apply_theme(user_data)
                        font_choice = user_data.get("theme_font", "Consolas") if user_data else "Consolas"
                        try:
                            FONT_PANEL  = pygame.font.SysFont(font_choice, 18, bold=True)
                            FONT_TEXT   = pygame.font.SysFont(font_choice, 18)
                            FONT_NAV    = pygame.font.SysFont(font_choice, 16)
                            FONT_SMALL  = pygame.font.SysFont(font_choice, 13)
                            FONT_NARRATOR_TITLE = pygame.font.SysFont(font_choice, 17, bold=True)
                            FONT_NARRATOR_BODY  = pygame.font.SysFont(font_choice, 20)
                            FONT_SMALL_REF = FONT_SMALL
                        except Exception:
                            pass
                        if is_fullscreen:
                            screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                            current_window_size = screen.get_size()
                        else:
                            current_window_size = (INTERNAL_WIDTH, INTERNAL_HEIGHT)
                            screen = pygame.display.set_mode(current_window_size, pygame.RESIZABLE)
                        chat_manager.auto_mode = was_auto
                        chat_manager.skip_mode = was_skip
                        chat_manager.last_advance_time = pygame.time.get_ticks()

                    else:
                        # --- Profile card gets first dibs on clicks ---
                        if profile_card.visible:
                            consumed = profile_card.handle_click(scaled_mouse_pos)
                            if profile_card.profile_requested:
                                req_name = profile_card.profile_requested
                                profile_card.profile_requested = None
                                profile_card.hide()
                                raw = req_name.lstrip('@')
                                npc_data = dict(npc_lookup.get(req_name) or npc_lookup.get(raw) or {})
                                live_status = chat_manager.personnel_db.get(req_name) \
                                              or chat_manager.personnel_db.get(raw) \
                                              or npc_data.get('STATUS', 'OFFLINE')
                                npc_data['STATUS'] = live_status
                                result = run_profile(screen, canvas, clock,
                                                     current_window_size, npc_data,
                                                     is_fullscreen, music_player=music_player)
                                if result == 'quit':
                                    running = False
                            if consumed:
                                continue

                        # CHOICE BUTTONS — only clickable when visible in this channel
                        if choices_visible_here:
                            for ci, crect in enumerate(choice_rects):
                                if crect.collidepoint(scaled_mouse_pos):
                                    chat_manager.select_choice(ci)
                                    choice_rects      = []
                                    choice_lines      = []
                                    choice_heights    = []
                                    last_choice_count = -1
                                    set_scroll(0)
                                    break

                        # LEFT PANEL
                        if left_panel.collidepoint(scaled_mouse_pos):
                            if nav_max_scroll > 0 and n_thumb_rect.collidepoint(scaled_mouse_pos):
                                dragging_nav_scroll    = True
                                drag_start_nav_mouse_y = scaled_mouse_pos[1]
                                drag_start_nav_offset  = nav_scroll
                            else:
                                clicked_ch, clicked_sub = _get_nav_click(
                                    scaled_mouse_pos, left_panel, channel_tree, nav_scroll,
                                    chat_manager.unlocked_private_channels)
                                if clicked_ch is not None:
                                    current_channel    = clicked_ch
                                    current_subchannel = clicked_sub
                                    prev_msg_count     = -1
                                    profile_card.hide()
                                    unread_channels.discard((clicked_ch, clicked_sub))

                        # CENTER PANEL — scrollbar OR click-to-advance
                        if center_panel.collidepoint(scaled_mouse_pos):
                            if max_scroll > 0 and thumb_rect.collidepoint(scaled_mouse_pos):
                                dragging_scrollbar = True
                                drag_start_mouse_y = scaled_mouse_pos[1]
                                drag_start_offset  = get_scroll()
                            else:
                                chat_manager.advance_on_click()
                        elif max_scroll > 0 and thumb_rect.collidepoint(scaled_mouse_pos):
                            dragging_scrollbar = True
                            drag_start_mouse_y = scaled_mouse_pos[1]
                            drag_start_offset  = get_scroll()

                        # RIGHT PANEL — scrollbar OR user click
                        if right_panel.collidepoint(scaled_mouse_pos):
                            if pers_max_scroll > 0 and p_thumb_rect.collidepoint(scaled_mouse_pos):
                                dragging_pers_scroll    = True
                                drag_start_pers_mouse_y = scaled_mouse_pos[1]
                                drag_start_pers_offset  = personnel_scroll
                            else:
                                clicked_user, anchor = _get_personnel_click(
                                    scaled_mouse_pos, right_panel, all_users,
                                    personnel_scroll, pers_area_h)
                                if clicked_user is not None:
                                    uname = clicked_user['name']
                                    if uname != player_name:
                                        raw_name = uname.lstrip('@')
                                        npc_info = npc_lookup.get(raw_name, {})
                                        if profile_card.visible and profile_card.npc_name == uname:
                                            profile_card.hide()
                                        else:
                                            profile_card.show(uname, npc_info, anchor)

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    dragging_scrollbar   = False
                    dragging_pers_scroll = False
                    dragging_nav_scroll  = False

            elif event.type == pygame.MOUSEMOTION:
                if dragging_scrollbar and max_scroll > 0:
                    dy    = scaled_mouse_pos[1] - drag_start_mouse_y
                    delta = int(dy * max_scroll / max(1, chat_area_h - thumb_h))
                    set_scroll(max(0, min(max_scroll, drag_start_offset - delta)))
                elif dragging_pers_scroll and pers_max_scroll > 0:
                    dy    = scaled_mouse_pos[1] - drag_start_pers_mouse_y
                    delta = int(dy * pers_max_scroll / max(1, pers_area_h - p_thumb_h))
                    personnel_scroll = max(0, min(pers_max_scroll, drag_start_pers_offset + delta))
                elif dragging_nav_scroll and nav_max_scroll > 0:
                    dy    = scaled_mouse_pos[1] - drag_start_nav_mouse_y
                    delta = int(dy * nav_max_scroll / max(1, nav_area_h - n_thumb_h))
                    nav_scroll = max(0, min(nav_max_scroll, drag_start_nav_offset + delta))

        # --- TOP NAVIGATION ---
        top_nav_rect = pygame.Rect(0, 0, INTERNAL_WIDTH, 40)
        pygame.draw.rect(canvas, COLOR_PANEL_BG, top_nav_rect)
        pygame.draw.line(canvas, COLOR_LINE, (0, 40), (INTERNAL_WIDTH, 40), 2)
        x_start = 20
        nav_item_rects = {}
        for item in nav_items:
            is_active_mode = (item == 'SKIP' and chat_manager.skip_mode) or \
                             (item == 'AUTO' and chat_manager.auto_mode)

            item_surf = FONT_NAV.render(item, True, COLOR_TEXT)
            item_rect = item_surf.get_rect(topleft=(x_start, 12))
            is_hov    = item_rect.collidepoint(scaled_mouse_pos)

            if is_active_mode:
                pill = pygame.Rect(item_rect.x - 6, item_rect.y - 3,
                                   item_rect.width + 12, item_rect.height + 6)
                pygame.draw.rect(canvas, COLOR_BTN_BG, pill, border_radius=4)
                pygame.draw.rect(canvas, COLOR_ACCENT, pill, 1, border_radius=4)
                item_surf = FONT_NAV.render(item, True, COLOR_ACCENT)
            elif item == 'BACK' and not chat_manager._choice_snapshots:
                item_surf = FONT_NAV.render(item, True, COLOR_MUTED)
            elif is_hov:
                item_surf = FONT_NAV.render(item, True, COLOR_ACCENT)

            canvas.blit(item_surf, item_rect)
            nav_item_rects[item] = item_rect
            x_start += 100

        # SAVED! flash label
        if now < save_flash_until:
            flash_surf = FONT_NAV.render("✓ SAVED", True, COLOR_ACCENT)
            canvas.blit(flash_surf, (x_start, 12))

        # Mode status indicator (top-right corner)
        if chat_manager.skip_mode:
            mode_label = "[ SKIP >> ]"
            mode_color = COLOR_ACCENT
        elif chat_manager.auto_mode:
            blink_on   = (now // 600) % 2 == 0
            mode_label = "[ AUTO ▶ ]" if blink_on else "[  AUTO  ]"
            mode_color = COLOR_ACCENT
        else:
            mode_label = ""
            mode_color = COLOR_MUTED

        if mode_label:
            mode_surf = FONT_NAV.render(mode_label, True, mode_color)
            canvas.blit(mode_surf, (INTERNAL_WIDTH - mode_surf.get_width() - 12, 12))

        # ── Channel guide — compute text only here, draw later on top of panels
        _guide_text = ''
        if (not chat_manager.is_narrator_active
                and not chat_manager.waiting_for_choice
                and chat_manager.script_index < len(chat_manager.full_script)):
            _next_row = chat_manager.full_script[chat_manager.script_index]
            _next_ch  = str(_next_row.get('CHANNEL',     '')).strip()
            _next_sub = str(_next_row.get('SUB-CHANNEL', 'general')).strip().lstrip('@')
            if _next_ch and not _next_ch.startswith('#'):
                _next_ch = '#' + _next_ch
            if _next_ch and (_next_ch != current_channel or _next_sub != current_subchannel.lstrip('@')):
                _guide_text = f"▶  go to  {_next_ch} / #{_next_sub}"

        # --- DRAW PANEL BACKGROUNDS ---
        panel_title = f"{current_channel}  #{current_subchannel}"
        draw_panel(canvas, left_panel,   "A.L.I.C.E. NET", FONT_PANEL)
        draw_panel(canvas, center_panel, panel_title,       FONT_PANEL)
        draw_panel(canvas, right_panel,  "PERSONNEL",       FONT_PANEL)

        # --- LEFT PANEL (A.L.I.C.E. NET) WITH SCROLL ---
        nav_area_top    = left_panel.y + 35
        nav_area_bottom = left_panel.y + left_panel.height - 10
        nav_area_h      = nav_area_bottom - nav_area_top
        nav_area_w      = left_panel.width - 18

        # Build nav, skipping locked private sub-channels entirely
        total_nav_h = 5
        for ch, subs in channel_tree.items():
            visible_subs = [
                s for s in subs
                if ch != PRIVATE_CHANNEL or s in chat_manager.unlocked_private_channels
            ]
            if not visible_subs and ch == PRIVATE_CHANNEL:
                # Don't even render the channel header if no subs are unlocked yet
                continue
            total_nav_h += 26
            total_nav_h += len(visible_subs) * 24

        nav_v_h    = max(total_nav_h, nav_area_h)
        nav_v_surf = pygame.Surface((nav_area_w, nav_v_h), pygame.SRCALPHA)
        nav_v_surf.fill((0, 0, 0, 0))

        y_off = 5
        for ch, subs in channel_tree.items():
            visible_subs = [
                s for s in subs
                if ch != PRIVATE_CHANNEL or s in chat_manager.unlocked_private_channels
            ]
            # Hide the entire PRIVATE channel header when nothing is unlocked
            if not visible_subs and ch == PRIVATE_CHANNEL:
                continue

            ch_color = COLOR_ACCENT if ch == current_channel else COLOR_TEXT
            ch_surf  = FONT_PANEL.render(f" {ch}", True, ch_color)
            nav_v_surf.blit(ch_surf, (1, y_off + 3))
            y_off += 26

            for sub in visible_subs:
                is_active  = (ch == current_channel and sub == current_subchannel)
                sub_color  = COLOR_ACCENT if is_active else COLOR_MUTED
                prefix     = "[>]" if is_active else "   "
                sub_surf   = FONT_TEXT.render(f"{prefix} #{sub}", True, sub_color)

                mouse_v_y  = scaled_mouse_pos[1] - nav_area_top + nav_scroll
                mouse_v_x  = scaled_mouse_pos[0] - (left_panel.x + 5)
                sub_rect_v = pygame.Rect(0, y_off, nav_area_w, 22)
                is_in_clip = pygame.Rect(left_panel.x + 5, nav_area_top, nav_area_w, nav_area_h).collidepoint(scaled_mouse_pos)
                if is_in_clip and sub_rect_v.collidepoint((mouse_v_x, mouse_v_y)) and not is_active:
                    pygame.draw.rect(nav_v_surf, COLOR_BTN_BG, sub_rect_v)

                nav_v_surf.blit(sub_surf, (11, y_off + 2))

                if (ch, sub) in unread_channels and not is_active:
                    blink_on    = (pygame.time.get_ticks() // 400) % 2 == 0
                    badge_color = COLOR_ACCENT if blink_on else COLOR_MUTED
                    badge_surf  = FONT_NAV.render("!", True, badge_color)
                    badge_x     = nav_area_w - badge_surf.get_width() - 6
                    badge_y     = y_off + (22 - badge_surf.get_height()) // 2
                    nav_v_surf.blit(badge_surf, (badge_x, badge_y))

                y_off += 24

        nav_max_scroll = max(0, nav_v_h - nav_area_h)
        nav_scroll     = min(nav_scroll, nav_max_scroll)

        src_rect_nav = pygame.Rect(0, nav_scroll, nav_area_w, nav_area_h)
        canvas.set_clip(pygame.Rect(left_panel.x + 5, nav_area_top, nav_area_w, nav_area_h))
        canvas.blit(nav_v_surf, (left_panel.x + 5, nav_area_top), area=src_rect_nav)
        canvas.set_clip(None)

        if nav_max_scroll > 0:
            nsb_x     = left_panel.x + left_panel.width - 12
            nsb_track = pygame.Rect(nsb_x, nav_area_top, 8, nav_area_h)
            pygame.draw.rect(canvas, COLOR_LINE, nsb_track, border_radius=4)
            n_thumb_ratio = nav_area_h / nav_v_h
            n_thumb_h     = max(20, int(nav_area_h * n_thumb_ratio))
            n_thumb_frac  = nav_scroll / nav_max_scroll
            n_thumb_y     = nav_area_top + int((nav_area_h - n_thumb_h) * n_thumb_frac)
            n_thumb_rect  = pygame.Rect(nsb_x, n_thumb_y, 8, n_thumb_h)
            n_thumb_color = COLOR_ACCENT if dragging_nav_scroll else COLOR_MUTED
            pygame.draw.rect(canvas, n_thumb_color, n_thumb_rect, border_radius=4)

        # --- NPC CONVERSATION HEADER (PRIVATE channels only) ---
        _conv_npc   = None
        _conv_hdr_h = 0
        _CONV_HDR_H = 64  # tall enough for avatar + two text rows + padding

        if current_channel == PRIVATE_CHANNEL:
            _sub_key  = current_subchannel
            _conv_npc = npc_lookup.get(_sub_key) or npc_lookup.get(_sub_key.lstrip('@'))
            if _conv_npc:
                _conv_hdr_h = _CONV_HDR_H

        if _conv_npc:
            # The header sits immediately below the panel title bar (y+30)
            hdr_rect = pygame.Rect(center_panel.x, center_panel.y + 30,
                                   center_panel.width, _CONV_HDR_H)

            # Solid dark background + bottom separator
            pygame.draw.rect(canvas, COLOR_PANEL_BG, hdr_rect)
            pygame.draw.line(canvas, COLOR_ACCENT,
                             (hdr_rect.x + 8, hdr_rect.bottom - 1),
                             (hdr_rect.right - 8, hdr_rect.bottom - 1), 1)

            # ── Resolve NPC data ──────────────────────────────────────────────
            _pid         = str(_conv_npc.get('PROFILE_ID', '')).strip()
            _fullname    = str(_conv_npc.get('FULLNAME', current_subchannel)).strip()
            _role        = str(_conv_npc.get('ROLE', '')).strip()
            _npc_uname   = str(_conv_npc.get('USERNAME', '')).strip()
            _live_status = (chat_manager.personnel_db.get(_npc_uname)
                            or chat_manager.personnel_db.get(_npc_uname.lstrip('@'), 'OFFLINE'))
            _is_online   = 'ONLINE' in _live_status.upper()
            _dot_col     = COLOR_ACCENT if _is_online else COLOR_MUTED
            _status_str  = _live_status.split('(')[0].strip()

            # ── Avatar (vertically centred, left-padded) ──────────────────────
            AV  = CONV_AVATAR_SIZE   # 36 px
            av_x = hdr_rect.x + 12
            av_y = hdr_rect.y + (_CONV_HDR_H - AV) // 2
            if _pid:
                canvas.blit(_get_conv_avatar(_pid), (av_x, av_y))
                # Online dot — bottom-right corner of avatar circle
                dot_cx = av_x + AV - 5
                dot_cy = av_y + AV - 5
                pygame.draw.circle(canvas, COLOR_PANEL_BG, (dot_cx, dot_cy), 6)
                pygame.draw.circle(canvas, _dot_col,       (dot_cx, dot_cy), 4)
            text_x = av_x + AV + 12

            # ── Text block: vertically centred as a group ─────────────────────
            name_surf   = FONT_PANEL.render(_fullname, True, COLOR_ACCENT)
            role_surf   = FONT_SMALL.render(_role,     True, COLOR_MUTED)
            # status line: dot + label inline
            dot_r       = 4
            stat_label  = FONT_SMALL.render(f"  {_status_str}", True, _dot_col)

            total_text_h = (name_surf.get_height() + 3
                            + role_surf.get_height() + 3
                            + stat_label.get_height())
            ty = hdr_rect.y + (_CONV_HDR_H - total_text_h) // 2

            # Name
            canvas.blit(name_surf, (text_x, ty))
            ty += name_surf.get_height() + 3

            # Role
            canvas.blit(role_surf, (text_x, ty))
            ty += role_surf.get_height() + 3

            # Status dot + text on same baseline
            dot_sy = ty + stat_label.get_height() // 2
            pygame.draw.circle(canvas, _dot_col, (text_x + dot_r, dot_sy), dot_r)
            canvas.blit(stat_label, (text_x, ty))

        # --- CENTER PANEL (CHAT FEED) ---
        input_bar_y      = center_panel.y + center_panel.height - 45
        typing_ind_y     = input_bar_y - 28
        chat_area_top    = center_panel.y + 35 + _conv_hdr_h
        chat_area_bottom = typing_ind_y - 5
        chat_area_h      = chat_area_bottom - chat_area_top
        chat_area_w      = center_panel.width - 18

        visible_msgs = [
            m for m in chat_manager.displayed_messages
            if str(m.get('CHANNEL', '')).strip()               == current_channel.strip()
            and str(m.get('SUB-CHANNEL', '')).strip().lstrip('@') == current_subchannel.strip().lstrip('@')
        ]

        cur_msg_count = len(visible_msgs)
        if cur_msg_count != prev_msg_count:
            prev_msg_count = cur_msg_count
        scroll_offset = get_scroll()

        # ── Per-message avatar size & layout constants ───────────────────────
        MSG_AV_SIZE   = 28          # avatar circle diameter
        MSG_AV_PAD    = 6           # gap between avatar and text column
        MSG_INDENT    = MSG_AV_SIZE + MSG_AV_PAD + 4   # text column left edge
        MSG_GAP       = 10          # vertical gap between messages
        CHAT_TEXT_X   = 10
        CHAT_MAX_W    = chat_area_w - MSG_INDENT - 14  # text wraps inside indent
        FONT_TEXT_REF = FONT_TEXT

        def _get_msg_avatar(char_name: str):
            """Return a 28px circle-cropped avatar for char_name, or None."""
            raw_name = char_name.lstrip('@')
            npc = npc_lookup.get(char_name) or npc_lookup.get(raw_name)
            if not npc:
                return None
            pid = str(npc.get('PROFILE_ID', '')).strip()
            if not pid:
                return None
            cache_key = f"msg_{pid}"
            if cache_key in _conv_avatar_cache:
                return _conv_avatar_cache[cache_key]
            img_path = resource_path(os.path.join("assets", "images", f"{pid}.png"))
            size = MSG_AV_SIZE
            try:
                raw    = pygame.image.load(img_path).convert_alpha()
                scaled = pygame.transform.smoothscale(raw, (size, size))
                result = pygame.Surface((size, size), pygame.SRCALPHA)
                result.fill((0, 0, 0, 0))
                cx_m = cy_m = size // 2
                for py_ in range(size):
                    for px_ in range(size):
                        if (px_ - cx_m)**2 + (py_ - cy_m)**2 <= (size//2)**2:
                            result.set_at((px_, py_), scaled.get_at((px_, py_)))
                pygame.draw.circle(result, COLOR_CARD_BORDER, (cx_m, cy_m), size//2, 1)
            except Exception:
                result = pygame.Surface((size, size), pygame.SRCALPHA)
                pygame.draw.circle(result, (30, 50, 30), (size//2, size//2), size//2)
                pygame.draw.circle(result, COLOR_CARD_BORDER, (size//2, size//2), size//2, 1)
            _conv_avatar_cache[cache_key] = result
            return result

        def _measure_msg(char, msg, timestamp):
            """Return the pixel height a message block will occupy."""
            is_player = (char == player_name)
            lh = FONT_TEXT_REF.get_linesize()
            # header row: avatar/name line
            h = lh + 2
            # message text lines
            max_w = CHAT_MAX_W if not is_player else (chat_area_w - 20)
            words = msg.split()
            line, lines = [], 0
            for word in words:
                test = ' '.join(line + [word])
                if FONT_TEXT_REF.size(test)[0] > max_w and line:
                    lines += 1
                    line = [word]
                else:
                    line.append(word)
            lines += 1   # last line
            h += lines * lh
            return h + MSG_GAP

        def _draw_msg(surf, char, msg, timestamp, v_y):
            """Draw a single message block onto surf at v_y. Returns new v_y."""
            is_player = (char == player_name)
            lh        = FONT_TEXT_REF.get_linesize()
            w         = surf.get_width()

            if is_player:
                # ── Player message: right-aligned, no avatar ─────────────────
                hdr = FONT_SMALL.render(f"{char}  [{timestamp}]", True, COLOR_MUTED)
                surf.blit(hdr, (w - hdr.get_width() - 8, v_y))
                v_y += lh + 2

                words = msg.split()
                line  = []
                lines = []
                max_w = w - 20
                for word in words:
                    test = ' '.join(line + [word])
                    if FONT_TEXT_REF.size(test)[0] > max_w and line:
                        lines.append(' '.join(line))
                        line = [word]
                    else:
                        line.append(word)
                if line:
                    lines.append(' '.join(line))
                for ln in lines:
                    ls = FONT_TEXT_REF.render(ln, True, COLOR_ACCENT)
                    surf.blit(ls, (w - ls.get_width() - 8, v_y))
                    v_y += lh

            else:
                # ── NPC message: avatar + name header + indented text ─────────
                avatar = _get_msg_avatar(char)
                av_x   = CHAT_TEXT_X
                av_y   = v_y + (lh - MSG_AV_SIZE) // 2 + 2
                if avatar:
                    surf.blit(avatar, (av_x, av_y))

                # Name + timestamp header
                name_col  = COLOR_ACCENT
                name_surf = FONT_PANEL.render(char, True, name_col)
                ts_surf   = FONT_SMALL.render(f"  [{timestamp}]", True, COLOR_MUTED)
                tx        = CHAT_TEXT_X + MSG_INDENT
                surf.blit(name_surf, (tx, v_y))
                surf.blit(ts_surf,   (tx + name_surf.get_width(), v_y + 2))
                v_y += lh + 2

                # Message text, indented
                words = msg.split()
                line  = []
                max_w = CHAT_MAX_W
                for word in words:
                    test = ' '.join(line + [word])
                    if FONT_TEXT_REF.size(test)[0] > max_w and line:
                        ls = FONT_TEXT_REF.render(' '.join(line), True, COLOR_TEXT)
                        surf.blit(ls, (tx, v_y))
                        v_y += lh
                        line = [word]
                    else:
                        line.append(word)
                if line:
                    ls = FONT_TEXT_REF.render(' '.join(line), True, COLOR_TEXT)
                    surf.blit(ls, (tx, v_y))
                    v_y += lh

            return v_y + MSG_GAP

        # ── Measure total virtual height ──────────────────────────────────────
        total_h = 5
        for row in visible_msgs:
            total_h += _measure_msg(str(row['CHARACTER']), str(row['MESSAGE']),
                                    str(row.get('TIME', '')))

        virtual_h    = max(total_h + 10, chat_area_h)
        virtual_surf = pygame.Surface((chat_area_w, virtual_h), pygame.SRCALPHA)
        virtual_surf.fill((0, 0, 0, 0))

        # ── Draw all messages ─────────────────────────────────────────────────
        v_y = 5
        for row in visible_msgs:
            v_y = _draw_msg(virtual_surf,
                            str(row['CHARACTER']),
                            str(row['MESSAGE']),
                            str(row.get('TIME', '')),
                            v_y)

        max_scroll    = max(0, virtual_h - chat_area_h)
        scroll_offset = min(scroll_offset, max_scroll)
        set_scroll(scroll_offset)

        view_y   = virtual_h - chat_area_h - scroll_offset
        view_y   = max(0, view_y)
        src_rect = pygame.Rect(0, view_y, chat_area_w, chat_area_h)

        canvas.set_clip(pygame.Rect(center_panel.x, chat_area_top, chat_area_w, chat_area_h))
        canvas.blit(virtual_surf, (center_panel.x, chat_area_top), area=src_rect)
        canvas.set_clip(None)

        sb_x     = center_panel.x + center_panel.width - 12
        sb_track = pygame.Rect(sb_x, chat_area_top, 8, chat_area_h)
        pygame.draw.rect(canvas, COLOR_LINE, sb_track, border_radius=4)

        if max_scroll > 0:
            thumb_ratio = chat_area_h / virtual_h
            thumb_h     = max(20, int(chat_area_h * thumb_ratio))
            thumb_frac  = 1.0 - (scroll_offset / max_scroll)
            thumb_y     = chat_area_top + int((chat_area_h - thumb_h) * thumb_frac)
            thumb_rect  = pygame.Rect(sb_x, thumb_y, 8, thumb_h)
            thumb_color = COLOR_ACCENT if dragging_scrollbar else (COLOR_ACCENT if scroll_offset > 0 else COLOR_MUTED)
            pygame.draw.rect(canvas, thumb_color, thumb_rect, border_radius=4)

        if scroll_offset > SCROLL_SPEED:
            badge_text = f"^ {scroll_offset // FONT_TEXT.get_linesize()} lines up  [scroll to return]"
            badge_surf = FONT_NAV.render(badge_text, True, COLOR_BG)
            badge_bg   = pygame.Surface((badge_surf.get_width() + 16, badge_surf.get_height() + 6))
            badge_bg.fill(COLOR_ACCENT)
            badge_bg.blit(badge_surf, (8, 3))
            canvas.blit(badge_bg, (center_panel.x + 10, chat_area_bottom - badge_bg.get_height() - 4))

        # --- CHOICE BUTTONS ---
        if choices_visible_here:
            choices = chat_manager.pending_choices

            if len(choices) != last_choice_count:
                btn_w      = center_panel.width - 40
                btn_pad_x  = 12
                btn_pad_y  = 8
                gap        = 8
                line_h     = FONT_TEXT.get_linesize()
                max_text_w = btn_w - btn_pad_x * 2

                choice_lines   = []
                choice_heights = []
                for ci, (_, crow) in enumerate(choices):
                    choice_msg = chat_manager._substitute(str(crow.get('MESSAGE', '')))
                    prefix     = f"[{ci + 1}] "
                    full_text  = prefix + choice_msg
                    words = full_text.split()
                    lines = []
                    cur_line = []
                    for word in words:
                        test = ' '.join(cur_line + [word])
                        if FONT_TEXT.size(test)[0] > max_text_w and cur_line:
                            lines.append(' '.join(cur_line))
                            cur_line = [word]
                        else:
                            cur_line.append(word)
                    if cur_line:
                        lines.append(' '.join(cur_line))
                    choice_lines.append(lines)
                    btn_h_c = len(lines) * line_h + btn_pad_y * 2
                    choice_heights.append(btn_h_c)

                total_btn_h = sum(choice_heights) + gap * (len(choices) - 1)
                start_y     = typing_ind_y - total_btn_h - 8
                choice_rects = []
                btn_y = start_y
                for ci, h in enumerate(choice_heights):
                    choice_rects.append(pygame.Rect(center_panel.x + 20, btn_y, btn_w, h))
                    btn_y += h + gap
                last_choice_count = len(choices)

            for ci, ((_, crow), btn_rect) in enumerate(zip(choices, choice_rects)):
                is_hov  = btn_rect.collidepoint(scaled_mouse_pos)
                bg_col  = COLOR_BTN_HOVER if is_hov else COLOR_BTN_BG
                bd_col  = COLOR_ACCENT if is_hov else COLOR_CARD_BORDER

                pygame.draw.rect(canvas, bg_col, btn_rect, border_radius=5)
                pygame.draw.rect(canvas, bd_col, btn_rect, 1, border_radius=5)

                line_h  = FONT_TEXT.get_linesize()
                text_y  = btn_rect.y + 8
                lines   = choice_lines[ci] if ci < len(choice_lines) else []
                for li, line in enumerate(lines):
                    c_surf = FONT_TEXT.render(line, True, COLOR_ACCENT if is_hov else COLOR_TEXT)
                    canvas.blit(c_surf, (btn_rect.x + 12, text_y))
                    text_y += line_h

        else:
            if choice_rects:
                choice_rects      = []
                choice_lines      = []
                choice_heights    = []
                last_choice_count = -1

        # "Click to continue" hint
        if not chat_manager.auto_mode and not chat_manager.skip_mode and \
           not choices_visible_here and not chat_manager.is_waiting and \
           not chat_manager.is_narrator_active and \
           chat_manager.script_index < len(chat_manager.full_script):
            blink_on  = (now // 550) % 2 == 0
            if blink_on:
                hint_text = "[ click to continue ]"
                hint_surf = FONT_SMALL.render(hint_text, True, COLOR_MUTED)
                hint_x    = center_panel.x + center_panel.width - hint_surf.get_width() - 14
                hint_y    = typing_ind_y + 4
                canvas.blit(hint_surf, (hint_x, hint_y))

        if chat_manager.is_waiting and \
           chat_manager.typing_channel == current_channel and \
           chat_manager.typing_subchannel == current_subchannel:
            dot_phase   = (now // 400) % 3   
            base_x      = center_panel.x + 10
            ind_y       = typing_ind_y
            label       = f"{chat_manager.current_typer} is typing "
            lbl_surf    = FONT_TEXT.render(label, True, COLOR_MUTED)
            canvas.blit(lbl_surf, (base_x, ind_y))
            dot_x       = base_x + lbl_surf.get_width()
            dot_spacing = FONT_TEXT.size("o")[0] + 4
            for i in range(3):
                color  = COLOR_ACCENT if i == dot_phase else COLOR_MUTED
                radius = 5 if i == dot_phase else 3
                dot_y  = ind_y + FONT_TEXT.get_height() // 2
                pygame.draw.circle(canvas, color, (dot_x + i * dot_spacing + radius, dot_y), radius)

        # DISABLED INPUT BAR
        input_rect = pygame.Rect(center_panel.x + 5, center_panel.y + center_panel.height - 45,
                                 center_panel.width - 10, 40)
        pygame.draw.rect(canvas, (25, 25, 35), input_rect)
        pygame.draw.rect(canvas, COLOR_LINE, input_rect, 1)
        cursor = "_" if (now // 500) % 2 == 0 else ""
        itxt   = FONT_TEXT.render(f"If it's your time to respond, you'll know. {cursor}", True, COLOR_MUTED)
        canvas.blit(itxt, (input_rect.x + 10, input_rect.y + 10))

        # --- RIGHT PANEL (PERSONNEL) ---
        pers_area_top    = right_panel.y + 35
        pers_area_bottom = right_panel.y + right_panel.height - 10
        pers_area_h      = pers_area_bottom - pers_area_top
        pers_area_w      = right_panel.width - 18

        total_pers_h = len(all_users) * 30 + 10
        pers_v_h     = max(total_pers_h, pers_area_h)
        pers_v_surf  = pygame.Surface((pers_area_w, pers_v_h), pygame.SRCALPHA)
        pers_v_surf.fill((0, 0, 0, 0))

        p_y = 5
        for user in all_users:
            uname       = user['name']
            display_str = f"{uname} ({user['status']})"
            is_online   = 'ONLINE' in user['status'].upper()
            is_player   = (uname == player_name)
            u_color     = COLOR_ACCENT if is_online else COLOR_MUTED

            mouse_v_y_p = scaled_mouse_pos[1] - pers_area_top + personnel_scroll
            mouse_v_x_p = scaled_mouse_pos[0] - (right_panel.x + 5)
            row_rect_v  = pygame.Rect(0, p_y - 2, pers_area_w, 28)
            in_clip     = pygame.Rect(right_panel.x + 5, pers_area_top, pers_area_w, pers_area_h)\
                              .collidepoint(scaled_mouse_pos)

            is_card_open_for_this = profile_card.visible and profile_card.npc_name == uname
            if (in_clip and row_rect_v.collidepoint((mouse_v_x_p, mouse_v_y_p)) and not is_player) \
               or is_card_open_for_this:
                pygame.draw.rect(pers_v_surf, COLOR_BTN_BG, row_rect_v, border_radius=3)
                if is_card_open_for_this:
                    pygame.draw.rect(pers_v_surf, COLOR_BTN_HOVER, row_rect_v, 1, border_radius=3)

            u_surf = FONT_TEXT.render(display_str, True, u_color)
            pers_v_surf.blit(u_surf, (5, p_y))
            p_y += 30

        pers_max_scroll  = max(0, pers_v_h - pers_area_h)
        personnel_scroll = min(personnel_scroll, pers_max_scroll)

        src_rect_pers = pygame.Rect(0, personnel_scroll, pers_area_w, pers_area_h)
        canvas.set_clip(pygame.Rect(right_panel.x + 5, pers_area_top, pers_area_w, pers_area_h))
        canvas.blit(pers_v_surf, (right_panel.x + 5, pers_area_top), area=src_rect_pers)
        canvas.set_clip(None)

        if pers_max_scroll > 0:
            psb_x     = right_panel.x + right_panel.width - 12
            psb_track = pygame.Rect(psb_x, pers_area_top, 8, pers_area_h)
            pygame.draw.rect(canvas, COLOR_LINE, psb_track, border_radius=4)
            p_thumb_ratio = pers_area_h / pers_v_h
            p_thumb_h     = max(20, int(pers_area_h * p_thumb_ratio))
            p_thumb_frac  = personnel_scroll / pers_max_scroll
            p_thumb_y     = pers_area_top + int((pers_area_h - p_thumb_h) * p_thumb_frac)
            p_thumb_rect  = pygame.Rect(psb_x, p_thumb_y, 8, p_thumb_h)
            thumb_color   = COLOR_ACCENT if dragging_pers_scroll else COLOR_MUTED
            pygame.draw.rect(canvas, thumb_color, p_thumb_rect, border_radius=4)

        # ── Channel guide (drawn on top of all panels) ────────────────────────
        if _guide_text:
            _blink_on   = (now // 700) % 2 == 0
            _guide_col  = COLOR_ACCENT if _blink_on else COLOR_MUTED
            _guide_surf = FONT_NAV.render(_guide_text, True, _guide_col)
            _pad        = 6
            _gw         = _guide_surf.get_width()  + _pad * 2
            _gh         = _guide_surf.get_height() + _pad * 2
            _gx         = INTERNAL_WIDTH - _gw - 8
            _gy         = 42
            _bg         = pygame.Surface((_gw, _gh), pygame.SRCALPHA)
            _bg.fill((*COLOR_PANEL_BG, 200))
            pygame.draw.rect(_bg, _guide_col, (0, 0, _gw, _gh), 1, border_radius=4)
            canvas.blit(_bg,         (_gx, _gy))
            canvas.blit(_guide_surf, (_gx + _pad, _gy + _pad))

        # --- NPC PROFILE CARD (drawn on top of everything except narrator) ---
        profile_card.draw(canvas, FONT_PANEL, FONT_SMALL, FONT_SMALL, scaled_mouse_pos)

        # --- NARRATOR OVERLAY (drawn last — sits above everything) ---
        narrator_overlay.draw(canvas, FONT_NARRATOR_TITLE, FONT_NARRATOR_BODY, now)

        # --- SCALE AND FLIP ---
        scaled_canvas = pygame.transform.scale(canvas, current_window_size)
        screen.blit(scaled_canvas, (0, 0))
        pygame.display.flip()
        clock.tick(30)