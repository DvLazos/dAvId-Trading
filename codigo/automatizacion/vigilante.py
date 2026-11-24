"""Vigilante · ¿la cuenta en vivo se porta como el backtest? ¿se acerca al límite de caída?

Busca resultados/<idea>_vivo.csv (el registro de operaciones reales o de demo de cada idea).
Para cada uno:
  1. CAÍDA. Mide la caída actual desde el máximo de la cuenta y la peor caída registrada.
     Aviso al 5 % y APAGAR al 8 % (supuesto de MI_HOJA_DE_RUTA.md: 50 % y 80 % de tu límite
     del 10 %). Si MI_PLAN.md trae otro límite, se usa ese con las mismas proporciones.
  2. VIVO CONTRA BACKTEST. Compara el retorno medio por operación en vivo con lo que daría el
     backtest (resultados/<idea>_operaciones.csv) con ese mismo número de operaciones:
     2.000 sorteos al azar de operaciones del backtest (semilla 42). Si lo real queda por debajo
     del 5 % peor de los sorteos → DESVÍO (se porta peor que el backtest, revisar).

Formato de <idea>_vivo.csv (supuesto; una fila por operación CERRADA):
  fecha            · fecha de salida (obligatoria)
  equity           · valor de la cuenta después de la operación (lo mejor para medir la caída)
  ret_cuenta       · o bien: variación de la cuenta por operación (0.01 = +1 %)
  ret              · retorno de la operación sobre su tamaño (igual que en el backtest)
  fraccion         · parte de la cuenta que usó la operación (si no hay equity ni ret_cuenta;
                     si falta, se toma 1 = toda la cuenta, que exagera la caída: prudente)
El vigilante SOLO avisa. Nunca abre ni cierra operaciones, nunca cambia el riesgo, nunca toca
el bróker. Apagar (el kill-switch) lo haces tú.

Uso: python3 codigo/automatizacion/vigilante.py [--json] [--aviso 5] [--apagado 8]
Código de salida: 0 normal · 2 alguna cuenta llegó al nivel de APAGAR.
"""
import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent.parent
RESULTADOS = RAIZ / "resultados"
SORTEOS, SEMILLA, MIN_OPS = 2000, 42, 5


def limite_plan():
    """Límite de caída de MI_PLAN.md (busca «caída ... 10 %»). Si no hay plan: 10 % (supuesto)."""
    plan = RAIZ / "MI_PLAN.md"
    if plan.exists():
        for l in plan.read_text(encoding="utf-8").splitlines():
            if re.search(r"ca[ií]da", l, re.I):
                m = re.search(r"(\d+(?:[.,]\d+)?)\s*%", l)
                if m:
                    return float(m.group(1).replace(",", ".")), "MI_PLAN.md"
    return 10.0, "supuesto de MI_HOJA_DE_RUTA.md (no hay MI_PLAN.md)"


def curva(df):
    if "equity" in df:
        eq = df["equity"].astype(float).to_numpy()
        return eq / eq[0], "equity"
    if "ret_cuenta" in df:
        return np.cumprod(1 + df["ret_cuenta"].astype(float).to_numpy()), "ret_cuenta"
    if "ret" in df:
        f = df["fraccion"].astype(float).to_numpy() if "fraccion" in df else 1.0
        fuente = "ret × fraccion" if "fraccion" in df else "ret con toda la cuenta (supuesto prudente)"
        return np.cumprod(1 + df["ret"].astype(float).to_numpy() * f), fuente
    return None, "sin columnas equity, ret_cuenta ni ret"


def revisar(ruta, aviso, apagado):
    idea = ruta.stem[:-len("_vivo")]
    r = {"idea": idea, "archivo": str(ruta.relative_to(RAIZ))}
    try:
        df = pd.read_csv(ruta)
    except Exception as e:
        r.update(estado="ERROR", detalle=f"no se pudo leer: {e}")
        return r
    r["operaciones"] = len(df)
    if df.empty:
        r.update(estado="OK", detalle="sin operaciones cerradas todavía", caida_actual_pct=0.0, caida_max_pct=0.0)
        return r
    eq, fuente = curva(df)
    if eq is None:
        r.update(estado="ERROR", detalle=fuente)
        return r
    if fuente == "equity":
        pico = np.maximum.accumulate(eq)
    else:  # el capital inicial (1) también cuenta como máximo
        pico = np.maximum.accumulate(np.concatenate([[1.0], eq]))[1:]
    dd = eq / pico - 1
    r["caida_actual_pct"] = round(-dd[-1] * 100, 2)
    r["caida_max_pct"] = round(-dd.min() * 100, 2)
    r["fuente_caida"] = fuente
    if r["caida_actual_pct"] >= apagado:
        r["estado"] = "APAGAR"
    elif r["caida_actual_pct"] >= aviso:
        r["estado"] = "AVISO"
    else:
        r["estado"] = "OK"

    # Vivo contra backtest
    bt = RESULTADOS / f"{idea}_operaciones.csv"
    if "ret" not in df:
        r["comparacion"] = "sin columna ret: no se puede comparar con el backtest"
    elif not bt.exists():
        r["comparacion"] = f"no existe {bt.relative_to(RAIZ)}: no se puede comparar"
    elif len(df) < MIN_OPS:
        r["comparacion"] = f"solo {len(df)} operaciones: muy pocas para comparar (mínimo {MIN_OPS})"
    else:
        ret_bt = pd.read_csv(bt)["ret"].astype(float).to_numpy()
        vivo = df["ret"].astype(float).to_numpy()
        rng = np.random.default_rng(SEMILLA)
        medias = rng.choice(ret_bt, size=(SORTEOS, len(vivo)), replace=True).mean(axis=1)
        p5, p50 = np.percentile(medias, 5), np.percentile(medias, 50)
        r.update(media_vivo_pct=round(vivo.mean() * 100, 2), media_bt_p50_pct=round(p50 * 100, 2),
                 media_bt_p5_pct=round(p5 * 100, 2), ganadoras_vivo_pct=round((vivo > 0).mean() * 100),
                 ganadoras_bt_pct=round((ret_bt > 0).mean() * 100))
        r["desvio"] = bool(vivo.mean() < p5)
        r["comparacion"] = ("DESVÍO: rinde peor que el 95 % de lo que daría el backtest" if r["desvio"]
                            else "dentro de lo esperable según el backtest")
    return r


def vigilar(aviso=None, apagado=None):
    limite, fuente = limite_plan()
    aviso = aviso if aviso is not None else 0.5 * limite
    apagado = apagado if apagado is not None else 0.8 * limite
    cuentas = [revisar(p, aviso, apagado) for p in sorted(RESULTADOS.glob("*_vivo.csv"))]
    return {"limite_pct": limite, "fuente_limite": fuente, "aviso_pct": aviso, "apagado_pct": apagado,
            "cuentas": cuentas, "sin_cuentas": not cuentas,
            "apagar": [c["idea"] for c in cuentas if c.get("estado") == "APAGAR"],
            "avisos": [c["idea"] for c in cuentas if c.get("estado") in ("AVISO", "ERROR") or c.get("desvio")]}


def main():
    ap = argparse.ArgumentParser(description="Vigila las cuentas en vivo (solo avisa).")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--aviso", type=float, help="caída en %% para avisar (defecto: 50 %% del límite)")
    ap.add_argument("--apagado", type=float, help="caída en %% para APAGAR (defecto: 80 %% del límite)")
    a = ap.parse_args()
    v = vigilar(a.aviso, a.apagado)
    if a.json:
        print(json.dumps(v, ensure_ascii=False, indent=1))
    else:
        print(f"VIGILANTE · límite {v['limite_pct']:g} % ({v['fuente_limite']}) · aviso {v['aviso_pct']:g} % · apagar {v['apagado_pct']:g} %")
        if v["sin_cuentas"]:
            print("Sin cuentas en vivo (no hay resultados/*_vivo.csv).")
        for c in v["cuentas"]:
            print(f"  {c['idea']}: {c['estado']} · caída actual {c.get('caida_actual_pct', '?')} % "
                  f"(peor {c.get('caida_max_pct', '?')} %) · {c.get('operaciones', 0)} operaciones")
            if c.get("comparacion"):
                print(f"    {c['comparacion']}")
            if c.get("detalle"):
                print(f"    {c['detalle']}")
    sys.exit(2 if v["apagar"] else 0)


if __name__ == "__main__":
    main()
