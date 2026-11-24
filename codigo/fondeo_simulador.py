"""Simulador de fondeo · genérico (cualquier idea con su lista de operaciones).

Aplica las reglas de un reto de empresa de fondeo (objetivo de ganancia, pérdida diaria, pérdida
total fija o arrastrada, días mínimos, consistencia, costo) a las operaciones de un backtest.
Monte Carlo con remuestreo (semilla 42, 10.000 intentos): cada intento arma una historia nueva
sacando días y operaciones al azar del backtest, y mira si pasa, falla o no termina a tiempo.

Los perfiles están en codigo/fondeo_perfiles.json y sus números son EJEMPLOS: el trader los copia
de las reglas oficiales vigentes de cada empresa. Este simulador no compra nada ni aprueba nada.

Uso: python3 codigo/fondeo_simulador.py resultados/<idea>_operaciones.csv [perfil]
         [--riesgo 0.5] [--horizonte 260] [--json]
     Sin perfil corre todos los perfiles del JSON.
"""
import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from riesgo import RAIZ, cargar_operaciones, estado_validacion, nombre_idea, num, pct

SIMS, SEMILLA = 10_000, 42
REJILLA = [0.0025, 0.005, 0.0075, 0.01, 0.0125, 0.015, 0.02, 0.025, 0.03]   # riesgo por operación
DIAS_MES = 21


def calendario(ops):
    """Cuántas operaciones cierran cada día hábil del backtest (incluye los días sin operaciones)."""
    dias = pd.bdate_range(ops["entrada"].min().normalize(), ops["salida"].max().normalize())
    cuenta = ops["salida"].dt.normalize().value_counts()
    return cuenta.reindex(dias, fill_value=0).to_numpy()


def sorteo(ops, horizonte):
    """Sorteo común para todos los niveles de riesgo (así la comparación es justa)."""
    rng = np.random.default_rng(SEMILLA)
    por_dia = calendario(ops)
    k = rng.choice(por_dia, size=(SIMS, horizonte)).astype(np.int16)
    maxk = max(int(k.max()), 1)
    idx = rng.integers(0, len(ops), size=(SIMS, horizonte, maxk), dtype=np.int32)
    return k, idx, por_dia


def simular(R, k, idx, perfil, riesgo):
    """Un intento por fila. Devuelve el estado final de cada intento."""
    n, H = k.shape
    cta = float(perfil["cuenta"])
    riesgo_dinero = riesgo * cta                      # fijo sobre la cuenta inicial (supuesto)
    objetivo = perfil["objetivo_pct"] / 100 * cta
    pdiaria = perfil.get("perdida_diaria_max_pct")
    base_diaria = perfil.get("base_perdida_diaria", "saldo_inicio_dia")
    ptotal = perfil.get("perdida_total_max_pct")
    arrastre = perfil.get("caida_arrastrada_pct")
    congela = cta * (1 + (perfil.get("arrastrada_se_congela_en_pct") or 0) / 100)
    dmin = perfil.get("dias_minimos") or 0
    cons = perfil.get("consistencia_max_dia_pct")

    bal = np.full(n, cta)
    pico = np.full(n, cta)
    estado = np.zeros(n, np.int8)                     # 0 en curso · 1 pasa · 2 falla
    motivo = np.full(n, "", dtype=object)
    dias_op = np.zeros(n, np.int32)
    ops_n = np.zeros(n, np.int32)
    mejor_dia = np.zeros(n)
    dia_fin = np.full(n, H, np.int32)
    ops_fin = np.zeros(n, np.int32)

    for d in range(H):
        vivo = estado == 0
        if not vivo.any():
            break
        inicio = bal.copy()
        pnl_dia = np.zeros(n)
        for j in range(idx.shape[2]):
            m = vivo & (estado == 0) & (k[:, d] > j)
            if not m.any():
                break
            p = riesgo_dinero * R[idx[m, d, j]]
            bal[m] += p
            pnl_dia[m] += p
            ops_n[m] += 1
            falla = np.zeros(n, bool)
            if pdiaria:
                base = inicio if base_diaria == "saldo_inicio_dia" else cta
                fd = m & (bal <= inicio - pdiaria / 100 * base)
                motivo[fd & (estado == 0)] = "pérdida diaria"
                falla |= fd
            if ptotal:
                ft = m & (bal <= cta * (1 - ptotal / 100))
                motivo[ft & (estado == 0) & ~falla] = "pérdida total"
                falla |= ft
            if arrastre:
                piso = np.minimum(pico - arrastre / 100 * cta, congela)
                fa = m & (bal <= piso)
                motivo[fa & (estado == 0) & ~falla] = "caída arrastrada"
                falla |= fa
            nuevo = falla & (estado == 0)
            estado[nuevo] = 2
            dia_fin[nuevo] = d + 1
            ops_fin[nuevo] = ops_n[nuevo]
        # cierre del día
        sigue = vivo & (estado == 0)
        dias_op[sigue & (k[:, d] > 0)] += 1
        mejor_dia[sigue] = np.maximum(mejor_dia[sigue], pnl_dia[sigue])
        pico[sigue] = np.maximum(pico[sigue], bal[sigue])   # arrastre sobre el saldo de cierre (supuesto)
        ganancia = bal - cta
        ok = sigue & (ganancia >= objetivo) & (dias_op >= dmin)
        if cons:
            ok &= mejor_dia <= cons / 100 * ganancia
        estado[ok] = 1
        dia_fin[ok] = d + 1
        ops_fin[ok] = ops_n[ok]
    ops_fin[estado == 0] = ops_n[estado == 0]
    return dict(estado=estado, dia_fin=dia_fin, ops_fin=ops_fin, motivo=motivo)


def medir(res, perfil):
    e = res["estado"]
    p_pasa, p_falla, p_nada = (e == 1).mean(), (e == 2).mean(), (e == 0).mean()
    if perfil.get("tipo_costo") == "mensual":
        costo = perfil["costo_reto"] * np.ceil(res["dia_fin"] / DIAS_MES)
    else:
        costo = np.full(len(e), float(perfil["costo_reto"]))
    pasan = e == 1
    motivos = pd.Series(res["motivo"][e == 2]).value_counts(normalize=True).to_dict()
    return dict(p_pasa=float(p_pasa), p_falla=float(p_falla), p_sin_terminar=float(p_nada),
                mediana_dias=float(np.median(res["dia_fin"][pasan])) if pasan.any() else None,
                mediana_ops=float(np.median(res["ops_fin"][pasan])) if pasan.any() else None,
                costo_intento=float(costo.mean()),
                costo_por_fondeada=float(costo.mean() / p_pasa) if p_pasa > 0 else None,
                motivos_falla=motivos)


def encaje(ops, por_dia):
    semanas = max(len(por_dia) / 5, 1e-9)
    por_semana = len(ops) / semanas
    dur = float((ops["salida"] - ops["entrada"]).dt.days.median())
    avisos = []
    if por_semana < 2:
        avisos.append(f"pocas operaciones: {num(por_semana, 2)} por semana. Un reto suele pedir llegar al objetivo en pocas semanas.")
    if dur > 1:
        avisos.append(f"duración mediana de {num(dur, 0)} días naturales: deja posiciones abiertas de noche y el fin de semana, "
                      "algo que muchas empresas limitan o prohíben. Además, la empresa mide la pérdida diaria con lo abierto "
                      "(flotante) y este simulador solo ve operaciones cerradas: la realidad sería peor.")
    return por_semana, dur, avisos


def main():
    ap = argparse.ArgumentParser(description="Simulador de retos de fondeo (Monte Carlo). No compra ni aprueba nada.")
    ap.add_argument("csv")
    ap.add_argument("perfil", nargs="?", help="nombre del perfil en codigo/fondeo_perfiles.json (por defecto, todos)")
    ap.add_argument("--riesgo", type=float, default=0.5, help="riesgo por operación en %% de la cuenta (defecto 0,5)")
    ap.add_argument("--horizonte", type=int, default=260, help="días hábiles máximos si el perfil no trae límite")
    ap.add_argument("--json", action="store_true", help="imprime solo un resumen JSON de una línea")
    a = ap.parse_args()

    perfiles_todos = json.loads((RAIZ / "codigo" / "fondeo_perfiles.json").read_text(encoding="utf-8"))
    perfiles = {k: v for k, v in perfiles_todos.items() if not k.startswith("_")}
    if a.perfil:
        if a.perfil not in perfiles:
            raise SystemExit(f"Perfil «{a.perfil}» no existe. Hay: {', '.join(perfiles)}")
        perfiles = {a.perfil: perfiles[a.perfil]}

    idea = nombre_idea(a.csv)
    ops, fuente_stop = cargar_operaciones(a.csv)
    R = ops["R"].to_numpy()
    validada, det_val = estado_validacion(idea, fases=(1, 2, 3, 4, 5, 6, 7))
    riesgo = a.riesgo / 100

    L = [f"# Fondeo · {idea} · simulador de retos\n"]
    L.append("> **Ningún reto se compra si la estrategia no aprobó las fases 01 a 07** y tú no aceptaste por escrito "
             "la probabilidad de pasar. Este informe propone; tú decides.\n")
    if not validada:
        L.append(f"> **SOLO EJERCICIO, ESTRATEGIA NO VALIDADA** ({det_val}). Sirve para aprender a usar el simulador.\n")
    L.append(f"> **Los números de los perfiles son EJEMPLOS** (`codigo/fondeo_perfiles.json`). Cópialos de las reglas "
             "oficiales vigentes de cada empresa antes de sacar conclusiones.\n")

    resultados, ops_por_dia = {}, None
    for nombre, perfil in perfiles.items():
        H = perfil.get("dias_maximos") or a.horizonte
        k, idx, por_dia = sorteo(ops, H)
        ops_por_dia = por_dia
        base = medir(simular(R, k, idx, perfil, riesgo), perfil)
        rejilla = [(r, medir(simular(R, k, idx, perfil, r), perfil)) for r in REJILLA]
        mejor_r, mejor = max(rejilla, key=lambda x: (round(x[1]["p_pasa"], 4), -x[0]))
        resultados[nombre] = dict(perfil=perfil, H=H, base=base, rejilla=rejilla, mejor=(mejor_r, mejor))

    por_semana, dur, avisos = encaje(ops, ops_por_dia)
    L.append("## Datos de partida")
    L.append(f"- {len(ops)} operaciones de `{a.csv}` · {num(por_semana, 2)} por semana · duración mediana {num(dur, 0)} días.")
    L.append(f"- Riesgo = distancia al stop ({fuente_stop}). 1 R = perder un stop completo.")
    L.append(f"- Riesgo por operación de referencia: {pct(riesgo, 2)} de la cuenta inicial"
             f"{' (supuesto)' if a.riesgo == 0.5 else ''}, fijo (sin interés compuesto).")
    L.append(f"- Monte Carlo: {num(SIMS, 0)} intentos, semilla 42. Cada día se sortea cuántas operaciones cierran "
             "(copiando los días reales del backtest, también los vacíos) y qué resultado tiene cada una.\n")
    if avisos:
        L.append("## Encaje con el fondeo: POBRE")
        for t in avisos:
            L.append(f"- {t}")
        L.append("- Los retos de fondeo suelen operarse en índices, forex o futuros y premian llegar al objetivo en pocas "
                 "semanas. Una estrategia semanal en acciones encaja mal: el fondeo probablemente necesite ideas propias más rápidas.\n")

    L.append("**Palabras clave.** *Objetivo*: ganancia que hay que alcanzar para pasar. *Pérdida diaria / total*: "
             "si la cuenta baja eso, el reto se pierde. *Caída arrastrada (trailing)*: el límite de pérdida sube con "
             "el máximo de la cuenta. *Consistencia*: el mejor día no puede ser más de cierto % de la ganancia total.\n")

    for nombre, r in resultados.items():
        p, b, (mr, m) = r["perfil"], r["base"], r["mejor"]
        L.append(f"## Perfil «{nombre}» (EJEMPLO, no es una empresa real)")
        L.append(f"- {p['descripcion']}")
        reglas = [f"cuenta {num(p['cuenta'], 0)}", f"objetivo {num(p['objetivo_pct'])} %"]
        if p.get("perdida_diaria_max_pct"):
            reglas.append(f"pérdida diaria {num(p['perdida_diaria_max_pct'])} %")
        if p.get("perdida_total_max_pct"):
            reglas.append(f"pérdida total {num(p['perdida_total_max_pct'])} % ({'arrastrada' if p.get('tipo_perdida_total') == 'arrastrada' else 'fija'})")
        if p.get("caida_arrastrada_pct"):
            reglas.append(f"caída arrastrada {num(p['caida_arrastrada_pct'])} %")
        if p.get("dias_minimos"):
            reglas.append(f"{p['dias_minimos']} días mínimos con operaciones")
        if p.get("consistencia_max_dia_pct"):
            reglas.append(f"consistencia: mejor día ≤ {num(p['consistencia_max_dia_pct'], 0)} % de la ganancia")
        reglas.append(f"costo {num(p['costo_reto'], 0)} ({'cada mes' if p.get('tipo_costo') == 'mensual' else 'pago único'})")
        L.append("- Reglas usadas: " + " · ".join(reglas) + ".")
        L.append(f"- Plazo: {r['H']} días hábiles{'' if p.get('dias_maximos') else ' (supuesto: el perfil no trae límite)'}.")
        L.append(f"- **Con {pct(riesgo, 2)} por operación:** pasa {pct(b['p_pasa'])} · falla {pct(b['p_falla'])} · "
                 f"no termina a tiempo {pct(b['p_sin_terminar'])}.")
        if b["mediana_dias"] is not None:
            L.append(f"- Cuando pasa: mediana de {num(b['mediana_dias'], 0)} días hábiles y {num(b['mediana_ops'], 0)} operaciones.")
        if b["motivos_falla"]:
            L.append("- Por qué falla: " + ", ".join(f"{k} {pct(v, 0)}" for k, v in b["motivos_falla"].items()) + ".")
        cpf = b["costo_por_fondeada"]
        L.append(f"- Costo medio por intento {num(b['costo_intento'], 0)} → **costo esperado por cuenta fondeada: "
                 f"{num(cpf, 0) if cpf else 'infinito (nunca pasa)'}** (costo por intento ÷ probabilidad de pasar).")
        L.append("\nRejilla de riesgo por operación → pasa · falla · no termina · costo por fondeada:")
        for rv, mm in r["rejilla"]:
            c = mm["costo_por_fondeada"]
            L.append(f"- {pct(rv, 2)} → {pct(mm['p_pasa'])} · {pct(mm['p_falla'])} · {pct(mm['p_sin_terminar'])} · "
                     f"{num(c, 0) if c else '—'}")
        L.append(f"\n**Riesgo que maximiza la probabilidad de pasar en la rejilla: {pct(mr, 2)}** "
                 f"(pasa {pct(m['p_pasa'])}, falla {pct(m['p_falla'])}). Ojo: más riesgo también acerca la pérdida "
                 "máxima; en una cuenta fondeada real el riesgo suele tener que bajar. Nunca uses más riesgo que el que "
                 "aceptaste en la fase 07 (`resultados/<idea>_riesgo.md`) solo para pasar más rápido.\n")

    L.append("## Antes de comprar cualquier reto (lista corta; la completa está en la skill fondeo)")
    L.append("- [ ] La estrategia aprobó las fases 01 a 07.")
    L.append("- [ ] Leíste en la web oficial, con fecha, si permiten: robots/EA, copiar operaciones, webhooks/puentes, "
             "VPS, dejar posiciones de noche y fin de semana, operar noticias, y la misma estrategia en varias cuentas.")
    L.append("- [ ] Copiaste las reglas a un perfil propio y volviste a correr este simulador.")
    L.append("- [ ] Aceptaste por escrito la probabilidad de pasar y el costo esperado.")
    L.append("\n## Supuestos")
    L.append("- Los perfiles son ejemplos, no reglas reales.")
    L.append("- La pérdida diaria y la caída arrastrada se miden con operaciones cerradas (las empresas suelen usar el "
             "flotante: la realidad es más dura). El arrastre se actualiza con el saldo de cierre del día.")
    L.append("- Días con operación = días en que cierra al menos una operación. Riesgo fijo sobre la cuenta inicial.")
    L.append("- Las operaciones y los días del backtest representan a los futuros (remuestreo con reemplazo, sin racimos). "
             "Se usan todas las operaciones del CSV, también las de dentro de muestra, que suelen ser optimistas.")
    L.append("\n*Generado por `codigo/fondeo_simulador.py`. Determinista: mismo CSV y mismos perfiles, mismo resultado.*")

    salida = RAIZ / "resultados" / f"{idea}_fondeo.md"
    salida.write_text("\n".join(L) + "\n", encoding="utf-8")

    resumen = dict(idea=idea, skill="fondeo", validada=validada, estado_ficha=det_val, riesgo_pct=a.riesgo,
                   encaje="pobre" if avisos else "aceptable", informe=str(salida.relative_to(RAIZ)),
                   perfiles={n: dict(p_pasa=round(r["base"]["p_pasa"], 4), p_falla=round(r["base"]["p_falla"], 4),
                                     p_sin_terminar=round(r["base"]["p_sin_terminar"], 4),
                                     mediana_dias=r["base"]["mediana_dias"],
                                     costo_por_fondeada=round(r["base"]["costo_por_fondeada"], 0) if r["base"]["costo_por_fondeada"] else None,
                                     mejor_riesgo_pct=round(r["mejor"][0] * 100, 2),
                                     mejor_p_pasa=round(r["mejor"][1]["p_pasa"], 4))
                             for n, r in resultados.items()},
                   compra_permitida=False if not validada else "solo si el trader lo acepta por escrito")
    if a.json:
        print(json.dumps(resumen, ensure_ascii=False))
    else:
        print("\n".join(L))
        print(f"\nInforme: {salida.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
