"""
load_page.py
Visual novel-style load screen. 10 slots, terminal aesthetic.
Returns: 'back'               — player cancelled
         ('loaded', slot_n)   — player loaded slot N (caller must rebuild state)
"""

import pygame
import os
import json
import sys
from save_manager import all_slot_metas, load_slot, delete_slot, SLOT_COUNT

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
COLOR_RED        = (200, 60,  60)
COLOR_RED_HOVER  = (255, 80,  80)

SLOT_H         = 70
SLOT_GAP       = 8
COLS           = 2
SLOTS_PER_COL  = SLOT_COUNT // COLS

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
    
    # <-- Use the safe path here! -->
    save_file_path = get_save_path("player_data.json")
    
    try:
        if os.path.exists(save_file_path):
            with open(save_file_path, "r") as f:
                user_data = json.load(f)
    except Exception:
        pass # If no file exists, we just use defaults

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


def _draw_slot_card(canvas, fonts, slot_n, meta, rect, is_hov, confirm_mode, smp):
    """
    confirm_mode: None | 'load' | 'delete'
    Returns (action_rects) dict with rects for interactive sub-buttons, or {}
    """
    F_LABEL, F_BODY, F_SMALL = fonts

    # Card background
    if confirm_mode:
        bg = (30, 10, 10) if confirm_mode == 'delete' else (10, 30, 10)
    elif is_hov and meta:
        bg = COLOR_BTN_HOVER
    elif meta:
        bg = COLOR_BTN_BG
    else:
        bg = (16, 18, 16)

    pygame.draw.rect(canvas, bg, rect, border_radius=5)
    border_col = COLOR_ACCENT if is_hov or confirm_mode else COLOR_BORDER
    pygame.draw.rect(canvas, border_col, rect, 1, border_radius=5)

    # Slot number badge
    badge_w    = 36
    badge_rect = pygame.Rect(rect.x + 8, rect.y + (rect.height - 26) // 2, badge_w, 26)
    badge_bg   = COLOR_BTN_HOVER if meta else (20, 22, 20)
    pygame.draw.rect(canvas, badge_bg,    badge_rect, border_radius=3)
    pygame.draw.rect(canvas, COLOR_BORDER, badge_rect, 1, border_radius=3)
    num_col  = COLOR_ACCENT if meta else COLOR_MUTED
    num_surf = F_LABEL.render(str(slot_n), True, num_col)
    canvas.blit(num_surf, (badge_rect.centerx - num_surf.get_width()  // 2,
                            badge_rect.centery - num_surf.get_height() // 2))

    content_x = rect.x + badge_w + 18
    action_rects = {}

    # ── Empty slot ────────────────────────────────────────────────────────────
    if meta is None:
        es = F_BODY.render("— EMPTY SLOT —", True, COLOR_MUTED)
        canvas.blit(es, (content_x, rect.centery - es.get_height() // 2))
        return action_rects

    # ── Confirm: load ─────────────────────────────────────────────────────────
    if confirm_mode == 'load':
        warn = F_BODY.render("LOAD THIS SAVE?", True, COLOR_ACCENT)
        canvas.blit(warn, (content_x, rect.y + 8))
        yes_r = pygame.Rect(content_x,      rect.y + 34, 60, 24)
        no_r  = pygame.Rect(content_x + 70, rect.y + 34, 60, 24)
        for r, lbl, col in [(yes_r, "LOAD", COLOR_ACCENT), (no_r, "CANCEL", COLOR_MUTED)]:
            hov = r.collidepoint(smp)
            pygame.draw.rect(canvas, COLOR_BTN_HOVER if hov else COLOR_BTN_BG, r, border_radius=3)
            pygame.draw.rect(canvas, col, r, 1, border_radius=3)
            ls = F_SMALL.render(lbl, True, col)
            canvas.blit(ls, (r.x + (r.width - ls.get_width()) // 2,
                             r.y + (r.height - ls.get_height()) // 2))
        action_rects = {'yes': yes_r, 'no': no_r}
        return action_rects

    # ── Confirm: delete ───────────────────────────────────────────────────────
    if confirm_mode == 'delete':
        warn = F_BODY.render("DELETE THIS SAVE?", True, COLOR_RED)
        canvas.blit(warn, (content_x, rect.y + 8))
        yes_r = pygame.Rect(content_x,      rect.y + 34, 70, 24)
        no_r  = pygame.Rect(content_x + 80, rect.y + 34, 60, 24)
        yes_hov = yes_r.collidepoint(smp)
        no_hov  = no_r.collidepoint(smp)
        pygame.draw.rect(canvas, COLOR_RED_HOVER if yes_hov else COLOR_RED, yes_r, border_radius=3)
        pygame.draw.rect(canvas, COLOR_BTN_HOVER  if no_hov  else COLOR_BTN_BG, no_r, border_radius=3)
        pygame.draw.rect(canvas, COLOR_BORDER, no_r, 1, border_radius=3)
        for r, lbl, col in [(yes_r, "DELETE", (10,10,10)), (no_r, "CANCEL", COLOR_ACCENT)]:
            ls = F_SMALL.render(lbl, True, col)
            canvas.blit(ls, (r.x + (r.width - ls.get_width()) // 2,
                             r.y + (r.height - ls.get_height()) // 2))
        action_rects = {'yes': yes_r, 'no': no_r}
        return action_rects

    # ── Normal filled slot ────────────────────────────────────────────────────
    ts_surf = F_SMALL.render(meta.get("timestamp", ""), True, COLOR_DIM_ACCENT)
    canvas.blit(ts_surf, (content_x, rect.y + 6))

    preview = meta.get("preview_msg", "")
    if len(preview) > 46:
        preview = preview[:43] + "..."
    prev_surf = F_BODY.render(preview, True, COLOR_TEXT)
    canvas.blit(prev_surf, (content_x, rect.y + 24))

    count_s = F_SMALL.render(
        f"{len(meta.get('displayed_ids',[]))} msgs  |  "
        f"{len(meta.get('ignored_ids',[]))} branches resolved",
        True, COLOR_MUTED)
    canvas.blit(count_s, (content_x, rect.y + 46))

    # Delete button (small, far right)
    del_rect = pygame.Rect(rect.right - 58, rect.y + 8, 50, 20)
    del_hov  = del_rect.collidepoint(smp)
    pygame.draw.rect(canvas, COLOR_RED if del_hov else (60, 20, 20), del_rect, border_radius=3)
    dl = F_SMALL.render("DEL", True, (255, 255, 255))
    canvas.blit(dl, (del_rect.centerx - dl.get_width()  // 2,
                     del_rect.centery - dl.get_height() // 2))
    action_rects['delete'] = del_rect

    return action_rects


def run_load_page(screen, canvas, clock, current_window_size,
                  chat_manager, is_fullscreen=False):
    """
    Returns
    -------
    'back'            — user closed without loading
    ('loaded', slot)  — loaded slot N; caller should reset scroll/prev_msg_count
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

    MARGIN        = 24
    TOP_H         = 44
    GRID_X        = MARGIN
    GRID_Y        = TOP_H + 16
    GRID_W        = INTERNAL_WIDTH - MARGIN * 2
    COL_W         = (GRID_W - 16) // COLS

    metas         = all_slot_metas()
    confirm_slot  = None     # slot number
    confirm_mode  = None     # 'load' | 'delete'
    flash_msg     = ""
    flash_until   = 0

    back_rect = pygame.Rect(MARGIN, 8, 100, 28)

    # Cache action rects per slot so clicks work next frame
    slot_action_rects = {}   # slot_n -> {'yes':Rect, 'no':Rect, 'delete':Rect}

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
                        confirm_mode = None
                    else:
                        return 'back'
                elif event.type == pygame.K_F11:
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
                if back_rect.collidepoint(smp):
                    return 'back'

                # Check confirm sub-buttons first (from previous frame's rects)
                if confirm_slot is not None:
                    arects = slot_action_rects.get(confirm_slot, {})
                    if arects.get('yes', pygame.Rect(0,0,0,0)).collidepoint(smp):
                        if confirm_mode == 'load':
                            ok = load_slot(confirm_slot, chat_manager)
                            if ok:
                                return ('loaded', confirm_slot)
                        elif confirm_mode == 'delete':
                            delete_slot(confirm_slot)
                            metas = all_slot_metas()
                            flash_msg   = f"✓  SLOT {confirm_slot} DELETED"
                            flash_until = now + 2000
                        confirm_slot = None
                        confirm_mode = None
                        continue
                    elif arects.get('no', pygame.Rect(0,0,0,0)).collidepoint(smp):
                        confirm_slot = None
                        confirm_mode = None
                        continue
                    else:
                        # Click outside confirm → cancel
                        confirm_slot = None
                        confirm_mode = None

                # Slot card clicks
                for i in range(SLOT_COUNT):
                    col    = i // SLOTS_PER_COL
                    row    = i  % SLOTS_PER_COL
                    cx     = GRID_X + col * (COL_W + 16)
                    cy     = GRID_Y + row * (SLOT_H + SLOT_GAP)
                    srect  = pygame.Rect(cx, cy, COL_W, SLOT_H)
                    slot_n = i + 1

                    if not srect.collidepoint(smp):
                        continue

                    meta = metas[i]
                    if meta is None:
                        break  # empty — ignore click

                    # Check delete sub-button (always present on filled slots)
                    arects = slot_action_rects.get(slot_n, {})
                    if arects.get('delete', pygame.Rect(0,0,0,0)).collidepoint(smp):
                        confirm_slot = slot_n
                        confirm_mode = 'delete'
                        break

                    # Normal click → load confirm
                    confirm_slot = slot_n
                    confirm_mode = 'load'
                    break

        # ── Background grid ───────────────────────────────────────────────────
        for gx in range(0, INTERNAL_WIDTH, 40):
            pygame.draw.line(canvas, (14, 18, 14), (gx, 0), (gx, INTERNAL_HEIGHT))
        for gy in range(0, INTERNAL_HEIGHT, 40):
            pygame.draw.line(canvas, (14, 18, 14), (0, gy), (INTERNAL_WIDTH, gy))

        # ── Top bar ───────────────────────────────────────────────────────────
        pygame.draw.rect(canvas, COLOR_PANEL_BG, (0, 0, INTERNAL_WIDTH, TOP_H))
        pygame.draw.line(canvas, COLOR_BORDER, (0, TOP_H), (INTERNAL_WIDTH, TOP_H), 1)

        b_col = COLOR_BTN_HOVER if back_rect.collidepoint(smp) else COLOR_BTN_BG
        pygame.draw.rect(canvas, b_col, back_rect, border_radius=4)
        pygame.draw.rect(canvas, COLOR_BORDER, back_rect, 1, border_radius=4)
        canvas.blit(F_NAV.render("◄  BACK", True, COLOR_ACCENT), (back_rect.x + 10, back_rect.y + 6))

        title_surf = F_TITLE.render("// LOAD SAVE", True, COLOR_ACCENT)
        canvas.blit(title_surf, (INTERNAL_WIDTH // 2 - title_surf.get_width() // 2, 10))

        hint = F_SMALL.render("CLICK SLOT TO LOAD  |  DEL to delete  |  ESC to cancel",
                               True, COLOR_MUTED)
        canvas.blit(hint, (INTERNAL_WIDTH - hint.get_width() - MARGIN, 16))

        # ── Slot grid ─────────────────────────────────────────────────────────
        slot_action_rects = {}
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
            c_mode = confirm_mode if is_con else None

            arects = _draw_slot_card(canvas, fonts, slot_n, meta,
                                      srect, is_hov, c_mode, smp)
            if arects:
                slot_action_rects[slot_n] = arects

        # ── Flash message ─────────────────────────────────────────────────────
        if now < flash_until:
            fs = F_LABEL.render(flash_msg, True, COLOR_ACCENT)
            canvas.blit(fs, (INTERNAL_WIDTH // 2 - fs.get_width() // 2,
                             INTERNAL_HEIGHT - 30))

        cur = "_" if (now // 500) % 2 == 0 else " "
        canvas.blit(F_SMALL.render(f">{cur}", True, COLOR_DIM_ACCENT),
                    (INTERNAL_WIDTH - 28, INTERNAL_HEIGHT - 18))

        scaled = pygame.transform.scale(canvas, current_window_size)
        screen.blit(scaled, (0, 0))
        pygame.display.flip()
        clock.tick(30)

    return 'back'