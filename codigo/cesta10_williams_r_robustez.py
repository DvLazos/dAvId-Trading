"""Fase 06 · Robustez · cesta10_williams_r
Regla tal cual (fase 05): %R 14 semanas, armado < -80, disparo al cruzar -40, salida 12 semanas, stop 10 %.
  a. Costes ×2 en el OOS                       → pasa si FB ≥ 1,1
  b. Monte Carlo del orden (1.000)             → pasa si la caída del percentil 95 < 30 %
  c. Remuestreo con reemplazo (1.000)          → pasa si el FB del percentil 5 > 1
  d. Años malos (todo el periodo)              → pasa si gana ≥ la mitad de los años y FB sin el mejor año > 1
  Extra: sesgo de selección → la misma regla en las 10 mayores del QQQ al 12-oct-2022 (Insider Monkey).
Semilla fija 42. Uso: python3 codigo/cesta10_williams_r_robustez.py
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HOY = ["AAPL", "NVDA", "MSFT", "GOOGL", "AMZN", "MU", "AMD", "TSLA", "META", "WMT"]
OCT2022 = ["AAPL", "MSFT", "AMZN", "TSLA", "GOOGL", "META", "NVDA", "PEP", "COST", "AVGO"]
N, ARMA, DISPARA, SALIDA, STOP, COSTE = 14, -80, -40, 12, 0.10, 0.0005
CORTE = pd.Timestamp("2022-07-11")
SIMS, PESO = 1000, 0.10                    # cada operación usa el 10 % del capital (una cuenta por acción)
rng = np.random.default_rng(42)


def semanal(tk):
    d = pd.read_csv(f"datos/{tk}_1D.csv", parse_dates=["fecha"]).set_index("fecha")
    w = d.resample("W-FRI").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    hh, ll = w["high"].rolling(N).max(), w["low"].rolling(N).min()
    w["wr"] = (hh - w["close"]) / (hh - ll) * -100
    armada, s, wr = False, np.zeros(len(w), bool), w["wr"].to_numpy()
    for i in range(len(w)):
        if np.isnan(wr[i]):
            continue
        if wr[i] < ARMA:
            armada = True
        elif armada and i > 0 and wr[i - 1] <= DISPARA < wr[i]:
            s[i], armada = True, False
    w["senal"] = s
    return w


def operaciones(tickers, coste):
    ops = []
    for tk in tickers:
        w = SEM[tk]
        o, l, c, s, f = w["open"].to_numpy(), w["low"].to_numpy(), w["close"].to_numpy(), w["senal"].to_numpy(), w.index
        i = 0
        while i < len(w) - 1:
            if not s[i]:
                i += 1
                continue
            e = i + 1
            ent, nivel = o[e], o[e] * (1 - STOP)
            x = px = None
            for k in range(e, min(e + SALIDA, len(w))):
                if l[k] <= nivel:
                    x, px = k, (o[k] if (k > e and o[k] < nivel) else nivel)
                    break
                if k == e + SALIDA - 1:
                    x, px = k, c[k]
            if x is None:
                x, px = len(w) - 1, c[-1]
            ops.append(dict(tk=tk, entrada=f[e], salida=f[x], e=e, x=x, p_ent=ent, p_sal=px,
                            ret=px * (1 - coste) / (ent * (1 + coste)) - 1))
            i = x
    return pd.DataFrame(ops).sort_values("entrada").reset_index(drop=True)


def pf(r):
    r = np.asarray(r)
    p = -r[r < 0].sum()
    return r[r > 0].sum() / p if p > 0 else np.inf


def caida_cartera(sub, tickers, d0, d1, coste):
    """Caída máxima de 10 cuentas iguales marcadas a mercado cada semana (igual que la fase 04)."""
    semanas = pd.DatetimeIndex(sorted(set().union(*[set(SEM[t].index[(SEM[t].index >= d0) & (SEM[t].index < d1)]) for t in tickers])))
    total = pd.Series(0.0, index=semanas)
    for tk in tickers:
        w, eq = SEM[tk], 0.1
        cuenta = pd.Series(np.nan, index=semanas)
        cuenta.iloc[0] = eq
        for _, t in sub[sub["tk"] == tk].iterrows():
            acc = eq / (t["p_ent"] * (1 + coste))
            for k in range(t["e"], t["x"] + 1):
                if w.index[k] in cuenta.index:
                    cuenta[w.index[k]] = acc * (t["p_sal"] * (1 - coste) if k == t["x"] else w["close"].iloc[k])
            eq = acc * t["p_sal"] * (1 - coste)
        total += cuenta.ffill()
    return (total / total.cummax() - 1).min()


def caida_secuencia(r):
    eq = np.cumprod(1 + PESO * np.asarray(r))
    eq = np.concatenate([[1.0], eq])
    return (eq / np.maximum.accumulate(eq) - 1).min()


SEM = {tk: semanal(tk) for tk in sorted(set(HOY + OCT2022))}
FIN = max(w.index[-1] for w in SEM.values()) + pd.Timedelta(days=1)

ops1 = operaciones(HOY, COSTE)
oos = ops1[ops1["entrada"] >= CORTE]
print(f"Comprobación fase 04: {len(oos)} operaciones OOS, FB {pf(oos['ret']):.2f} (debe ser 68 y 1,99)\n")
res = []

# a. Costes ×2
ops2 = operaciones(HOY, 2 * COSTE)
oos2 = ops2[ops2["entrada"] >= CORTE]
pf2 = pf(oos2["ret"])
res.append(("a. Costes ×2 (0,10 % por lado): FB OOS ≥ 1,1", pf2 >= 1.1, f"FB {pf2:.2f}"))

# b. Monte Carlo del orden
r = oos["ret"].to_numpy()
dd_real = caida_secuencia(r)
dds = np.array([caida_secuencia(rng.permutation(r)) for _ in range(SIMS)])
p95 = np.percentile(dds, 5)                          # caídas son negativas: el 95 % cae menos que esto
res.append(("b. Monte Carlo del orden: caída p95 < 30 %", p95 > -0.30,
            f"p95 {p95*100:.1f} % (orden real {dd_real*100:.1f} %, peor de 1.000 {dds.min()*100:.1f} %)"))

# c. Remuestreo
pfs = np.array([pf(rng.choice(r, size=len(r), replace=True)) for _ in range(SIMS)])
p5 = np.percentile(pfs, 5)
res.append(("c. Remuestreo: FB p5 > 1", p5 > 1, f"p5 {p5:.2f} (mediana {np.median(pfs):.2f})"))

# d. Años malos (todo el periodo)
por_año = ops1.groupby(ops1["entrada"].dt.year)["ret"]
suma = por_año.sum()
ganan = (suma > 0).sum()
mejor = suma.idxmax()
pf_sin = pf(ops1[ops1["entrada"].dt.year != mejor]["ret"])
res.append(("d. Años malos: ≥ mitad de años ganan y FB sin el mejor año > 1",
            ganan >= len(suma) / 2 and pf_sin > 1,
            f"{ganan} de {len(suma)} años ganan; sin {mejor}: FB {pf_sin:.2f}"))

print("== Fase 06 · 4 pruebas ==")
for txt, ok, v in res:
    print(f"  {'✓' if ok else '✕'} {txt}: {v}")
print(f"  Robustez: {sum(ok for _, ok, _ in res)}/4")
print("\nPor año (suma de retornos por operación, nº ops):")
print("  " + ", ".join(f"{a}: {suma[a]*100:+.0f} % ({por_año.count()[a]})" for a in suma.index))

# Extra: sesgo de selección
print("\n== Extra · sesgo de selección: las 10 mayores del QQQ al 12-oct-2022 ==")
opsx = operaciones(OCT2022, COSTE)
ox = opsx[opsx["entrada"] >= CORTE]
rx = ox["ret"]
ddx = caida_cartera(ox, OCT2022, CORTE, FIN, COSTE)
bh = np.mean([SEM[t].loc[SEM[t].index >= CORTE, "close"].iloc[-1] / SEM[t].loc[SEM[t].index >= CORTE, "close"].iloc[0] for t in OCT2022])
m = [("FB ≥ 1,3", pf(rx) >= 1.3, f"{pf(rx):.2f}"), ("≥ 30 operaciones", len(rx) >= 30, f"{len(rx)}"),
     ("Caída máxima < 20 %", ddx > -0.20, f"{ddx*100:.1f} %"),
     ("FB sin la mejor > 1", pf(rx.drop(rx.idxmax())) > 1, f"{pf(rx.drop(rx.idxmax())):.2f}")]
for txt, ok, v in m:
    print(f"  {'✓' if ok else '✕'} {txt}: {v}")
print(f"  OOS: {sum(ok for _, ok, _ in m)}/4 · ganadoras {(rx > 0).mean()*100:.0f} % · media {rx.mean()*100:+.2f} % · comprar y mantener esa cesta x{bh:.2f}")
print("  Por acción:", ", ".join(f"{k}: {len(g)}/{g['ret'].mean()*100:+.1f}%" for k, g in ox.groupby("tk")))

# Gráficas
fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 5))
for _ in range(200):
    a1.plot(np.cumprod(1 + PESO * rng.permutation(r)), color="#9aa7b8", lw=0.6, alpha=0.35)
a1.plot(np.cumprod(1 + PESO * r), color="#c0392b", lw=2.2, label="orden real")
a1.set_title("Monte Carlo del orden · OOS (200 de 1.000 barajas)")
a1.set_xlabel("Operación nº"); a1.set_ylabel("Capital (10 % por operación)"); a1.legend()
colores = ["#2e7d32" if v > 0 else "#c62828" for v in suma.values]
a2.bar([str(a) for a in suma.index], suma.values * 100, color=colores)
a2.axvline(list(suma.index).index(CORTE.year) - 0.5, color="black", ls="--", lw=1)
a2.text(list(suma.index).index(CORTE.year) - 0.4, a2.get_ylim()[1] * 0.9, "corte OOS", fontsize=8)
a2.set_title("Resultado por año (suma de retornos por operación)")
a2.set_ylabel("%"); a2.tick_params(axis="x", rotation=60)
fig.tight_layout()
fig.savefig("resultados/cesta10_williams_r_robustez.png", dpi=130)
print("\nGráficas: resultados/cesta10_williams_r_robustez.png")
