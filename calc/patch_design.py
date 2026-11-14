#!/usr/bin/env python3
"""
Entwurfsrechnung für eine rechteckige Mikrostreifen-Patchantenne mit Inset-Speisung.

Transmission-Line-Modell nach Balanis, "Antenna Theory", Kap. 14.
Liefert Startwerte für die Feldsimulation, keine Endmaße: Die Resonanzfrequenz
trifft das Modell auf etwa 1-2 %, die Inset-Tiefe deutlich schlechter.

Aufruf:
    python patch_design.py                 # 2,45 GHz, FR-4 1,6 mm
    python patch_design.py --f 5.8e9 --er 3.66 --h 0.508e-3
"""
import argparse

import numpy as np
from scipy.integrate import quad
from scipy.optimize import brentq
from scipy.special import j0

C0 = 299_792_458.0


def patch(f, er, h):
    """Gibt W, L, eps_eff, dL, R_Kante, y0(50 Ohm) zurück (SI-Einheiten)."""
    W = C0 / (2 * f) * np.sqrt(2 / (er + 1))
    ee = (er + 1) / 2 + (er - 1) / 2 * (1 + 12 * h / W) ** -0.5
    dL = 0.412 * h * (ee + 0.3) * (W / h + 0.264) / ((ee - 0.258) * (W / h + 0.8))
    L = C0 / (2 * f * np.sqrt(ee)) - 2 * dL

    # Strahlungsleitwert eines Schlitzes (G1) und Koppelleitwert (G12)
    k0 = 2 * np.pi * f / C0
    kern = lambda th: np.sin(k0 * W / 2 * np.cos(th)) ** 2 / np.cos(th) ** 2 * np.sin(th) ** 3
    G1 = quad(kern, 0, np.pi)[0] / (120 * np.pi ** 2)
    G12 = quad(lambda th: kern(th) * j0(k0 * L * np.sin(th)), 0, np.pi)[0] / (120 * np.pi ** 2)
    R_kante = 1 / (2 * (G1 + G12))

    # Inset-Tiefe für 50 Ohm: R(y0) = R_Kante * cos^2(pi*y0/L)
    y0 = L / np.pi * np.arccos(np.sqrt(50 / R_kante))
    return W, L, ee, dL, R_kante, y0


def leitungsbreite(z0, er, h):
    """Breite einer Mikrostreifenleitung mit Wellenwiderstand z0 (Hammerstad, W/h > 1)."""
    def z(w):
        e = (er + 1) / 2 + (er - 1) / 2 * (1 + 12 * h / w) ** -0.5
        u = w / h
        return 120 * np.pi / (np.sqrt(e) * (u + 1.393 + 0.667 * np.log(u + 1.444)))
    return brentq(lambda w: z(w) - z0, 0.2 * h, 10 * h)


def main():
    p = argparse.ArgumentParser(description="Entwurfsrechnung Patchantenne")
    p.add_argument("--f", type=float, default=2.45e9, help="Frequenz [Hz]")
    p.add_argument("--er", type=float, default=4.4, help="relative Permittivität")
    p.add_argument("--h", type=float, default=1.6e-3, help="Substratdicke [m]")
    a = p.parse_args()

    print(f"f = {a.f / 1e9:.3f} GHz, h = {a.h * 1e3:.2f} mm, lambda0 = {C0 / a.f * 1e3:.1f} mm\n")
    print(f"{'eps_r':>6} {'W/mm':>7} {'L/mm':>7} {'eps_eff':>8} {'dL/mm':>6} {'R_Kante/Ohm':>12} {'y0/mm':>6} {'w50/mm':>7}")
    for er in (a.er - 0.2, a.er, a.er + 0.2):
        W, L, ee, dL, R, y0 = patch(a.f, er, a.h)
        w50 = leitungsbreite(50, er, a.h)
        print(f"{er:6.2f} {W * 1e3:7.2f} {L * 1e3:7.2f} {ee:8.3f} {dL * 1e3:6.2f} {R:12.0f} {y0 * 1e3:6.2f} {w50 * 1e3:7.2f}")


if __name__ == "__main__":
    main()
