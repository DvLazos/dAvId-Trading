"""Fase 04 · Backtest · nvda_media_toque
Regla (pseudocódigo en fichas/nvda_media_toque.md, fase 03), probada tal cual:
  - SMA200 = media de los últimos 200 cierres de 4H.
  - SEÑAL en la vela t: mínimo ≤ SMA200 ≤ máximo y cierre > SMA200.
  - Si estoy fuera y hay SEÑAL: COMPRA a la apertura de la vela t+1.
  - Salgo al cierre de la vela 20 contando la de entrada como la 1.
  - Una operación a la vez; las señales mientras estoy dentro se ignoran.
  - Costes: 0,05 % por lado (comisión + deslizamiento), 0,10 % ida y vuelta.
  - Todo el capital en cada operación, sin apalancamiento, con interés compuesto.
Uso: python3 codigo/nvda_media_toque_backtest.py [CSV]
"""
import sys
import numpy as np
import pandas as pd

CSV = sys.argv[1] if len(sys.argv) > 1 else "datos/NVDA_4H_2016_2026.csv"
SMA_N, BARRAS, COSTE_LADO = 200, 20, 0.0005
INICIO = "2017-01-01"

df = pd.read_csv(CSV, parse_dates=["fecha_ny"]).set_index("fecha_ny")
df["sma"] = df["close"].rolling(SMA_N).mean()
df["senal"] = (df["low"] <= df["sma"]) & (df["sma"] <= df["high"]) & (df["close"] > df["sma"])

o, c, s = df["open"].to_numpy(), df["close"].to_numpy(), df["senal"].to_numpy()
fechas = df.index
ini = np.searchsorted(fechas, pd.Timestamp(INICIO))

ops = []
i = ini
while i < len(df) - 1:
    if s[i]:
        e = i + 1                          # vela de entrada
        x = min(e + BARRAS - 1, len(df) - 1)  # vela de salida (cierre)
        pe, px = o[e] * (1 + COSTE_LADO), c[x] * (1 - COSTE_LADO)
        ops.append({"entrada": fechas[e], "salida": fechas[x], "e": e, "x": x,
                    "p_ent": o[e], "p_sal": c[x], "ret": px / pe - 1,
                    "abierta": x - e + 1 < BARRAS})
        i = x                              # tras salir, la vela de salida ya puede dar señal
        continue
    i += 1
ops = pd.DataFrame(ops)

# Curva de capital vela a vela (marcando a mercado) para la caída máxima
def curva(desde, hasta):
    sub = ops[(ops["entrada"] >= desde) & (ops["entrada"] <= hasta)]
    eq, valores = 1.0, []
    for _, t in sub.iterrows():
        base = eq / (t["p_ent"] * (1 + COSTE_LADO))
        for k in range(t["e"], t["x"] + 1):
            precio = c[k] * (1 - COSTE_LADO) if k == t["x"] else c[k]
            valores.append(base * precio)
        eq = valores[-1]
    v = np.array([1.0] + valores)
    dd = (v / np.maximum.accumulate(v) - 1).min()
    return sub, eq, dd

def pf(r):
    g, p = r[r > 0].sum(), -r[r < 0].sum()
    return g / p if p > 0 else float("inf")

def informe(nombre, desde, hasta):
    # hasta incluye todo ese día (antes cortaba a las 00:00 y dejaba fuera sus entradas)
    sub, eq, dd = curva(pd.Timestamp(desde), pd.Timestamp(hasta) + pd.Timedelta(hours=23, minutes=59))
    r = sub["ret"]
    sin_mejor = r.drop(r.idxmax()) if len(r) > 1 else r
    pf_, pf_sm = pf(r), pf(sin_mejor)
    bh = df.loc[desde:hasta, "close"]
    print(f"\n== {nombre}: {desde} -> {hasta} ==")
    print(f"Operaciones: {len(r)}  ganadoras {(r > 0).mean()*100:.0f} %  media {r.mean()*100:+.2f} %"
          f"  mejor {r.max()*100:+.2f} %  peor {r.min()*100:+.2f} %"
          + ("  (la última sigue abierta: cerrada al último cierre)" if sub["abierta"].any() else ""))
    print(f"Capital final x{eq:.2f}  |  comprar y mantener x{bh.iloc[-1]/bh.iloc[0]:.2f}"
          f"  |  tiempo dentro {sub.apply(lambda t: t['x']-t['e']+1, axis=1).sum()/len(bh)*100:.0f} %")
    marcas = [("Factor de beneficio ≥ 1,3", pf_ >= 1.3, f"{pf_:.2f}"),
              ("Al menos 30 operaciones", len(r) >= 30, f"{len(r)}"),
              ("Caída máxima < 20 %", dd > -0.20, f"{dd*100:.1f} %"),
              ("FB sin la mejor operación > 1", pf_sm > 1, f"{pf_sm:.2f}")]
    for txt, ok, val in marcas:
        print(f"  {'✓' if ok else '✕'} {txt}: {val}")
    print(f"  Veredicto: {sum(ok for _, ok, _ in marcas)}/4")
    print("  Por año:", ", ".join(f"{a}: {len(g)} ops {g['ret'].sum()*100:+.1f} %"
                                for a, g in sub.groupby(sub['entrada'].dt.year)))

ultimo = str(fechas[-1].date())
informe("DENTRO DE MUESTRA (IS del trader)", "2017-01-01", "2021-12-31")
informe("FUERA DE MUESTRA (OOS del trader)", "2022-01-01", ultimo)
# Corte del método: 70 % más antiguo / 30 % más reciente, desde 2017
f17 = fechas[ini:]
corte = f17[int(len(f17) * 0.7)]
informe("OOS 30 % del método", str(corte.date()), ultimo)
print(f"\n(corte 70/30 del método: {corte})")
ops.drop(columns=["e", "x"]).to_csv("resultados/nvda_media_toque_operaciones.csv", index=False)
