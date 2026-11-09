"""Fase 05 · Optimización · cesta10_williams_r
Rejilla de 2 parámetros que la regla YA tiene, SOLO dentro de muestra (datos cortados antes del 11-jul-2022):
  - DISPARA: nivel que el %R cruza hacia arriba (actual -40)
  - SALIDA: semanas hasta salir por tiempo (actual 12)
Fijos: %R de 14 semanas, armado bajo -80, stop 10 %, costes 0,05 % por lado (igual que la fase 04).
Uso: python3 codigo/cesta10_williams_r_optimizar.py
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

TICKERS = ["AAPL", "NVDA", "MSFT", "GOOGL", "AMZN", "MU", "AMD", "TSLA", "META", "WMT"]
N, ARMA, STOP, COSTE = 14, -80, 0.10, 0.0005
CORTE = pd.Timestamp("2022-07-11")
DISPAROS = [-60, -55, -50, -45, -40, -35, -30, -25, -20]
SALIDAS = [6, 8, 10, 12, 14, 16, 18]
ACTUAL = (-40, 12)


def semanal(tk):
    d = pd.read_csv(f"datos/{tk}_1D.csv", parse_dates=["fecha"]).set_index("fecha")
    d = d[d.index < CORTE]                      # el OOS ni siquiera se carga
    w = d.resample("W-FRI").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    hh, ll = w["high"].rolling(N).max(), w["low"].rolling(N).min()
    w["wr"] = (hh - w["close"]) / (hh - ll) * -100
    return w


SEM = {tk: semanal(tk) for tk in TICKERS}


def senales(wr, dispara):
    armada, out = False, np.zeros(len(wr), bool)
    for i in range(len(wr)):
        if np.isnan(wr[i]):
            continue
        if wr[i] < ARMA:
            armada = True
        elif armada and i > 0 and wr[i - 1] <= dispara < wr[i]:
            out[i], armada = True, False
    return out


def operaciones(dispara, salida):
    rets = []
    for w in SEM.values():
        o, l, c = w["open"].to_numpy(), w["low"].to_numpy(), w["close"].to_numpy()
        s = senales(w["wr"].to_numpy(), dispara)
        i = 0
        while i < len(w) - 1:
            if not s[i]:
                i += 1
                continue
            e = i + 1
            if e + salida - 1 >= len(w):        # no cabe entera antes del corte: no se cuenta
                break
            ent, nivel = o[e], o[e] * (1 - STOP)
            for k in range(e, e + salida):
                if l[k] <= nivel:
                    px = o[k] if (k > e and o[k] < nivel) else nivel
                    break
                if k == e + salida - 1:
                    px = c[k]
            rets.append(px * (1 - COSTE) / (ent * (1 + COSTE)) - 1)
            i = k
    r = np.array(rets)
    pf = r[r > 0].sum() / -r[r < 0].sum() if (r < 0).any() else np.inf
    return pf, len(r)


pf = pd.DataFrame(index=SALIDAS, columns=DISPAROS, dtype=float)
n = pf.copy()
for d in DISPAROS:
    for s in SALIDAS:
        pf.loc[s, d], n.loc[s, d] = operaciones(d, s)

print(f"Rejilla: {len(DISPAROS)} niveles de disparo × {len(SALIDAS)} salidas = {pf.size} combinaciones (solo IS)\n")
print("Factor de beneficio (filas = semanas de salida, columnas = nivel de disparo):")
print(pf.round(2).to_string())
print("\nOperaciones:")
print(n.astype(int).to_string())

d0, s0 = ACTUAL
pf0 = pf.loc[s0, d0]
di, si = DISPAROS.index(d0), SALIDAS.index(s0)
vecinos = [(SALIDAS[a], DISPAROS[b]) for a in range(si - 1, si + 2) for b in range(di - 1, di + 2)
           if (a, b) != (si, di) and 0 <= a < len(SALIDAS) and 0 <= b < len(DISPAROS)]
print(f"\nCombinación actual: disparo {d0}, salida {s0} semanas → FB {pf0:.2f}, {int(n.loc[s0, d0])} operaciones")
ok_total = True
for s, d in vecinos:
    v_pf, v_n = pf.loc[s, d], int(n.loc[s, d])
    ok = v_pf >= 1.3 and v_n >= 30 and v_pf >= 0.7 * pf0
    ok_total &= ok
    print(f"  vecino disparo {d}, salida {s}: FB {v_pf:.2f} ({v_pf / pf0 * 100:.0f} % del actual), {v_n} ops  {'✓' if ok else '✕'}")
print(f"\n{'MESETA' if ok_total else 'PICO'} (umbral: vecinos con FB ≥ 1,3, ≥ 30 ops y ≥ 70 % del FB actual)")
print(f"Combinaciones de toda la rejilla con FB ≥ 1,3 y ≥ 30 ops: {((pf >= 1.3) & (n >= 30)).sum().sum()} de {pf.size}")

fig, ax = plt.subplots(figsize=(9, 5.5))
im = ax.imshow(pf.to_numpy(), cmap="RdYlGn", vmin=0.8, vmax=max(3.0, np.nanmax(pf.to_numpy())), aspect="auto")
ax.set_xticks(range(len(DISPAROS)), [str(x) for x in DISPAROS])
ax.set_yticks(range(len(SALIDAS)), [str(x) for x in SALIDAS])
ax.set_xlabel("Nivel de disparo del %R (cruce hacia arriba)")
ax.set_ylabel("Semanas hasta la salida")
for a in range(len(SALIDAS)):
    for b in range(len(DISPAROS)):
        ax.text(b, a, f"{pf.iloc[a, b]:.2f}", ha="center", va="center", fontsize=8)
ax.add_patch(plt.Rectangle((di - 0.5, si - 0.5), 1, 1, fill=False, lw=3, ec="black"))
ax.set_title("Cesta 10 · %R semanal · factor de beneficio dentro de muestra (2010 – jul 2022)\nrecuadro = parámetros de la fase 04")
fig.colorbar(im, ax=ax, label="Factor de beneficio")
fig.tight_layout()
fig.savefig("resultados/cesta10_williams_r_meseta.png", dpi=130)
print("\nMapa: resultados/cesta10_williams_r_meseta.png")
