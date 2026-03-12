"""
credits_page.py
───────────────────────────────────────────────────────────────────────────────
Asset credits screen for "Ping: Connection Linked".
Displayed from the main menu. Scrollable, terminal aesthetic.

To add or update credits, edit the CREDITS list below — no other code needs
to change.

Returns: 'back'
"""

import pygame
import os
import json
import sys

# ── Internal resolution (matches main_interface) ──────────────────────────────
INTERNAL_WIDTH  = 1000
INTERNAL_HEIGHT = 600

# ── Default colours (overwritten by apply_theme) ──────────────────────────────
COLOR_BG         = (10,  10,  15)
COLOR_PANEL_BG   = (18,  18,  25)
COLOR_TEXT       = (200, 255, 200)
COLOR_MUTED      = (80,  100, 80)
COLOR_ACCENT     = (0,   255, 0)
COLOR_DIM_ACCENT = (0,   160, 0)
COLOR_LINE       = (40,  40,  60)
COLOR_BORDER     = (0,   200, 0)
COLOR_BTN_BG     = (0,   45,  0)
COLOR_BTN_HOVER  = (0,   80,  0)


# ══════════════════════════════════════════════════════════════════════════════
#  CREDITS DATA
#  ─────────────────────────────────────────────────────────────────────────────
#  Each entry is a dict with:
#    "section"  : str  — bold category header (set to "" for continuation rows)
#    "name"     : str  — asset / library / person name
#    "role"     : str  — what it's used for
#    "author"   : str  — creator / studio (optional, "" if none)
#    "license"  : str  — licence identifier e.g. "MIT", "CC BY 4.0", "OFL 1.1"
#    "url"      : str  — source URL shown as reference (optional)
#
#  To add a new chapter's assets, just append more dicts.
# ══════════════════════════════════════════════════════════════════════════════

CREDITS = [

    # ── ENGINE & CORE LIBRARIES ───────────────────────────────────────────────
    {
        "section": "ENGINE & LIBRARIES",
        "name":    "Pygame-CE",
        "role":    "Game engine / rendering",
        "author":  "Pygame Community",
        "license": "LGPL 2.1",
        "url":     "https://pyga.me",
    },
    {
        "section": "",
        "name":    "OpenPyXL",
        "role":    "Script (.xlsx) loading",
        "author":  "OpenPyXL Contributors",
        "license": "MIT",
        "url":     "https://openpyxl.readthedocs.io",
    },
    {
        "section": "",
        "name":    "Pandas",
        "role":    "Spreadsheet data processing",
        "author":  "Pandas Development Team",
        "license": "BSD 3-Clause",
        "url":     "https://pandas.pydata.org",
    },

    # ── FONTS ─────────────────────────────────────────────────────────────────
    {
        "section": "FONTS",
        "name":    "Consolas",
        "role":    "Default terminal font",
        "author":  "Microsoft Corporation",
        "license": "Proprietary (bundled with Windows)",
        "url":     "",
    },

    # ── SOUND & MUSIC ─────────────────────────────────────────────────────────
    {
        "section": "SOUND & MUSIC",
        "name":    "Easy HipHop",
        "role":    "Background music",
        "author":  "VibeDepot via Free Music Archive",
        "license": "CC BY-ND 4.0",
        "url":     "https://creativecommons.org/licenses/by-nd/4.0/",
    },
    {
        "section": "",
        "name":    "Urban",
        "role":    "Background music",
        "author":  "VibeDepot via Free Music Archive",
        "license": "CC BY-ND 4.0",
        "url":     "https://creativecommons.org/licenses/by-nd/4.0/",
    },
    {
        "section": "",
        "name":    "Lofi Background",
        "role":    "Background music",
        "author":  "VibeDepot via Free Music Archive",
        "license": "CC BY-ND 4.0",
        "url":     "https://creativecommons.org/licenses/by-nd/4.0/",
    },
    {
        "section": "",
        "name":    "Lofi Background Music",
        "role":    "Background music",
        "author":  "VibeDepot via Free Music Archive",
        "license": "CC BY-ND 4.0",
        "url":     "https://creativecommons.org/licenses/by-nd/4.0/",
    },
    {
        "section": "",
        "name":    "Lofi Vice",
        "role":    "Background music",
        "author":  "Snoozy Beats via Free Music Archive",
        "license": "CC BY 4.0",
        "url":     "https://creativecommons.org/licenses/by/4.0/",
    },
    {
        "section": "",
        "name":    "Lofi Chillin",
        "role":    "Background music",
        "author":  "Snoozy Beats via Free Music Archive",
        "license": "CC BY 4.0",
        "url":     "https://creativecommons.org/licenses/by/4.0/",
    },
    {
        "section": "",
        "name":    "LoFi Dreams",
        "role":    "Background music",
        "author":  "Pro Tunes via Free Music Archive",
        "license": "CC BY 4.0",
        "url":     "https://creativecommons.org/licenses/by/4.0/",
    },
    {
        "section": "",
        "name":    "Sleeping (Lofi)",
        "role":    "Background music",
        "author":  "Benjamin Lee via Free Music Archive",
        "license": "CC BY 4.0",
        "url":     "https://creativecommons.org/licenses/by/4.0/",
    },
    {
        "section": "",
        "name":    "Waiting Around (LoFi, Calm)",
        "role":    "Background music",
        "author":  "Holizna via Free Music Archive",
        "license": "CC0 / Public Domain",
        "url":     "",
    },
    {
        "section": "",
        "name":    "Shimmer (LoFi, Chill)",
        "role":    "Background music",
        "author":  "Holizna via Free Music Archive",
        "license": "CC0 / Public Domain",
        "url":     "",
    },
    {
        "section": "",
        "name":    "Lucid (Lofi, Dreamy, Chill)",
        "role":    "Background music",
        "author":  "Holizna via Free Music Archive",
        "license": "CC0 / Public Domain",
        "url":     "",
    },
    {
        "section": "",
        "name":    "Moon Unit (Lofi, Reflection, Dreamy)",
        "role":    "Background music",
        "author":  "Holizna via Free Music Archive",
        "license": "CC0 / Public Domain",
        "url":     "",
    },

    # ── IMAGES & ART ──────────────────────────────────────────────────────────
    # Add your image / sprite credits here.
    # {
    #     "section": "IMAGES & ART",
    #     "name":    "Asset Name",
    #     "role":    "Character portrait — Dr. Aris",
    #     "author":  "Artist Handle",
    #     "license": "CC BY-NC 4.0",
    #     "url":     "https://example.com",
    # },

    # ── SPECIAL THANKS ────────────────────────────────────────────────────────
    {
        "section": "SPECIAL THANKS",
        "name":    "You",
        "role":    "For playing",
        "author":  "",
        "license": "",
        "url":     "",
    },
]


# ══════════════════════════════════════════════════════════════════════════════
#  Theme helper (reads player_data.json directly, same pattern as save/load)
# ══════════════════════════════════════════════════════════════════════════════

def get_save_path(filename):
    """ Gets the real folder where the .exe is sitting to save data safely. """
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.abspath(".")
    return os.path.join(base_dir, filename)

def apply_theme():
    """Update module-level colour globals from player_data.json."""
    global COLOR_TEXT, COLOR_MUTED, COLOR_ACCENT, COLOR_DIM_ACCENT
    global COLOR_BORDER, COLOR_BTN_BG, COLOR_BTN_HOVER

    user_data = {}
    save_file_path = get_save_path("player_data.json") # <-- USE SAFE PATH HERE
    
    try:
        if os.path.exists(save_file_path):
            with open(save_file_path, "r") as f:
                user_data = json.load(f)
    except Exception:
        pass

    color_map = {
        "GREEN":   {"accent": (0, 255, 0),     "text": (200, 255, 200), "muted": (80, 100, 80),
                    "border": (0, 200, 0),     "btn_bg": (0, 45, 0),     "btn_hov": (0, 80, 0)},
        "AMBER":   {"accent": (255, 176, 0),   "text": (255, 230, 150), "muted": (160, 110, 0),
                    "border": (200, 140, 0),   "btn_bg": (60, 40, 0),    "btn_hov": (100, 70, 0)},
        "CYAN":    {"accent": (0, 255, 255),   "text": (200, 255, 255), "muted": (0, 160, 160),
                    "border": (0, 200, 200),   "btn_bg": (0, 45, 60),    "btn_hov": (0, 80, 100)},
        "RED":     {"accent": (255, 50, 50),   "text": (255, 200, 200), "muted": (180, 50, 50),
                    "border": (200, 0, 0),     "btn_bg": (60, 0, 0),     "btn_hov": (100, 0, 0)},
        "BLUE":    {"accent": (100, 150, 255), "text": (200, 220, 255), "muted": (50, 100, 200),
                    "border": (50, 100, 200),  "btn_bg": (0, 20, 60),    "btn_hov": (0, 50, 100)},
        "MAGENTA": {"accent": (255, 0, 255),   "text": (255, 200, 255), "muted": (160, 0, 160),
                    "border": (200, 0, 200),   "btn_bg": (60, 0, 60),    "btn_hov": (100, 0, 100)},
        "WHITE":   {"accent": (220, 220, 220), "text": (255, 255, 255), "muted": (140, 140, 140),
                    "border": (180, 180, 180), "btn_bg": (50, 50, 50),   "btn_hov": (90, 90, 90)},
    }

    choice = user_data.get("theme_color", "GREEN")
    if choice in color_map:
        c = color_map[choice]
        COLOR_ACCENT     = c["accent"]
        COLOR_TEXT       = c["text"]
        COLOR_MUTED      = c["muted"]
        COLOR_DIM_ACCENT = c["muted"]
        COLOR_BORDER     = c["border"]
        COLOR_BTN_BG     = c["btn_bg"]
        COLOR_BTN_HOVER  = c["btn_hov"]

    return user_data.get("theme_font", "Consolas")


# ══════════════════════════════════════════════════════════════════════════════
#  Main entry point
# ══════════════════════════════════════════════════════════════════════════════

def run_credits(screen, canvas, clock, current_window_size, is_fullscreen=False, music_player=None):
    """
    Show the credits screen.
    Returns 'back' when the player exits.
    """
    font_name = apply_theme()

    def _font(size, bold=False):
        try:
            return pygame.font.SysFont(font_name, size, bold=bold)
        except Exception:
            return pygame.font.SysFont("Consolas", size, bold=bold)

    F_TITLE   = _font(22, bold=True)
    F_SECTION = _font(15, bold=True)
    F_NAME    = _font(15)
    F_META    = _font(13)
    F_NAV     = _font(15)
    F_TINY    = _font(12)

    TOP_H      = 44
    MARGIN     = 36
    COL_X      = MARGIN                      # left edge of content
    CONTENT_W  = INTERNAL_WIDTH - MARGIN * 2
    back_rect  = pygame.Rect(MARGIN, 8, 100, 28)

    # ── Pre-render credit rows into a virtual surface ─────────────────────────
    # We'll regenerate if the window resizes (unlikely but safe).
    def _build_rows():
        """Returns a list of (y, render_fn) where render_fn(surf, y) draws the row."""
        rows = []
        y = 16

        for entry in CREDITS:
            # Section header
            if entry["section"]:
                y += 10
                # Divider line + label
                rows.append((y, entry["section"], "section"))
                y += 28

            # Asset row
            rows.append((y, entry, "entry"))
            y += 52

        return rows, y   # rows, total virtual height

    rows, virtual_h = _build_rows()

    # Scrolling state
    scroll        = 0
    scroll_target = 0
    drag_start_y  = None
    dragging      = False
    AREA_TOP      = TOP_H + 8
    AREA_H        = INTERNAL_HEIGHT - AREA_TOP - 24   # leave footer room
    max_scroll    = max(0, virtual_h - AREA_H + 32)

    # Scrollbar geometry
    SB_W     = 6
    SB_X     = INTERNAL_WIDTH - MARGIN + 6
    SB_TRACK = pygame.Rect(SB_X, AREA_TOP, SB_W, AREA_H)

    scan_off = 0

    while True:
        now = pygame.time.get_ticks()
        if music_player:
            music_player.update()
        canvas.fill(COLOR_BG)
        scan_off = (scan_off + 1) % 8

        mx, my = pygame.mouse.get_pos()
        sx_scale = INTERNAL_WIDTH  / current_window_size[0]
        sy_scale = INTERNAL_HEIGHT / current_window_size[1]
        smp = (int(mx * sx_scale), int(my * sy_scale))

        # ── Smooth scroll interpolation ───────────────────────────────────────
        scroll += (scroll_target - scroll) * 0.15
        if abs(scroll - scroll_target) < 0.5:
            scroll = scroll_target

        # ── Events ───────────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'back'

            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                    return 'back'
                elif event.key == pygame.K_DOWN:
                    scroll_target = min(max_scroll, scroll_target + 40)
                elif event.key == pygame.K_UP:
                    scroll_target = max(0, scroll_target - 40)
                elif event.key == pygame.K_PAGEDOWN:
                    scroll_target = min(max_scroll, scroll_target + AREA_H)
                elif event.key == pygame.K_PAGEUP:
                    scroll_target = max(0, scroll_target - AREA_H)
                elif event.key == pygame.K_HOME:
                    scroll_target = 0
                elif event.key == pygame.K_END:
                    scroll_target = max_scroll
                elif event.key == pygame.K_F11:
                    is_fullscreen = not is_fullscreen
                    if is_fullscreen:
                        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                        current_window_size = screen.get_size()
                    else:
                        current_window_size = (INTERNAL_WIDTH, INTERNAL_HEIGHT)
                        screen = pygame.display.set_mode(current_window_size, pygame.RESIZABLE)

            elif event.type == pygame.VIDEORESIZE and not is_fullscreen:
                current_window_size = (event.w, event.h)
                screen = pygame.display.set_mode(current_window_size, pygame.RESIZABLE)

            elif event.type == pygame.MOUSEWHEEL:
                scroll_target = max(0, min(max_scroll, scroll_target - event.y * 40))

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_rect.collidepoint(smp):
                    return 'back'
                # Scrollbar drag
                if max_scroll > 0:
                    thumb_h, thumb_y = _thumb_geometry(scroll, max_scroll, SB_TRACK)
                    thumb_rect = pygame.Rect(SB_TRACK.x, thumb_y, SB_W, thumb_h)
                    if thumb_rect.collidepoint(smp):
                        dragging     = True
                        drag_start_y = smp[1]
                        drag_scroll0 = scroll_target

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                dragging = False

            elif event.type == pygame.MOUSEMOTION and dragging:
                delta = smp[1] - drag_start_y
                ratio = delta / max(1, SB_TRACK.h)
                scroll_target = max(0, min(max_scroll, drag_scroll0 + ratio * max_scroll))

        # ── Background grid ───────────────────────────────────────────────────
        for gx in range(0, INTERNAL_WIDTH, 40):
            pygame.draw.line(canvas, (14, 18, 14), (gx, 0), (gx, INTERNAL_HEIGHT))
        for gy in range(0, INTERNAL_HEIGHT, 40):
            pygame.draw.line(canvas, (14, 18, 14), (0, gy), (INTERNAL_WIDTH, gy))

        # Scanlines
        scan_surf = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT), pygame.SRCALPHA)
        for sy in range(scan_off, INTERNAL_HEIGHT, 6):
            pygame.draw.line(scan_surf, (0, 0, 0, 14), (0, sy), (INTERNAL_WIDTH, sy))
        canvas.blit(scan_surf, (0, 0))

        # ── Top bar ───────────────────────────────────────────────────────────
        pygame.draw.rect(canvas, COLOR_PANEL_BG, (0, 0, INTERNAL_WIDTH, TOP_H))
        pygame.draw.line(canvas, COLOR_BORDER, (0, TOP_H), (INTERNAL_WIDTH, TOP_H), 1)

        b_hov = back_rect.collidepoint(smp)
        pygame.draw.rect(canvas, COLOR_BTN_HOVER if b_hov else COLOR_BTN_BG,
                         back_rect, border_radius=4)
        pygame.draw.rect(canvas, COLOR_BORDER, back_rect, 1, border_radius=4)
        canvas.blit(F_NAV.render("◄  BACK", True, COLOR_ACCENT),
                    (back_rect.x + 10, back_rect.y + 6))

        title_surf = F_TITLE.render("// CREDITS & ATTRIBUTIONS", True, COLOR_ACCENT)
        canvas.blit(title_surf,
                    (INTERNAL_WIDTH // 2 - title_surf.get_width() // 2, 10))

        hint_surf = F_TINY.render(
            "↑↓ / SCROLL / DRAG  |  ESC: back", True, COLOR_MUTED)
        canvas.blit(hint_surf,
                    (INTERNAL_WIDTH - hint_surf.get_width() - MARGIN, 16))

        # ── Scrollable content area ───────────────────────────────────────────
        canvas.set_clip(pygame.Rect(0, AREA_TOP, INTERNAL_WIDTH, AREA_H))

        for (vy, data, kind) in rows:
            draw_y = AREA_TOP + vy - int(scroll)

            # Skip rows outside the visible area
            if draw_y > AREA_TOP + AREA_H + 60:
                continue
            if draw_y < AREA_TOP - 60:
                continue

            if kind == "section":
                # Section divider + label
                label = data
                pygame.draw.line(canvas, COLOR_LINE,
                                 (COL_X, draw_y + 10),
                                 (INTERNAL_WIDTH - MARGIN - 20, draw_y + 10), 1)
                tag_surf = F_SECTION.render(f"[ {label} ]", True, COLOR_ACCENT)
                tag_bg   = pygame.Rect(COL_X - 2, draw_y - 1,
                                       tag_surf.get_width() + 8, tag_surf.get_height() + 4)
                pygame.draw.rect(canvas, COLOR_BG, tag_bg)
                canvas.blit(tag_surf, (COL_X + 2, draw_y))

            elif kind == "entry":
                entry = data
                card  = pygame.Rect(COL_X, draw_y, CONTENT_W - SB_W - 10, 46)

                # Card background
                pygame.draw.rect(canvas, COLOR_PANEL_BG, card, border_radius=4)
                pygame.draw.rect(canvas, COLOR_LINE, card, 1, border_radius=4)

                # Left accent bar
                pygame.draw.rect(canvas, COLOR_BORDER,
                                 pygame.Rect(card.x, card.y, 3, card.h),
                                 border_radius=2)

                # Name + role (top line)
                name_surf = F_NAME.render(entry["name"], True, COLOR_ACCENT)
                role_surf = F_META.render(entry["role"], True, COLOR_TEXT)
                canvas.blit(name_surf, (card.x + 12, card.y + 6))
                canvas.blit(role_surf, (card.x + 12, card.y + 24))

                # Author + license (right-aligned)
                right_x = card.right - 12
                if entry.get("author"):
                    auth_surf = F_META.render(entry["author"], True, COLOR_MUTED)
                    canvas.blit(auth_surf,
                                (right_x - auth_surf.get_width(), card.y + 6))
                if entry.get("license"):
                    lic_surf = F_META.render(
                        entry["license"], True, COLOR_DIM_ACCENT)
                    canvas.blit(lic_surf,
                                (right_x - lic_surf.get_width(), card.y + 24))

                # URL (tiny, very muted, far right of role line if present)
                if entry.get("url"):
                    url_surf = F_TINY.render(entry["url"], True, COLOR_MUTED)
                    # Clamp so it doesn't overlap the name
                    url_x = min(
                        card.x + 12 + name_surf.get_width() + 16,
                        right_x - url_surf.get_width()
                    )
                    canvas.blit(url_surf, (url_x, card.y + 8))

        canvas.set_clip(None)

        # ── Fade edges (top and bottom of content area) ───────────────────────
        for edge_y, direction in [(AREA_TOP, 1), (AREA_TOP + AREA_H, -1)]:
            for i in range(20):
                alpha = int(220 * (1 - i / 20))
                fade_surf = pygame.Surface((INTERNAL_WIDTH, 1), pygame.SRCALPHA)
                fade_surf.fill((10, 10, 15, alpha))
                canvas.blit(fade_surf, (0, edge_y + i * direction))

        # ── Scrollbar ─────────────────────────────────────────────────────────
        if max_scroll > 0:
            # Track
            pygame.draw.rect(canvas, (20, 22, 28), SB_TRACK, border_radius=3)

            thumb_h, thumb_y = _thumb_geometry(scroll, max_scroll, SB_TRACK)
            thumb_rect = pygame.Rect(SB_TRACK.x, thumb_y, SB_W, thumb_h)
            thumb_col  = COLOR_ACCENT if dragging else COLOR_BORDER
            pygame.draw.rect(canvas, thumb_col, thumb_rect, border_radius=3)

        # ── Footer ────────────────────────────────────────────────────────────
        footer_y = INTERNAL_HEIGHT - 18
        cur = "_" if (now // 500) % 2 == 0 else " "
        canvas.blit(F_TINY.render(f">{cur}", True, COLOR_DIM_ACCENT),
                    (INTERNAL_WIDTH - 28, footer_y))

        # Progress indicator
        if max_scroll > 0:
            pct = int(min(100, scroll / max_scroll * 100))
            prog_surf = F_TINY.render(f"{pct}%", True, COLOR_MUTED)
            canvas.blit(prog_surf,
                        (INTERNAL_WIDTH // 2 - prog_surf.get_width() // 2, footer_y))

        scaled = pygame.transform.scale(canvas, current_window_size)
        screen.blit(scaled, (0, 0))
        pygame.display.flip()
        clock.tick(30)

    return 'back'


def _thumb_geometry(scroll, max_scroll, track_rect):
    """Returns (thumb_height, thumb_y) for the scrollbar thumb."""
    ratio    = track_rect.h / max(1, track_rect.h + max_scroll)
    thumb_h  = max(20, int(track_rect.h * ratio))
    scroll_pct = scroll / max_scroll if max_scroll > 0 else 0
    thumb_y  = track_rect.y + int(scroll_pct * (track_rect.h - thumb_h))
    return thumb_h, thumb_y