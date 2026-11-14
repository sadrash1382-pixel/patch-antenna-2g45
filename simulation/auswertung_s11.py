#!/usr/bin/env python3
"""
Wertet einen CST-Export (XY Data Exchange Format, S11 komplex) aus:
Resonanzfrequenz, Tiefe, Eingangsimpedanz und -10-dB-Bandbreite je Lauf,
dazu ein Plot aller Kurven.

Aufruf:  python auswertung_s11.py results/s11_sweep_y0.txt
"""
import re
import sys

import numpy as np


def lese_cst(pfad):
    """Gibt eine Liste von (parameter_dict, f_GHz, s11_komplex, z_ref) zurück."""
    laeufe = []
    for blk in open(pfad).read().split("Curvelabel")[1:]:
        par = dict(kv.split("=") for kv in re.search(r"Parameters\s*=\s*\{(.*?)\}", blk).group(1).split("; "))
        par = {k.strip(): float(v) for k, v in par.items()}
        d = np.array([l.split() for l in blk.splitlines() if re.match(r"^[\d.]+\t", l)], float)
        laeufe.append((par, d[:, 0], d[:, 1] + 1j * d[:, 2], d[:, 3]))
    return laeufe


def kennwerte(f, s, zref):
    db = 20 * np.log10(np.abs(s))
    i = db.argmin()
    z = zref[i] * (1 + s[i]) / (1 - s[i])
    band = f[db < -10]
    bw = (band.max() - band.min()) * 1000 if len(band) else 0.0
    return f[i], db[i], z, bw


def main():
    pfad = sys.argv[1] if len(sys.argv) > 1 else "results/s11_sweep_y0.txt"
    laeufe = lese_cst(pfad)

    print(f"{'L/mm':>6} {'y0/mm':>6} {'f_res/GHz':>10} {'S11/dB':>7} {'Z/Ohm':>14} {'BW/MHz':>7}")
    for par, f, s, zref in laeufe:
        fr, db, z, bw = kennwerte(f, s, zref)
        print(f"{par['L']:6.2f} {par['y0']:6.2f} {fr:10.4f} {db:7.1f} {z.real:7.1f}{z.imag:+6.1f}j {bw:7.0f}")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ink, muted, grid = "#0b0b0b", "#52514e", "#e6e8eb"
    sweep = [l for l in laeufe if l[0]["L"] == laeufe[-1][0]["L"]]
    start = [l for l in laeufe if l[0]["L"] != laeufe[-1][0]["L"]]
    blau = plt.get_cmap("Blues")(np.linspace(0.35, 0.95, len(sweep)))

    fig, ax = plt.subplots(figsize=(7.5, 4.4), dpi=150)
    for par, f, s, _ in start:
        ax.plot(f, 20 * np.log10(np.abs(s)), color=muted, lw=1.5, ls="--",
                label=f"Startwert: L = {par['L']:g} mm, y0 = {par['y0']:g} mm")
    for farbe, (par, f, s, _) in zip(blau, sweep):
        ax.plot(f, 20 * np.log10(np.abs(s)), color=farbe, lw=2, label=f"y0 = {par['y0']:g} mm")
    ax.axhline(-10, color=muted, lw=0.8)
    ax.text(2.61, -9.5, "−10 dB", color=muted, fontsize=8)
    ax.axvline(2.45, color=muted, lw=0.8, ls=":")
    ax.set_xlim(2.2, 2.7)
    ax.set_xlabel("Frequenz [GHz]", color=ink)
    ax.set_ylabel("|S11| [dB]", color=ink)
    ax.set_title(f"S11 über Inset-Tiefe y0 (L = {sweep[0][0]['L']:g} mm, CST-Simulation)",
                 color=ink, fontsize=10, loc="left")
    ax.grid(True, color=grid, lw=0.8)
    ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    for sp in ("left", "bottom"):
        ax.spines[sp].set_color(muted)
    ax.tick_params(colors=muted)
    ax.legend(frameon=False, fontsize=8, loc="lower left")
    fig.tight_layout()
    ziel = pfad.rsplit(".", 1)[0] + ".png"
    fig.savefig(ziel, facecolor="white")
    print(f"\nPlot: {ziel}")


if __name__ == "__main__":
    main()
