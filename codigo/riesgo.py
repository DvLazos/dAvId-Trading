"""Fase 07 · Tamaño y riesgo · genérico (cualquier idea con su lista de operaciones).

Propone cuánto arriesgar por operación. NO aprueba nada: la fase 07 es CRITERIO y decide el trader.

Entrada : resultados/<idea>_operaciones.csv  (columnas mínimas: entrada, salida, ret;
          opcionales: motivo, stop_pct)
Límite  : la caída máxima que acepta el trader, leída de MI_PLAN.md; si no existe, 10 % (supuesto).
Métodos :
  1. Fracción fija   → arriesgar un % fijo del capital en cada operación. El "riesgo" es lo que
                       se pierde si salta el stop (distancia al stop). Sin stop: se usa el
                       percentil 5 de los retornos como "pérdida típica mala" (supuesto).
  2. Objetivo de volatilidad → el tamaño de cada operación se ajusta para que su vaivén esperado
                       (desviación típica de las últimas 20 operaciones cerradas) sea constante.
Monte Carlo: 10.000 barajas del orden de las operaciones (semilla 42). Se busca el mayor tamaño
cuya caída del percentil 95 queda por debajo del objetivo (70 % del límite = 7 % si el límite es 10 %).
Niveles de vigilancia (supuesto, hoja de ruta): aviso al 50 % del límite (5 %), apagado al 80 % (8 %).

Uso: python3 codigo/riesgo.py resultados/<idea>_operaciones.csv [--limite 10] [--objetivo 7]
                               [--desde AAAA-MM-DD] [--capital 10000] [--json]
"""
import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
SIMS, SEMILLA, VENTANA_VOL, MIN_VOL = 10_000, 42, 20, 10
LIMITE_DEFECTO = 10.0


# ---------- utilidades compartidas (también las usa fondeo_simulador.py) ----------

def nombre_idea(ruta_csv):
    return Path(ruta_csv).stem.replace("_operaciones", "")


def cargar_operaciones(ruta_csv, desde=None):
    """Lee la lista de operaciones y calcula R (resultado medido en "riesgos": −1 R = saltó el stop)."""
    ops = pd.read_csv(ruta_csv)
    for c in ("entrada", "salida", "ret"):
        if c not in ops.columns:
            sys.exit(f"Falta la columna «{c}» en {ruta_csv}")
    ops["entrada"] = pd.to_datetime(ops["entrada"])
    ops["salida"] = pd.to_datetime(ops["salida"])
    ops = ops.dropna(subset=["ret"]).sort_values(["entrada", "salida"]).reset_index(drop=True)
    if desde:
        ops = ops[ops["entrada"] >= pd.Timestamp(desde)].reset_index(drop=True)
    if len(ops) < 10:
        sys.exit(f"Solo hay {len(ops)} operaciones: no alcanza para medir riesgo.")

    if "stop_pct" in ops.columns and ops["stop_pct"].notna().all():
        dist = ops["stop_pct"].abs().astype(float)
        fuente = "columna stop_pct del CSV"
    elif "motivo" in ops.columns and (ops["motivo"] == "stop").sum() >= 3:
        d = float(np.median(-ops.loc[ops["motivo"] == "stop", "ret"]))
        dist = pd.Series(d, index=ops.index)
        fuente = f"inferida de las salidas por stop: mediana {num(d*100, 2)} % con costes"
    else:
        d = float(abs(np.percentile(ops["ret"], 5)))
        dist = pd.Series(d, index=ops.index)
        fuente = f"sin stop en el CSV: percentil 5 de los retornos, {num(d*100, 2)} % (supuesto)"
    ops["R"] = ops["ret"] / dist
    return ops, fuente


def estado_validacion(idea, fases=(4, 5, 6)):
    """Lee fichas/<idea>.md. Validada solo si cada fase pedida tiene bloque y TODOS dicen APRUEBA."""
    ficha = RAIZ / "fichas" / f"{idea}.md"
    if not ficha.exists():
        return False, f"no existe fichas/{idea}.md"
    texto = ficha.read_text(encoding="utf-8")
    bloques = re.split(r"(?m)^## ", texto)
    faltan, fallan = [], []
    for f in fases:
        veredictos = []
        for b in bloques:
            if re.match(rf"Fase 0?{f}\b", b):
                m = re.search(r"(?m)^Veredicto:\s*(.*)$", b)
                titulo = b.splitlines()[0].strip()
                veredictos.append((titulo, m.group(1).strip() if m else "sin veredicto"))
        if not veredictos:
            faltan.append(f"0{f}")
        for titulo, v in veredictos:
            if not v.upper().startswith("APRUEBA"):
                fallan.append(f"{titulo} → {v.split('(')[0].strip()}")
    ok = not faltan and not fallan
    partes = []
    if faltan:
        partes.append("sin bloque: fase " + ", ".join(faltan))
    if fallan:
        partes.append("; ".join(fallan))
    return ok, ("fases " + "-".join(f"0{f}" for f in (fases[0], fases[-1])) + " aprobadas") if ok else " · ".join(partes)


def limite_del_plan():
    """Busca en MI_PLAN.md la caída máxima aceptada (primer «NN %» en una línea que hable de caída)."""
    plan = RAIZ / "MI_PLAN.md"
    if plan.exists():
        for linea in plan.read_text(encoding="utf-8").splitlines():
            if re.search(r"ca[ií]da|drawdown", linea, re.I):
                m = re.search(r"(\d+(?:[.,]\d+)?)\s*%", linea)
                if m:
                    return float(m.group(1).replace(",", ".")), "MI_PLAN.md"
    return LIMITE_DEFECTO, "no existe MI_PLAN.md o no trae la caída: 10 % (supuesto)"


def max_simultaneas(ops):
    ev = [(e, 1) for e in ops["entrada"]] + [(s, -1) for s in ops["salida"]]
    ev.sort(key=lambda x: (x[0], x[1]))            # a igual fecha, primero cierra y luego abre
    n = m = 0
    for _, d in ev:
        n += d
        m = max(m, n)
    return m


def num(x, dec=1):
    return f"{x:,.{dec}f}".replace(",", "_").replace(".", ",").replace("_", ".")


def pct(x, dec=1):
    return f"{num(x*100, dec)} %"


# ---------- Monte Carlo ----------

def caidas_mc(pasos, perms):
    """Caída máxima (número negativo) de cada baraja. pasos = cambio del capital por operación."""
    out = np.empty(len(perms))
    for a in range(0, len(perms), 2000):
        p = perms[a:a + 2000]
        log_eq = np.cumsum(np.log1p(pasos[p]), axis=1)
        log_eq = np.concatenate([np.zeros((len(p), 1)), log_eq], axis=1)
        out[a:a + 2000] = (np.exp(log_eq - np.maximum.accumulate(log_eq, axis=1)) - 1).min(axis=1)
    return out


def resumen(pasos, perms):
    dd = caidas_mc(pasos, perms)
    final = np.exp(np.log1p(pasos).sum()) - 1        # igual para todas las barajas (mismo producto)
    eq = np.concatenate([[0], np.cumsum(np.log1p(pasos))])
    dd_real = (np.exp(eq - np.maximum.accumulate(eq)) - 1).min()
    return dict(p50=np.percentile(dd, 50), p95=np.percentile(dd, 5), p99=np.percentile(dd, 1),
                peor=dd.min(), real=dd_real, final=final, dd=dd)


def buscar(rejilla, pasos_de, perms, objetivo):
    """Mayor valor de la rejilla cuya caída p95 no supera el objetivo (rejilla creciente)."""
    mejor, filas = None, []
    for v in rejilla:
        r = resumen(pasos_de(v), perms)
        filas.append((v, r))
        if -r["p95"] <= objetivo:
            mejor = (v, r)
        else:
            break
    return mejor, filas


def pasos_vol(ops, objetivo_vol):
    """Fracción del capital en cada operación = objetivo / vol. reciente (sin mirar el futuro), tope 100 %."""
    ret = ops["ret"].to_numpy()
    sal = ops["salida"].to_numpy()
    sig0 = np.std(ret[:VENTANA_VOL], ddof=1)          # arranque: primeras 20 operaciones (supuesto)
    expo = np.empty(len(ops))
    for i, e in enumerate(ops["entrada"].to_numpy()):
        previas = ops.loc[sal < e].sort_values("salida")["ret"].to_numpy()[-VENTANA_VOL:]
        s = np.std(previas, ddof=1) if len(previas) >= MIN_VOL else sig0
        expo[i] = min(1.0, objetivo_vol / s) if s > 0 else 1.0
    return expo


# ---------- principal ----------

def main():
    ap = argparse.ArgumentParser(description="Fase 07 · propone el riesgo por operación (decide el trader).")
    ap.add_argument("csv")
    ap.add_argument("--limite", type=float, help="caída máxima aceptada en %% (manda sobre MI_PLAN.md)")
    ap.add_argument("--objetivo", type=float, help="caída p95 objetivo en %% (por defecto 70 %% del límite)")
    ap.add_argument("--desde", help="usar solo operaciones con entrada desde esta fecha (p. ej. el corte OOS)")
    ap.add_argument("--capital", type=float, default=10_000, help="capital de ejemplo para pasar % a dinero")
    ap.add_argument("--json", action="store_true", help="imprime solo un resumen JSON de una línea")
    a = ap.parse_args()

    idea = nombre_idea(a.csv)
    ops, fuente_stop = cargar_operaciones(a.csv, a.desde)
    if a.limite:
        limite, fuente_lim = a.limite, "argumento --limite"
    else:
        limite, fuente_lim = limite_del_plan()
    objetivo = (a.objetivo if a.objetivo else 0.7 * limite) / 100
    obj_sup = "" if a.objetivo else " (supuesto: 70 % del límite, margen de seguridad)"
    aviso, apagado = 0.5 * limite / 100, 0.8 * limite / 100
    validada, det_val = estado_validacion(idea)

    n = len(ops)
    años = max((ops["salida"].max() - ops["entrada"].min()).days / 365.25, 1e-9)
    simult = max_simultaneas(ops)
    R = ops["R"].to_numpy()
    rng = np.random.default_rng(SEMILLA)
    perms = np.argsort(rng.random((SIMS, n)), axis=1)

    # 1. Fracción fija
    rejilla_ff = np.round(np.arange(0.0005, 0.0501, 0.0005), 4)
    if (1 + rejilla_ff.max() * R.min()) <= 0:
        rejilla_ff = rejilla_ff[1 + rejilla_ff * R.min() > 0.05]
    ff, filas_ff = buscar(rejilla_ff, lambda f: f * R, perms, objetivo)

    # 1b. Versión prudente: además, que la caída del orden real tampoco pase el objetivo
    f_prud = None
    for f in rejilla_ff:
        eq = np.concatenate([[0], np.cumsum(np.log1p(f * R))])
        if -(np.exp(eq - np.maximum.accumulate(eq)) - 1).min() <= objetivo:
            f_prud = f
        else:
            break
    if ff and f_prud is not None:
        f_prud = min(f_prud, ff[0])

    # 2. Objetivo de volatilidad
    rejilla_vol = np.round(np.arange(0.001, 0.2001, 0.001), 4)
    ret = ops["ret"].to_numpy()
    cache = {}

    def pv(t):
        cache[t] = pasos_vol(ops, t)
        return cache[t] * ret
    vt, _ = buscar(rejilla_vol, pv, perms, objetivo)

    def prob(r, nivel):
        return float((r["dd"] <= -nivel).mean())

    # ---------- informe ----------
    L = []
    L.append(f"# Riesgo · {idea} · fase 07 · tamaño y riesgo · CRITERIO\n")
    if not validada:
        L.append(f"> **SOLO EJERCICIO, ESTRATEGIA NO VALIDADA.** La ficha no tiene aprobadas las fases 04-06 "
                 f"({det_val}). Estos números sirven para aprender y probar la tubería, no para operar.\n")
    L.append("> **Esta skill propone; no aprueba.** La fase 07 es de CRITERIO: el riesgo final lo decides tú, "
             "por escrito en la ficha. Nada de esto es una señal ni promete rentabilidad.\n")
    L.append("## Datos de partida")
    L.append(f"- Operaciones: {n} (archivo `{a.csv}`{', desde ' + a.desde if a.desde else ', todo el periodo: incluye las de dentro de muestra, que suelen ser optimistas'}).")
    L.append(f"- Periodo: {ops['entrada'].min():%d-%m-%Y} a {ops['salida'].max():%d-%m-%Y} (≈ {num(años)} años, {num(n/años)} operaciones por año).")
    L.append(f"- Ganadoras: {pct((ret > 0).mean(), 0)} · retorno medio por operación {pct(ret.mean(), 2)}.")
    L.append(f"- Distancia al stop (lo que se pierde si salta): {fuente_stop}.")
    L.append(f"- Peor operación: {num(R.min(), 2)} R (1 R = una pérdida completa de stop; más de 1 R significa hueco de precio).")
    L.append(f"- Límite de caída: {limite:.0f} % ({fuente_lim}). Objetivo para la caída p95: {pct(objetivo, 0)}{obj_sup}.")
    L.append(f"- Niveles de vigilancia (supuesto, hoja de ruta): aviso al {pct(aviso, 0)} y apagado al {pct(apagado, 0)} de caída.\n")
    L.append("**Palabras clave.** *Caída* = la peor bajada desde un máximo de la cuenta. *Monte Carlo* = barajar "
             f"{num(SIMS, 0)} veces el orden de las operaciones para ver otras historias posibles. *Percentil 95 (p95)* = "
             "el 95 % de las barajas cae menos que esto.\n")

    L.append("## 1. Fracción fija (un % del capital en riesgo por operación)")
    if ff:
        f, r = ff
        L.append(f"- **Propuesta máxima: {pct(f, 2)} de riesgo por operación.** Con {num(a.capital, 0)} de capital (ejemplo) "
                 f"son {num(f*a.capital, 0)} en riesgo por operación.")
        L.append(f"- Caída: mediana {pct(-r['p50'])} · p95 {pct(-r['p95'])} · p99 {pct(-r['p99'])} · peor baraja {pct(-r['peor'])} · orden real {pct(-r['real'])}.")
        L.append(f"- Probabilidad de tocar el aviso ({pct(aviso, 0)}): {pct(prob(r, aviso), 0)} · de tocar el apagado ({pct(apagado, 0)}): {pct(prob(r, apagado), 1)}.")
        L.append(f"- Resultado acumulado de la muestra con ese tamaño: {pct(r['final'], 0)} (el pasado no se repite).")
        if -r["real"] > limite / 100:
            peor_que = float((r["dd"] > r["real"]).mean())
            L.append(f"- **Alerta:** en el orden real de la historia la caída fue {pct(-r['real'])}, más que tu límite "
                     f"de {limite:.0f} % y peor que el {pct(peor_que, 1)} de las barajas. Señal de que las pérdidas "
                     "llegan en racimos (varias operaciones a la vez caen juntas): barajar el orden rompe esos racimos "
                     "y subestima la caída.")
        if f_prud is not None and f_prud < f:
            L.append(f"- **Propuesta prudente: {pct(f_prud, 2)}**, el mayor tamaño con el que la caída p95 del Monte Carlo "
                     f"**y** la caída del orden real quedan bajo {pct(objetivo, 0)}.")
        L.append(f"- **Ojo, operaciones a la vez:** hasta {simult} posiciones abiertas al mismo tiempo. Si todas saltan "
                 f"juntas, la pérdida sería ≈ {pct(f*simult, 1)} de golpe. El Monte Carlo trata las operaciones "
                 "una tras otra, así que subestima ese riesgo cuando hay muchas a la vez.")
    else:
        L.append(f"- Ni con {pct(rejilla_ff[0], 2)} por operación la caída p95 queda bajo {pct(objetivo, 0)}. No se propone tamaño.")
    L.append("\nTabla corta (riesgo por operación → caída p95 · probabilidad de tocar el apagado):")
    for v in (0.0025, 0.005, 0.0075, 0.01, 0.015, 0.02):
        if 1 + v * R.min() > 0:
            r = resumen(v * R, perms)
            L.append(f"- {pct(v, 2)} → {pct(-r['p95'])} · {pct(prob(r, apagado), 0)}")
    L.append("")

    L.append("## 2. Objetivo de volatilidad (tamaño que se ajusta al vaivén reciente)")
    if vt:
        t, r = vt
        expo = cache[t]
        L.append(f"- **Propuesta máxima: vaivén objetivo {pct(t, 1)} del capital por operación.** El tamaño de cada "
                 f"operación = {pct(t, 1)} ÷ desviación típica de las últimas {VENTANA_VOL} operaciones cerradas "
                 "(sin mirar el futuro), con tope de 100 % del capital (sin apalancamiento, supuesto).")
        L.append(f"- Parte del capital que entra en cada operación: mediana {pct(np.median(expo), 0)} (mín. {pct(expo.min(), 0)}, máx. {pct(expo.max(), 0)}).")
        L.append(f"- Caída: mediana {pct(-r['p50'])} · p95 {pct(-r['p95'])} · p99 {pct(-r['p99'])} · orden real {pct(-r['real'])}.")
        L.append(f"- Probabilidad de tocar el aviso: {pct(prob(r, aviso), 0)} · el apagado: {pct(prob(r, apagado), 1)}.")
        L.append(f"- Resultado acumulado de la muestra: {pct(r['final'], 0)}.")
    else:
        L.append(f"- Ni con el vaivén objetivo más pequeño la caída p95 queda bajo {pct(objetivo, 0)}.")
    L.append("")

    L.append("## Qué decides tú (fase 07 · CRITERIO)")
    L.append("1. ¿Qué riesgo por operación aceptas? Puede ser igual o **menor** que la propuesta, nunca mayor sin volver a correr esto.")
    L.append(f"2. ¿Confirmas los niveles de aviso ({pct(aviso, 0)}) y apagado ({pct(apagado, 0)})?")
    L.append("3. Escríbelo en el bloque «Fase 07» de la ficha. Mientras METODO.md diga «umbral: se fija en el Reto», la fase 07 queda PENDIENTE.")
    if not validada:
        L.append("4. Esta estrategia no está validada: el veredicto de la fase 07 es **NO APRUEBA / solo ejercicio**, aunque los números se vean bien.")
    L.append("\n## Supuestos")
    L.append(f"- Límite de caída {limite:.0f} % ({fuente_lim}); objetivo p95 {pct(objetivo, 0)}; aviso 50 % y apagado 80 % del límite.")
    L.append(f"- Monte Carlo del orden, {num(SIMS, 0)} barajas, semilla 42. Las operaciones se suman una tras otra (interés compuesto).")
    L.append("- Las operaciones del pasado representan a las futuras. Si la estrategia cambia de comportamiento, todo esto cambia.")
    L.append(f"- Arranque del objetivo de volatilidad con las primeras {VENTANA_VOL} operaciones (mira un poco el futuro solo al principio).")
    L.append("\n*Generado por `codigo/riesgo.py`. Determinista: mismo CSV, mismo resultado.*")

    salida = RAIZ / "resultados" / f"{idea}_riesgo.md"
    salida.write_text("\n".join(L) + "\n", encoding="utf-8")

    res = dict(idea=idea, skill="riesgo", fase="07", validada=validada, estado_ficha=det_val,
               operaciones=n, limite_pct=limite, objetivo_p95_pct=round(objetivo * 100, 2),
               aviso_pct=round(aviso * 100, 2), apagado_pct=round(apagado * 100, 2),
               ff_riesgo_pct=round(ff[0] * 100, 3) if ff else None,
               ff_riesgo_prudente_pct=round(f_prud * 100, 3) if f_prud is not None else None,
               ff_caida_p95_pct=round(-ff[1]["p95"] * 100, 2) if ff else None,
               vol_objetivo_pct=round(vt[0] * 100, 2) if vt else None,
               vol_caida_p95_pct=round(-vt[1]["p95"] * 100, 2) if vt else None,
               max_simultaneas=simult, informe=str(salida.relative_to(RAIZ)),
               decision="la toma el trader")
    if a.json:
        print(json.dumps(res, ensure_ascii=False))
    else:
        print("\n".join(L))
        print(f"\nInforme: {salida.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
