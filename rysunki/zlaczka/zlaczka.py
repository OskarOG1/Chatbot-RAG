#!/usr/bin/env python3
"""Rysunek techniczny złączki gwintowanej (mosiądz), arkusz A4 poziomo, skala 2:1.

Rzuty prostokątne metodą europejską (E, PN-EN ISO 128, ISO 5456-2):
widok z przodu w półprzekroju, widok z lewej (po prawej stronie), widok z góry (pod spodem).
Rzut izometryczny w skali 1:1: w 2:1 ma ok. 130x108 mm i nie mieści się obok tabliczki.

Wynik: zlaczka.svg (jednostki mm), zlaczka.pdf (cairosvg), zlaczka.png (podgląd).
Na końcu skrypt sprawdza wyrównanie rzutów, sumę długości, wyjście poza ramkę
oraz kolizje tekstów z liniami i z innymi tekstami.

Użycie: python3 zlaczka.py [--autor "Imię Nazwisko"] [--data 28.10.2026] [--out KATALOG]
"""
import argparse
import math
import sys
from pathlib import Path

import cairosvg
from PIL import ImageFont

# --- arkusz i konwencje (mm arkusza) ----------------------------------------------
SHEET_W, SHEET_H = 297.0, 210.0
FRAME = (20.0, 10.0, 287.0, 200.0)      # ISO 5457: 20 mm z lewej, 10 mm z pozostałych stron
S = 2.0                                  # skala rzutów prostokątnych
S_ISO = 1.0                              # skala izometrii
THICK, THIN, FRAME_W = 0.5, 0.25, 0.7
H_DIM, H_LABEL, H_NAME = 3.5, 1.8, 5.0   # wysokość pisma (ISO 3098)
ARROW_L, ARROW_W = 2.5, 0.9              # strzałka zamknięta: długość i szerokość podstawy
EXT_OVER = 2.0                           # wysunięcie linii pomocniczej za linię wymiarową
TEXT_GAP = 1.0                           # odstęp liczby od linii wymiarowej
AXIS_OVER = 3.0                          # wysunięcie osi poza obrys
HATCH_STEP = 2.0
FONT_FILE = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_FAMILY = "DejaVu Sans"
CAP = 0.729                              # wysokość wersalika DejaVu Sans / em
C30 = math.cos(math.radians(30))

# --- geometria (mm rzeczywiste); oś obrotu = X, Z w górę, Y w głąb ------------------
X_THR, X_HEX, X_NECK, X_COLLAR, L = 15.0, 40.0, 43.0, 46.0, 49.0   # końce odcinków
R_THR, R_THR_CORE = 12.5, 11.5           # gwint zewnętrzny Ø25, rdzeń Ø23
S_HEX = 25.0                             # rozwartość klucza
R_HEX = S_HEX / 2 / C30                  # 14,434 (e = 28,87), naroża w ±Z
R_NECK, R_COLLAR, R_TOP = 14.0, 15.0, 13.5
R_BORE1, R_BORE2 = 9.5, 11.0             # otwór Ø19 (x 0–15), Ø22 (x 15–49)
X_ITHR, R_ITHR = 40.0, 12.0              # gwint wewnętrzny x 40–49, dno rowków Ø24
THREAD_PITCH_ISO = 1.8                   # odstęp półelips gwintu w izometrii

# (x od, x do, zasięg w Z) i (x od, x do, zasięg w Y) dla odcinków zewnętrznych
PROFILE_Z = [(0.0, X_THR, R_THR), (X_THR, X_HEX, R_HEX), (X_HEX, X_NECK, R_NECK),
             (X_NECK, X_COLLAR, R_COLLAR), (X_COLLAR, L, R_TOP)]
PROFILE_Y = [(0.0, X_THR, R_THR), (X_THR, X_HEX, S_HEX / 2), (X_HEX, X_NECK, R_NECK),
             (X_NECK, X_COLLAR, R_COLLAR), (X_COLLAR, L, R_TOP)]
STEPS_X = sorted({x for x0, x1, _ in PROFILE_Z for x in (x0, x1)})

# --- rozmieszczenie na arkuszu ----------------------------------------------------
X0 = 40.0                     # x = 0 widoku z przodu i widoku z góry
YF = 70.0                     # oś widoku z przodu i widoku z lewej
XL = 200.0                    # oś pionowa widoku z lewej
YT = 152.0                    # oś widoku z góry
ISO_BOX = (215.0, 105.0)      # lewy górny róg obrysu izometrii
TB = (177.0, 166.0, 287.0, 200.0)


def front(x, z):
    return (X0 + S * x, YF - S * z)


def left(y, z):
    # patrzymy od x = 0 w stronę +X: na arkuszu w prawo jest -Y
    return (XL - S * y, YF - S * z)


def top(x, y):
    # patrzymy z góry w stronę -Z: na arkuszu w górę jest +Y
    return (X0 + S * x, YT - S * y)


def fmt(v):
    return f"{v:g}".replace(".", ",")


class Sheet:
    def __init__(self):
        self.out = []
        self.segs = []      # (a, b, rodzaj, widok) do kontroli
        self.texts = []     # (bbox, napis, widok)
        self.view = "arkusz"
        self.font = ImageFont.truetype(FONT_FILE, 1000)

    def _reg(self, pts, kind, closed=False):
        pts = list(pts)
        nxt = pts[1:] + pts[:1] if closed else pts[1:]
        self.segs.extend((a, b, kind, self.view) for a, b in zip(pts, nxt))

    def line(self, p, q, w=THICK, kind="krawędź"):
        self.out.append(f'<line x1="{p[0]:.3f}" y1="{p[1]:.3f}" x2="{q[0]:.3f}" '
                        f'y2="{q[1]:.3f}" stroke-width="{w}"/>')
        self._reg([p, q], kind)

    def poly(self, pts, w=THICK, closed=False, fill=None, kind="krawędź"):
        tag = "polygon" if closed else "polyline"
        d = " ".join(f"{x:.3f},{y:.3f}" for x, y in pts)
        f = f' fill="{fill}"' if fill else ""
        self.out.append(f'<{tag} points="{d}" stroke-width="{w}"{f}/>')
        self._reg(pts, kind, closed)

    def arc(self, c, r, a0, a1, w=THICK, kind="krawędź"):
        """Łuk o kątach w stopniach, liczonych przeciwnie do zegara od osi +x arkusza."""
        n = max(2, int(abs(a1 - a0) * 2))
        pts = []
        for i in range(n + 1):
            a = math.radians(a0 + (a1 - a0) * i / n)
            pts.append((c[0] + r * math.cos(a), c[1] - r * math.sin(a)))
        self.poly(pts, w, kind=kind)

    def circle(self, c, r, w=THICK, kind="krawędź"):
        self.out.append(f'<circle cx="{c[0]:.3f}" cy="{c[1]:.3f}" r="{r:.3f}" stroke-width="{w}"/>')
        pts = [(c[0] + r * math.cos(2 * math.pi * i / 144), c[1] + r * math.sin(2 * math.pi * i / 144))
               for i in range(144)]
        self._reg(pts, kind, closed=True)

    def center_line(self, p, q, dash=8.0, gap=1.0, dot=0.25):
        """Linia punktowa cienka; zaczyna się i kończy kreską, nieparzysta liczba kresek,
        więc osie krzyżują się na kreskach."""
        length = math.dist(p, q)
        link = 2 * gap + dot
        n = max(1, round((length + link) / (dash + link)))
        if n % 2 == 0:
            n = min((n - 1, n + 1), key=lambda k: abs((length - (k - 1) * link) / k - dash))
        d = (length - (n - 1) * link) / n
        self.out.append(f'<line x1="{p[0]:.3f}" y1="{p[1]:.3f}" x2="{q[0]:.3f}" y2="{q[1]:.3f}" '
                        f'stroke-width="{THIN}" stroke-linecap="butt" '
                        f'stroke-dasharray="{d:.3f} {gap} {dot} {gap}"/>')
        self._reg([p, q], "oś")

    def arrow(self, tip, d):
        """Strzałka zamknięta zaczerniona; d to kierunek grotu (wektor jednostkowy)."""
        ux, uy = d
        bx, by = tip[0] - ux * ARROW_L, tip[1] - uy * ARROW_L
        px, py = -uy * ARROW_W / 2, ux * ARROW_W / 2
        pts = [tip, (bx + px, by + py), (bx - px, by - py)]
        d = " ".join(f"{x:.3f},{y:.3f}" for x, y in pts)
        self.out.append(f'<polygon points="{d}" fill="#000" stroke="none"/>')
        self._reg(pts, "grot", closed=True)

    def text_len(self, s, h=H_DIM):
        return self.font.getlength(s) / 1000 * h / CAP

    def text(self, x, y, s, h=H_DIM, anchor="middle", rot=0):
        fs = h / CAP
        w = self.text_len(s, h)
        _, top_, _, bot = self.font.getbbox(s, anchor="ls")
        t, b = top_ / 1000 * fs, bot / 1000 * fs           # względem linii bazowej
        dx0 = {"start": 0.0, "middle": -w / 2, "end": -w}[anchor]
        if rot == 0:
            box = (x + dx0, y + t, x + dx0 + w, y + b)
        elif rot == -90:                                   # czytane od prawej strony
            box = (x + t, y - dx0 - w, x + b, y - dx0)
        else:
            raise ValueError(rot)
        tr = f' transform="rotate({rot} {x:.3f} {y:.3f})"' if rot else ""
        self.out.append(f'<text x="{x:.3f}" y="{y:.3f}" font-size="{fs:.3f}" '
                        f'text-anchor="{anchor}" fill="#000" stroke="none"{tr}>{s}</text>')
        self.texts.append((box, s, self.view))

    def svg(self):
        head = (f'<?xml version="1.0" encoding="UTF-8"?>\n'
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{SHEET_W:g}mm" height="{SHEET_H:g}mm" '
                f'viewBox="0 0 {SHEET_W:g} {SHEET_H:g}">\n'
                f'<rect width="{SHEET_W:g}" height="{SHEET_H:g}" fill="#fff"/>\n'
                f'<g fill="none" stroke="#000" stroke-linecap="round" stroke-linejoin="round" '
                f'font-family="{FONT_FAMILY}">\n')
        return head + "\n".join(self.out) + "\n</g>\n</svg>\n"


# --- wymiarowanie -----------------------------------------------------------------
def dim_h(sh, xa, xb, y, value, ext=(), text_x=None):
    """Wymiar poziomy na wysokości y; ext: punkty (x, y), od których idą linie pomocnicze."""
    for x, y_from in ext:
        sh.line((x, y_from), (x, y + math.copysign(EXT_OVER, y - y_from)), THIN, "pomocnicza")
    sh.line((xa, y), (xb, y), THIN, "wymiarowa")
    sh.arrow((xa, y), (-1, 0))
    sh.arrow((xb, y), (1, 0))
    sh.text((xa + xb) / 2 if text_x is None else text_x, y - TEXT_GAP, value)


def dim_v(sh, x, ya, yb, value, ext_from=None, text_y=None):
    """Wymiar pionowy na x, od ya (góra) do yb (dół); linie pomocnicze od x = ext_from."""
    if ext_from is not None:
        for y in (ya, yb):
            sh.line((ext_from, y), (x + math.copysign(EXT_OVER, x - ext_from), y), THIN, "pomocnicza")
    sh.line((x, ya), (x, yb), THIN, "wymiarowa")
    sh.arrow((x, ya), (0, -1))
    sh.arrow((x, yb), (0, 1))
    sh.text(x - TEXT_GAP, (ya + yb) / 2 if text_y is None else text_y, value, rot=-90)


def half_dim_v(sh, x, y_tip, y_free, value, text_y):
    """Półwymiar średnicy w półprzekroju: linia nieco za osią, jeden grot na obrysie."""
    sh.line((x, y_free), (x, y_tip), THIN, "wymiarowa")
    sh.arrow((x, y_tip), (0, math.copysign(1, y_tip - y_free)))
    sh.text(x - TEXT_GAP, text_y, value, rot=-90)


def hatch(sh, poly, step=HATCH_STEP):
    """Kreskowanie pod 45° (linie x + y = c na arkuszu), przycięte do wielokąta."""
    dc = step * math.sqrt(2)
    sums = [x + y for x, y in poly]
    c = math.floor(min(sums) / dc) * dc + dc / 2
    while c < max(sums):
        xs = []
        for (ax, ay), (bx, by) in zip(poly, poly[1:] + poly[:1]):
            fa, fb = ax + ay - c, bx + by - c
            if (fa > 0) != (fb > 0):
                xs.append(ax + fa / (fa - fb) * (bx - ax))
        xs.sort()
        for xa, xb in zip(xs[::2], xs[1::2]):
            if (xb - xa) * math.sqrt(2) > 0.5:      # pomijamy okruchy w narożach
                sh.line((xa, c - xa), (xb, c - xb), THIN, "kreskowanie")
        c += dc


# --- rzuty ------------------------------------------------------------------------
def front_view(sh):
    sh.view = "przód"
    P = front
    reach = {x: max(r for x0, x1, r in PROFILE_Z if x0 <= x <= x1) for x in STEPS_X}
    sh.center_line((X0 - AXIS_OVER, YF), (P(L, 0)[0] + AXIS_OVER, YF))

    # górna połowa: przekrój
    section = [(0, R_BORE1), (0, R_THR), (X_THR, R_THR), (X_THR, R_HEX), (X_HEX, R_HEX),
               (X_HEX, R_NECK), (X_NECK, R_NECK), (X_NECK, R_COLLAR), (X_COLLAR, R_COLLAR),
               (X_COLLAR, R_TOP), (L, R_TOP), (L, R_BORE2), (X_THR, R_BORE2), (X_THR, R_BORE1)]
    pts = [P(x, z) for x, z in section]
    hatch(sh, pts)
    sh.poly(pts, closed=True)
    for x, r in ((0, R_BORE1), (X_THR, R_BORE1), (L, R_BORE2)):   # krawędzie otworu za przekrojem
        sh.line(P(x, 0), P(x, r))
    sh.line(P(0, R_THR_CORE), P(X_THR, R_THR_CORE), THIN, "gwint")      # rdzeń Ø23
    sh.line(P(X_ITHR, R_ITHR), P(L, R_ITHR), THIN, "gwint")            # dno gwintu wewn. Ø24
    sh.line(P(X_THR, R_THR_CORE), P(X_THR, R_THR))                     # koniec gwintu zewn.
    sh.line(P(X_ITHR, R_BORE2), P(X_ITHR, R_ITHR))                      # koniec gwintu wewn.

    # dolna połowa: widok
    for x0, x1, r in PROFILE_Z:
        sh.line(P(x0, -r), P(x1, -r))
    for x in STEPS_X:
        sh.line(P(x, 0), P(x, -reach[x]))
    sh.line(P(X_THR, -R_HEX / 2), P(X_HEX, -R_HEX / 2))                # krawędź między ścianami
    sh.line(P(0, -R_THR_CORE), P(X_THR, -R_THR_CORE), THIN, "gwint")

    # długości nad widokiem
    y1 = YF - S * R_COLLAR - 10
    y2 = y1 - 8
    for x in STEPS_X:
        y_end = (y2 if x in (0, L) else y1) - EXT_OVER
        sh.line(P(x, reach[x]), (P(x, 0)[0], y_end), THIN, "pomocnicza")
    for x0, x1, _ in PROFILE_Z:
        dim_h(sh, P(x0, 0)[0], P(x1, 0)[0], y1, fmt(x1 - x0))
    dim_h(sh, P(0, 0)[0], P(L, 0)[0], y2, fmt(L))

    # średnice zewnętrzne
    dim_v(sh, X0 - 10, P(0, R_THR)[1], P(0, -R_THR)[1], "Ø" + fmt(2 * R_THR), ext_from=X0)
    x_end = P(L, 0)[0]
    dim_v(sh, x_end + 10, P(0, R_TOP)[1], P(0, -R_TOP)[1], "Ø" + fmt(2 * R_TOP), ext_from=x_end)
    dim_v(sh, x_end + 19, P(0, R_COLLAR)[1], P(0, -R_COLLAR)[1], "Ø" + fmt(2 * R_COLLAR),
          ext_from=P(X_COLLAR, 0)[0])

    # Ø28: szyjka ma 6 mm na arkuszu, więc grot od zewnątrz, a liczba pod obrysem
    s28 = "Ø" + fmt(2 * R_NECK)
    x = P((X_HEX + X_NECK) / 2, 0)[0]
    y_tip = P(0, -R_NECK)[1]
    y_txt0 = P(0, -R_HEX)[1] + 4
    y_txt1 = y_txt0 + sh.text_len(s28)
    sh.line((x, YF - 3), (x, y_txt1 + 1), THIN, "wymiarowa")
    sh.arrow((x, y_tip), (0, -1))
    sh.text(x - TEXT_GAP, (y_txt0 + y_txt1) / 2, s28, rot=-90)

    # średnice otworu w półprzekroju
    half_dim_v(sh, P(7.5, 0)[0], P(0, R_BORE1)[1], YF + 3, "Ø" + fmt(2 * R_BORE1), P(0, R_BORE1 / 2)[1])
    half_dim_v(sh, P(25, 0)[0], P(0, R_BORE2)[1], YF + 3, "Ø" + fmt(2 * R_BORE2), P(0, R_BORE2 / 2)[1])

    # głębokość gwintu wewnętrznego: od końca gwintu do czoła x = 49
    y9 = P(0, 6.5)[1]
    dim_h(sh, P(X_ITHR, 0)[0], x_end, y9, fmt(L - X_ITHR), ext=[(P(X_ITHR, 0)[0], P(0, R_BORE2)[1])])


def left_view(sh):
    sh.view = "lewy"
    c = left(0, 0)
    r_out = S * R_COLLAR + AXIS_OVER
    sh.center_line((c[0] - r_out, c[1]), (c[0] + r_out, c[1]))
    sh.center_line((c[0], c[1] - r_out), (c[0], c[1] + r_out))
    sh.circle(c, S * R_COLLAR)                                         # kołnierz Ø30
    sh.poly([left(R_HEX * math.cos(math.radians(90 + 60 * k)), R_HEX * math.sin(math.radians(90 + 60 * k)))
             for k in range(6)], closed=True)
    # szyjka Ø28 wystaje poza ściany sześciokąta (14 > 12,5): 6 widocznych łuków
    phi = math.degrees(math.acos(S_HEX / 2 / R_NECK))
    for k in range(6):
        sh.arc(c, S * R_NECK, 60 * k - phi, 60 * k + phi)
    sh.circle(c, S * R_THR)                                            # gwint Ø25
    sh.arc(c, S * R_THR_CORE, 100, 370, THIN, "gwint")                 # rdzeń Ø23, ok. 3/4 okręgu
    sh.circle(c, S * R_BORE1)                                          # otwór Ø19


def top_view(sh):
    sh.view = "góra"
    P = top
    reach = {x: max(r for x0, x1, r in PROFILE_Y if x0 <= x <= x1) for x in STEPS_X}
    sh.center_line((X0 - AXIS_OVER, YT), (P(L, 0)[0] + AXIS_OVER, YT))
    for x0, x1, r in PROFILE_Y:
        sh.line(P(x0, r), P(x1, r))
        sh.line(P(x0, -r), P(x1, -r))
    for x in STEPS_X:
        sh.line(P(x, -reach[x]), P(x, reach[x]))
    sh.line(P(X_THR, 0), P(X_HEX, 0))                                  # naroże sześciokąta (Y = 0)
    for sgn in (1, -1):
        sh.line(P(0, sgn * R_THR_CORE), P(X_THR, sgn * R_THR_CORE), THIN, "gwint")
    dim_v(sh, P(30, 0)[0], P(0, S_HEX / 2)[1], P(0, -S_HEX / 2)[1], fmt(S_HEX),
          text_y=P(0, S_HEX / 4)[1])


# --- izometria --------------------------------------------------------------------
SOLIDS = [("cyl", 0.0, X_THR, R_THR), ("hex", X_THR, X_HEX, None), ("cyl", X_HEX, X_NECK, R_NECK),
          ("cyl", X_NECK, X_COLLAR, R_COLLAR), ("cyl", X_COLLAR, L, R_TOP)]


def iso_uv(x, y, z):
    return ((x - y) * C30 * S_ISO, ((x + y) * 0.5 - z) * S_ISO)


def ring(x, r, n=360, a0=0.0, a1=360.0):
    return [(x, r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n)]


def hex_ring(x):
    # k = 0: naroże 90° (+Z), k = 5: naroże 30°
    return [(x, R_HEX * math.cos(math.radians(90 + 60 * k)), R_HEX * math.sin(math.radians(90 + 60 * k)))
            for k in range(6)]


def end_section(kind, x, r):
    return hex_ring(x) if kind == "hex" else ring(x, r)


def convex_hull(pts):
    pts = sorted(set(pts))

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def iso_view(sh):
    """Odcinki od x = 0 do x = 49 (od tyłu do przodu), każdy jako biała bryła przykrywająca
    poprzednie. Punkt o mniejszym x nigdy nie zasłania punktu o większym x, bo kierunek
    patrzenia to (1, 1, 1)."""
    sh.view = "izometria"
    uv = [iso_uv(*p) for kind, x0, x1, r in SOLIDS for x in (x0, x1) for p in end_section(kind, x, r)]
    du = ISO_BOX[0] - min(u for u, _ in uv)
    dv = ISO_BOX[1] - min(v for _, v in uv)

    def Q(p):
        u, v = iso_uv(*p)
        return (u + du, v + dv)

    for i, (kind, x0, x1, r) in enumerate(SOLIDS):
        back, face = end_section(kind, x0, r), end_section(kind, x1, r)
        sh.poly(convex_hull([Q(p) for p in back + face]), closed=True, fill="#fff")
        if kind == "hex":
            sh.poly([Q(p) for p in face], closed=True)
            for k in (0, 5):                     # krawędzie między trzema widocznymi ścianami
                sh.line(Q(back[k]), Q(face[k]))
            continue
        nxt = SOLIDS[i + 1] if i + 1 < len(SOLIDS) else None
        if nxt is None or (nxt[0] == "cyl" and nxt[3] < r):          # czoło odsłonięte
            sh.poly([Q(p) for p in face], closed=True)
        if i == 0:                               # gwint: widoczne półelipsy (normalna·(0,1,1) > 0)
            n = int((X_THR - 1) // THREAD_PITCH_ISO)
            for k in range(1, n + 1):
                sh.poly([Q(p) for p in ring(k * THREAD_PITCH_ISO, R_THR, 90, -45, 135)]
                        + [Q((k * THREAD_PITCH_ISO, R_THR * math.cos(math.radians(135)),
                              R_THR * math.sin(math.radians(135))))], THIN, kind="gwint")
    sh.poly([Q(p) for p in ring(L, R_BORE2)], closed=True)                    # otwór Ø22
    sh.poly([Q(p) for p in ring(L, R_ITHR)], THIN, closed=True, kind="gwint")  # dno gwintu Ø24

    hull = [Q(p) for p in [q for kind, x0, x1, r in SOLIDS for x in (x0, x1) for q in end_section(kind, x, r)]]
    y_bottom = max(y for _, y in hull)
    sh.text(ISO_BOX[0], y_bottom, f"{S_ISO:g}:1", anchor="start")


# --- ramka i tabliczka ------------------------------------------------------------
def frame(sh):
    sh.view = "ramka"
    x0, y0, x1, y1 = FRAME
    sh.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], FRAME_W, closed=True, kind="ramka")
    cx, cy = SHEET_W / 2, SHEET_H / 2
    for p, q in (((0, cy), (x0 + 5, cy)), ((SHEET_W, cy), (x1 - 5, cy)),
                 ((cx, 0), (cx, y0 + 5)), ((cx, SHEET_H), (cx, y1 - 5))):   # znaki centrujące
        sh.line(p, q, FRAME_W, "ramka")


def projection_symbol(sh, x, cy):
    """Symbol metody E (ISO 5456-2): stożek ścięty, węższy koniec z lewej, okręgi po prawej."""
    r = 2.75
    w = 0.35
    sh.poly([(x, cy - r / 2), (x + 2 * r, cy - r), (x + 2 * r, cy + r), (x, cy + r / 2)], w, closed=True)
    cc = x + 2 * r + 1.5 + r
    sh.circle((cc, cy), r, w)
    sh.circle((cc, cy), r / 2, w)
    sh.center_line((x - 1, cy), (cc + r + 1, cy), dash=3.0, gap=0.6)
    sh.center_line((cc, cy - r - 1), (cc, cy + r + 1), dash=3.0, gap=0.6)


def title_block(sh, autor, data):
    sh.view = "tabliczka"
    x0, y0, x1, y1 = TB
    ya, yb = y0 + 12, y0 + 24
    xb1, xb2 = x0 + 45, x0 + 70
    sh.line((x0, y0), (x1, y0), THICK, "tabliczka")
    sh.line((x0, y0), (x0, y1), THICK, "tabliczka")
    for p, q in (((x0, ya), (x1, ya)), ((x0, yb), (x1, yb)), ((xb1, ya), (xb1, yb)), ((xb2, ya), (xb2, y1))):
        sh.line(p, q, THIN, "tabliczka")

    def cell(x, y, h_row, label, value, h=H_DIM):
        sh.text(x + 1.2, y + 1.2 + H_LABEL, label, H_LABEL, "start")
        if value:
            sh.text(x + 2, y + h_row - 2.2, value, h, "start")

    cell(x0, y0, 12, "Nazwa", "Złączka gwintowana", H_NAME)
    cell(x0, ya, 12, "Materiał", "mosiądz")
    cell(xb1, ya, 12, "Skala", f"{S:g}:1")
    cell(xb2, ya, 12, "Metoda rzutowania", None)
    projection_symbol(sh, xb2 + 5, ya + 7.8)
    sh.text(xb2 + 28, ya + 9.8, "E", anchor="start")
    cell(x0, yb, 10, "Autor", autor)
    cell(xb2, yb, 10, "Data", data)


# --- kontrola ---------------------------------------------------------------------
def seg_hits_box(a, b, box):
    """Czy odcinek ab przecina prostokąt (Liang–Barsky)."""
    x0, y0, x1, y1 = box
    dx, dy = b[0] - a[0], b[1] - a[1]
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, a[0] - x0), (dx, x1 - a[0]), (-dy, a[1] - y0), (dy, y1 - a[1])):
        if p == 0:
            if q < 0:
                return False
        else:
            t = q / p
            if p < 0:
                t0 = max(t0, t)
            else:
                t1 = min(t1, t)
            if t0 > t1:
                return False
    return True


def boxes_overlap(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def check(sh):
    problems = []
    # 1. wyrównanie rzutów
    if abs(front(0, 0)[1] - left(0, 0)[1]) > 1e-9:
        problems.append("oś widoku z lewej nie jest na wysokości osi widoku z przodu")
    if any(abs(front(x, 0)[0] - top(x, 0)[0]) > 1e-9 for x in STEPS_X):
        problems.append("widok z góry nie jest wyrównany w X z widokiem z przodu")
    # 2. suma długości
    if abs(sum(x1 - x0 for x0, x1, _ in PROFILE_Z) - L) > 1e-9:
        problems.append("suma długości odcinków różna od długości całkowitej")
    # 3. wszystko w ramce
    fx0, fy0, fx1, fy1 = FRAME
    inside = lambda x, y: fx0 <= x <= fx1 and fy0 <= y <= fy1   # tabliczka dochodzi do ramki
    for a, b, kind, view in sh.segs:
        if kind != "ramka" and not (inside(*a) and inside(*b)):
            problems.append(f"{view}: linia {kind} poza ramką {a}–{b}")
    for box, s, view in sh.texts:
        if not (inside(box[0], box[1]) and inside(box[2], box[3])):
            problems.append(f"{view}: tekst '{s}' poza ramką")
    # 4. kolizje tekstów (z zapasem 0,3 mm)
    for i, (box, s, view) in enumerate(sh.texts):
        big = (box[0] - 0.3, box[1] - 0.3, box[2] + 0.3, box[3] + 0.3)
        for a, b, kind, v in sh.segs:
            if seg_hits_box(a, b, big):
                problems.append(f"{view}: tekst '{s}' koliduje z linią {kind} ({v})")
                break
        for box2, s2, _ in sh.texts[i + 1:]:
            if boxes_overlap(big, box2):
                problems.append(f"{view}: tekst '{s}' nachodzi na '{s2}'")
    # 5. rzuty nie nachodzą na siebie (obrysy razem z wymiarami)
    boxes = {}
    for a, b, _, view in sh.segs:
        for x, y in (a, b):
            bx = boxes.setdefault(view, [x, y, x, y])
            bx[:] = [min(bx[0], x), min(bx[1], y), max(bx[2], x), max(bx[3], y)]
    for box, _, view in sh.texts:
        bx = boxes.setdefault(view, list(box))
        bx[:] = [min(bx[0], box[0]), min(bx[1], box[1]), max(bx[2], box[2]), max(bx[3], box[3])]
    names = [v for v in boxes if v != "ramka"]
    for i, v1 in enumerate(names):
        for v2 in names[i + 1:]:
            if boxes_overlap(boxes[v1], boxes[v2]):
                problems.append(f"obszary rzutów '{v1}' i '{v2}' nachodzą na siebie")
    return problems, boxes


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--autor", default="")
    ap.add_argument("--data", default="28.10.2026")
    ap.add_argument("--out", type=Path, default=Path(__file__).resolve().parent)
    args = ap.parse_args()

    sh = Sheet()
    frame(sh)
    front_view(sh)
    left_view(sh)
    top_view(sh)
    iso_view(sh)
    title_block(sh, args.autor, args.data)

    args.out.mkdir(parents=True, exist_ok=True)
    svg = args.out / "zlaczka.svg"
    svg.write_text(sh.svg(), encoding="utf-8")
    cairosvg.svg2pdf(url=str(svg), write_to=str(args.out / "zlaczka.pdf"))
    cairosvg.svg2png(url=str(svg), write_to=str(args.out / "zlaczka.png"), output_width=3508)

    problems, boxes = check(sh)
    for view, b in boxes.items():
        print(f"{view:10s} x {b[0]:6.1f}–{b[2]:6.1f}  y {b[1]:6.1f}–{b[3]:6.1f}")
    if problems:
        print("KONTROLA: problemy:")
        for p in problems:
            print("  -", p)
        sys.exit(1)
    print("KONTROLA: OK (wyrównanie, suma 15+25+3+3+3 = 49, ramka, kolizje tekstów)")


if __name__ == "__main__":
    main()
