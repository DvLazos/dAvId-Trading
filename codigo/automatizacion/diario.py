"""Trabajo diario de la cueva (orquestador). Lo puede lanzar launchd cada mañana o tú a mano.

Pasos:
  a. ACTUALIZAR DATOS · codigo/automatizacion/actualizar_datos.py --json (si existe y no pides --sin-datos).
  b. RÉPLICA          · replica.py --json: ¿los backtests se repiten byte a byte?
  c. FICHAS           · estado_fichas.py --json: fase, veredicto y siguiente paso de cada idea.
  d. RIESGO Y FONDEO  · codigo/riesgo.py y codigo/fondeo_simulador.py <csv> --json para las ideas
                        que llegaron a la fase 06 (si esos scripts existen). Solo informan:
                        la fase 07 es CRITERIO y la decides tú.
  e. VIGILANTE        · vigilante.py --json: cuentas en vivo (resultados/*_vivo.csv) contra
                        backtest y caída contra los niveles de aviso (5 %) y apagado (8 %).
Escribe resultados/diario/informe_AAAA-MM-DD.md y añade una línea por paso a
resultados/diario/registro.log.

Nunca: aprueba fases, cambia el riesgo, opera, paga retos ni edita fichas.

Uso (desde cualquier carpeta):
  python3 codigo/automatizacion/diario.py               # completo
  python3 codigo/automatizacion/diario.py --sin-datos   # sin descargar datos (sin internet)
Código de salida: 0 todo bien · 1 algún backtest NO REPLICA · 2 alguna cuenta llegó a APAGAR
                  (si pasan las dos cosas, 2).
"""
import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent.parent
AUTO = RAIZ / "codigo" / "automatizacion"
CARPETA = RAIZ / "resultados" / "diario"
REGISTRO = CARPETA / "registro.log"
TIEMPO_MAX = 3600


def log(msg):
    CARPETA.mkdir(parents=True, exist_ok=True)
    with REGISTRO.open("a", encoding="utf-8") as f:
        f.write(f"{datetime.now():%Y-%m-%d %H:%M:%S}\t{msg}\n")


def correr(args, nombre):
    """Corre un script y devuelve (código, JSON o None, texto de error)."""
    t0 = datetime.now()
    try:
        p = subprocess.run([sys.executable, *map(str, args)], cwd=RAIZ, capture_output=True, text=True,
                           timeout=TIEMPO_MAX)
        codigo, out, err = p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        codigo, out, err = -1, "", f"tardó más de {TIEMPO_MAX} s"
    datos = None
    for intento in (out, out.strip().splitlines()[-1] if out.strip() else ""):
        try:
            datos = json.loads(intento)
            break
        except (json.JSONDecodeError, TypeError):
            continue
    seg = (datetime.now() - t0).total_seconds()
    ultimo_error = (err.strip().splitlines() or [""])[-1]
    log(f"{nombre}\tcódigo={codigo}\t{seg:.0f}s" + (f"\t{ultimo_error}" if codigo not in (0, 1, 2) or datos is None else ""))
    return codigo, datos, ultimo_error


def pct(x):
    return f"{x * 100:.0f} %"


def es(x):
    """Número con coma decimal y sin ceros sobrantes: 10.0 → 10 · 0.35 → 0,35."""
    if isinstance(x, (int, float)):
        return f"{x:g}".replace(".", ",")
    return str(x)


def main():
    ap = argparse.ArgumentParser(description="Trabajo diario de la cueva: datos, réplica, fichas, riesgo, vigilante.")
    ap.add_argument("--sin-datos", action="store_true", help="no descarga datos (paso a)")
    a = ap.parse_args()
    hoy = datetime.now()
    log(f"INICIO\t{'--sin-datos' if a.sin_datos else 'completo'}")
    criterio = []         # lo que necesita tu criterio hoy (lo urgente primero)
    criterio_fichas = []  # decisiones de fase pendientes (van al final)
    L = [f"# Informe diario · {hoy:%Y-%m-%d}", "",
         "> Lo escribe la máquina (codigo/automatizacion/diario.py). Solo informa: no aprueba fases, "
         "no cambia el riesgo, no opera y no paga retos. Tú decides.", ""]
    resumen = []

    # a. Datos -------------------------------------------------------------------------------
    act = AUTO / "actualizar_datos.py"
    L.append("## 1. Datos")
    if a.sin_datos:
        L.append("- No se descargaron datos hoy (`--sin-datos`).")
        resumen.append("datos: sin descargar")
    elif not act.exists():
        L.append("- Todavía no existe `codigo/automatizacion/actualizar_datos.py`: no se descargó nada.")
        resumen.append("datos: sin actualizador")
    else:
        c, d, err = correr([act, "--json"], "actualizar_datos")
        if d:
            conteo = ", ".join(f"{k}: {v}" for k, v in d.get("conteo", {}).items()) or "sin detalle"
            L.append(f"- Estado: **{d.get('estado', '?')}** ({conteo}).")
            malos = [r for r in d.get("archivos", []) if r.get("problemas")]
            for r in malos[:8]:
                L.append(f"  - {r.get('ticker')}: {'; '.join(r['problemas'])}")
            if malos:
                criterio.append(f"Revisa {len(malos)} archivo(s) de datos que no se actualizaron "
                                "(detalle en resultados/datos_actualizacion_calidad.md).")
            resumen.append(f"datos: {d.get('estado', '?')}")
        else:
            L.append(f"- El actualizador falló (código {c}): {err or 'sin detalle'}.")
            criterio.append("El actualizador de datos falló: mira resultados/diario/registro.log.")
            resumen.append("datos: ERROR")
    L.append("")

    # b. Réplica -----------------------------------------------------------------------------
    L.append("## 2. Réplica de los backtests")
    L.append("_Réplica = volver a correr cada script y comprobar que da exactamente lo mismo que está "
             "guardado. Si no, algo cambió (datos, versiones o código) y las fichas ya no se pueden creer a ciegas._")
    L.append("")
    c, rep, err = correr([AUTO / "replica.py", "--json"], "replica")
    falla_replica = False
    if rep:
        n_ok = sum(s["veredicto"] == "REPLICA" for s in rep["scripts"])
        n = len(rep["scripts"])
        L.append(f"- **{n_ok} de {n} REPLICA**" + (" (primera vez: se creó la base de huellas)." if rep.get("primera_vez") else "."))
        for s in rep["scripts"]:
            if s["veredicto"] != "REPLICA":
                L.append(f"  - {s['veredicto']} · `{s['id']}`")
                for dlt in s["diferencias"][:6]:
                    L.append(f"    - `{dlt}`")
        if rep.get("datos"):
            cambios = ", ".join(f"{k.replace('datos/', '')} ({v})" for k, v in sorted(rep["datos"].items()))
            L.append(f"- Datos distintos de la base: {cambios}. «ampliado» = solo se añadieron días nuevos "
                     "(normal); «modificado» = cambió la historia (no normal).")
        if rep.get("restaurados"):
            L.append(f"- OJO: se restauraron en resultados/: {', '.join(rep['restaurados'])}.")
        falla_replica = not rep["ok"]
        if falla_replica:
            criterio.append("Algún backtest NO REPLICA: no avances fases de esa idea hasta saber por qué "
                            "(pide al Director que revise la diferencia).")
        if any(s["veredicto"] == "NO COMPARABLE" for s in rep["scripts"]):
            criterio.append("Cambió la historia de algún CSV. Decide si aceptas los datos nuevos como base "
                            "(`replica.py --nueva-base`): las cifras de las fichas pueden dejar de coincidir.")
        resumen.append(f"réplica: {n_ok}/{n}")
    else:
        falla_replica = True
        L.append(f"- La réplica no pudo correr (código {c}): {err or 'sin detalle'}.")
        criterio.append("La réplica no pudo correr: mira resultados/diario/registro.log.")
        resumen.append("réplica: ERROR")
    L.append("")

    # c. Fichas ------------------------------------------------------------------------------
    L.append("## 3. Tus ideas (fichas)")
    c, ideas, err = correr([AUTO / "estado_fichas.py", "--json"], "estado_fichas")
    ideas = ideas or []
    for i in ideas:
        extra = f", llegó hasta la 0{i['fase_maxima']}" if i.get("fase_maxima", 0) > i.get("fase", 0) else ""
        L.append(f"- **{i['idea']}** · {i['fase_nombre']} → **{i['veredicto']}**{extra}.")
        L.append(f"  - Siguiente paso: {i['siguiente_paso']}")
        if i.get("proxima_es_criterio"):
            criterio_fichas.append(f"{i['idea']}: lo siguiente es la fase {i['proxima_fase']:02d}, que es CRITERIO "
                            "(la decides tú; la máquina no avanza sola).")
    if not ideas:
        L.append("- No se pudieron leer las fichas." if c else "- No hay fichas todavía.")
    resumen.append(f"fichas: {len(ideas)}")
    L.append("")

    # d. Riesgo y fondeo ---------------------------------------------------------------------
    L.append("## 4. Riesgo y fondeo (solo para ideas que llegaron a la fase 06)")
    L.append("_Son cálculos de ejemplo. La fase 07 (cuánto arriesgar) es CRITERIO: la decides tú. "
             "Nada se compra ni se activa._")
    L.append("")
    candidatas = [i for i in ideas if i.get("fase_maxima", 0) >= 6]
    scripts_d = [("riesgo", RAIZ / "codigo" / "riesgo.py"), ("fondeo", RAIZ / "codigo" / "fondeo_simulador.py")]
    if not candidatas:
        L.append("- Ninguna idea llegó a la fase 06.")
    for i in candidatas:
        csv = RAIZ / "resultados" / f"{i['idea']}_operaciones.csv"
        if not csv.exists():
            L.append(f"- {i['idea']}: falta resultados/{csv.name}.")
            continue
        aviso_ficha = "" if i["veredicto"] == "APRUEBA" else f" (OJO: su último veredicto es {i['veredicto']}: solo ejercicio)"
        L.append(f"- **{i['idea']}**{aviso_ficha}")
        for nombre, script in scripts_d:
            if not script.exists():
                L.append(f"  - {nombre}: el script todavía no existe (se salta).")
                continue
            c, d, err = correr([script, csv.relative_to(RAIZ), "--json"], f"{nombre} {i['idea']}")
            if not d:
                L.append(f"  - {nombre}: falló (código {c}): {err or 'sin detalle'}.")
                continue
            if nombre == "riesgo":
                L.append(f"  - riesgo: con un límite de caída del {es(d.get('limite_pct', '?'))} %, fracción fija propuesta "
                         f"{es(d.get('ff_riesgo_pct', '?'))} % por operación (prudente {es(d.get('ff_riesgo_prudente_pct', '?'))} %); "
                         f"caída del percentil 95 (el 95 % de los casos cae menos) {es(d.get('ff_caida_p95_pct', '?'))} %. "
                         f"Informe: {d.get('informe', '?')}.")
            else:
                perf = d.get("perfiles", {})
                txt = "; ".join(f"{k}: pasa {pct(v.get('p_pasa', 0))}" for k, v in perf.items())
                L.append(f"  - fondeo (riesgo {es(d.get('riesgo_pct', '?'))} %): {txt or 'sin perfiles'}; "
                         f"encaje {d.get('encaje', '?')}; compra permitida: {'sí' if d.get('compra_permitida') else 'no'}. "
                         f"Informe: {d.get('informe', '?')}.")
    L.append("")

    # e. Vigilante ---------------------------------------------------------------------------
    L.append("## 5. Vigilante (cuentas en vivo)")
    c, vig, err = correr([AUTO / "vigilante.py", "--json"], "vigilante")
    apagar = False
    if vig is None:
        L.append(f"- El vigilante falló (código {c}): {err or 'sin detalle'}.")
        criterio.append("El vigilante no pudo correr: revisa tus cuentas a mano hoy.")
        resumen.append("vigilante: ERROR")
    elif vig["sin_cuentas"]:
        L.append("- Sin cuentas en vivo (no hay `resultados/*_vivo.csv`).")
        resumen.append("vigilante: sin cuentas en vivo")
    else:
        L.append(f"- Niveles: aviso {es(vig['aviso_pct'])} % · apagar {es(vig['apagado_pct'])} % "
                 f"(límite {es(vig['limite_pct'])} %, {vig['fuente_limite']}).")
        for cta in vig["cuentas"]:
            L.append(f"- **{cta['idea']}**: {cta['estado']} · caída actual {es(cta.get('caida_actual_pct', '?'))} % "
                     f"(peor {es(cta.get('caida_max_pct', '?'))} %) · {cta.get('operaciones', 0)} operaciones.")
            if cta.get("comparacion"):
                L.append(f"  - Vivo contra backtest: {cta['comparacion']}.")
            if cta["estado"] == "APAGAR":
                criterio.insert(0, f"**APAGAR {cta['idea']}**: su caída llegó al {es(cta['caida_actual_pct'])} %. "
                                   "Apaga tú el robot y las alertas (kill-switch). La máquina no lo hace.")
            elif cta["estado"] == "AVISO":
                criterio.append(f"{cta['idea']}: caída en zona de aviso ({es(cta['caida_actual_pct'])} %). Mírala hoy.")
            if cta.get("desvio"):
                criterio.append(f"{cta['idea']}: en vivo rinde peor que el backtest. Revisa costes y ejecución.")
        apagar = bool(vig["apagar"])
        resumen.append(f"vigilante: {len(vig['cuentas'])} cuenta(s), apagar: {len(vig['apagar'])}")
    L.append("")

    # Criterio -------------------------------------------------------------------------------
    L.append("## Lo que necesita tu criterio hoy")
    criterio += criterio_fichas
    if criterio:
        L += [f"{n}. {t}" for n, t in enumerate(dict.fromkeys(criterio), 1)]
    else:
        L.append("Nada urgente. Todo replica y no hay alertas.")
    L.append("")
    L.append("_Glosario rápido: **fase CRITERIO** = la decides tú · **backtest** = probar la regla en el pasado · "
             "**caída** = cuánto baja la cuenta desde su máximo · **kill-switch** = apagar todo._")

    CARPETA.mkdir(parents=True, exist_ok=True)
    ruta = CARPETA / f"informe_{hoy:%Y-%m-%d}.md"
    ruta.write_text("\n".join(L) + "\n", encoding="utf-8")
    codigo = 2 if apagar else (1 if falla_replica else 0)
    log(f"FIN\tcódigo={codigo}\t{' · '.join(resumen)}\t{ruta.relative_to(RAIZ)}")
    print(f"Informe: {ruta.relative_to(RAIZ)}")
    print(" · ".join(resumen))
    print(f"Código de salida: {codigo}")
    sys.exit(codigo)


if __name__ == "__main__":
    main()
