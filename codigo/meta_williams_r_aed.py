"""Fase 02 · AED · meta_williams_r
¿Cuando el Williams %R(14) diario viene de sobreventa (< -80) y cruza -40 hacia arriba,
el retorno a 1, 5, 20 y 60 sesiones es mejor que el de un día cualquiera?
Solo se mira el 70 % más antiguo (dentro de muestra). El 30 % reciente se reserva para la fase 04.
Uso: python3 codigo/meta_williams_r_aed.py            (diario)
     python3 codigo/meta_williams_r_aed.py semanal    (velas semanales armadas con el diario)
"""
import sys
import numpy as np
import pandas as pd

CSV, N, ARMA, DISPARA = "datos/META_1D.csv", 14, -80, -40
SEMANAL = len(sys.argv) > 1 and sys.argv[1] == "semanal"
HORIZONTES = [1, 4, 12, 26] if SEMANAL else [1, 5, 20, 60]
SALIDA = 12 if SEMANAL else 60          # 12 semanas ≈ 60 sesiones
CORTE_OOS = pd.Timestamp("2022-07-11")  # el mismo corte del estudio diario: el OOS sigue sin mirarse

df = pd.read_csv(CSV, parse_dates=["fecha"]).set_index("fecha")
if SEMANAL:
    # semana de lunes a viernes; la vela se fecha el viernes (o el último día con mercado)
    df = df.resample("W-FRI").agg({"open": "first", "high": "max", "low": "min",
                                   "close": "last", "volume": "sum"}).dropna()
hh, ll = df["high"].rolling(N).max(), df["low"].rolling(N).min()
df["wr"] = (hh - df["close"]) / (hh - ll) * -100

# Señal: se arma al bajar de -80; dispara cuando cruza -40 hacia arriba; luego se desarma
armada, senal = False, []
wr = df["wr"].to_numpy()
for i in range(len(df)):
    s = False
    if not np.isnan(wr[i]):
        if wr[i] < ARMA:
            armada = True
        elif armada and i > 0 and wr[i - 1] <= DISPARA < wr[i]:
            s, armada = True, False
    senal.append(s)
df["senal"] = senal
for k in HORIZONTES:
    df[f"r{k}"] = df["close"].shift(-k) / df["close"] - 1

validas = df.dropna(subset=["wr"])
corte = CORTE_OOS
# los retornos futuros no pueden usar velas del OOS
for k in HORIZONTES:
    fin = validas.index.to_series().shift(-k)
    validas.loc[fin >= corte, f"r{k}"] = np.nan
is_ = validas[validas.index < corte].dropna(subset=[f"r{k}" for k in HORIZONTES])
unidad = "semanas" if SEMANAL else "días"
print(f"IS: {is_.index[0].date()} -> {is_.index[-1].date()}  ({len(is_)} {unidad}). OOS reservado desde {corte.date()}")

def fila(nombre, sub):
    partes = [f"{nombre:<22} n={len(sub):>4}"]
    for k in HORIZONTES:
        r = sub[f"r{k}"]
        partes.append(f"r{k} {r.mean()*100:+.2f}% (>0 {(r > 0).mean()*100:.0f}%)")
    print(" | ".join(partes))

print()
fila("Señal %R", is_[is_["senal"]])
fila("Todos los días (base)", is_)

# Independientes: una operación a la vez, SALIDA velas
col = f"r{SALIDA}"
idx, ult, ind = np.flatnonzero(is_["senal"].to_numpy()), -10**9, []
for i in idx:
    if i - ult >= SALIDA:
        ind.append(i); ult = i
rs = is_.iloc[ind][col]
t = rs.mean() / (rs.std(ddof=1) / np.sqrt(len(rs))) if len(rs) > 1 else float("nan")
print(f"\nIndependientes (sin solaparse {SALIDA} velas): n={len(rs)}  {col} {rs.mean()*100:+.2f}%"
      f"  >0 {(rs > 0).mean()*100:.0f}%  t≈{t:.2f}")
print("Fechas de señal:", ", ".join(str(d.date()) for d in is_.index[is_["senal"]]))

print(f"\nPor año ({col} medio de la señal vs base):")
for a in sorted(set(is_.index.year)):
    s = is_[is_["senal"] & (is_.index.year == a)][col]
    b = is_[is_.index.year == a][col]
    print(f"{a}: señal {s.mean()*100 if len(s) else float('nan'):+.2f}% (n={len(s)})  base {b.mean()*100:+.2f}%"
          f"  {'SÍ' if len(s) and s.mean() > b.mean() else 'no'}")
