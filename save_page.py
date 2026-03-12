"""
save_page.py
Visual novel-style save screen. 10 slots, terminal aesthetic.
Returns: 'back'  — player cancelled
         ('saved', slot_number) — player saved to a slot
"""

import pygame
import os
import json
import sys
from save_manager import all_slot_metas, save_slot, SLOT_COUNT

# ── Shared constants ──────────────────────────────────────────────────────────
INTERNAL_WIDTH  = 1000
INTERNAL_HEIGHT = 600

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
COLOR_EMPTY      = (25,  30,  25)
COLOR_CONFIRM_BG = (10,  10,  10)
COLOR_RED        = (200, 60,  60)
COLOR_RED_HOVER  = (255, 80,  80)

SLOT_H    = 70
SLOT_GAP  = 8
COLS      = 2
SLOTS_PER_COL = SLOT_COUNT // COLS   # 5 per column

def get_save_path(filename):
    """ Gets the real folder where the .exe is sitting to save data safely. """
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.abspath(".")
    return os.path.join(base_dir, filename)

def apply_theme():
    """Reads the save file directly to grab the theme and updates global colors."""
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

    color_choice = user_data.get("theme_color", "GREEN")
    
    color_map = {
        "GREEN":   {"accent": (0, 255, 0),     "text": (200, 255, 200), "muted": (80, 100, 80),   "border": (0, 200, 0),     "btn_bg": (0, 45, 0),     "btn_hov": (0, 80, 0)},
        "AMBER":   {"accent": (255, 176, 0),   "text": (255, 230, 150), "muted": (160, 110, 0),   "border": (200, 140, 0),   "btn_bg": (60, 40, 0),    "btn_hov": (100, 70, 0)},
        "CYAN":    {"accent": (0, 255, 255),   "text": (200, 255, 255), "muted": (0, 160, 160),   "border": (0, 200, 200),   "btn_bg": (0, 45, 60),    "btn_hov": (0, 80, 100)},
        "RED":     {"accent": (255, 50, 50),   "text": (255, 200, 200), "muted": (180, 50, 50),   "border": (200, 0, 0),     "btn_bg": (60, 0, 0),     "btn_hov": (100, 0, 0)},
        "BLUE":    {"accent": (100, 150, 255), "text": (200, 220, 255), "muted": (50, 100, 200),  "border": (50, 100, 200),  "btn_bg": (0, 20, 60),    "btn_hov": (0, 50, 100)},
        "MAGENTA": {"accent": (255, 0, 255),   "text": (255, 200, 255), "muted": (160, 0, 160),   "border": (200, 0, 200),   "btn_bg": (60, 0, 60),    "btn_hov": (100, 0, 100)},
        "WHITE":   {"accent": (220, 220, 220), "text": (255, 255, 255), "muted": (140, 140, 140), "border": (180, 180, 180), "btn_bg": (50, 50, 50),   "btn_hov": (90, 90, 90)}
    }
    
    if color_choice in color_map:
        c = color_map[color_choice]
        COLOR_ACCENT     = c["accent"]
        COLOR_TEXT       = c["text"]
        COLOR_MUTED      = c["muted"]
        COLOR_DIM_ACCENT = c["muted"] 
        COLOR_BORDER     = c["border"]
        COLOR_BTN_BG     = c["btn_bg"]
        COLOR_BTN_HOVER  = c["btn_hov"]

    return user_data.get("theme_font", "Consolas")


def _draw_scanlines(canvas, w, h):
    for y in range(0, h, 4):
        pygame.draw.line(canvas, (0, 0, 0, 25), (0, y), (w, y))


def _draw_slot_card(canvas, fonts, slot_n, meta, rect, is_hov, is_confirm, smp):
    """Draw a single save slot card. Returns True if overwrite confirm shown."""
    F_LABEL, F_BODY, F_SMALL = fonts

    # Card bg
    bg = COLOR_BTN_HOVER if is_hov and not is_confirm else COLOR_BTN_BG
    if is_confirm:
        bg = (30, 10, 10)
    pygame.draw.rect(canvas, bg, rect, border_radius=5)
    border_col = COLOR_ACCENT if is_hov else COLOR_BORDER
    pygame.draw.rect(canvas, border_col, rect, 1, border_radius=5)

    # Slot number badge
    badge_w = 36
    badge_rect = pygame.Rect(rect.x + 8, rect.y + (rect.height - 26) // 2, badge_w, 26)
    pygame.draw.rect(canvas, COLOR_BTN_HOVER if meta else (20, 22, 20), badge_rect, border_radius=3)
    pygame.draw.rect(canvas, COLOR_BORDER, badge_rect, 1, border_radius=3)
    num_surf = F_LABEL.render(str(slot_n), True, COLOR_ACCENT)
    canvas.blit(num_surf, (badge_rect.centerx - num_surf.get_width() // 2,
                           badge_rect.centery - num_surf.get_height() // 2))

    content_x = rect.x + badge_w + 18

    if is_confirm:
        # Overwrite confirmation
        warn = F_BODY.render("OVERWRITE?", True, COLOR_RED)
        canvas.blit(warn, (content_x, rect.y + 8))

        yes_rect = pygame.Rect(content_x, rect.y + 32, 70, 24)
        no_rect  = pygame.Rect(content_x + 80, rect.y + 32, 60, 24)
        yes_hov  = yes_rect.collidepoint(smp)
        no_hov   = no_rect.collidepoint(smp)

        pygame.draw.rect(canvas, COLOR_RED_HOVER if yes_hov else COLOR_RED, yes_rect, border_radius=3)
        pygame.draw.rect(canvas, COLOR_BTN_HOVER if no_hov else COLOR_BTN_BG, no_rect, border_radius=3)
        pygame.draw.rect(canvas, COLOR_BORDER, no_rect, 1, border_radius=3)

        yes_s = F_SMALL.render("OVERWRITE", True, (10, 10, 10) if yes_hov else COLOR_TEXT)
        no_s  = F_SMALL.render("CANCEL", True, COLOR_ACCENT)
        canvas.blit(yes_s, (yes_rect.x + 4, yes_rect.y + 5))
        canvas.blit(no_s,  (no_rect.x  + 8, no_rect.y  + 5))
        return yes_rect, no_rect

    if meta is None:
        # Empty slot
        empty_s = F_BODY.render("— EMPTY SLOT —", True, COLOR_MUTED)
        canvas.blit(empty_s, (content_x, rect.centery - empty_s.get_height() // 2))
        return None, None

    # Filled slot
    ts_surf = F_SMALL.render(meta.get("timestamp", ""), True, COLOR_DIM_ACCENT)
    canvas.blit(ts_surf, (content_x, rect.y + 8))

    preview = meta.get("preview_msg", "")
    if len(preview) > 48:
        preview = preview[:45] + "..."
    prev_surf = F_BODY.render(preview, True, COLOR_TEXT)
    canvas.blit(prev_surf, (content_x, rect.y + 28))

    count_s = F_SMALL.render(
        f"{len(meta.get('displayed_ids', []))} msgs  |  "
        f"{len(meta.get('ignored_ids', []))} branches resolved",
        True, COLOR_MUTED)
    canvas.blit(count_s, (content_x, rect.y + 48))

    return None, None


def run_save_page(screen, canvas, clock, current_window_size,
                  chat_manager, is_fullscreen=False):
    """
    Parameters
    ----------
    chat_manager : ChatManager — live instance to pull state from when saving

    Returns
    -------
    'back'              — user closed without saving
    ('saved', slot)     — saved to slot N
    """
    
    font_choice = apply_theme()
    
    try:
        F_TITLE = pygame.font.SysFont(font_choice, 22, bold=True)
        F_LABEL = pygame.font.SysFont(font_choice, 16, bold=True)
        F_BODY  = pygame.font.SysFont(font_choice, 14)
        F_SMALL = pygame.font.SysFont(font_choice, 12)
        F_NAV   = pygame.font.SysFont(font_choice, 15)
    except Exception:
        F_TITLE = pygame.font.SysFont("Consolas", 22, bold=True)
        F_LABEL = pygame.font.SysFont("Consolas", 16, bold=True)
        F_BODY  = pygame.font.SysFont("Consolas", 14)
        F_SMALL = pygame.font.SysFont("Consolas", 12)
        F_NAV   = pygame.font.SysFont("Consolas", 15)
        
    fonts   = (F_LABEL, F_BODY, F_SMALL)

    # Layout
    MARGIN   = 24
    TOP_H    = 44
    GRID_X   = MARGIN
    GRID_Y   = TOP_H + 16
    GRID_W   = INTERNAL_WIDTH - MARGIN * 2
    COL_W    = (GRID_W - 16) // COLS

    # State
    metas         = all_slot_metas()   # list of 10, None = empty
    confirm_slot  = None               # slot awaiting overwrite confirm
    flash_msg     = ""
    flash_until   = 0

    back_rect = pygame.Rect(MARGIN, 8, 100, 28)

    running = True
    while running:
        now = pygame.time.get_ticks()
        canvas.fill(COLOR_BG)

        mx, my = pygame.mouse.get_pos()
        sx = INTERNAL_WIDTH  / current_window_size[0]
        sy = INTERNAL_HEIGHT / current_window_size[1]
        smp = (int(mx * sx), int(my * sy))

        # ── Events ───────────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'back'
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if confirm_slot:
                        confirm_slot = None
                    else:
                        return 'back'
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
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Back button
                if back_rect.collidepoint(smp):
                    return 'back'

                # Slot cards
                for i in range(SLOT_COUNT):
                    col   = i // SLOTS_PER_COL
                    row   = i  % SLOTS_PER_COL
                    cx    = GRID_X + col * (COL_W + 16)
                    cy    = GRID_Y + row * (SLOT_H + SLOT_GAP)
                    srect = pygame.Rect(cx, cy, COL_W, SLOT_H)
                    slot_n = i + 1

                    if not srect.collidepoint(smp):
                        continue

                    if confirm_slot == slot_n:
                        # Click is on the confirm card — check yes/no sub-buttons
                        # (handled below via stored rects)
                        continue

                    if confirm_slot is not None:
                        # Click elsewhere cancels confirm
                        confirm_slot = None
                        break

                    # First click on a filled slot → ask confirm; empty → save directly
                    if metas[i] is not None:
                        confirm_slot = slot_n
                    else:
                        # Get last displayed message as preview
                        preview = ""
                        if chat_manager.displayed_messages:
                            last = chat_manager.displayed_messages[-1]
                            preview = f"{last.get('CHARACTER','')}: {last.get('MESSAGE','')}"
                        ok = save_slot(slot_n, chat_manager, preview)
                        if ok:
                            metas = all_slot_metas()
                            flash_msg   = f"✓  SAVED TO SLOT {slot_n}"
                            flash_until = now + 2000
                            confirm_slot = None
                            return ('saved', slot_n)
                    break

                # Handle confirm sub-buttons (yes/no drawn this frame)
                if confirm_slot is not None:
                    i     = confirm_slot - 1
                    col   = i // SLOTS_PER_COL
                    row   = i  % SLOTS_PER_COL
                    cx    = GRID_X + col * (COL_W + 16)
                    cy    = GRID_Y + row * (SLOT_H + SLOT_GAP)
                    # Reconstruct yes/no rects (same as draw logic)
                    badge_w  = 36
                    content_x = cx + badge_w + 18
                    yes_rect = pygame.Rect(content_x, cy + 32, 70, 24)
                    no_rect  = pygame.Rect(content_x + 80, cy + 32, 60, 24)

                    if yes_rect.collidepoint(smp):
                        preview = ""
                        if chat_manager.displayed_messages:
                            last = chat_manager.displayed_messages[-1]
                            preview = f"{last.get('CHARACTER','')}: {last.get('MESSAGE','')}"
                        ok = save_slot(confirm_slot, chat_manager, preview)
                        if ok:
                            metas = all_slot_metas()
                            flash_msg   = f"✓  SAVED TO SLOT {confirm_slot}"
                            flash_until = now + 2000
                            result_slot = confirm_slot
                            confirm_slot = None
                            return ('saved', result_slot)
                    elif no_rect.collidepoint(smp):
                        confirm_slot = None

        # ── Background grid ───────────────────────────────────────────────────
        for gx in range(0, INTERNAL_WIDTH, 40):
            pygame.draw.line(canvas, (14, 18, 14), (gx, 0), (gx, INTERNAL_HEIGHT))
        for gy in range(0, INTERNAL_HEIGHT, 40):
            pygame.draw.line(canvas, (14, 18, 14), (0, gy), (INTERNAL_WIDTH, gy))

        # ── Top bar ───────────────────────────────────────────────────────────
        pygame.draw.rect(canvas, COLOR_PANEL_BG, (0, 0, INTERNAL_WIDTH, TOP_H))
        pygame.draw.line(canvas, COLOR_BORDER, (0, TOP_H), (INTERNAL_WIDTH, TOP_H), 1)

        # Back button
        b_col = COLOR_BTN_HOVER if back_rect.collidepoint(smp) else COLOR_BTN_BG
        pygame.draw.rect(canvas, b_col, back_rect, border_radius=4)
        pygame.draw.rect(canvas, COLOR_BORDER, back_rect, 1, border_radius=4)
        canvas.blit(F_NAV.render("◄  BACK", True, COLOR_ACCENT), (back_rect.x + 10, back_rect.y + 6))

        # Title
        title_surf = F_TITLE.render("// SAVE PROGRESS", True, COLOR_ACCENT)
        canvas.blit(title_surf, (INTERNAL_WIDTH // 2 - title_surf.get_width() // 2, 10))

        # Hint
        hint = F_SMALL.render("SELECT A SLOT  |  ESC to cancel", True, COLOR_MUTED)
        canvas.blit(hint, (INTERNAL_WIDTH - hint.get_width() - MARGIN, 16))

        # ── Slot grid ─────────────────────────────────────────────────────────
        for i in range(SLOT_COUNT):
            col    = i // SLOTS_PER_COL
            row    = i  % SLOTS_PER_COL
            cx     = GRID_X + col * (COL_W + 16)
            cy     = GRID_Y + row * (SLOT_H + SLOT_GAP)
            srect  = pygame.Rect(cx, cy, COL_W, SLOT_H)
            slot_n = i + 1
            meta   = metas[i]
            is_hov = srect.collidepoint(smp) and confirm_slot is None
            is_con = (confirm_slot == slot_n)

            _draw_slot_card(canvas, fonts, slot_n, meta, srect, is_hov, is_con, smp)

        # ── Flash message ─────────────────────────────────────────────────────
        if now < flash_until:
            fs = F_LABEL.render(flash_msg, True, COLOR_ACCENT)
            canvas.blit(fs, (INTERNAL_WIDTH // 2 - fs.get_width() // 2,
                             INTERNAL_HEIGHT - 30))

        # ── Cursor blink ──────────────────────────────────────────────────────
        cur = "_" if (now // 500) % 2 == 0 else " "
        canvas.blit(F_SMALL.render(f">{cur}", True, COLOR_DIM_ACCENT),
                    (INTERNAL_WIDTH - 28, INTERNAL_HEIGHT - 18))

        scaled = pygame.transform.scale(canvas, current_window_size)
        screen.blit(scaled, (0, 0))
        pygame.display.flip()
        clock.tick(30)

    return 'back'