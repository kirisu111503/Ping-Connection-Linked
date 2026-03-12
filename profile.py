import pygame
import os
import json
import sys

# ── Shared constants (mirror chat_interface.py) ──────────────────────────────
INTERNAL_WIDTH  = 1000
INTERNAL_HEIGHT = 600

COLOR_BG         = (10,  10,  15)
COLOR_TEXT       = (200, 255, 200)
COLOR_PANEL_BG   = (18,  18,  25)
COLOR_LINE       = (40,  40,  60)
COLOR_MUTED      = (80,  100, 80)
COLOR_ACCENT     = (0,   255, 0)
COLOR_DIM_ACCENT = (0,   160, 0)
COLOR_CARD_BG    = (22,  28,  22)
COLOR_BORDER     = (0,   200, 0)
COLOR_BTN_BG     = (0,   50,  0)
COLOR_BTN_HOVER  = (0,   90,  0)
COLOR_RED        = (255, 80,  80)
COLOR_SCANLINE   = (0,   255, 0, 12)

AVATAR_SIZE = 140

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_save_path(filename):
    """ Gets the real folder where the .exe is sitting to save data safely. """
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.abspath(".")
    return os.path.join(base_dir, filename)

def apply_theme():
    global COLOR_TEXT, COLOR_MUTED, COLOR_ACCENT, COLOR_DIM_ACCENT
    global COLOR_BORDER, COLOR_BTN_BG, COLOR_BTN_HOVER
    
    user_data = {}
    save_file_path = get_save_path("player_data.json")
    try:
        if os.path.exists("player_data.json"):
            with open("player_data.json", "r") as f:
                user_data = json.load(f)
    except Exception:
        pass 

    color_choice = user_data.get("theme_color", "GREEN")
    
    color_map = {
        "GREEN":   {"accent": (0, 255, 0),     "text": (200, 255, 200), "muted": (80, 100, 80),   "border": (0, 200, 0),     "btn_bg": (0, 50, 0),     "btn_hov": (0, 90, 0)},
        "AMBER":   {"accent": (255, 176, 0),   "text": (255, 230, 150), "muted": (160, 110, 0),   "border": (200, 140, 0),   "btn_bg": (60, 40, 0),    "btn_hov": (100, 70, 0)},
        "CYAN":    {"accent": (0, 255, 255),   "text": (200, 255, 255), "muted": (0, 160, 160),   "border": (0, 200, 200),   "btn_bg": (0, 50, 60),    "btn_hov": (0, 90, 100)},
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

def _load_avatar(profile_id: str, size: int) -> pygame.Surface:
    img_path = resource_path(os.path.join("assets", "images", f"{profile_id}.png"))
    try:
        raw    = pygame.image.load(img_path).convert_alpha()
        scaled = pygame.transform.smoothscale(raw, (size, size))
    except Exception as e:
        print(f"[PROFILE] Avatar load failed ({img_path}): {e}")
        return _placeholder_avatar(size)

    result = pygame.Surface((size, size), pygame.SRCALPHA)
    result.fill((0, 0, 0, 0))
    cx = cy = size // 2
    r  = size // 2
    for py in range(size):
        for px in range(size):
            if (px - cx) ** 2 + (py - cy) ** 2 <= r * r:
                result.set_at((px, py), scaled.get_at((px, py)))
    pygame.draw.circle(result, COLOR_BORDER, (cx, cy), r, 3)
    return result


def _placeholder_avatar(size: int) -> pygame.Surface:
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.circle(surf, (25, 40, 25),    (size//2, size//2), size//2)
    pygame.draw.circle(surf, COLOR_BORDER,    (size//2, size//2), size//2, 3)
    head_r = size // 5
    pygame.draw.circle(surf, (80, 130, 80),   (size//2, size//3), head_r)
    body   = pygame.Rect(size//2 - head_r - 3, size//3 + head_r,
                         (head_r + 3) * 2, head_r + 8)
    pygame.draw.ellipse(surf, (60, 110, 60),  body)
    return surf


def _make_scanline_overlay(w: int, h: int) -> pygame.Surface:
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    surf.fill((0, 0, 0, 0))
    for y in range(0, h, 4):
        pygame.draw.line(surf, (0, 0, 0, 30), (0, y), (w, y))
    return surf


def _draw_tag(surface, font, text, x, y, color, bg):
    pad_x, pad_y = 8, 3
    tw, th = font.size(text)
    tag_rect = pygame.Rect(x, y, tw + pad_x * 2, th + pad_y * 2)
    pygame.draw.rect(surface, bg,    tag_rect, border_radius=3)
    pygame.draw.rect(surface, color, tag_rect, 1, border_radius=3)
    surface.blit(font.render(text, True, color), (x + pad_x, y + pad_y))
    return tag_rect.right + 8


def _wrap_text(text: str, font, max_w: int) -> list[str]:
    words = text.split()
    lines, line = [], []
    for word in words:
        test = ' '.join(line + [word])
        if font.size(test)[0] > max_w and line:
            lines.append(' '.join(line))
            line = [word]
        else:
            line.append(word)
    if line:
        lines.append(' '.join(line))
    return lines or ['']


def _glitch_surface(surf: pygame.Surface, offset: int = 3) -> pygame.Surface:
    w, h  = surf.get_size()
    out   = pygame.Surface((w + offset, h), pygame.SRCALPHA)
    out.fill((0, 0, 0, 0))
    r_surf = surf.copy(); r_surf.fill((255, 0, 0, 180), special_flags=pygame.BLEND_RGBA_MULT)
    g_surf = surf.copy(); g_surf.fill((0, 255, 0, 180), special_flags=pygame.BLEND_RGBA_MULT)
    b_surf = surf.copy(); b_surf.fill((0, 0, 255, 180), special_flags=pygame.BLEND_RGBA_MULT)
    out.blit(r_surf, (0,      0))
    out.blit(b_surf, (offset, 0))
    out.blit(g_surf, (offset//2, 0))
    return out


def run_profile(screen, canvas, clock, current_window_size, npc_info: dict,
                is_fullscreen: bool = False, music_player=None):
    """
    Full-screen NPC profile viewer.

    Parameters
    ----------
    npc_info      : dict  — One row from NPC.xlsx
    music_player  : MusicPlayer | None — passed in so tracks advance while
                    the profile screen is open (update() called each frame).
    """

    font_choice = apply_theme()
    
    try:
        F_TITLE   = pygame.font.SysFont(font_choice, 28, bold=True)
        F_HEAD    = pygame.font.SysFont(font_choice, 17, bold=True)
        F_BODY    = pygame.font.SysFont(font_choice, 15)
        F_SMALL   = pygame.font.SysFont(font_choice, 13)
        F_BADGE   = pygame.font.SysFont(font_choice, 12, bold=True)
        F_NAV     = pygame.font.SysFont(font_choice, 16)
    except Exception:
        F_TITLE   = pygame.font.SysFont("Consolas", 28, bold=True)
        F_HEAD    = pygame.font.SysFont("Consolas", 17, bold=True)
        F_BODY    = pygame.font.SysFont("Consolas", 15)
        F_SMALL   = pygame.font.SysFont("Consolas", 13)
        F_BADGE   = pygame.font.SysFont("Consolas", 12, bold=True)
        F_NAV     = pygame.font.SysFont("Consolas", 16)

    fullname   = str(npc_info.get('FULLNAME',   'UNKNOWN')).strip() or 'UNKNOWN'
    username   = str(npc_info.get('USERNAME',   '@???')).strip()
    age        = str(npc_info.get('AGE',        '?')).strip()
    sex        = str(npc_info.get('SEX',        '?')).strip()
    role       = str(npc_info.get('ROLE',       'UNKNOWN')).strip()
    bio        = str(npc_info.get('BIO',        '')).strip()
    profile_id = str(npc_info.get('PROFILE_ID', '')).strip()
    if profile_id.endswith('.0'):
        profile_id = profile_id[:-2]
    status     = str(npc_info.get('STATUS', 'OFFLINE')).upper().strip() or 'OFFLINE'
    try:
        clearance  = max(1, min(5, int(float(str(npc_info.get('CLEARANCE', 1))))))
    except Exception:
        clearance  = 1
    is_online  = 'ONLINE' in status

    avatar      = _load_avatar(profile_id, AVATAR_SIZE) if profile_id else _placeholder_avatar(AVATAR_SIZE)
    scanlines   = _make_scanline_overlay(INTERNAL_WIDTH, INTERNAL_HEIGHT)
    name_surf_base = F_TITLE.render(fullname, True, COLOR_ACCENT)

    MARGIN      = 24
    LEFT_COL_W  = AVATAR_SIZE + MARGIN * 2 + 20
    RIGHT_X     = LEFT_COL_W + MARGIN
    RIGHT_W     = INTERNAL_WIDTH - RIGHT_X - MARGIN

    back_rect   = pygame.Rect(MARGIN, MARGIN - 4, 110, 30)

    glitch_timer    = 0
    glitch_active   = False
    glitch_offset   = 0

    running = True
    while running:
        now = pygame.time.get_ticks()
        canvas.fill(COLOR_BG)

        # ── Tick music so tracks advance while profile is open ────────────────
        if music_player:
            music_player.update()

        mx, my = pygame.mouse.get_pos()
        sx = INTERNAL_WIDTH  / current_window_size[0]
        sy = INTERNAL_HEIGHT / current_window_size[1]
        smp = (int(mx * sx), int(my * sy))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'quit'
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                    return 'back'
                elif event.key == pygame.K_F11:
                    is_fullscreen = not is_fullscreen
                    if is_fullscreen:
                        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                        current_window_size = screen.get_size()
                    else:
                        current_window_size = (INTERNAL_WIDTH, INTERNAL_HEIGHT)
                        screen = pygame.display.set_mode(current_window_size, pygame.RESIZABLE)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_rect.collidepoint(smp):
                    return 'back'
            elif event.type == pygame.VIDEORESIZE and not is_fullscreen:
                current_window_size = (event.w, event.h)
                screen = pygame.display.set_mode(current_window_size, pygame.RESIZABLE)

        if now - glitch_timer > 4000 and not glitch_active:
            glitch_active  = True
            glitch_timer   = now
            glitch_offset  = 4
        if glitch_active and now - glitch_timer > 120:
            glitch_active  = False
            glitch_offset  = 0

        for gx in range(0, INTERNAL_WIDTH, 40):
            pygame.draw.line(canvas, (15, 20, 15), (gx, 0), (gx, INTERNAL_HEIGHT))
        for gy in range(0, INTERNAL_HEIGHT, 40):
            pygame.draw.line(canvas, (15, 20, 15), (0, gy), (INTERNAL_WIDTH, gy))

        pygame.draw.rect(canvas, COLOR_PANEL_BG, (0, 0, INTERNAL_WIDTH, 44))
        pygame.draw.line(canvas, COLOR_BORDER,   (0, 44), (INTERNAL_WIDTH, 44), 1)

        b_color = COLOR_BTN_HOVER if back_rect.collidepoint(smp) else COLOR_BTN_BG
        pygame.draw.rect(canvas, b_color,   back_rect, border_radius=4)
        pygame.draw.rect(canvas, COLOR_BORDER, back_rect, 1, border_radius=4)
        back_lbl = F_NAV.render("◄  BACK", True, COLOR_ACCENT)
        canvas.blit(back_lbl, (back_rect.x + 10, back_rect.y + 6))

        bc_parts = [
            ("A.L.I.C.E. NET", COLOR_MUTED),
            ("  /  ", COLOR_LINE),
            ("PERSONNEL", COLOR_MUTED),
            ("  /  ", COLOR_LINE),
            (username, COLOR_ACCENT),
        ]
        bc_x = back_rect.right + 20
        for bc_text, bc_col in bc_parts:
            bs = F_SMALL.render(bc_text, True, bc_col)
            canvas.blit(bs, (bc_x, 14))
            bc_x += bs.get_width()

        left_panel = pygame.Rect(MARGIN, 56, LEFT_COL_W - MARGIN, INTERNAL_HEIGHT - 70)
        pygame.draw.rect(canvas, COLOR_CARD_BG, left_panel, border_radius=6)
        pygame.draw.rect(canvas, COLOR_LINE,    left_panel, 1, border_radius=6)

        av_x = left_panel.x + (left_panel.width - AVATAR_SIZE) // 2
        av_y = left_panel.y + 20
        canvas.blit(avatar, (av_x, av_y))

        dot_y   = av_y + AVATAR_SIZE + 12
        dot_col = COLOR_ACCENT if is_online else COLOR_RED
        dot_cx  = left_panel.centerx
        pygame.draw.circle(canvas, dot_col, (dot_cx - 30, dot_y + 7), 5)
        st_surf = F_SMALL.render(status, True, dot_col)
        canvas.blit(st_surf, (dot_cx - 22, dot_y))

        div_y = dot_y + 22
        pygame.draw.line(canvas, COLOR_LINE,
                         (left_panel.x + 10, div_y),
                         (left_panel.right - 10, div_y))

        stats = [
            ("USERNAME", username),
            ("AGE",      age),
            ("SEX",      sex),
        ]
        sy_off = div_y + 10
        for label, val in stats:
            lbl_s = F_SMALL.render(label, True, COLOR_MUTED)
            val_s = F_BODY.render(val,   True, COLOR_TEXT)
            canvas.blit(lbl_s, (left_panel.x + 12, sy_off))
            sy_off += lbl_s.get_height() + 1
            canvas.blit(val_s, (left_panel.x + 12, sy_off))
            sy_off += val_s.get_height() + 8

        role_bg   = (0, 45, 0)
        role_col  = COLOR_ACCENT
        role_surf = F_BADGE.render(f"  {role.upper()}  ", True, role_col)
        role_rect = role_surf.get_rect(
            centerx = left_panel.centerx,
            bottom  = left_panel.bottom - 14
        )
        pygame.draw.rect(canvas, role_bg,  role_rect.inflate(4, 4), border_radius=4)
        pygame.draw.rect(canvas, role_col, role_rect.inflate(4, 4), 1, border_radius=4)
        canvas.blit(role_surf, role_rect)

        right_panel = pygame.Rect(RIGHT_X, 56, RIGHT_W, INTERNAL_HEIGHT - 70)
        pygame.draw.rect(canvas, COLOR_CARD_BG, right_panel, border_radius=6)
        pygame.draw.rect(canvas, COLOR_LINE,    right_panel, 1, border_radius=6)

        ry = right_panel.y + 20
        rx = right_panel.x + 20
        rw = right_panel.width - 40

        if glitch_active and glitch_offset:
            glitched = _glitch_surface(name_surf_base, glitch_offset)
            canvas.blit(glitched, (rx - glitch_offset // 2, ry))
            name_w = glitched.get_width()
        else:
            canvas.blit(name_surf_base, (rx, ry))
            name_w = name_surf_base.get_width()

        ry += name_surf_base.get_height() + 4
        pygame.draw.line(canvas, COLOR_ACCENT, (rx, ry), (rx + name_w, ry), 1)
        ry += 10

        next_x = _draw_tag(canvas, F_BADGE, role.upper(), rx, ry, COLOR_ACCENT, (0, 40, 0))
        id_tag = f"ID#{profile_id}" if profile_id else "ID#???"
        _draw_tag(canvas, F_BADGE, id_tag, next_x, ry, COLOR_MUTED, (20, 25, 20))
        ry += 24

        ry += 6
        sec_lbl = F_HEAD.render("▌ PERSONNEL FILE", True, COLOR_DIM_ACCENT)
        canvas.blit(sec_lbl, (rx, ry))
        ry += sec_lbl.get_height() + 6
        pygame.draw.line(canvas, COLOR_LINE, (rx, ry), (right_panel.right - 20, ry))
        ry += 10

        if bio:
            bio_lines = _wrap_text(bio, F_BODY, rw)
            for line in bio_lines:
                ls = F_BODY.render(line, True, COLOR_TEXT)
                canvas.blit(ls, (rx, ry))
                ry += ls.get_height() + 3
        else:
            nb = F_BODY.render("[NO FILE FOUND]", True, COLOR_MUTED)
            canvas.blit(nb, (rx, ry))
            ry += nb.get_height() + 3

        ry += 16
        sec2 = F_HEAD.render("▌ LAST KNOWN STATUS", True, COLOR_DIM_ACCENT)
        canvas.blit(sec2, (rx, ry))
        ry += sec2.get_height() + 6
        pygame.draw.line(canvas, COLOR_LINE, (rx, ry), (right_panel.right - 20, ry))
        ry += 10

        status_line = F_BODY.render(status, True, dot_col)
        canvas.blit(status_line, (rx, ry))
        ry += status_line.get_height() + 3

        ry += 16
        sec3 = F_HEAD.render("▌ SYSTEM ACCESS", True, COLOR_DIM_ACCENT)
        canvas.blit(sec3, (rx, ry))
        ry += sec3.get_height() + 6
        pygame.draw.line(canvas, COLOR_LINE, (rx, ry), (right_panel.right - 20, ry))
        ry += 10

        bar_w    = rw
        bar_h    = 14
        bar_rect = pygame.Rect(rx, ry, bar_w, bar_h)
        pygame.draw.rect(canvas, (15, 25, 15), bar_rect, border_radius=3)
        fill_frac = clearance / 5
        fill_rect = pygame.Rect(rx, ry, int(bar_w * fill_frac), bar_h)
        bar_col = [
            (0, 140, 0),
            (80, 160, 0),
            (180, 160, 0),
            (200, 100, 0),
            (200, 40,  0),
        ][clearance - 1]
        pygame.draw.rect(canvas, bar_col, fill_rect, border_radius=3)
        pygame.draw.rect(canvas, COLOR_LINE, bar_rect,  1, border_radius=3)
        lvl_text = F_SMALL.render(f"CLEARANCE  {clearance}/5", True, COLOR_MUTED)
        canvas.blit(lvl_text, (rx, ry + bar_h + 4))
        ry += bar_h + 20

        stamp_surf = F_TITLE.render("[ CLASSIFIED ]", True, (180, 30, 30))
        stamp_surf.set_alpha(22)
        canvas.blit(stamp_surf,
                    (right_panel.centerx - stamp_surf.get_width() // 2,
                     right_panel.bottom  - stamp_surf.get_height() - 18))

        cursor = "_" if (now // 500) % 2 == 0 else ""
        cur_s  = F_SMALL.render(f">{cursor}", True, COLOR_DIM_ACCENT)
        canvas.blit(cur_s, (right_panel.right - 30, right_panel.bottom - 20))

        canvas.blit(scanlines, (0, 0))

        scaled = pygame.transform.scale(canvas, current_window_size)
        screen.blit(scaled, (0, 0))
        pygame.display.flip()
        clock.tick(30)

    return 'back'