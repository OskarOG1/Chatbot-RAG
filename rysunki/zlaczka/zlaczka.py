#!/usr/bin/env python3
"""Rysunek techniczny złączki gwintowanej (mosiądz), arkusz A4 poziomo, skala 2:1.

Rzuty prostokątne metodą europejską (E, PN-EN ISO 128, ISO 5456-2):
widok z przodu w półprzekroju, widok z lewej (po prawej stronie), widok z góry (pod spodem).
Rzut izometryczny w skali 1:1: w 2:1 ma ok. 130x108 mm i nie mieści się obok tabliczki.
Linie grupy 0,7 (gruba 0,7, cienka 0,35), pismo wymiarowe 5 mm, żeby łatwo było przerysować.

Wynik (wersja do przerysowania ręcznego):
  zlaczka.pdf                  3 strony: rysunek, arkusz konstrukcyjny, kolejność rysowania
  zlaczka.svg / .png           strona 1: rysunek z wymiarami
  zlaczka_konstrukcja.svg/.png strona 2: ten sam arkusz bez wymiarów, z niebieskimi współrzędnymi
  zlaczka_kroki.svg/.png       strona 3: kolejność rysowania w 6 krokach
Strony SVG zamienia na PDF cairosvg, a łączy je pdfunite.
Na końcu skrypt sprawdza wyrównanie rzutów, sumę długości, wyjście poza ramkę
oraz kolizje tekstów z liniami i z innymi tekstami na każdej stronie.

Użycie: python3 zlaczka.py [--autor "Imię Nazwisko"] [--data 28.10.2026] [--out KATALOG]
"""
import argparse
import math
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import cairosvg
from PIL import ImageFont

# --- arkusz i konwencje (mm arkusza) ----------------------------------------------
SHEET_W, SHEET_H = 297.0, 210.0
FRAME = (20.0, 10.0, 287.0, 200.0)      # ISO 5457: 20 mm z lewej, 10 mm z pozostałych stron
S = 2.0                                  # skala rzutów prostokątnych
S_ISO = 1.0                              # skala izometrii
THICK, THIN, FRAME_W = 0.7, 0.35, 0.7    # grupa linii 0,7 (ISO 128-20)
H_DIM, H_LABEL, H_VALUE, H_NAME = 5.0, 2.5, 5.0, 6.0   # wysokość pisma (ISO 3098)
H_NOTE, H_SMALL = 2.5, 2.2               # pismo pomocnicze na stronach 2 i 3
ARROW_L, ARROW_W = 2.5, 1.0              # strzałka zamknięta: długość i szerokość podstawy
EXT_OVER = 2.0                           # wysunięcie linii pomocniczej za linię wymiarową
TEXT_GAP = 1.0                           # odstęp liczby od linii wymiarowej
DIM_ROW = 10.0                           # odstęp rzędów wymiarów (od obrysu i między sobą)
AXIS_OVER = 3.0                          # wysunięcie osi poza obrys
HATCH_STEP = 2.0
FONT_FILE = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_FAMILY = "DejaVu Sans"
CAP = 0.729                              # wysokość wersalika DejaVu Sans / em
C30 = math.cos(math.radians(30))
BLUE, GRAY = "#1565c0", "#b4b4b4"        # współrzędne konstrukcyjne; wcześniejsze kroki

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
REACH_Z = {x: max(r for x0, x1, r in PROFILE_Z if x0 <= x <= x1) for x in STEPS_X}
REACH_Y = {x: max(r for x0, x1, r in PROFILE_Y if x0 <= x <= x1) for x in STEPS_X}

# --- rozmieszczenie na arkuszu ----------------------------------------------------
X0 = 42.0                     # x = 0 widoku z przodu i widoku z góry
YF = 68.0                     # oś widoku z przodu i widoku z lewej
XL = 205.0                    # oś pionowa widoku z lewej
YT = 152.0                    # oś widoku z góry
ISO_BOX = (220.0, 104.0)      # lewy górny róg obrysu izometrii
TB = (177.0, 162.0, 287.0, 200.0)
TB_ROWS = (14.0, 12.0, 12.0)  # nazwa; materiał, skala, metoda; autor, data


def front(x, z):
    return (X0 + S * x, YF - S * z)


def left(y, z):
    # patrzymy od x = 0 w stronę +X: na arkuszu w prawo jest -Y
    return (XL - S * y, YF - S * z)


def top(x, y):
    # patrzymy z góry w stronę -Z: na arkuszu w górę jest +Y
    return (X0 + S * x, YT - S * y)


def fmt(v, nd=2):
    return f"{round(v, nd) + 0.0:g}".replace(".", ",").replace("-", "−")   # + 0.0: bez „−0”


class Sheet:
    """Elementy SVG z numerem kroku rysowania (1–6) albo "K" dla współrzędnych konstrukcyjnych."""

    def __init__(self):
        self.els = []       # (krok, svg)
        self.segs = []      # (a, b, rodzaj, widok, krok) do kontroli
        self.texts = []     # (bbox, napis, widok, krok)
        self.view = "arkusz"
        self.overlay = False
        self.font = ImageFont.truetype(FONT_FILE, 1000)

    def _step(self, kind, text=False):
        if self.overlay:
            return "K"
        if self.view == "ramka":
            return 1
        if self.view == "tabliczka":
            return 1 if kind == "tabliczka" else 6
        if self.view == "izometria":
            return 6
        if text:
            return 5
        return {"oś": 2, "krawędź": 3, "gwint": 4, "kreskowanie": 4}.get(kind, 5)

    def _add(self, svg, pts, kind, closed=False):
        step = self._step(kind)
        self.els.append((step, svg))
        pts = list(pts)
        nxt = pts[1:] + pts[:1] if closed else pts[1:]
        self.segs.extend((a, b, kind, self.view, step) for a, b in zip(pts, nxt))

    def _col(self):
        return f' stroke="{BLUE}"' if self.overlay else ""

    def raw(self, svg, step=0):
        self.els.append((step, svg))

    def line(self, p, q, w=THICK, kind="krawędź"):
        self._add(f'<line x1="{p[0]:.3f}" y1="{p[1]:.3f}" x2="{q[0]:.3f}" y2="{q[1]:.3f}" '
                  f'stroke-width="{w}"{self._col()}/>', [p, q], kind)

    def poly(self, pts, w=THICK, closed=False, fill=None, kind="krawędź"):
        tag = "polygon" if closed else "polyline"
        d = " ".join(f"{x:.3f},{y:.3f}" for x, y in pts)
        f = f' fill="{fill}"' if fill else ""
        self._add(f'<{tag} points="{d}" stroke-width="{w}"{f}{self._col()}/>', pts, kind, closed)

    def arc(self, c, r, a0, a1, w=THICK, kind="krawędź"):
        """Łuk o kątach w stopniach, liczonych przeciwnie do zegara od osi +x arkusza."""
        n = max(2, int(abs(a1 - a0) * 2))
        pts = []
        for i in range(n + 1):
            a = math.radians(a0 + (a1 - a0) * i / n)
            pts.append((c[0] + r * math.cos(a), c[1] - r * math.sin(a)))
        self.poly(pts, w, kind=kind)

    def circle(self, c, r, w=THICK, kind="krawędź"):
        pts = [(c[0] + r * math.cos(2 * math.pi * i / 144), c[1] + r * math.sin(2 * math.pi * i / 144))
               for i in range(144)]
        self._add(f'<circle cx="{c[0]:.3f}" cy="{c[1]:.3f}" r="{r:.3f}" stroke-width="{w}"{self._col()}/>',
                  pts, kind, closed=True)

    def center_line(self, p, q, dash=8.0, gap=1.2, dot=THIN):
        """Linia punktowa cienka; zaczyna się i kończy kreską, nieparzysta liczba kresek,
        więc osie krzyżują się na kreskach."""
        length = math.dist(p, q)
        link = 2 * gap + dot
        n = max(1, round((length + link) / (dash + link)))
        if n % 2 == 0:
            n = min((n - 1, n + 1), key=lambda k: abs((length - (k - 1) * link) / k - dash))
        d = (length - (n - 1) * link) / n
        self._add(f'<line x1="{p[0]:.3f}" y1="{p[1]:.3f}" x2="{q[0]:.3f}" y2="{q[1]:.3f}" '
                  f'stroke-width="{THIN}" stroke-linecap="butt" '
                  f'stroke-dasharray="{d:.3f} {gap} {dot} {gap}"/>', [p, q], "oś")

    def arrow(self, tip, d):
        """Strzałka zamknięta zaczerniona; d to kierunek grotu (wektor jednostkowy)."""
        ux, uy = d
        bx, by = tip[0] - ux * ARROW_L, tip[1] - uy * ARROW_L
        px, py = -uy * ARROW_W / 2, ux * ARROW_W / 2
        pts = [tip, (bx + px, by + py), (bx - px, by - py)]
        d = " ".join(f"{x:.3f},{y:.3f}" for x, y in pts)
        self._add(f'<polygon points="{d}" fill="#000" stroke="none"/>', pts, "grot", closed=True)

    def text_len(self, s, h=H_DIM):
        return self.font.getlength(s) / 1000 * h / CAP

    def wrap(self, s, width, h=H_SMALL):
        lines, cur = [], ""
        for word in filter(None, s.split(" ")):   # twarda spacja nie łamie wiersza
            cand = f"{cur} {word}".strip()
            if cur and self.text_len(cand, h) > width:
                lines.append(cur)
                cur = word
            else:
                cur = cand
        return lines + [cur] if cur else lines

    def descent(self, s, h):
        return self.font.getbbox(s, anchor="ls")[3] / 1000 * h / CAP

    def text_box(self, x, y, s, h=H_DIM, anchor="middle", rot=0):
        fs = h / CAP
        w = self.text_len(s, h)
        _, top_, _, bot = self.font.getbbox(s, anchor="ls")
        t, b = top_ / 1000 * fs, bot / 1000 * fs           # względem linii bazowej
        dx0 = {"start": 0.0, "middle": -w / 2, "end": -w}[anchor]
        if rot == 0:
            return (x + dx0, y + t, x + dx0 + w, y + b)
        if rot == -90:                                     # czytane od prawej strony
            return (x + t, y - dx0 - w, x + b, y - dx0)
        raise ValueError(rot)

    def free_label(self, p, s, h, skip_steps=(5,)):
        """Etykieta punktu w pierwszym wolnym miejscu wokół p (bez kolizji z liniami i tekstami)."""
        segs = [sg for sg in self.segs if sg[4] not in skip_steps]
        for r in (1.5, 3.0, 4.5):
            for dx, dy, anchor in ((-r, -r, "end"), (r, -r, "start"), (-r, r + H_NOTE, "end"),
                                   (r, r + H_NOTE, "start"), (0, -r - 0.5, "middle"), (0, r + H_NOTE + 0.5, "middle")):
                bx = self.text_box(p[0] + dx, p[1] + dy, s, h, anchor)
                big = (bx[0] - 0.3, bx[1] - 0.3, bx[2] + 0.3, bx[3] + 0.3)
                if not any(seg_hits_box(a, b, big) for a, b, *_ in segs) and \
                        not any(boxes_overlap(big, t[0]) for t in self.texts if t[3] not in skip_steps):
                    self.text(p[0] + dx, p[1] + dy, s, h, anchor)
                    return
        raise RuntimeError(f"brak miejsca na etykietę {s}")

    def text(self, x, y, s, h=H_DIM, anchor="middle", rot=0, kind="opis"):
        fs = h / CAP
        box = self.text_box(x, y, s, h, anchor, rot)
        tr = f' transform="rotate({rot} {x:.3f} {y:.3f})"' if rot else ""
        col = BLUE if self.overlay else "#000"
        s_xml = s.replace("&", "&amp;").replace("<", "&lt;")
        step = self._step(kind, text=True)
        self.els.append((step, f'<text x="{x:.3f}" y="{y:.3f}" font-size="{fs:.3f}" '
                               f'text-anchor="{anchor}" fill="{col}" stroke="none"{tr}>{s_xml}</text>'))
        self.texts.append((box, s, self.view, step))

    def text_block(self, x, y, items, width, h=H_SMALL, lead=1.6):
        """Akapity zawijane do szerokości; y to linia bazowa pierwszego wiersza."""
        for item in items:
            for ln in self.wrap(item, width, h):
                self.text(x, y, ln, h, "start")
                y += h * lead
        return y

    def svg(self, include, w=SHEET_W, h=SHEET_H):
        body = "\n".join(el for step, el in self.els if include(step))
        return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:g}mm" height="{h:g}mm" '
                f'viewBox="0 0 {w:g} {h:g}">\n'
                f'<rect width="{w:g}" height="{h:g}" fill="#fff"/>\n'
                f'<g fill="none" stroke="#000" stroke-linecap="round" stroke-linejoin="round" '
                f'font-family="{FONT_FAMILY}">\n{body}\n</g>\n</svg>\n')

    def thumbnail(self, k, x, y, scale, widen=1.6):
        """Miniatura arkusza po kroku k: krok k czarny, wcześniejsze szare. Linie pogrubione."""
        out = [f'<g transform="translate({x:.3f} {y:.3f}) scale({scale:.5f})">',
               f'<rect width="{SHEET_W:g}" height="{SHEET_H:g}" fill="#fff" stroke="#000" '
               f'stroke-width="{0.3 / scale:.3f}"/>']
        cur = None
        for step, el in self.els:
            if step == "K" or step > k:
                continue
            col = "#000" if step == k else GRAY
            if col != cur:
                out.append(("</g>" if cur else "") + f'<g stroke="{col}">')
                cur = col
            el = re.sub(r'stroke-width="([\d.]+)"', lambda m: f'stroke-width="{float(m[1]) * widen:.3f}"', el)
            out.append(el.replace('fill="#000"', f'fill="{col}"'))
        out.append("</g></g>")
        return "\n".join(out)


# --- wymiarowanie -----------------------------------------------------------------
def dim_h(sh, xa, xb, y, value, ext=(), text_x=None, gap=TEXT_GAP):
    """Wymiar poziomy na wysokości y; ext: punkty (x, y), od których idą linie pomocnicze."""
    for x, y_from in ext:
        sh.line((x, y_from), (x, y + math.copysign(EXT_OVER, y - y_from)), THIN, "pomocnicza")
    sh.line((xa, y), (xb, y), THIN, "wymiarowa")
    sh.arrow((xa, y), (-1, 0))
    sh.arrow((xb, y), (1, 0))
    sh.text((xa + xb) / 2 if text_x is None else text_x, y - gap, value, kind="wymiar")


def dim_v(sh, x, ya, yb, value, ext_from=None, text_y=None):
    """Wymiar pionowy na x, od ya (góra) do yb (dół); linie pomocnicze od x = ext_from."""
    if ext_from is not None:
        for y in (ya, yb):
            sh.line((ext_from, y), (x + math.copysign(EXT_OVER, x - ext_from), y), THIN, "pomocnicza")
    sh.line((x, ya), (x, yb), THIN, "wymiarowa")
    sh.arrow((x, ya), (0, -1))
    sh.arrow((x, yb), (0, 1))
    sh.text(x - TEXT_GAP, (ya + yb) / 2 if text_y is None else text_y, value, rot=-90, kind="wymiar")


def half_dim_v(sh, x, y_tip, y_free, value):
    """Półwymiar średnicy w półprzekroju: linia nieco za osią, jeden grot na obrysie.
    Liczba na środku między osią a podstawą grotu."""
    sgn = math.copysign(1, y_tip - YF)
    sh.line((x, y_free), (x, y_tip), THIN, "wymiarowa")
    sh.arrow((x, y_tip), (0, sgn))
    sh.text(x - TEXT_GAP, (YF + y_tip - sgn * ARROW_L) / 2, value, rot=-90, kind="wymiar")


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
        sh.line(P(x, 0), P(x, -REACH_Z[x]))
    sh.line(P(X_THR, -R_HEX / 2), P(X_HEX, -R_HEX / 2))                # krawędź między ścianami
    sh.line(P(0, -R_THR_CORE), P(X_THR, -R_THR_CORE), THIN, "gwint")

    # długości nad widokiem
    y1 = YF - S * R_COLLAR - DIM_ROW
    y2 = y1 - DIM_ROW
    for x in STEPS_X:
        y_end = (y2 if x in (0, L) else y1) - EXT_OVER
        sh.line(P(x, REACH_Z[x]), (P(x, 0)[0], y_end), THIN, "pomocnicza")
    for x0, x1, _ in PROFILE_Z:
        # liczby nad końcami linii pomocniczych, żeby wąskie „3” nie zlewały się z nimi
        dim_h(sh, P(x0, 0)[0], P(x1, 0)[0], y1, fmt(x1 - x0), gap=EXT_OVER + 0.6)
    dim_h(sh, P(0, 0)[0], P(L, 0)[0], y2, fmt(L))

    # średnice zewnętrzne
    dim_v(sh, X0 - 10, P(0, R_THR)[1], P(0, -R_THR)[1], "Ø" + fmt(2 * R_THR), ext_from=X0)
    x_end = P(L, 0)[0]
    dim_v(sh, x_end + 12, P(0, R_TOP)[1], P(0, -R_TOP)[1], "Ø" + fmt(2 * R_TOP), ext_from=x_end)
    dim_v(sh, x_end + 24, P(0, R_COLLAR)[1], P(0, -R_COLLAR)[1], "Ø" + fmt(2 * R_COLLAR),
          ext_from=P(X_COLLAR, 0)[0])

    # Ø28: szyjka ma 6 mm na arkuszu, więc grot od zewnątrz, a liczba pod obrysem
    s28 = "Ø" + fmt(2 * R_NECK)
    x = P((X_HEX + X_NECK) / 2, 0)[0]
    y_tip = P(0, -R_NECK)[1]
    y_txt0 = P(0, -R_HEX)[1] + 4
    y_txt1 = y_txt0 + sh.text_len(s28)
    sh.line((x, YF - 3), (x, y_txt1 + 1), THIN, "wymiarowa")
    sh.arrow((x, y_tip), (0, -1))
    sh.text(x - TEXT_GAP, (y_txt0 + y_txt1) / 2, s28, rot=-90, kind="wymiar")

    # średnice otworu w półprzekroju
    half_dim_v(sh, P(7.5, 0)[0], P(0, R_BORE1)[1], YF + 3, "Ø" + fmt(2 * R_BORE1))
    half_dim_v(sh, P(25, 0)[0], P(0, R_BORE2)[1], YF + 3, "Ø" + fmt(2 * R_BORE2))

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
    sh.center_line((X0 - AXIS_OVER, YT), (P(L, 0)[0] + AXIS_OVER, YT))
    for x0, x1, r in PROFILE_Y:
        sh.line(P(x0, r), P(x1, r))
        sh.line(P(x0, -r), P(x1, -r))
    for x in STEPS_X:
        sh.line(P(x, -REACH_Y[x]), P(x, REACH_Y[x]))
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


def iso_map():
    """Funkcja (x, y, z) -> punkt arkusza, ustawiająca obrys izometrii w ISO_BOX."""
    uv = [iso_uv(*p) for kind, x0, x1, r in SOLIDS for x in (x0, x1) for p in end_section(kind, x, r)]
    du = ISO_BOX[0] - min(u for u, _ in uv)
    dv = ISO_BOX[1] - min(v for _, v in uv)

    def Q(p):
        u, v = iso_uv(*p)
        return (u + du, v + dv)

    return Q, max(v for _, v in uv) + dv


def iso_view(sh):
    """Odcinki od x = 0 do x = 49 (od tyłu do przodu), każdy jako biała bryła przykrywająca
    poprzednie. Punkt o mniejszym x nigdy nie zasłania punktu o większym x, bo kierunek
    patrzenia to (1, 1, 1)."""
    sh.view = "izometria"
    Q, y_bottom = iso_map()
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
                xk = k * THREAD_PITCH_ISO
                sh.poly([Q(p) for p in ring(xk, R_THR, 90, -45, 135) + ring(xk, R_THR, 1, 135, 136)],
                        THIN, kind="gwint")
    sh.poly([Q(p) for p in ring(L, R_BORE2)], closed=True)                    # otwór Ø22
    sh.poly([Q(p) for p in ring(L, R_ITHR)], THIN, closed=True, kind="gwint")  # dno gwintu Ø24
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


def projection_symbol(sh, x, cy, r=3.0):
    """Symbol metody E (ISO 5456-2): stożek ścięty, węższy koniec z lewej, okręgi po prawej."""
    w = 0.5
    sh.poly([(x, cy - r / 2), (x + 2 * r, cy - r), (x + 2 * r, cy + r), (x, cy + r / 2)], w, closed=True)
    cc = x + 2 * r + 1.5 + r
    sh.circle((cc, cy), r, w)
    sh.circle((cc, cy), r / 2, w)
    sh.center_line((x - 1, cy), (cc + r + 0.7, cy), dash=3.0, gap=0.6)
    sh.center_line((cc, cy - r - 0.7), (cc, cy + r + 0.7), dash=3.0, gap=0.6)


def title_cells():
    """Komórki tabliczki: (x0, y0, x1, y1, etykieta)."""
    x0, y0, x1, y1 = TB
    ya, yb = y0 + TB_ROWS[0], y0 + TB_ROWS[0] + TB_ROWS[1]
    return [(x0, y0, x1, ya, "Nazwa"),
            (x0, ya, x0 + 42, yb, "Materiał"), (x0 + 42, ya, x0 + 65, yb, "Skala"),
            (x0 + 65, ya, x1, yb, "Metoda rzutowania"),
            (x0, yb, x0 + 60, y1, "Autor"), (x0 + 60, yb, x1, y1, "Data")]


def title_block(sh, autor, data):
    sh.view = "tabliczka"
    x0, y0, x1, y1 = TB
    sh.line((x0, y0), (x1, y0), THICK, "tabliczka")
    sh.line((x0, y0), (x0, y1), THICK, "tabliczka")
    cells = title_cells()
    for cx0, cy0, cx1, cy1, _ in cells:               # podziały wewnętrzne
        if cy0 > y0:
            sh.line((cx0, cy0), (cx1, cy0), THIN, "tabliczka")
        if cx0 > x0:
            sh.line((cx0, cy0), (cx0, cy1), THIN, "tabliczka")
    values = {"Nazwa": ("Złączka gwintowana", H_NAME), "Materiał": ("mosiądz", H_VALUE),
              "Skala": (f"{S:g}:1", H_VALUE), "Autor": (autor, H_VALUE), "Data": (data, H_VALUE)}
    for cx0, cy0, cx1, cy1, label in cells:
        sh.text(cx0 + 1.2, cy0 + 1.2 + H_LABEL, label, H_LABEL, "start")
        value, h = values.get(label, (None, 0))
        if value:
            sh.text(cx0 + 2, cy1 - max(2.0, sh.descent(value, h) + 0.8), value, h, "start")
    mx0, my0, _, my1, _ = cells[3]
    projection_symbol(sh, mx0 + 5, (my0 + 1.2 + H_LABEL + my1) / 2, r=2.8)
    sh.text(mx0 + 30, my1 - 2, "E", H_VALUE, "start")


# --- strona 2: współrzędne konstrukcyjne ----------------------------------------------
def iso_facts():
    Q, _ = iso_map()
    a, b = Q((0, 0, 0)), Q((L, 0, 0))
    corners = [iso_uv(*p) for p in hex_ring(0)]
    return a, b, corners


def construction(sh):
    """Niebieskie współrzędne w mm od lewej (x) i górnej (y) krawędzi kartki."""
    sh.overlay = True
    W = 0.25
    sh.view = "opis"
    sh.text_block(24, 15, [
        "Strona konstrukcyjna. Niebieskie liczby pionowe: x od lewej krawędzi kartki; „y = …”: "
        "odległość od górnej krawędzi (mm). Liczba przy krawędzi: jej odległość od osi w mm arkusza "
        f"(w skali {S:g}:1 równa średnicy rzeczywistej)."],
        120, H_NOTE, 1.55)

    def x_tick(px, y_from, y_to):
        sh.line((px, y_from), (px, y_to), W, "konstr")
        up = y_to < y_from
        sh.text(px + H_NOTE / 2, y_to + (-0.8 if up else 0.8), fmt(px), H_NOTE,
                "start" if up else "end", rot=-90)

    # widok z przodu
    sh.view = "przód"
    y_t = YF - S * R_COLLAR - 3
    for x in STEPS_X:
        px, py = front(x, REACH_Z[x])
        x_tick(px, py - 0.6, y_t)
    sh.text(X0 - AXIS_OVER - 1, YF - 1, f"y = {fmt(YF)}", H_NOTE, "end")
    for x0, x1, r in PROFILE_Z:                          # dolny obrys
        sh.text(front((x0 + x1) / 2, 0)[0], front(0, -r)[1] + 0.8 + H_NOTE, fmt(S * r), H_NOTE)
    sh.text(front((X_THR + X_HEX) / 2, 0)[0], front(0, -R_HEX / 2)[1] - 0.8, fmt(S * R_HEX / 2), H_NOTE)
    sh.text(front(X_THR / 2, 0)[0], front(0, -R_THR_CORE)[1] - 0.8, fmt(S * R_THR_CORE), H_NOTE)
    sh.text(front(X_THR / 2, 0)[0], front(0, R_BORE1)[1] + 0.8 + H_NOTE, fmt(S * R_BORE1), H_NOTE)
    sh.text(front((X_THR + X_HEX) / 2, 0)[0], front(0, R_BORE2)[1] + 0.8 + H_NOTE, fmt(S * R_BORE2), H_NOTE)
    px, py = front(L, R_ITHR)
    sh.line((px + 0.6, py), (px + 3, py), W, "konstr")
    sh.text(px + 3.6, py + H_NOTE / 2, f"{fmt(S * R_ITHR)} dno gwintu", H_NOTE, "start")

    # widok z góry
    sh.view = "góra"
    y_b = YT + S * R_COLLAR + 3
    for x in STEPS_X:
        px, py = top(x, -REACH_Y[x])
        x_tick(px, py + 0.6, y_b)
    sh.text(X0 - AXIS_OVER - 1, YT - 1, f"y = {fmt(YT)}", H_NOTE, "end")
    sh.text(top(X_HEX / 2, 0)[0], top(0, S_HEX / 2)[1] - 0.8, fmt(S_HEX), H_NOTE)
    for x0, x1, r in PROFILE_Y[2:]:
        sh.text(top((x0 + x1) / 2, 0)[0], top(0, r)[1] - 0.8, fmt(S * r), H_NOTE)
    sh.text(top(X_THR / 2, 0)[0], top(0, R_THR_CORE)[1] + 0.8 + H_NOTE, fmt(S * R_THR_CORE), H_NOTE)

    # widok z lewej
    sh.view = "lewy"
    r_out = S * R_COLLAR + AXIS_OVER
    sh.text(XL + 1.5, YF - r_out - 0.5, f"x = {fmt(XL)}", H_NOTE, "start")
    sh.text(XL + r_out + 1.5, YF + H_NOTE / 2, f"y = {fmt(YF)}", H_NOTE, "start")
    sh.view = "opis"
    sh.text_block(241, 16, [
        "Widok z lewej, promienie od środka:",
        f"kołnierz {fmt(S * R_COLLAR)}", f"szyjka {fmt(S * R_NECK)} (6 łuków)",
        f"naroża sześciokąta {fmt(S * R_HEX)}", f"ściany {fmt(S * S_HEX / 2)} od środka",
        f"gwint {fmt(S * R_THR)}", f"rdzeń {fmt(S * R_THR_CORE)} (3/4 okręgu)", f"otwór {fmt(S * R_BORE1)}"],
        45, H_SMALL)

    # izometria
    sh.view = "izometria"
    Q, _ = iso_map()
    a, b, corners = iso_facts()
    sh.line(a, b, W, "konstr")
    for p in (a, b):
        sh.circle(p, 0.7, W, "konstr")
    for x in (X_THR, X_HEX, X_NECK, X_COLLAR):           # stacje na osi
        c = Q((x, 0, 0))
        sh.line((c[0] - 0.9, c[1] + 1.56), (c[0] + 0.9, c[1] - 1.56), W, "konstr")
    sh.free_label(a, "A", H_NOTE)
    sh.free_label(b, "B", H_NOTE)
    sh.view = "opis"
    # do rysowania ręcznego wystarcza 0,1 mm; twarde spacje trzymają pary razem
    ell = "; ".join(f"Ø{fmt(d)}\u00a0{fmt(d * math.sqrt(1.5) * S_ISO, 1)}×{fmt(d * math.sqrt(0.5) * S_ISO, 1)}"
                    for d in (22, 24, 25, 27, 28, 30)) + "."
    sh.text_block(146, 107, [
        f"Izometria {S_ISO:g}:1. A – środek czoła x = 0: ({fmt(a[0], 1)};\u00a0{fmt(a[1], 1)}), "
        f"B – środek czoła x = {fmt(L)}: ({fmt(b[0], 1)};\u00a0{fmt(b[1], 1)}).",
        f"Oś AB: {fmt(L * S_ISO)} mm pod 30° w dół w prawo; stacje od A: "
        f"{', '.join(fmt(x * S_ISO) for x in (X_THR, X_HEX, X_NECK, X_COLLAR))} mm.",
        "Elipsa okręgu ØD: oś wielka 1,22·D prostopadle do AB (60° do poziomu), oś mała 0,71·D wzdłuż AB:",
        ell,
        "Naroża sześciokąta od środka stacji (w prawo; w dół): "
        + " ".join(f"({fmt(u, 1)};\u00a0{fmt(v, 1)})" for u, v in corners)],
        70, H_SMALL)

    sh.view = "tabliczka"
    sh.text(TB[0] - 1.5, TB[1] + H_NOTE + 0.5, f"({fmt(TB[0])}; {fmt(TB[1])})", H_NOTE, "end")
    sh.overlay = False


# --- strona 3: kolejność rysowania ------------------------------------------------------
def steps_text(a):
    xs = ", ".join(fmt(front(x, 0)[0]) for x in STEPS_X)
    w, h = TB[2] - TB[0], TB[3] - TB[1]
    r_out = S * R_COLLAR + AXIS_OVER
    return [
        ("Ramka i tabliczka",
         f"Ramka linią {fmt(FRAME_W)}: {fmt(FRAME[0])} mm od lewej krawędzi kartki, {fmt(FRAME[1])} mm od "
         f"pozostałych. Tabliczka {fmt(w)}×{fmt(h)} mm w prawym dolnym rogu ramki, lewy górny róg "
         f"({fmt(TB[0])}; {fmt(TB[1])}), wiersze {', '.join(fmt(r) for r in TB_ROWS)} mm."),
        ("Osie symetrii",
         f"Linia cienka punktowa. Widok z przodu: y = {fmt(YF)}, x od {fmt(X0 - AXIS_OVER)} do "
         f"{fmt(front(L, 0)[0] + AXIS_OVER)}. Widok z góry: y = {fmt(YT)}, te same x. Widok z lewej: "
         f"środek ({fmt(XL)}; {fmt(YF)}), osie po {fmt(r_out)} mm w każdą stronę."),
        ("Obrysy i krawędzie",
         f"Linia gruba {fmt(THICK)}. Krawędzie poprzeczne na x = {xs}. Odległość krawędzi od osi = "
         f"średnica rzeczywista (skala {S:g}:1). Widok z lewej: okręgi r {fmt(S * R_COLLAR)}, "
         f"{fmt(S * R_THR)}, {fmt(S * R_BORE1)}, sześciokąt z narożami na r {fmt(S * R_HEX)}, "
         f"łuki r {fmt(S * R_NECK)}."),
        ("Gwinty i przekrój",
         f"Linia cienka: rdzeń gwintu {fmt(S * R_THR_CORE)} od osi (x {fmt(X0)}–{fmt(front(X_THR, 0)[0])}), "
         f"dno gwintu wewnętrznego {fmt(S * R_ITHR)} (x {fmt(front(X_ITHR, 0)[0])}–{fmt(front(L, 0)[0])}), "
         f"w widoku z lewej 3/4 okręgu r {fmt(S * R_THR_CORE)}. Górną połowę widoku z przodu kreskuj "
         f"pod 45° co {fmt(HATCH_STEP)} mm."),
        ("Wymiary",
         f"Linie cienkie {fmt(THIN)}: pierwszy rząd {fmt(DIM_ROW)} mm nad obrysem, drugi {fmt(DIM_ROW)} mm "
         f"wyżej. Strzałki zamknięte {fmt(ARROW_L)} mm, liczby {fmt(H_DIM)} mm nad linią wymiarową. "
         "Wartości przepisz ze strony 1."),
        ("Izometria i tabliczka",
         f"Oś AB od A ({fmt(a[0], 1)}; {fmt(a[1], 1)}), {fmt(L * S_ISO)} mm pod 30° w dół w prawo. Elipsy: "
         "oś wielka 1,22·D, mała 0,71·D (strona 2). Rysuj od tyłu (gwint) do przodu, bez linii "
         "zasłoniętych. Na koniec wypełnij tabliczkę."),
    ]


def steps_page(sh_draw):
    pg = Sheet()
    pg.view = "kroki"
    pg.text(10, 17, "Kolejność rysowania – złączka gwintowana (A4, skala 2:1)", 4.0, "start")
    pg.text(287, 17, "czarne – ten krok, szare – narysowane wcześniej", H_NOTE, "end")
    a, _, _ = iso_facts()
    col_w, gap = 87.0, 8.0
    thumb_w = 80.0
    scale = thumb_w / SHEET_W
    thumb_h = SHEET_H * scale
    for i, (title, body) in enumerate(steps_text(a)):
        cx = 10 + (i % 3) * (col_w + gap)
        ry = 24 + (i // 3) * 89
        pg.text(cx, ry + 4, f"{i + 1}. {title}", 3.5, "start")
        ty = ry + 7
        pg.raw(sh_draw.thumbnail(i + 1, cx, ty, scale))
        pg.segs.extend(((p, q, "miniatura", "kroki", 0) for p, q in zip(
            [(cx, ty), (cx + thumb_w, ty), (cx + thumb_w, ty + thumb_h), (cx, ty + thumb_h)],
            [(cx + thumb_w, ty), (cx + thumb_w, ty + thumb_h), (cx, ty + thumb_h), (cx, ty)])))
        pg.text_block(cx, ty + thumb_h + 4.5, [body], col_w, H_SMALL, 1.7)
    return pg


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


def check_page(sh, include, name, area=FRAME, views=False):
    problems = []
    segs = [s for s in sh.segs if include(s[4])]
    texts = [t for t in sh.texts if include(t[3])]
    fx0, fy0, fx1, fy1 = area
    inside = lambda x, y: fx0 <= x <= fx1 and fy0 <= y <= fy1   # tabliczka dochodzi do ramki
    for a, b, kind, view, _ in segs:
        if kind != "ramka" and not (inside(*a) and inside(*b)):
            problems.append(f"{name}/{view}: linia {kind} poza ramką {a}–{b}")
    for box, s, view, _ in texts:
        if not (inside(box[0], box[1]) and inside(box[2], box[3])):
            problems.append(f"{name}/{view}: tekst '{s}' poza ramką")
    for i, (box, s, view, _) in enumerate(texts):       # kolizje z zapasem 0,3 mm
        big = (box[0] - 0.3, box[1] - 0.3, box[2] + 0.3, box[3] + 0.3)
        for a, b, kind, v, _ in segs:
            if seg_hits_box(a, b, big):
                problems.append(f"{name}/{view}: tekst '{s}' koliduje z linią {kind} ({v})")
                break
        for box2, s2, _, _ in texts[i + 1:]:
            if boxes_overlap(big, box2):
                problems.append(f"{name}/{view}: tekst '{s}' nachodzi na '{s2}'")
    if views:                                            # obszary rzutów razem z wymiarami
        boxes = {}
        pts = [(p, v) for a, b, _, v, _ in segs for p in (a, b)]
        pts += [(p, v) for box, _, v, _ in texts for p in ((box[0], box[1]), (box[2], box[3]))]
        for (x, y), v in pts:
            bx = boxes.setdefault(v, [x, y, x, y])
            bx[:] = [min(bx[0], x), min(bx[1], y), max(bx[2], x), max(bx[3], y)]
        names = [v for v in boxes if v != "ramka"]
        for i, v1 in enumerate(names):
            for v2 in names[i + 1:]:
                if boxes_overlap(boxes[v1], boxes[v2]):
                    problems.append(f"{name}: obszary rzutów '{v1}' i '{v2}' nachodzą na siebie")
        for v, b in boxes.items():
            print(f"  {v:10s} x {b[0]:6.1f}–{b[2]:6.1f}  y {b[1]:6.1f}–{b[3]:6.1f}")
    return problems


def check_geometry():
    problems = []
    if abs(front(0, 0)[1] - left(0, 0)[1]) > 1e-9:
        problems.append("oś widoku z lewej nie jest na wysokości osi widoku z przodu")
    if any(abs(front(x, 0)[0] - top(x, 0)[0]) > 1e-9 for x in STEPS_X):
        problems.append("widok z góry nie jest wyrównany w X z widokiem z przodu")
    if abs(sum(x1 - x0 for x0, x1, _ in PROFILE_Z) - L) > 1e-9:
        problems.append("suma długości odcinków różna od długości całkowitej")
    return problems


def write_page(svg_text, path, width_px=3508):
    path.write_text(svg_text, encoding="utf-8")
    cairosvg.svg2png(url=str(path), write_to=str(path.with_suffix(".png")), output_width=width_px)


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
    construction(sh)
    pg = steps_page(sh)

    drawing = lambda step: step != "K"
    construct = lambda step: step != 5
    pages = [(sh.svg(drawing), args.out / "zlaczka.svg"),
             (sh.svg(construct), args.out / "zlaczka_konstrukcja.svg"),
             (pg.svg(lambda step: True), args.out / "zlaczka_kroki.svg")]
    args.out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        pdfs = []
        for i, (svg_text, path) in enumerate(pages):
            write_page(svg_text, path)
            pdfs.append(str(Path(tmp) / f"{i}.pdf"))
            cairosvg.svg2pdf(url=str(path), write_to=pdfs[-1])
        subprocess.run(["pdfunite", *pdfs, str(args.out / "zlaczka.pdf")], check=True)

    print("Obszary rzutów (strona 1):")
    problems = check_geometry()
    problems += check_page(sh, drawing, "strona 1", views=True)
    problems += check_page(sh, construct, "strona 2")
    problems += check_page(pg, lambda step: True, "strona 3", area=(8.0, 8.0, 289.0, 202.0))
    if problems:
        print("KONTROLA: problemy:")
        for p in problems:
            print("  -", p)
        sys.exit(1)
    print("KONTROLA: OK (wyrównanie, suma 15+25+3+3+3 = 49, ramka, kolizje tekstów na 3 stronach)")


if __name__ == "__main__":
    main()
