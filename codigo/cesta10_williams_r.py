"""cesta10_williams_r · Williams %R semanal en las 10 mayores del Nasdaq-100 (peso en QQQ, 8-nov-2026)
Señal por acción: %R(14 semanas) baja de -80 (se arma) y luego cruza -40 hacia arriba (dispara, se desarma).
  aed       → fase 02: retorno 1/4/12/26 semanas tras la señal vs cualquier semana, SOLO antes del corte OOS.
  backtest  → fase 04: regla completa con costes y stop; IS antes del corte, OOS desde el corte.
Uso: python3 codigo/cesta10_williams_r.py aed | backtest
"""
import sys
import numpy as np
import pandas as pd

TICKERS = ["AAPL", "NVDA", "MSFT", "GOOGL", "AMZN", "MU", "AMD", "TSLA", "META", "WMT"]
N, ARMA, DISPARA = 14, -80, -40
SALIDA, STOP, COSTE = 12, 0.10, 0.0005     # 12 semanas, stop 10 %, 0,05 % por lado
CORTE = pd.Timestamp("2022-07-11")         # mismo corte que meta_williams_r: el OOS no se mira en la fase 02
HORIZ = [1, 4, 12, 26]


def semanal(tk):
    d = pd.read_csv(f"datos/{tk}_1D.csv", parse_dates=["fecha"]).set_index("fecha")
    w = d.resample("W-FRI").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    hh, ll = w["high"].rolling(N).max(), w["low"].rolling(N).min()
    w["wr"] = (hh - w["close"]) / (hh - ll) * -100
    armada, sen, wr = False, [], w["wr"].to_numpy()
    for i in range(len(w)):
        s = False
        if not np.isnan(wr[i]):
            if wr[i] < ARMA:
                armada = True
            elif armada and i > 0 and wr[i - 1] <= DISPARA < wr[i]:
                s, armada = True, False
        sen.append(s)
    w["senal"] = sen
    w["tk"] = tk
    return w


DATOS = {tk: semanal(tk) for tk in TICKERS}


def aed():
    filas = []
    for tk, w in DATOS.items():
        w = w.copy()
        for k in HORIZ:
            w[f"r{k}"] = w["close"].shift(-k) / w["close"] - 1
            fin = w.index.to_series().shift(-k)
            w.loc[(fin >= CORTE) | fin.isna(), f"r{k}"] = np.nan   # ningún retorno usa precios del OOS
        filas.append(w[(w.index < CORTE)].dropna(subset=["wr"] + [f"r{k}" for k in HORIZ]))
    is_ = pd.concat(filas)
    print(f"IS: {is_.index.min().date()} -> {is_.index.max().date()}  ({len(is_)} semanas-acción). OOS desde {CORTE.date()} sin mirar\n")

    def fila(nombre, sub):
        print(f"{nombre:<24} n={len(sub):>5} | " + " | ".join(
            f"r{k} {sub[f'r{k}'].mean()*100:+.2f}% (>0 {(sub[f'r{k}'] > 0).mean()*100:.0f}%)" for k in HORIZ))
    fila("Señal %R (cesta)", is_[is_["senal"]])
    fila("Cualquier semana (base)", is_)

    print("\nPor acción (r12 señal vs base):")
    for tk in TICKERS:
        x = is_[is_["tk"] == tk]
        s = x[x["senal"]]["r12"]
        print(f"  {tk:<6} señal {s.mean()*100:+6.2f}% (n={len(s):>2})  base {x['r12'].mean()*100:+6.2f}%  "
              f"{'SÍ' if len(s) and s.mean() > x['r12'].mean() else 'no'}")
    print("\nPor año (r12 señal vs base):")
    for a in sorted(set(is_.index.year)):
        x = is_[is_.index.year == a]
        s = x[x["senal"]]["r12"]
        print(f"  {a}: señal {s.mean()*100 if len(s) else float('nan'):+6.2f}% (n={len(s):>2})  base {x['r12'].mean()*100:+6.2f}%  "
              f"{'SÍ' if len(s) and s.mean() > x['r12'].mean() else 'no'}")
    s = is_[is_["senal"]]["r12"]
    exceso = s.mean() - is_["r12"].mean()
    t = exceso / (s.std(ddof=1) / np.sqrt(len(s)))
    print(f"\nExceso r12 sobre la base: {exceso*100:+.2f} puntos  (t≈{t:.2f}, n={len(s)})")


def backtest():
    ops = []
    for tk, w in DATOS.items():
        o, l, c = w["open"].to_numpy(), w["low"].to_numpy(), w["close"].to_numpy()
        s, f = w["senal"].to_numpy(), w.index
        i = 0
        while i < len(w) - 1:
            if not s[i]:
                i += 1
                continue
            e = i + 1
            ent = o[e]
            nivel = ent * (1 - STOP)
            x, px, motivo = None, None, None
            for k in range(e, min(e + SALIDA, len(w))):
                if l[k] <= nivel:                       # a. primero el stop
                    x, px, motivo = k, (o[k] if (k > e and o[k] < nivel) else nivel), "stop"
                    break
                if k == e + SALIDA - 1:                 # b. después la salida por tiempo
                    x, px, motivo = k, c[k], "tiempo"
            if x is None:                               # datos agotados: se cierra al último cierre
                x, px, motivo = len(w) - 1, c[-1], "abierta"
            ret = px * (1 - COSTE) / (ent * (1 + COSTE)) - 1
            ops.append(dict(tk=tk, entrada=f[e], salida=f[x], e=e, x=x, p_ent=ent, p_sal=px, ret=ret, motivo=motivo))
            i = x                                       # la vela de salida puede dar una señal nueva
    ops = pd.DataFrame(ops).sort_values("entrada").reset_index(drop=True)
    ops.drop(columns=["e", "x"]).to_csv("resultados/cesta10_williams_r_operaciones.csv", index=False)

    def tramo(nombre, d0, d1):
        sub = ops[(ops["entrada"] >= d0) & (ops["entrada"] < d1)]
        # 10 cuentas iguales (una por acción), cada una con interés compuesto; curva semanal marcada a mercado
        semanas = pd.DatetimeIndex(sorted(set().union(*[set(w.index[(w.index >= d0) & (w.index < d1 + pd.Timedelta(weeks=SALIDA))]) for w in DATOS.values()])))
        total = pd.Series(0.0, index=semanas)
        for tk, w in DATOS.items():
            cuenta = pd.Series(np.nan, index=semanas)
            eq = 0.1
            cuenta.iloc[0] = eq
            for _, t in sub[sub["tk"] == tk].iterrows():
                acc = eq / (t["p_ent"] * (1 + COSTE))
                for k in range(t["e"], t["x"] + 1):
                    v = acc * (t["p_sal"] * (1 - COSTE) if k == t["x"] else w["close"].iloc[k])
                    if w.index[k] in cuenta.index:
                        cuenta[w.index[k]] = v
                eq = acc * t["p_sal"] * (1 - COSTE)
                if t["salida"] in cuenta.index:
                    cuenta[t["salida"]] = eq
            total += cuenta.ffill()
        dd = (total / total.cummax() - 1).min()
        r = sub["ret"]
        g, p = r[r > 0].sum(), -r[r < 0].sum()
        pf = g / p if p else float("inf")
        rs = r.drop(r.idxmax())
        pf2 = rs[rs > 0].sum() / -rs[rs < 0].sum()
        bh = np.mean([w.loc[(w.index >= d0) & (w.index < d1), "close"].iloc[-1] /
                      w.loc[(w.index >= d0) & (w.index < d1), "close"].iloc[0] for w in DATOS.values()])
        print(f"\n== {nombre}: {d0.date()} -> {(d1 - pd.Timedelta(days=1)).date()} ==")
        print(f"Operaciones {len(r)} · ganadoras {(r > 0).mean()*100:.0f} % · media {r.mean()*100:+.2f} % · "
              f"stops {(sub['motivo'] == 'stop').sum()} · abiertas {(sub['motivo'] == 'abierta').sum()} · "
              f"capital x{total.iloc[-1]:.2f} · comprar y mantener la cesta x{bh:.2f}")
        m = [("Factor de beneficio ≥ 1,3", pf >= 1.3, f"{pf:.2f}"), ("Al menos 30 operaciones", len(r) >= 30, f"{len(r)}"),
             ("Caída máxima < 20 %", dd > -0.20, f"{dd*100:.1f} %"), ("FB sin la mejor > 1", pf2 > 1, f"{pf2:.2f}")]
        for txt, ok, v in m:
            print(f"  {'✓' if ok else '✕'} {txt}: {v}")
        print(f"  Veredicto: {sum(ok for _, ok, _ in m)}/4")
        print("  Por año:", ", ".join(f"{a}: {len(g_)} ops {g_['ret'].mean()*100:+.1f} %" for a, g_ in sub.groupby(sub['entrada'].dt.year)))
        print("  Por acción:", ", ".join(f"{k}: {len(g_)}/{g_['ret'].mean()*100:+.1f}%" for k, g_ in sub.groupby("tk")))

    fin = max(w.index[-1] for w in DATOS.values()) + pd.Timedelta(days=1)
    tramo("DENTRO DE MUESTRA", pd.Timestamp("2010-01-01"), CORTE)
    tramo("FUERA DE MUESTRA", CORTE, fin)


if __name__ == "__main__":
    {"aed": aed, "backtest": backtest}[sys.argv[1] if len(sys.argv) > 1 else "aed"]()
