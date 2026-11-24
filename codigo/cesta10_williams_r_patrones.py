"""Búsqueda de patrones · cesta10_williams_r (exploratoria, genera hipótesis; no valida nada por sí sola)
Regla base tal cual: %R 14 semanas, armado < -80, disparo al cruzar -40, salida 12 semanas, stop 10 %, costes 0,05 %/lado.

DESCUBRIMIENTO: operaciones de la cesta de hoy SOLO antes del 11-jul-2022 (y que cierran antes del corte).
4 patrones decididos ANTES de mirar, medidos en la semana de la señal:
  P1 Tendencia larga: cierre sobre o bajo su media de 40 semanas.
  P2 Profundidad: caída del cierre desde el máximo de 52 semanas (<15 %, 15-30 %, >30 %).
  P3 Velocidad: semanas desde la última vez que el %R estuvo < -80 hasta el disparo (≤3, 4-8, >8).
  P4 Mercado: cuántas de las 10 acciones de la cesta de hoy tuvieron %R < -80 en las 4 semanas previas
     (≤2 = caída de una acción; ≥3 = caída general).
CRITERIO DE ELECCIÓN (fijado antes): un grupo se elige si tiene ≥ 30 operaciones, FB ≥ 1,25 × FB de la regla
base en el descubrimiento y FB > 1,3. Si varios cumplen, gana el de mayor FB. Solo se elige UNO.
VALIDACIÓN (una sola vez): las 10 acciones del puesto 11 al 20 del QQQ al 12-oct-2022, nunca miradas:
TMUS, CSCO, TXN, ADBE, AMGN, CMCSA, QCOM, HON, INTU, INTC. Se mide la regla base y la regla + patrón elegido.
Uso: python3 codigo/cesta10_williams_r_patrones.py
"""
import numpy as np
import pandas as pd

HOY = ["AAPL", "NVDA", "MSFT", "GOOGL", "AMZN", "MU", "AMD", "TSLA", "META", "WMT"]
VALIDA = ["TMUS", "CSCO", "TXN", "ADBE", "AMGN", "CMCSA", "QCOM", "HON", "INTU", "INTC"]
N, ARMA, DISPARA, SALIDA, STOP, COSTE = 14, -80, -40, 12, 0.10, 0.0005
CORTE = pd.Timestamp("2022-07-11")


def semanal(tk):
    d = pd.read_csv(f"datos/{tk}_1D.csv", parse_dates=["fecha"]).set_index("fecha")
    w = d.resample("W-FRI").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    hh, ll = w["high"].rolling(N).max(), w["low"].rolling(N).min()
    w["wr"] = (hh - w["close"]) / (hh - ll) * -100
    w["sma40"] = w["close"].rolling(40).mean()
    w["max52"] = w["high"].rolling(52).max()
    armada, s, wr = False, np.zeros(len(w), bool), w["wr"].to_numpy()
    ult_bajo, semanas_desde = -1, np.full(len(w), np.nan)
    for i in range(len(w)):
        if np.isnan(wr[i]):
            continue
        if wr[i] < ARMA:
            armada, ult_bajo = True, i
        elif armada and i > 0 and wr[i - 1] <= DISPARA < wr[i]:
            s[i], armada = True, False
            semanas_desde[i] = i - ult_bajo
    w["senal"], w["semanas_desde"] = s, semanas_desde
    return w


SEM = {tk: semanal(tk) for tk in HOY + VALIDA}
# P4: amplitud de la caída en la cesta de hoy (sólo usa precios hasta la semana de la señal)
bajo = pd.DataFrame({tk: (SEM[tk]["wr"] < ARMA) for tk in HOY}).fillna(False)
AMPLITUD = bajo.astype(int).rolling(4).max().sum(axis=1)


def operaciones(tickers, hasta=None):
    ops = []
    for tk in tickers:
        w = SEM[tk] if hasta is None else SEM[tk][SEM[tk].index < hasta]
        o, l, c, s, f = w["open"].to_numpy(), w["low"].to_numpy(), w["close"].to_numpy(), w["senal"].to_numpy(), w.index
        i = 0
        while i < len(w) - 1:
            if not s[i]:
                i += 1
                continue
            e = i + 1
            if hasta is not None and e + SALIDA - 1 >= len(w):
                break
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
            fila = w.iloc[i]
            ops.append(dict(tk=tk, senal=f[i], entrada=f[e], salida=f[x], e=e, x=x, p_ent=ent, p_sal=px,
                            ret=px * (1 - COSTE) / (ent * (1 + COSTE)) - 1,
                            P1="sobre SMA40" if fila["close"] > fila["sma40"] else "bajo SMA40",
                            caida=1 - fila["close"] / fila["max52"],
                            vel=fila["semanas_desde"],
                            amp=AMPLITUD.reindex([f[i]]).iloc[0]))
            i = x
    d = pd.DataFrame(ops).sort_values("entrada").reset_index(drop=True)
    d["P2"] = pd.cut(d["caida"], [-1, 0.15, 0.30, 2], labels=["caída <15 %", "caída 15-30 %", "caída >30 %"]).astype(str)
    d["P3"] = pd.cut(d["vel"], [0, 3, 8, 999], labels=["≤3 semanas", "4-8 semanas", ">8 semanas"]).astype(str)
    d["P4"] = np.where(d["amp"] >= 3, "caída general (≥3)", "caída individual (≤2)")
    return d


def pf(r):
    r = np.asarray(r)
    p = -r[r < 0].sum()
    return r[r > 0].sum() / p if p > 0 else np.inf


def caida_cartera(sub, tickers, d0, d1):
    semanas = pd.DatetimeIndex(sorted(set().union(*[set(SEM[t].index[(SEM[t].index >= d0) & (SEM[t].index < d1)]) for t in tickers])))
    total = pd.Series(0.0, index=semanas)
    for tk in tickers:
        w, eq = SEM[tk], 0.1
        cuenta = pd.Series(np.nan, index=semanas)
        cuenta.iloc[0] = eq
        for _, t in sub[sub["tk"] == tk].iterrows():
            acc = eq / (t["p_ent"] * (1 + COSTE))
            for k in range(t["e"], t["x"] + 1):
                if w.index[k] in cuenta.index:
                    cuenta[w.index[k]] = acc * (t["p_sal"] * (1 - COSTE) if k == t["x"] else w["close"].iloc[k])
            eq = acc * t["p_sal"] * (1 - COSTE)
        total += cuenta.ffill()
    return (total / total.cummax() - 1).min()


def cuatro(sub, tickers, d0, d1, nombre):
    r = sub["ret"].reset_index(drop=True)
    if len(r) < 2:
        print(f"  {nombre}: {len(r)} operaciones, no se puede medir")
        return
    dd = caida_cartera(sub, tickers, d0, d1)
    sin = r.drop(r.idxmax())
    m = [(pf(r) >= 1.3, f"FB {pf(r):.2f}"), (len(r) >= 30, f"{len(r)} ops"),
         (dd > -0.20, f"caída {dd*100:.1f} %"), (pf(sin) > 1, f"FB sin mejor {pf(sin):.2f}")]
    print(f"  {nombre}: " + " · ".join(f"{'✓' if ok else '✕'} {v}" for ok, v in m)
          + f"  → {sum(ok for ok, _ in m)}/4 · ganadoras {(r > 0).mean()*100:.0f} % · media {r.mean()*100:+.2f} %")


# ---------- DESCUBRIMIENTO ----------
desc = operaciones(HOY, hasta=CORTE)
base_pf = pf(desc["ret"])
print(f"DESCUBRIMIENTO (cesta de hoy, antes del {CORTE.date()}): {len(desc)} operaciones, FB base {base_pf:.2f}\n")
candidatos = []
for p, nombre in [("P1", "Tendencia larga"), ("P2", "Profundidad"), ("P3", "Velocidad"), ("P4", "Mercado")]:
    print(f"{p} · {nombre}")
    for g, x in desc.groupby(p):
        v = pf(x["ret"])
        ok = len(x) >= 30 and v >= 1.25 * base_pf and v > 1.3
        n_acc = (x.groupby("tk")["ret"].sum() > 0).sum()
        print(f"   {g:<24} n={len(x):>3}  FB {v:5.2f}  media {x['ret'].mean()*100:+6.2f} %  "
              f"acciones que ganan {n_acc}/{x['tk'].nunique()}  {'← cumple' if ok else ''}")
        if ok:
            candidatos.append((v, p, g))
print(f"\n(Se miraron {sum(desc[p].nunique() for p in ['P1','P2','P3','P4'])} grupos en total: con tantos, alguno sale bien por azar)")

# ---------- VALIDACIÓN ----------
fin = max(SEM[t].index[-1] for t in VALIDA) + pd.Timedelta(days=1)
val = operaciones(VALIDA)
print("\nVALIDACIÓN · 10 acciones nunca miradas (puestos 11-20 del QQQ, oct-2022)")
print(" Regla base, sin patrón:")
cuatro(val[val["entrada"] < CORTE], VALIDA, pd.Timestamp("2010-01-01"), CORTE, "2010 → jul-2022")
cuatro(val[val["entrada"] >= CORTE], VALIDA, CORTE, fin, "jul-2022 → nov-2026")
print("  Por acción (todo el periodo):", ", ".join(f"{k}: {len(g)}/{g['ret'].mean()*100:+.1f}%" for k, g in val.groupby("tk")))
if candidatos:
    v, p, g = max(candidatos)
    print(f"\n Regla + patrón elegido en el descubrimiento: {p} = «{g}» (FB descubrimiento {v:.2f})")
    vf = val[val[p] == g]
    cuatro(vf[vf["entrada"] < CORTE], VALIDA, pd.Timestamp("2010-01-01"), CORTE, "2010 → jul-2022")
    cuatro(vf[vf["entrada"] >= CORTE], VALIDA, CORTE, fin, "jul-2022 → nov-2026")
    resto = val[val[p] != g]
    print(f"  Operaciones que el patrón descarta: {len(resto)}, FB {pf(resto['ret']):.2f}, media {resto['ret'].mean()*100:+.2f} %")
else:
    print("\n Ningún grupo cumplió el criterio fijado: no hay patrón que validar.")
val.drop(columns=["e", "x"]).to_csv("resultados/cesta10_williams_r_validacion_operaciones.csv", index=False)
