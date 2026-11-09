"""Fase 02 · AED · nas100_media_toque
¿Comprar cuando el mínimo de la vela 4H toca la SMA 200 (y cierra por encima) da mejor
retorno a 1, 5 y 20 velas que una vela cualquiera? Solo IS 2017-2021.
2016 se usa SOLO para calcular la media (calentamiento), no se mide.
Uso: python3 codigo/nas100_media_toque_aed.py
"""
import sys
import numpy as np
import pandas as pd

# Otro activo (huella), misma regla sin cambios: python3 codigo/nas100_media_toque_aed.py datos/NVDA_4H_2016_2021.csv
CSV = sys.argv[1] if len(sys.argv) > 1 else "datos/NDX_4H_2016_2021.csv"
SMA_N = 200
HORIZONTES = [1, 5, 20]
IS_INI, IS_FIN = "2017-01-01", "2021-12-31 23:59"

df = pd.read_csv(CSV, parse_dates=["fecha_ny"]).set_index("fecha_ny")
df["sma"] = df["close"].rolling(SMA_N).mean()
df["toque"] = (df["low"] <= df["sma"]) & (df["sma"] <= df["high"]) & (df["close"] > df["sma"])
df["encima"] = df["close"] > df["sma"]
for k in HORIZONTES:
    df[f"r{k}"] = df["close"].shift(-k) / df["close"] - 1  # retorno de cierre a cierre

is_ = df.loc[IS_INI:IS_FIN].dropna(subset=["sma"] + [f"r{k}" for k in HORIZONTES])
print(f"Velas IS medibles: {len(is_)}  ({is_.index[0]} -> {is_.index[-1]})")

def resumen(nombre, sub):
    fila = [f"{nombre:<26} n={len(sub):>4}"]
    for k in HORIZONTES:
        r = sub[f"r{k}"]
        fila.append(f"r{k}: media {r.mean()*100:+.3f}%  >0 {(r > 0).mean()*100:4.1f}%")
    print(" | ".join(fila))

print("\n== Retorno tras la condición vs líneas base ==")
resumen("Toque SMA200 (señal)", is_[is_["toque"]])
resumen("Todas las velas (base)", is_)
resumen("Velas sobre la SMA (base 2)", is_[is_["encima"]])

# Señales no encimadas: una operación a la vez (20 velas), como la regla
idx = np.flatnonzero(is_["toque"].to_numpy())
indep, ultimo = [], -10**9
for i in idx:
    if i - ultimo > 20:
        indep.append(i); ultimo = i
ind = is_.iloc[indep]
r20 = ind["r20"]
t = r20.mean() / (r20.std(ddof=1) / np.sqrt(len(r20))) if len(r20) > 1 else float("nan")
print(f"\n== Señales independientes (sin solaparse 20 velas) ==")
print(f"n={len(ind)}  r20 media {r20.mean()*100:+.3f}%  >0 {(r20 > 0).mean()*100:.1f}%  t≈{t:.2f}")

print("\n== Por año: r20 medio (señal vs todas las velas) y nº de señales independientes ==")
for año in range(2017, 2022):
    s = is_[is_["toque"] & (is_.index.year == año)]["r20"]
    b = is_[is_.index.year == año]["r20"]
    si = ind[ind.index.year == año]["r20"]
    gana = "SÍ" if len(s) and s.mean() > b.mean() else "no"
    print(f"{año}: señal {s.mean()*100 if len(s) else float('nan'):+.3f}% (n={len(s)})  "
          f"base {b.mean()*100:+.3f}%  independientes={len(si)}  supera base: {gana}")
