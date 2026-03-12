import pygame
import json
import os
import sys
import random
import chat_interface

import ctypes

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('mygame.unique.id')
except:
    pass

try:
    import cv2
    import numpy
    _CV2_AVAILABLE = True
except ImportError:
    _CV2_AVAILABLE = False
from load_page import run_load_page
from credits_page import run_credits
from boot_screen import run_boot as _run_boot_screen
from music_player import MusicPlayer, MODES

INTERNAL_WIDTH  = 1000
INTERNAL_HEIGHT = 600
TITLE           = "Ping: Connection Linked"
LAB_NAME        = "A.L.I.C.E. SECURE TERMINAL"
DATA_FILE       = "player_data.json"

COLOR_BG         = (10,  10,  15)
COLOR_TEXT       = (200, 255, 200)
COLOR_ACCENT     = (0,   255, 0)
COLOR_DIM_ACCENT = (0,   160, 0)
COLOR_ERROR      = (255, 50,  50)
COLOR_BOX        = (30,  30,  40)
COLOR_BOX_ACTIVE = (50,  50,  70)
COLOR_MUTED      = (80,  100, 80)
COLOR_LINE       = (40,  40,  60)
COLOR_PANEL_BG   = (18,  18,  25)

pygame.mixer.pre_init(44100, -16, 2, 2048)
pygame.init()
icon = pygame.image.load(resource_path('assets/images/lab_logo.png'))
small_icon = pygame.transform.scale(icon, (16, 16))
pygame.display.set_icon(small_icon)
pygame.display.set_caption("My Awesome Game")
pygame.mixer.init()

current_window_size = (INTERNAL_WIDTH, INTERNAL_HEIGHT)
screen  = pygame.display.set_mode(current_window_size, pygame.RESIZABLE)
pygame.display.set_caption(TITLE)
canvas  = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT))
clock   = pygame.time.Clock()

FONT_TITLE  = pygame.font.SysFont("Consolas", 36, bold=True)
FONT_HEAD   = pygame.font.SysFont("Consolas", 22, bold=True)
FONT_TEXT   = pygame.font.SysFont("Consolas", 20)
FONT_SMALL  = pygame.font.SysFont("Consolas", 14)
FONT_TINY   = pygame.font.SysFont("Consolas", 12)

def apply_theme(user_data):
    global COLOR_ACCENT, COLOR_DIM_ACCENT
    global FONT_TITLE, FONT_HEAD, FONT_TEXT, FONT_SMALL, FONT_TINY
    if not user_data:
        return
    color_map = {
        "GREEN":   ((0, 255, 0),     (0, 160, 0)),
        "AMBER":   ((255, 176, 0),   (160, 110, 0)),
        "CYAN":    ((0, 255, 255),   (0, 160, 160)),
        "RED":     ((255, 50, 50),   (180, 0, 0)),
        "BLUE":    ((100, 150, 255), (0, 80, 200)),
        "MAGENTA": ((255, 0, 255),   (160, 0, 160)),
        "WHITE":   ((220, 220, 220), (140, 140, 140))
    }
    c = user_data.get("theme_color", "GREEN")
    if c in color_map:
        COLOR_ACCENT, COLOR_DIM_ACCENT = color_map[c]
    f = user_data.get("theme_font", "Consolas")
    try:
        FONT_TITLE = pygame.font.SysFont(f, 36, bold=True)
        FONT_HEAD  = pygame.font.SysFont(f, 22, bold=True)
        FONT_TEXT  = pygame.font.SysFont(f, 20)
        FONT_SMALL = pygame.font.SysFont(f, 14)
        FONT_TINY  = pygame.font.SysFont(f, 12)
    except Exception:
        pass

LOGO_PATH = resource_path(os.path.join("assets", "images", "lab_logo.png"))
try:
    _raw_logo  = pygame.image.load(LOGO_PATH).convert_alpha()
    _logo_w    = 160   # ← reduced from 280
    _logo_h    = int(_logo_w * _raw_logo.get_height() / _raw_logo.get_width())
    login_logo = pygame.transform.smoothscale(_raw_logo, (_logo_w, _logo_h))
except FileNotFoundError:
    login_logo = None


# ── UI Components ─────────────────────────────────────────────────────────────

class InputBox:
    def __init__(self, x, y, w, h, label, text='', is_password=False):
        self.rect        = pygame.Rect(x, y, w, h)
        self.color       = COLOR_BOX
        self.label       = label
        self.text        = text
        self.is_password = is_password
        self.active      = False
        self._refresh()

    def _refresh(self):
        disp = "*" * len(self.text) if self.is_password else self.text
        self.txt_surface = FONT_TEXT.render(disp, True, COLOR_TEXT)

    def handle_event(self, event, smp):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(smp)
            self.color  = COLOR_BOX_ACTIVE if self.active else COLOR_BOX
        if event.type == pygame.KEYDOWN and self.active:
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER): return "SUBMIT"
            elif event.key == pygame.K_BACKSPACE: self.text = self.text[:-1]
            elif event.key == pygame.K_TAB: return "NEXT"
            elif event.unicode.isprintable(): self.text += event.unicode
            self._refresh()
        return None

    def draw(self, surface):
        surface.blit(FONT_SMALL.render(self.label, True, COLOR_TEXT), (self.rect.x, self.rect.y - 20))
        pygame.draw.rect(surface, self.color, self.rect)
        pygame.draw.rect(surface, COLOR_ACCENT if self.active else (100,100,100), self.rect, 2)
        surface.blit(self.txt_surface, (self.rect.x + 10, self.rect.y + 10))
        if self.active and (pygame.time.get_ticks() // 500) % 2 == 0:
            cx = self.rect.x + 10 + self.txt_surface.get_width() + 2
            pygame.draw.line(surface, COLOR_ACCENT, (cx, self.rect.y+8), (cx, self.rect.y+self.rect.h-8), 2)


class Dropdown:
    def __init__(self, x, y, w, h, label, options, max_visible=4):
        self.rect           = pygame.Rect(x, y, w, h)
        self.label          = label
        self.options        = options
        self.selected_index = 0
        self.text           = options[0]
        self.active         = False
        self.is_open        = False
        self.hovered_option = -1
        self.color          = COLOR_BOX
        self.max_visible    = max_visible
        self.scroll_offset  = 0

    def handle_event(self, event, smp):
        if self.is_open:
            visible_count = min(self.max_visible, len(self.options) - self.scroll_offset)
            drop_h  = self.rect.h * visible_count
            opens_up = (self.rect.bottom + drop_h) > INTERNAL_HEIGHT
            def _row_rect(i):
                row_y = (self.rect.y - drop_h + i * self.rect.h) if opens_up else (self.rect.y + self.rect.h * (i+1))
                return pygame.Rect(self.rect.x, row_y, self.rect.w, self.rect.h)
            if event.type == pygame.MOUSEWHEEL:
                if event.y > 0: self.scroll_offset = max(0, self.scroll_offset - 1)
                elif event.y < 0: self.scroll_offset = min(max(0, len(self.options)-self.max_visible), self.scroll_offset+1)
            if event.type == pygame.MOUSEMOTION:
                self.hovered_option = -1
                for i in range(visible_count):
                    if _row_rect(i).collidepoint(smp): self.hovered_option = self.scroll_offset + i
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                chosen = False
                for i in range(visible_count):
                    if _row_rect(i).collidepoint(smp):
                        self.selected_index = self.scroll_offset + i
                        self.text = self.options[self.selected_index]
                        self.is_open = False; chosen = True; break
                if not chosen:
                    self.is_open = False
                    if not self.rect.collidepoint(smp): self.active = False
        else:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.rect.collidepoint(smp): self.active = True; self.is_open = True
                else: self.active = False
        self.color = COLOR_BOX_ACTIVE if self.active else COLOR_BOX
        if event.type == pygame.KEYDOWN and self.active:
            if   event.key == pygame.K_TAB:    self.is_open = False; return "NEXT"
            elif event.key == pygame.K_RETURN:
                if self.is_open: self.is_open = False
                else: return "SUBMIT"
            elif event.key == pygame.K_SPACE:  self.is_open = not self.is_open
            elif event.key == pygame.K_DOWN and self.is_open:
                self.selected_index = min(len(self.options)-1, self.selected_index+1)
                self.text = self.options[self.selected_index]
                if self.selected_index >= self.scroll_offset + self.max_visible:
                    self.scroll_offset = self.selected_index - self.max_visible + 1
            elif event.key == pygame.K_UP and self.is_open:
                self.selected_index = max(0, self.selected_index-1)
                self.text = self.options[self.selected_index]
                if self.selected_index < self.scroll_offset: self.scroll_offset = self.selected_index
        return None

    def draw(self, surface):
        surface.blit(FONT_SMALL.render(self.label, True, COLOR_TEXT), (self.rect.x, self.rect.y - 20))
        pygame.draw.rect(surface, self.color, self.rect)
        pygame.draw.rect(surface, COLOR_ACCENT if self.active else (100,100,100), self.rect, 2)
        surface.blit(FONT_TEXT.render(self.text, True, COLOR_TEXT), (self.rect.x+10, self.rect.y+10))
        surface.blit(FONT_TEXT.render("V" if not self.is_open else "X", True, COLOR_TEXT), (self.rect.right-25, self.rect.y+10))

    def draw_dropdown(self, surface):
        if not self.is_open: return
        visible_count = min(self.max_visible, len(self.options) - self.scroll_offset)
        drop_h  = self.rect.h * visible_count
        opens_up = (self.rect.bottom + drop_h) > INTERNAL_HEIGHT
        for i in range(visible_count):
            actual_idx = self.scroll_offset + i
            row_y = (self.rect.y - drop_h + i*self.rect.h) if opens_up else (self.rect.y + self.rect.h*(i+1))
            r = pygame.Rect(self.rect.x, row_y, self.rect.w, self.rect.h)
            pygame.draw.rect(surface, COLOR_BOX_ACTIVE if actual_idx==self.hovered_option else COLOR_BOX, r)
            pygame.draw.rect(surface, (100,100,100), r, 1)
            surface.blit(FONT_TEXT.render(self.options[actual_idx], True, COLOR_TEXT), (r.x+10, r.y+10))
        if len(self.options) > self.max_visible:
            sb_w = 8
            sb_top = (self.rect.y - drop_h + 2) if opens_up else (self.rect.y + self.rect.h + 2)
            sb = pygame.Rect(self.rect.right - sb_w - 2, sb_top, sb_w, drop_h - 4)
            pygame.draw.rect(surface, (20,20,30), sb)
            max_s = len(self.options) - self.max_visible
            th = max(10, int(sb.h * self.max_visible / len(self.options)))
            pct = self.scroll_offset / max_s if max_s > 0 else 0
            pygame.draw.rect(surface, COLOR_ACCENT, pygame.Rect(sb.x, sb.y + pct*(sb.h-th), sb_w, th))


class Button:
    def __init__(self, x, y, w, h, text):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text

    def draw(self, surface, smp):
        hov = self.rect.collidepoint(smp)
        pygame.draw.rect(surface, COLOR_BOX_ACTIVE if hov else COLOR_BOX, self.rect)
        pygame.draw.rect(surface, COLOR_ACCENT if hov else (100,100,100), self.rect, 1)
        ts = FONT_SMALL.render(self.text, True, COLOR_TEXT)
        surface.blit(ts, ts.get_rect(center=self.rect.center))

    def is_clicked(self, event, smp):
        return event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(smp)


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_user_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f: return json.load(f)
    return None

def save_user_data(data_dict):
    data_dict["status"] = "active"
    with open(DATA_FILE, 'w') as f: json.dump(data_dict, f, indent=2)

def draw_centered(surface, text, font, color, y):
    s = font.render(text, True, color)
    surface.blit(s, s.get_rect(center=(INTERNAL_WIDTH//2, y)))

def set_active(inputs, idx=0):
    for b in inputs: b.active = False; b.color = COLOR_BOX
    inputs[idx].active = True; inputs[idx].color = COLOR_BOX_ACTIVE

def get_smp():
    mx, my = pygame.mouse.get_pos()
    return (int(mx * INTERNAL_WIDTH / current_window_size[0]),
            int(my * INTERNAL_HEIGHT / current_window_size[1]))

def handle_window_event(event, local_fullscreen_ref=None):
    global screen, current_window_size, is_fullscreen
    if local_fullscreen_ref is not None:
        _fs = local_fullscreen_ref[0]
        if event.type == pygame.VIDEORESIZE and not _fs:
            current_window_size = (event.w, event.h)
            screen = pygame.display.set_mode(current_window_size, pygame.RESIZABLE)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
            _fs = not _fs
            screen = pygame.display.set_mode((0,0) if _fs else (INTERNAL_WIDTH,INTERNAL_HEIGHT),
                                              pygame.FULLSCREEN if _fs else pygame.RESIZABLE)
            current_window_size = screen.get_size()
            local_fullscreen_ref[0] = _fs; is_fullscreen = _fs
    else:
        if event.type == pygame.VIDEORESIZE and not is_fullscreen:
            current_window_size = (event.w, event.h)
            screen = pygame.display.set_mode(current_window_size, pygame.RESIZABLE)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
            is_fullscreen = not is_fullscreen
            screen = pygame.display.set_mode((0,0) if is_fullscreen else (INTERNAL_WIDTH,INTERNAL_HEIGHT),
                                              pygame.FULLSCREEN if is_fullscreen else pygame.RESIZABLE)
            current_window_size = screen.get_size()

def _advance_input(inputs, i):
    inputs[i].active = False; inputs[i].color = COLOR_BOX
    nxt = (i+1) % len(inputs)
    inputs[nxt].active = True; inputs[nxt].color = COLOR_BOX_ACTIVE


# ── Video Background ──────────────────────────────────────────────────────────

class VideoBackground:
    OVERLAY_ALPHA = 180
    def __init__(self, path):
        self.available = False; self._frames = []; self._index = 0; self._forward = True
        if not _CV2_AVAILABLE or not os.path.exists(path): return
        try:
            cap = cv2.VideoCapture(path)
            if not cap.isOpened(): return
            while True:
                ret, frame = cap.read()
                if not ret: break
                surf = pygame.surfarray.make_surface(numpy.rot90(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
                self._frames.append(pygame.transform.scale(surf, (INTERNAL_WIDTH, INTERNAL_HEIGHT)))
            cap.release()
            if not self._frames: return
            self.available = True
            self._overlay = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT), pygame.SRCALPHA)
            self._overlay.fill((0,0,0,self.OVERLAY_ALPHA))
            print(f"[VIDEO] Loaded {len(self._frames)} frames.")
        except Exception as e:
            print(f"[VIDEO] Error: {e}")

    def draw(self, surface):
        if not self.available or not self._frames: return
        surface.blit(self._frames[self._index], (0,0))
        surface.blit(self._overlay, (0,0))
        if self._forward:
            self._index += 1
            if self._index >= len(self._frames): self._index = len(self._frames)-2; self._forward = False
        else:
            self._index -= 1
            if self._index < 0: self._index = 1; self._forward = True

_VIDEO_PATH = resource_path(os.path.join("assets","videos","bgv.mp4"))
_video_bg = None
def _get_video_bg():
    global _video_bg
    if _video_bg is None: _video_bg = VideoBackground(_VIDEO_PATH)
    return _video_bg


# ── Screens ───────────────────────────────────────────────────────────────────

def run_boot():
    _run_boot_screen(screen, canvas, clock, current_window_size,
                     color_bg=COLOR_BG, color_text=COLOR_TEXT, color_accent=COLOR_ACCENT,
                     font=FONT_TEXT, is_fullscreen=is_fullscreen)


def run_title():
    items = [("START","[ S ]"),("LOAD","[ L ]"),("SETTINGS","[ T ]"),("CREDITS","[ C ]"),("EXIT","[ ESC ]")]
    key_map = {pygame.K_s:'start', pygame.K_l:'load', pygame.K_t:'settings',
               pygame.K_c:'credits', pygame.K_ESCAPE:'exit'}
    ITEM_H = 52; ITEM_W = 320
    # Menu starts at y=230 — leaves room for the smaller 160px logo above
    start_y  = 230
    center_x = INTERNAL_WIDTH // 2
    scan_off = 0

    while True:
        canvas.fill(COLOR_BG); now = pygame.time.get_ticks(); smp = get_smp()
        scan_off = (scan_off + 1) % 8

        for event in pygame.event.get():
            if event.type == pygame.QUIT: return 'exit'
            handle_window_event(event)
            if event.type == pygame.KEYDOWN and event.key in key_map: return key_map[event.key]
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for idx, (label, _) in enumerate(items):
                    r = pygame.Rect(center_x-ITEM_W//2, start_y+idx*(ITEM_H+12), ITEM_W, ITEM_H)
                    if r.collidepoint(smp): return label.lower()

        vbg = _get_video_bg()
        if vbg.available:
            vbg.draw(canvas)
            ss = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT), pygame.SRCALPHA)
            for y in range(scan_off, INTERNAL_HEIGHT, 6): pygame.draw.line(ss,(0,0,0,22),(0,y),(INTERNAL_WIDTH,y))
            canvas.blit(ss, (0,0))
        else:
            for gx in range(0,INTERNAL_WIDTH,40): pygame.draw.line(canvas,(14,18,14),(gx,0),(gx,INTERNAL_HEIGHT))
            for gy in range(0,INTERNAL_HEIGHT,40): pygame.draw.line(canvas,(14,18,14),(0,gy),(INTERNAL_WIDTH,gy))

        # Logo: 160px wide, centered at y=75
        if login_logo:
            canvas.blit(login_logo, login_logo.get_rect(center=(center_x, 75)))
        else:
            draw_centered(canvas, LAB_NAME, FONT_TITLE, COLOR_ACCENT, 60)

        # Title text sits just below the smaller logo
        draw_centered(canvas, "PING: CONNECTION LINKED",       FONT_HEAD,  COLOR_ACCENT, 168)
        draw_centered(canvas, "A.L.I.C.E. SECURE TERMINAL v0.1", FONT_SMALL, COLOR_MUTED,  190)
        pygame.draw.line(canvas, COLOR_LINE, (center_x-200,210),(center_x+200,210))

        for idx, (label, hint) in enumerate(items):
            iy   = start_y + idx*(ITEM_H+12)
            rect = pygame.Rect(center_x-ITEM_W//2, iy, ITEM_W, ITEM_H)
            hov  = rect.collidepoint(smp)
            pygame.draw.rect(canvas, (0,55,0) if hov else (18,22,18), rect, border_radius=4)
            pygame.draw.rect(canvas, COLOR_ACCENT if hov else COLOR_LINE, rect, 1, border_radius=4)
            if hov: pygame.draw.rect(canvas, COLOR_ACCENT, pygame.Rect(rect.x,rect.y,4,rect.h), border_radius=2)
            canvas.blit(FONT_HEAD.render(label,True,COLOR_ACCENT if hov else COLOR_TEXT),(rect.x+22,rect.y+8))
            hs = FONT_TINY.render(hint,True,COLOR_MUTED)
            canvas.blit(hs,(rect.right-hs.get_width()-14, rect.y+rect.h-hs.get_height()-8))

        draw_centered(canvas,"F11: TOGGLE FULLSCREEN",FONT_TINY,COLOR_MUTED,INTERNAL_HEIGHT-18)
        cur = "_" if (now//500)%2==0 else " "
        canvas.blit(FONT_TINY.render(f">{cur}",True,COLOR_DIM_ACCENT),(INTERNAL_WIDTH-28,INTERNAL_HEIGHT-18))
        screen.blit(pygame.transform.scale(canvas, current_window_size),(0,0))
        pygame.display.flip(); clock.tick(30)


def run_login(user_data):
    in_user  = InputBox(400,310,200,35,"USERNAME")
    in_pass  = InputBox(400,380,200,35,"PASSWORD",is_password=True)
    inputs   = [in_user, in_pass]
    btn_reg  = Button(350,530,300,30,"[ INITIATE NEW USER ONBOARDING ]")
    btn_back = Button(20,10,80,28,"◄ BACK")
    status_msg=""; status_color=COLOR_TEXT
    set_active(inputs,0)

    while True:
        canvas.fill(COLOR_BG); now=pygame.time.get_ticks(); smp=get_smp()
        for event in pygame.event.get():
            if event.type==pygame.QUIT: pygame.quit(); sys.exit()
            handle_window_event(event)
            if event.type==pygame.KEYDOWN and event.key==pygame.K_ESCAPE: return 'back'
            if btn_back.is_clicked(event,smp): return 'back'
            if btn_reg.is_clicked(event,smp):
                r=run_register()
                if isinstance(r,dict): return r
            for i,box in enumerate(inputs):
                res=box.handle_event(event,smp)
                if res=="NEXT": _advance_input(inputs,i); break
                elif res=="SUBMIT":
                    if user_data is None: status_msg="ERR: NO PROFILE FOUND."; status_color=COLOR_ERROR
                    elif in_user.text==user_data["username"] and in_pass.text==user_data["password"]: return user_data
                    else: status_msg="ERR: INVALID CREDENTIALS"; status_color=COLOR_ERROR

        for gx in range(0,INTERNAL_WIDTH,40): pygame.draw.line(canvas,(14,18,14),(gx,0),(gx,INTERNAL_HEIGHT))
        for gy in range(0,INTERNAL_HEIGHT,40): pygame.draw.line(canvas,(14,18,14),(0,gy),(INTERNAL_WIDTH,gy))
        if login_logo: canvas.blit(login_logo, login_logo.get_rect(center=(INTERNAL_WIDTH//2,100)))
        draw_centered(canvas,LAB_NAME,FONT_TITLE,COLOR_ACCENT,185)
        draw_centered(canvas,"SYSTEM MODE: AUTHORIZED LOGIN",FONT_SMALL,COLOR_MUTED,218)
        for box in inputs: box.draw(canvas)
        draw_centered(canvas,"[ENTER: SUBMIT]  [TAB: NEXT]  [ESC: BACK]",FONT_SMALL,(100,100,100),450)
        draw_centered(canvas,status_msg,FONT_TEXT,status_color,488)
        btn_reg.draw(canvas,smp); btn_back.draw(canvas,smp)
        screen.blit(pygame.transform.scale(canvas,current_window_size),(0,0))
        pygame.display.flip(); clock.tick(30)


def run_register(prefill=None):
    p=prefill or {}; is_edit=prefill is not None
    heading="EDIT PERSONNEL FILE" if is_edit else "A.L.I.C.E. PERSONNEL ONBOARDING"
    sub="MODIFY YOUR DETAILS BELOW" if is_edit else "PLEASE COMPLETE ALL FIELDS FOR CLEARANCE"
    in_name=InputBox(250,200,200,35,"FULL NAME",p.get('name',''))
    in_user=InputBox(250,270,200,35,"USERNAME",p.get('username',''))
    in_pass=InputBox(250,340,200,35,"PASSWORD",p.get('password',''),is_password=True)
    in_sex=Dropdown(550,200,200,35,"SEX",["MALE","FEMALE"])
    in_age=InputBox(550,270,200,35,"AGE",str(p.get('age','')))
    in_role=InputBox(550,340,200,35,"ASSIGNED ROLE",p.get('role',''))
    in_bio=InputBox(250,410,500,35,"SHORT BIO / ASSIGNMENT DETAILS",p.get('bio',''))
    if is_edit and p.get('sex'):
        sv=p['sex'].upper()
        if sv in in_sex.options: in_sex.selected_index=in_sex.options.index(sv); in_sex.text=sv
    inputs=[in_name,in_sex,in_user,in_age,in_pass,in_role,in_bio]
    btn_cancel=Button(400,555,200,30,"[ CANCEL ]"); btn_submit=Button(610,555,200,30,"[ CONFIRM ]")
    btn_back=Button(20,10,80,28,"◄ BACK")
    status_msg=""; status_color=COLOR_TEXT
    set_active(inputs,0)

    def _build():
        d=dict(p); d.update({"name":in_name.text.strip(),"username":in_user.text.strip(),
            "password":in_pass.text.strip(),"sex":in_sex.text,"age":in_age.text.strip(),
            "role":in_role.text.strip(),"bio":in_bio.text.strip()}); return d

    while True:
        canvas.fill(COLOR_BG); smp=get_smp()
        for event in pygame.event.get():
            if event.type==pygame.QUIT: pygame.quit(); sys.exit()
            handle_window_event(event)
            if event.type==pygame.KEYDOWN and event.key==pygame.K_ESCAPE: return 'back'
            if btn_back.is_clicked(event,smp) or btn_cancel.is_clicked(event,smp): return 'back'
            if btn_submit.is_clicked(event,smp):
                if not in_user.text.strip() or not in_pass.text.strip():
                    status_msg="ERR: USERNAME AND PASSWORD REQUIRED"; status_color=COLOR_ERROR
                else: d=_build(); save_user_data(d); return d
            for i,box in enumerate(inputs):
                res=box.handle_event(event,smp)
                if res=="NEXT": _advance_input(inputs,i); break
                elif res=="SUBMIT":
                    if not in_user.text.strip() or not in_pass.text.strip():
                        status_msg="ERR: USERNAME AND PASSWORD REQUIRED"; status_color=COLOR_ERROR
                    else: d=_build(); save_user_data(d); return d

        for gx in range(0,INTERNAL_WIDTH,40): pygame.draw.line(canvas,(14,18,14),(gx,0),(gx,INTERNAL_HEIGHT))
        for gy in range(0,INTERNAL_HEIGHT,40): pygame.draw.line(canvas,(14,18,14),(0,gy),(INTERNAL_WIDTH,gy))
        draw_centered(canvas,heading,FONT_TITLE,COLOR_ACCENT,55)
        draw_centered(canvas,sub,FONT_SMALL,COLOR_MUTED,95)
        for box in inputs: box.draw(canvas)
        for box in inputs:
            if hasattr(box,'draw_dropdown'): box.draw_dropdown(canvas)
        draw_centered(canvas,"[TAB: NEXT FIELD]  [SPACE: OPEN DROPDOWN]  [ENTER: SUBMIT]",FONT_SMALL,(100,100,100),490)
        draw_centered(canvas,status_msg,FONT_TEXT,status_color,518)
        btn_cancel.draw(canvas,smp); btn_submit.draw(canvas,smp); btn_back.draw(canvas,smp)
        screen.blit(pygame.transform.scale(canvas,current_window_size),(0,0))
        pygame.display.flip(); clock.tick(30)


def run_settings(user_data, is_fullscreen=False, music_player=None):
    fs_ref=[is_fullscreen]
    BTN_W=340; BTN_H=50; center_x=INTERNAL_WIDTH//2
    btn_edit=pygame.Rect(80,260,BTN_W,BTN_H); btn_back_r=pygame.Rect(20,10,80,28)
    if user_data is None: user_data={}
    apply_theme(user_data)
    current_color=user_data.get("theme_color","GREEN"); current_font=user_data.get("theme_font","Consolas")
    color_options=["GREEN","AMBER","CYAN","RED","BLUE","MAGENTA","WHITE"]
    font_options=["Consolas","Courier New","Arial","Verdana","Impact","Georgia"]
    mp=music_player
    track_names=[os.path.splitext(os.path.basename(p))[0] for p in (mp.tracks if mp else [])]
    track_scroll=0; vol_dragging=False
    drop_color=Dropdown(80,350,200,35,"TERMINAL COLOR",color_options)
    drop_color.selected_index=color_options.index(current_color) if current_color in color_options else 0
    drop_color.text=current_color
    drop_font=Dropdown(80,420,200,35,"SYSTEM FONT",font_options)
    drop_font.selected_index=font_options.index(current_font) if current_font in font_options else 0
    drop_font.text=current_font
    dropdowns=[drop_font,drop_color]
    preview_fonts={}
    def get_pf(n):
        if n not in preview_fonts: preview_fonts[n]=pygame.font.SysFont(n,18)
        return preview_fonts[n]
    pcolor_map={"GREEN":(0,255,0),"AMBER":(255,176,0),"CYAN":(0,255,255),"RED":(255,50,50),
                "BLUE":(100,150,255),"MAGENTA":(255,0,255),"WHITE":(220,220,220)}

    while True:
        canvas.fill(COLOR_BG); smp=get_smp(); now=pygame.time.get_ticks()
        for event in pygame.event.get():
            if event.type==pygame.QUIT: pygame.quit(); sys.exit()
            handle_window_event(event,fs_ref)
            if event.type==pygame.KEYDOWN and event.key==pygame.K_ESCAPE: return user_data,fs_ref[0]
            click_handled=False
            if event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
                for drop in dropdowns:
                    if drop.is_open: drop.handle_event(event,smp); click_handled=True; break
            if not click_handled:
                if event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
                    if btn_back_r.collidepoint(smp): return user_data,fs_ref[0]
                    if btn_edit.collidepoint(smp):
                        r=run_register(prefill=user_data)
                        if isinstance(r,dict): user_data=r; apply_theme(user_data)
                for drop in dropdowns:
                    wo=drop.is_open; drop.handle_event(event,smp)
                    if not wo and drop.is_open:
                        for o in dropdowns:
                            if o!=drop: o.is_open=False
                        break
            if drop_color.text!=current_color:
                current_color=drop_color.text; user_data["theme_color"]=current_color
                save_user_data(user_data); apply_theme(user_data)
            if drop_font.text!=current_font:
                current_font=drop_font.text; user_data["theme_font"]=current_font
                save_user_data(user_data); apply_theme(user_data)
            if mp and mp.tracks and not click_handled:
                ML_X,ML_Y=80,465; TL_X,TL_Y=460,465; TL_W=450; SB_X=TL_X+TL_W+6
                vbar=pygame.Rect(ML_X,ML_Y+108,258,14)
                if event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
                    for mi,ml in enumerate(MODES):
                        mr=pygame.Rect(ML_X+mi*86,ML_Y+16,78,24)
                        if mr.collidepoint(smp): mp.set_mode(ml); mp.save(user_data); save_user_data(user_data)
                    if pygame.Rect(ML_X,ML_Y+46,36,24).collidepoint(smp): mp.prev_track(); mp.save(user_data); save_user_data(user_data)
                    if pygame.Rect(ML_X+42,ML_Y+46,36,24).collidepoint(smp): mp.next_track(); mp.save(user_data); save_user_data(user_data)
                    if pygame.Rect(ML_X+84,ML_Y+46,84,24).collidepoint(smp): mp.toggle_pause()
                    if vbar.collidepoint(smp): vol_dragging=True; mp.set_volume((smp[0]-vbar.x)/vbar.w)
                    for ti in range(min(4,len(track_names)-track_scroll)):
                        tr=pygame.Rect(TL_X,TL_Y+16+ti*24,TL_W,22)
                        if tr.collidepoint(smp): mp.set_track(track_scroll+ti); mp.save(user_data); save_user_data(user_data)
                    if pygame.Rect(SB_X,TL_Y+16,20,20).collidepoint(smp): track_scroll=max(0,track_scroll-1)
                    if pygame.Rect(SB_X,TL_Y+16+72,20,20).collidepoint(smp): track_scroll=min(max(0,len(track_names)-4),track_scroll+1)
                if event.type==pygame.MOUSEBUTTONUP and event.button==1:
                    if vol_dragging: mp.save(user_data); save_user_data(user_data)
                    vol_dragging=False
                if event.type==pygame.MOUSEMOTION and vol_dragging:
                    mp.set_volume(max(0.0,min(1.0,(smp[0]-vbar.x)/vbar.w)))
                if event.type==pygame.MOUSEWHEEL:
                    track_scroll=max(0,min(max(0,len(track_names)-4),track_scroll-event.y))

        for gx in range(0,INTERNAL_WIDTH,40): pygame.draw.line(canvas,(14,18,14),(gx,0),(gx,INTERNAL_HEIGHT))
        for gy in range(0,INTERNAL_HEIGHT,40): pygame.draw.line(canvas,(14,18,14),(0,gy),(INTERNAL_WIDTH,gy))
        bh=btn_back_r.collidepoint(smp)
        pygame.draw.rect(canvas,(0,55,0) if bh else COLOR_BOX,btn_back_r,border_radius=4)
        pygame.draw.rect(canvas,COLOR_ACCENT if bh else COLOR_LINE,btn_back_r,1,border_radius=4)
        canvas.blit(FONT_SMALL.render("◄  BACK",True,COLOR_ACCENT),(btn_back_r.x+8,btn_back_r.y+6))
        draw_centered(canvas,"// SETTINGS",FONT_HEAD,COLOR_ACCENT,80)
        draw_centered(canvas,"A.L.I.C.E. TERMINAL CONFIGURATION",FONT_SMALL,COLOR_MUTED,110)
        pygame.draw.line(canvas,COLOR_LINE,(center_x-200,135),(center_x+200,135))
        if user_data.get('username'):
            card=pygame.Rect(80,150,BTN_W,90)
            pygame.draw.rect(canvas,(18,22,18),card,border_radius=5)
            pygame.draw.rect(canvas,COLOR_LINE,card,1,border_radius=5)
            canvas.blit(FONT_SMALL.render("CURRENT PROFILE",True,COLOR_MUTED),(card.x+12,card.y+8))
            canvas.blit(FONT_TEXT.render(f"{user_data.get('username','?')}  |  {user_data.get('name','?')}",True,COLOR_ACCENT),(card.x+12,card.y+28))
            canvas.blit(FONT_SMALL.render(f"Role: {user_data.get('role','?')}   Age: {user_data.get('age','?')}",True,COLOR_TEXT),(card.x+12,card.y+58))
        eh=btn_edit.collidepoint(smp)
        pygame.draw.rect(canvas,(0,55,0) if eh else COLOR_BOX,btn_edit,border_radius=4)
        pygame.draw.rect(canvas,COLOR_ACCENT if eh else COLOR_LINE,btn_edit,1,border_radius=4)
        if eh: pygame.draw.rect(canvas,COLOR_ACCENT,pygame.Rect(btn_edit.x,btn_edit.y,4,btn_edit.h),border_radius=2)
        lbl=FONT_HEAD.render("EDIT PROFILE",True,COLOR_ACCENT if eh else COLOR_TEXT)
        canvas.blit(lbl,lbl.get_rect(center=btn_edit.center))
        pr=pygame.Rect(460,150,460,305)
        pygame.draw.rect(canvas,(10,10,15),pr,border_radius=8)
        pygame.draw.rect(canvas,COLOR_LINE,pr,2,border_radius=8)
        pygame.draw.rect(canvas,COLOR_BOX_ACTIVE,(pr.x,pr.y,pr.w,30),border_radius=8)
        canvas.blit(FONT_SMALL.render("LIVE THEME PREVIEW",True,COLOR_TEXT),(pr.x+15,pr.y+8))
        pf=get_pf(current_font); pa=pcolor_map.get(current_color,(0,255,0))
        py2=pr.y+45
        for line in [f"INITIALIZING {current_font.upper()}...","CONNECTION SECURE."," ",
                     "ABCDEFGHIJKLMNOPQRSTUVWXYZ","abcdefghijklmnopqrstuvwxyz",
                     "0123456789 !@#$%^&*()"," ","THE QUICK BROWN FOX JUMPS","OVER THE LAZY DOG."]:
            canvas.blit(pf.render(line,True,pa),(pr.x+15,py2)); py2+=24
        cur="_" if (now//500)%2==0 else " "
        canvas.blit(pf.render(f">{cur}",True,pa),(pr.x+15,py2))
        for drop in dropdowns: drop.draw(canvas)
        if mp:
            ML_X,ML_Y=80,465; TL_X,TL_Y=460,465; TL_W=450; SB_X=TL_X+TL_W+6
            canvas.blit(FONT_SMALL.render("MUSIC PLAYER",True,COLOR_MUTED),(ML_X,ML_Y))
            pygame.draw.line(canvas,COLOR_LINE,(ML_X,ML_Y+13),(ML_X+270,ML_Y+13),1)
            canvas.blit(FONT_SMALL.render("TRACKS",True,COLOR_MUTED),(TL_X,TL_Y))
            pygame.draw.line(canvas,COLOR_LINE,(TL_X,TL_Y+13),(SB_X+20,TL_Y+13),1)
            if mp.tracks:
                for mi,ml in enumerate(MODES):
                    mr=pygame.Rect(ML_X+mi*86,ML_Y+16,78,24); act=(ml==mp.mode); mh=mr.collidepoint(smp)
                    pygame.draw.rect(canvas,COLOR_ACCENT if act else (COLOR_BOX_ACTIVE if mh else COLOR_BOX),mr,border_radius=4)
                    pygame.draw.rect(canvas,COLOR_ACCENT if act else COLOR_LINE,mr,1,border_radius=4)
                    ms=FONT_SMALL.render(ml,True,COLOR_BG if act else (COLOR_ACCENT if mh else COLOR_TEXT))
                    canvas.blit(ms,ms.get_rect(center=mr.center))
                for br,bl in [(pygame.Rect(ML_X,ML_Y+46,36,24),"|<"),(pygame.Rect(ML_X+42,ML_Y+46,36,24),">|"),
                              (pygame.Rect(ML_X+84,ML_Y+46,84,24),"|| PAUSE" if not mp.paused else "> PLAY")]:
                    bh2=br.collidepoint(smp)
                    pygame.draw.rect(canvas,COLOR_BOX_ACTIVE if bh2 else COLOR_BOX,br,border_radius=4)
                    pygame.draw.rect(canvas,COLOR_ACCENT if bh2 else COLOR_LINE,br,1,border_radius=4)
                    bs=FONT_SMALL.render(bl,True,COLOR_ACCENT if bh2 else COLOR_TEXT)
                    canvas.blit(bs,bs.get_rect(center=br.center))
                nn=mp.track_name[:32]+("..." if len(mp.track_name)>32 else "")
                canvas.blit(FONT_SMALL.render(f"NOW: {nn}",True,COLOR_ACCENT),(ML_X,ML_Y+76))
                canvas.blit(FONT_SMALL.render(f"VOL  {int(mp.volume*100)}%",True,COLOR_MUTED),(ML_X,ML_Y+93))
                vbar=pygame.Rect(ML_X,ML_Y+108,258,14)
                pygame.draw.rect(canvas,COLOR_BOX,vbar,border_radius=4)
                pygame.draw.rect(canvas,COLOR_ACCENT,pygame.Rect(vbar.x,vbar.y,int(vbar.w*mp.volume),vbar.h),border_radius=4)
                pygame.draw.rect(canvas,COLOR_LINE,vbar,1,border_radius=4)
                tx=max(vbar.x,vbar.x+int(vbar.w*mp.volume)-4)
                pygame.draw.rect(canvas,COLOR_TEXT,pygame.Rect(tx,vbar.y,6,vbar.h),border_radius=2)
                ur=pygame.Rect(SB_X,TL_Y+16,20,20)
                pygame.draw.rect(canvas,COLOR_BOX_ACTIVE if ur.collidepoint(smp) else COLOR_BOX,ur,border_radius=3)
                canvas.blit(FONT_SMALL.render("^",True,COLOR_ACCENT),(ur.x+4,ur.y+2))
                for ti in range(min(4,len(track_names)-track_scroll)):
                    idx2=track_scroll+ti; tr=pygame.Rect(TL_X,TL_Y+16+ti*24,TL_W,22)
                    ic=(idx2==mp.track_index); th2=tr.collidepoint(smp) and not ic
                    pygame.draw.rect(canvas,COLOR_ACCENT if ic else (COLOR_BOX_ACTIVE if th2 else COLOR_BOX),tr,border_radius=3)
                    pygame.draw.rect(canvas,COLOR_ACCENT if ic else COLOR_LINE,tr,1,border_radius=3)
                    dn2=track_names[idx2][:52]+("..." if len(track_names[idx2])>52 else "")
                    canvas.blit(FONT_SMALL.render(dn2,True,COLOR_BG if ic else COLOR_TEXT),(tr.x+6,tr.y+4))
                dr2=pygame.Rect(SB_X,TL_Y+16+72,20,20)
                pygame.draw.rect(canvas,COLOR_BOX_ACTIVE if dr2.collidepoint(smp) else COLOR_BOX,dr2,border_radius=3)
                canvas.blit(FONT_SMALL.render("v",True,COLOR_ACCENT),(dr2.x+4,dr2.y+2))
            else:
                canvas.blit(FONT_SMALL.render("NO .MP3 FILES FOUND IN assets/audio/",True,COLOR_ERROR),(ML_X,ML_Y+20))
        draw_centered(canvas,"[ESC: BACK TO TITLE]",FONT_TINY,COLOR_MUTED,INTERNAL_HEIGHT-18)
        canvas.blit(FONT_TINY.render(f">{cur}",True,COLOR_DIM_ACCENT),(INTERNAL_WIDTH-28,INTERNAL_HEIGHT-18))
        for drop in dropdowns: drop.draw_dropdown(canvas)
        screen.blit(pygame.transform.scale(canvas,current_window_size),(0,0))
        pygame.display.flip(); clock.tick(30)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    global screen, current_window_size, is_fullscreen
    is_fullscreen = False
    run_boot()
    user_data = load_user_data()
    apply_theme(user_data)
    music_player = MusicPlayer(user_data)

    while True:
        music_player.update()
        choice = run_title()

        if choice == 'exit':
            break

        elif choice == 'start':
            if user_data is None:
                result = run_register()
                if isinstance(result, dict):
                    user_data = result
                    chat_interface.run_chat(screen, canvas, clock, current_window_size,
                                            user_data, is_fullscreen, music_player=music_player)
                    user_data = load_user_data() or user_data; apply_theme(user_data)
            else:
                result = run_login(user_data)
                if isinstance(result, dict):
                    user_data = result
                    chat_interface.run_chat(screen, canvas, clock, current_window_size,
                                            user_data, is_fullscreen, music_player=music_player)
                    user_data = load_user_data() or user_data; apply_theme(user_data)

        elif choice == 'load':
            if user_data is None:
                result = run_register()
                if isinstance(result, dict): user_data = result
                else: continue

            from save_manager import load_slot, all_slot_metas
            from load_page import run_load_page as _rlp

            class _TempCM:
                def __init__(self):
                    self.displayed_messages        = []
                    self.ignored_ids               = set()
                    self.script_index              = 0
                    self.current_chapter           = 0
                    self.unlocked_private_channels = set()
                    self._all_chapters_done        = False
                    self.is_waiting                = False
                    self.waiting_for_choice        = False
                    self.pending_choices           = []
                    self.last_advance_time         = 0
                    self.personnel_db              = {}
                    # Only load chapter 0 — save_manager will swap to correct chapter
                    _cfs = chat_interface.discover_chapters()
                    self.chapter_files = _cfs
                    self.full_script   = (chat_interface.load_chapter(_cfs[0], 0)
                                          if _cfs else [])
                    self._id_index = {}
                    for i, row in enumerate(self.full_script):
                        rid = str(row.get('ID', '')).strip()
                        if rid.endswith('.0'): rid = rid[:-2]
                        if rid: self._id_index[rid] = i

                def _substitute(self, text):
                    return (text
                            .replace('{USERNAME}', f'@{user_data.get("username","")}')
                            .replace('{NAME}',      user_data.get("name", "")))

            tmp_cm    = _TempCM()
            lp_result = _rlp(screen, canvas, clock, current_window_size, tmp_cm, is_fullscreen)
            if isinstance(lp_result, tuple) and lp_result[0] == 'loaded':
                chat_interface.run_chat(screen, canvas, clock, current_window_size,
                                        user_data, is_fullscreen,
                                        preloaded_cm=tmp_cm, music_player=music_player)
                user_data = load_user_data() or user_data; apply_theme(user_data)

        elif choice == 'settings':
            result = run_settings(user_data, is_fullscreen=is_fullscreen, music_player=music_player)
            if isinstance(result, tuple): user_data, is_fullscreen = result
            else: user_data = result
            screen = pygame.display.set_mode((0,0) if is_fullscreen else (INTERNAL_WIDTH,INTERNAL_HEIGHT),
                                              pygame.FULLSCREEN if is_fullscreen else pygame.RESIZABLE)
            current_window_size = screen.get_size()

        elif choice == 'credits':
            run_credits(screen, canvas, clock, current_window_size, is_fullscreen, music_player=music_player)

    pygame.quit(); sys.exit()


if __name__ == "__main__":
    main()