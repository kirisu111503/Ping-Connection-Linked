"""
boot_screen.py
───────────────────────────────────────────────────────────────────────────────
Startup / loading intro sequence for "Ping: Connection Linked".

Simulates a realistic network security monitor boot:
  - Network interface enumeration
  - Packet capture initialization (libpcap)
  - Internal SYN port sweep
  - IDS/IPS rule load (Suricata-style)
  - Live traffic classification feed
  - Encrypted tunnel + session establishment

To customise, edit the PHASES list and constants at the top.
No other file needs to change.
"""

import pygame
import random
import time

# ── Timing ────────────────────────────────────────────────────────────────────
DELAY_EXIT    = 1400   # ms pause after final line before handing off to title
LINE_INTERVAL = 55     # ms between log lines (lower = faster scroll)

# ── Data pools (feel free to extend these) ────────────────────────────────────
_IFACES   = ["eth0", "eth1", "wlan0", "tun0", "ens3", "bond0", "br0"]
_PROTOS   = ["TCP", "UDP", "ICMP", "TLS1.3", "DNS", "ARP", "BGP", "OSPF"]
_FLAGS    = ["SYN", "ACK", "SYN-ACK", "FIN", "RST", "PSH", "URG"]
_THREATS  = ["BENIGN", "BENIGN", "BENIGN", "SUSPICIOUS", "ANOMALY", "BLOCKED"]
_SERVICES = {
    22: "SSH",    23: "TELNET",  25: "SMTP",   53: "DNS",
    80: "HTTP",  110: "POP3",   143: "IMAP",  443: "HTTPS",
    445: "SMB", 3306: "MYSQL", 3389: "RDP",  8080: "HTTP-ALT",
}
_THREAT_COLOR = {
    "BENIGN":     None,               # use default text color
    "SUSPICIOUS": (255, 176,   0),
    "ANOMALY":    (255, 120,   0),
    "BLOCKED":    (220,  50,  50),
}


# ── Phase generators ──────────────────────────────────────────────────────────
# Each is a plain generator function that yields one log string per step.
# Add, remove, or reorder entries in PHASES at the bottom of this section.

def _phase_iface():
    yield "[ SYS  ] Linux kernel 6.1.0-alice  SMP  x86_64"
    yield "[ SYS  ] Loading kernel network modules..."
    for mod in ["nf_conntrack", "xt_NFQUEUE", "af_packet", "8021q", "bonding"]:
        yield f"[ SYS  ]   insmod {mod}.ko  [OK]"
    yield f"[ SYS  ] Detected {random.randint(3, 6)} network interface(s)"
    ifaces = random.sample(_IFACES, k=random.randint(3, 5))
    for iface in ifaces:
        mac  = ":".join(f"{random.randint(0,255):02X}" for _ in range(6))
        mtu  = random.choice([1500, 9000, 65536])
        spd  = random.choice(["1000Mb/s", "10Gb/s", "25Gb/s"])
        yield f"[ IFACE] {iface:<8}  MAC {mac}  MTU {mtu}  {spd}  state UP"
    yield f"[ IFACE] Binding raw capture socket on {ifaces[0]}  fd=7"
    yield f"[ IFACE] Promiscuous mode ENABLED on {ifaces[0]}"
    yield f"[ IFACE] VLAN tagging 802.1Q ENABLED  trunk port"
    yield f"[ IFACE] NIC offload: GRO=on  LRO=off  TSO=on  checksum=off"
    yield  "[ SYS  ] Interface enumeration complete"


def _phase_capture():
    buf = random.choice([128, 256, 512, 1024])
    yield f"[ CAP  ] Initializing libpcap  version 1.10.4"
    yield f"[ CAP  ] Allocating ring buffer  [{buf} MB]  AF_PACKET mmap"
    yield  "[ CAP  ] BPF filter compiled: 'not port 22 and not arp'"
    yield  "[ CAP  ] BPF JIT enabled  —  kernel-side filtering active"
    yield f"[ CAP  ] snaplen=65535  promisc=1  timeout=0ms"
    yield  "[ CAP  ] Capture engine ready"
    yield  "[ CAP  ] Starting packet dissection threads..."
    for t in range(random.randint(4, 8)):
        cpu = random.randint(0, 15)
        yield f"[ CAP  ]   worker-{t:02d}  CPU#{cpu:02d}  pid={random.randint(1200,9999)}  RUNNING"
    yield  "[ CAP  ] Flow hash table allocated  65536 buckets"
    yield  "[ CAP  ] Defrag engine online  max-frags=8192"
    yield  "[ CAP  ] Stream engine online  reassembly-buf=32MB"


def _phase_portscan():
    subnet  = f"10.{random.randint(0,9)}.{random.randint(0,9)}.0/24"
    hosts   = [f"10.{random.randint(1,9)}.{random.randint(1,9)}.{random.randint(1,254)}"
               for _ in range(random.randint(2, 4))]
    yield f"[ SCAN ] Starting internal network audit"
    yield f"[ SCAN ] Target range: {subnet}"
    yield  "[ SCAN ] Phase 1: ICMP ping sweep (type 8)..."
    alive = random.randint(8, 22)
    yield f"[ SCAN ] {alive} host(s) responding  ({256-alive} filtered/down)"
    yield  "[ SCAN ] Phase 2: TCP SYN scan  top-1000 ports  rate=500pps"
    for host in hosts:
        ports = sorted(random.sample(list(_SERVICES.keys()), k=random.randint(3, 7)))
        yield f"[ SCAN ] Scanning {host}..."
        for port in ports:
            svc    = _SERVICES.get(port, "unknown")
            banner = random.choice(["OpenSSH_8.9p1", "nginx/1.24.0",
                                    "Apache/2.4.57", "Microsoft-IIS/10.0",
                                    "vsftpd 3.0.5", "Postfix smtpd", ""])
            yield f"[ SCAN ]   {host}:{port:<5}  OPEN   {svc:<12} {banner}".rstrip()
        yield f"[ SCAN ]   {host}  done  —  {len(ports)} open  {1000-len(ports)} filtered"
    yield  "[ SCAN ] Phase 3: UDP scan  common ports..."
    for p in [53, 123, 161, 500]:
        state = random.choice(["open", "open|filtered"])
        yield f"[ SCAN ]   {hosts[0]}:{p:<5}  {state:<16} {_SERVICES.get(p,'unknown')}"
    yield f"[ SCAN ] Audit complete  hosts={len(hosts)}  elapsed={random.randint(12,60)}s"


def _phase_ids():
    total = random.randint(28000, 36000)
    yield  "[ IDS  ] Starting Suricata 7.0.3"
    yield f"[ IDS  ] Loading rule set  ({total:,} rules total)"
    cats  = [("ET OPEN",  random.randint(4000, 7000)),
             ("ET PRO",   random.randint(6000, 9000)),
             ("GPL",      random.randint(800,  2000)),
             ("CUSTOM",   random.randint(100,   500)),
             ("EMERGING", random.randint(2000, 5000))]
    for cat, count in cats:
        skipped = random.randint(0, 12)
        yield f"[ IDS  ]   {cat:<12}  {count:>6,} rules loaded  {skipped} skipped"
    yield  "[ IDS  ] Rule compilation complete"
    yield  "[ IDS  ] Flow engine initialized  timeout=120s  emergency-mode=off"
    yield f"[ IDS  ] Threading model: {random.randint(4,12)} workers  autofp"
    yield  "[ IDS  ] Output: EVE JSON → /var/log/suricata/eve.json"
    yield  "[ IDS  ] IPS mode ACTIVE  —  NFQUEUE  drop-threshold=0.85"
    yield  "[ IDS  ] Protocol parsers: HTTP  TLS  DNS  SMB  FTP  SSH  SMTP"
    yield f"[ IDS  ] File extraction enabled  max-size={random.choice([10,25,50])}MB"


def _phase_vuln():
    """Vulnerability feed and CVE watch."""
    yield  "[ VULN ] Loading NVD CVE feed  (last 90 days)"
    yield f"[ VULN ] {random.randint(800,1400)} CVEs indexed  {random.randint(40,120)} critical"
    cves = [
        ("CVE-2024-3094", "9.8", "xz-utils backdoor  CRITICAL  patch URGENT"),
        ("CVE-2024-1086", "7.8", "Linux netfilter UAF  kernel<6.3  mitigated"),
        ("CVE-2023-44487", "7.5", "HTTP/2 Rapid Reset  DoS  WAF rule active"),
        ("CVE-2024-21626", "8.6", "runc container escape  patched"),
        ("CVE-2023-4911",  "7.8", "glibc looney tunables  patched"),
    ]
    for cve, score, desc in cves:
        col_tag = "CRITICAL" if float(score) >= 9.0 else ("HIGH" if float(score) >= 7.0 else "MED")
        yield f"[ VULN ]   {cve}  CVSS={score}  [{col_tag}]  {desc}"
    yield  "[ VULN ] Threat intel feeds synchronized"
    for feed in ["Abuse.ch URLhaus", "Emerging Threats IPs", "AlienVault OTX", "Shodan Monitor"]:
        yield f"[ VULN ]   {feed:<28}  [SYNCED]  {random.randint(500,8000)} IOCs"


def _phase_traffic():
    yield "[ FLOW ] Starting flow classifier  model=RandomForest-v3"
    yield "[ FLOW ] Baseline model loaded  (7-day rolling avg)"
    yield f"[ FLOW ] Feature set: {random.randint(70,90)} features  scaler=MinMax"
    yield  "[ FLOW ] Sampling live traffic..."
    for _ in range(random.randint(16, 24)):
        src   = f"{random.randint(1,254)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
        dst   = f"10.0.{random.randint(0,9)}.{random.randint(1,254)}"
        sp    = random.randint(1024, 65535)
        dp    = random.choice(list(_SERVICES.keys()))
        svc   = _SERVICES.get(dp, "?")
        proto = random.choice(_PROTOS)
        flag  = random.choice(_FLAGS)
        size  = random.randint(40, 1480)
        t     = random.choice(_THREATS)
        conf  = random.randint(70, 99)
        yield f"[ FLOW ] {src}:{sp} → {dst}:{dp}/{svc}  {proto} {flag}  {size}B  [{t}] {conf}%"
    blocked = sum(1 for _ in range(3) if random.random() > 0.6)
    yield f"[ FLOW ] Classification summary  blocked={blocked}  alerted={random.randint(1,5)}  clean={random.randint(18,22)}"


def _phase_tunnel():
    peer = f"203.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
    gw   = f"10.0.0.{random.randint(1,10)}"
    yield f"[ TUN  ] Initiating WireGuard handshake → {peer}:51820"
    yield  "[ TUN  ] Cipher suite  AES-256-GCM / ECDHE-RSA-SHA384"
    yield  "[ TUN  ] OCSP stapling verified  cert chain OK"
    yield  "[ TUN  ] Certificate  CN=alice.uplink  issuer=ALICE-CA  [VALID]"
    yield  "[ TUN  ] ECDH key exchange  curve=X25519  PFS enabled"
    yield  "[ TUN  ] Handshake complete"
    yield f"[ TUN  ] Tunnel UP  gw={gw}  peer={peer}  RTT={random.randint(8,80)}ms"
    yield  "[ TUN  ] Session token issued  TTL=3600s  scope=monitor:read,write"
    yield  "[ TUN  ] Traffic shaping  QoS policy applied"
    yield  " "
    yield  "[ AUTH ] Contacting A.L.I.C.E. authentication service..."
    yield  "[ AUTH ] Challenge-response exchange..."
    yield  "[ AUTH ] MFA token verified  method=TOTP"
    yield  "[ AUTH ] Identity confirmed  role=OPERATOR  clearance=L3"
    yield  "[ AUTH ] Access GRANTED  session-id=" + \
           "".join(random.choices("0123456789abcdef", k=16))
    yield  " "
    yield  "[ SYS  ] Mounting secure workspace..."
    yield  "[ SYS  ] Audit logging enabled  →  /var/log/alice/session.log"
    yield  "[ SYS  ] All subsystems nominal"
    yield  "[ SYS  ] Redirecting to A.L.I.C.E. login portal..."


# Phase execution order — comment out any phase to skip it
PHASES = [
    _phase_iface,
    _phase_capture,
    _phase_portscan,
    _phase_ids,
    _phase_vuln,
    _phase_traffic,
    _phase_tunnel,
]

# ── Color defaults ────────────────────────────────────────────────────────────
_COLOR_BG     = (10,  10,  15)
_COLOR_TEXT   = (200, 255, 200)
_COLOR_ACCENT = (0,   255,   0)
_COLOR_MUTED  = (80,  100,  80)


# ─────────────────────────────────────────────────────────────────────────────

def run_boot(screen, canvas, clock, current_window_size,
             color_bg=None, color_text=None, color_accent=None,
             font=None, is_fullscreen=False):
    """
    Run the boot intro sequence.

    screen, canvas, clock, current_window_size — standard pygame objects.
    color_bg / color_text / color_accent — theme colours (optional).
    font — pygame.font.Font for log text (optional, defaults to Consolas 16).
    """
    bg     = color_bg     or _COLOR_BG
    fg     = color_text   or _COLOR_TEXT
    accent = color_accent or _COLOR_ACCENT
    muted  = _COLOR_MUTED

    if font is None:
        try:    font = pygame.font.SysFont("Consolas", 16)
        except: font = pygame.font.SysFont(None, 16)

    try:    font_sm = pygame.font.SysFont("Consolas", 13)
    except: font_sm = font

    LINE_H   = font.get_height() + 3
    MAX_LINES = (canvas.get_height() - 46) // LINE_H

    # Tag → color mapping (evaluated each line)
    TAG_COLORS = {
        "[ SCAN ]": (100, 200, 255),
        "[ IDS  ]": (180, 130, 255),
        "[ TUN  ]": accent,
        "[ AUTH ]": accent,
        "[ CAP  ]": (120, 220, 180),
        "[ SYS  ]": muted,
        "[ IFACE]": fg,
        "[ FLOW ]": fg,   # further refined by threat classification below
    }

    lines      = []      # list of (text_str, color)
    phase_gen  = None
    phase_idx  = 0
    last_line_t= 0
    done       = False
    done_t     = 0
    waiting_click = False   # True once all phases finished, waiting for click

    def _push(txt, col=None):
        lines.append((txt, col or fg))
        if len(lines) > MAX_LINES:
            lines.pop(0)

    def _line_color(txt):
        """Derive display colour from tag and content."""
        for tag, col in TAG_COLORS.items():
            if tag in txt:
                if tag == "[ FLOW ]":
                    for threat, tcol in _THREAT_COLOR.items():
                        if f"[{threat}]" in txt:
                            return tcol or fg
                return col
        return fg

    def _draw_header():
        ts  = time.strftime("%Y-%m-%d  %H:%M:%S")
        bar = f"  A.L.I.C.E. NETWORK MONITOR  v2.4.1  |  {ts}  |  IDS/IPS: ACTIVE"
        pygame.draw.rect(canvas, (16, 20, 16), (0, 0, canvas.get_width(), 24))
        pygame.draw.line(canvas, accent, (0, 24), (canvas.get_width(), 24), 1)
        canvas.blit(font_sm.render(bar, True, accent), (8, 4))
        # Live blink dot
        dot_col = (50, 255, 50) if (pygame.time.get_ticks() // 600) % 2 == 0 else (20, 80, 20)
        pygame.draw.circle(canvas, dot_col, (canvas.get_width() - 14, 12), 5)

    def _draw_footer():
        if waiting_click:
            # Blink the continue prompt
            if (pygame.time.get_ticks() // 600) % 2 == 0:
                prompt = font_sm.render("[ CLICK ANYWHERE TO CONTINUE ]", True, accent)
                canvas.blit(prompt, (canvas.get_width() // 2 - prompt.get_width() // 2,
                                     canvas.get_height() - prompt.get_height() - 6))
        else:
            hint = font_sm.render("CLICK  —  skip boot sequence", True, muted)
            canvas.blit(hint, (canvas.get_width() - hint.get_width() - 10,
                               canvas.get_height() - hint.get_height() - 4))

    while True:
        canvas.fill(bg)
        now = pygame.time.get_ticks()

        # ── Events ───────────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); raise SystemExit
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if waiting_click:
                    return          # click anywhere to continue
                else:
                    # Skip remaining boot phases, jump straight to prompt
                    done          = True
                    done_t        = now
                    waiting_click = True
                    phase_gen     = None
                    phase_idx     = len(PHASES)
            elif event.type == pygame.VIDEORESIZE and not is_fullscreen:
                current_window_size = (event.w, event.h)
                screen = pygame.display.set_mode(current_window_size, pygame.RESIZABLE)

        # ── Advance log ───────────────────────────────────────────────────────
        if not done and now - last_line_t >= LINE_INTERVAL:
            last_line_t = now

            if phase_gen is None:
                if phase_idx < len(PHASES):
                    phase_gen = PHASES[phase_idx]()
                    phase_idx += 1
                    _push(" ")          # blank line between phases
                else:
                    done          = True
                    done_t        = now
                    waiting_click = True

            if phase_gen is not None:
                try:
                    line = next(phase_gen)
                    _push(line, _line_color(line))
                except StopIteration:
                    phase_gen = None

        # ── Render ────────────────────────────────────────────────────────────
        _draw_header()

        y = 30
        for txt, col in lines:
            canvas.blit(font.render(txt, True, col), (12, y))
            y += LINE_H

        # Blinking block cursor
        if (now // 500) % 2 == 0:
            canvas.blit(font.render("█", True, accent), (12, y))

        _draw_footer()

        screen.blit(pygame.transform.scale(canvas, current_window_size), (0, 0))
        pygame.display.flip()
        clock.tick(60)