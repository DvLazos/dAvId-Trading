"""Informe semanal · una página para leer el lunes y decidir.

Junta los 7 informes diarios más recientes (resultados/diario/informe_AAAA-MM-DD.md) y escribe
resultados/informe_semanal_AAAA-MM-DD.md con:
  - cuántos días replicaron los backtests y qué falló,
  - avisos del vigilante (caída, desvíos, APAGAR),
  - el estado de cada idea (del informe más reciente),
  - lo que necesita tu criterio (cuántos días apareció cada punto),
  - la lección de la semana: un término del glosario, rotando por número de semana.
Solo lee los informes diarios: no corre backtests, no aprueba nada, no opera.

Uso: python3 codigo/automatizacion/semanal.py [--dias 7]
"""
import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent.parent
CARPETA = RAIZ / "resultados" / "diario"
REGISTRO = CARPETA / "registro.log"

# Glosario mínimo para la «lección de la semana». Cuando exista metodo/GLOSARIO.md, puede
# reemplazarlo. Cada entrada: (término, explicación simple, pregunta para pensar).
GLOSARIO = [
    ("Fuera de muestra (OOS)", "El 30 % más reciente de los datos, que la regla no vio al diseñarse. Es el único examen que cuenta.",
     "¿Alguna de tus ideas se diseñó mirando datos que después usaste para juzgarla?"),
    ("Factor de beneficio", "Lo que ganan las operaciones ganadoras dividido entre lo que pierden las perdedoras. 1,3 o más pide TIS.",
     "Si quitas la mejor operación, ¿sigue por encima de 1?"),
    ("Caída máxima (drawdown)", "La peor bajada de la cuenta desde un máximo. Tu límite personal es 10 %.",
     "¿Cuánto dinero sería un 8 % de tu cuenta? ¿Lo aguantarías sin tocar nada?"),
    ("Sesgo de supervivencia", "Probar solo con las acciones que siguen vivas o que crecieron. Infla los resultados (pasó en cesta10).",
     "¿Tu lista de acciones se eligió con información de hoy?"),
    ("Sobreajuste", "Que la regla se adapte al ruido del pasado y no a algo que se repite. Pasa más cuantas más variantes pruebas.",
     "¿Cuántas versiones de la misma idea llevas probadas sobre los mismos datos?"),
    ("Meseta, no pico", "Una regla buena funciona también con parámetros vecinos. Si solo funciona con uno exacto, es un pico: casualidad.",
     "Si cambias un parámetro un poco, ¿el resultado se derrumba?"),
    ("Monte Carlo", "Barajar miles de veces el orden de las operaciones para ver caídas posibles que el backtest no mostró.",
     "¿Tu caída aceptable cubre el 95 % de esos órdenes posibles?"),
    ("Costes y deslizamiento", "Comisión + diferencia entre el precio que esperabas y el que te dieron. Sin costes, el resultado no cuenta.",
     "¿Qué pasa con tu idea si los costes se duplican?"),
    ("Réplica", "Volver a correr el backtest y obtener exactamente lo mismo. Si no replica, el número de la ficha ya no es de fiar.",
     "¿Sabrías volver a obtener las cifras de tu ficha dentro de un año?"),
    ("Kill-switch", "El interruptor que apaga robots y alertas. Lo aprietas tú cuando la caída llega al nivel de apagado (8 %).",
     "¿Puedes apagar todo en menos de 5 minutos? ¿Lo has practicado?"),
    ("Fase CRITERIO", "Las fases 01 (hipótesis), 02 (AED) y 07 (riesgo) las decides tú. La máquina ordena; tú apruebas.",
     "¿Qué decisión de criterio llevas más tiempo posponiendo?"),
    ("Fracción fija", "Arriesgar el mismo % de la cuenta en cada operación (por ejemplo, 0,5 %). Al crecer la cuenta, crece el tamaño.",
     "¿Cuánto perderías en 10 operaciones perdedoras seguidas con tu fracción?"),
]


def leer(ruta):
    texto = ruta.read_text(encoding="utf-8")
    secciones, actual = {}, None
    for l in texto.splitlines():
        if l.startswith("## "):
            actual = l[3:].strip()
            secciones[actual] = []
        elif actual:
            secciones[actual].append(l)
    return secciones


def seccion(secs, inicio):
    for k, v in secs.items():
        if k.startswith(inicio) or inicio in k:
            return v
    return []


def main():
    ap = argparse.ArgumentParser(description="Informe semanal a partir de los informes diarios.")
    ap.add_argument("--dias", type=int, default=7, help="cuántos informes diarios juntar (defecto 7)")
    a = ap.parse_args()
    hoy = datetime.now()
    diarios = sorted(CARPETA.glob("informe_????-??-??.md"))[-a.dias:]
    L = [f"# Informe semanal · {hoy:%Y-%m-%d}", "",
         "> Resumen de la semana para que tú decidas. Lo escribe codigo/automatizacion/semanal.py "
         "a partir de los informes diarios. No aprueba fases, no cambia el riesgo, no opera.", ""]
    if not diarios:
        L += ["No hay informes diarios en resultados/diario/. Corre primero "
              "`python3 codigo/automatizacion/diario.py --sin-datos`.", ""]
    else:
        fechas = [d.stem.replace("informe_", "") for d in diarios]
        L.append(f"Informes leídos: {len(diarios)} (del {fechas[0]} al {fechas[-1]}).")
        L.append("")
        datos = {f: leer(d) for f, d in zip(fechas, diarios)}

        # Réplica día a día
        L.append("## 1. Réplica de los backtests")
        dias_ok = 0
        fallos = []
        for f, secs in datos.items():
            sec = seccion(secs, "2. Réplica")
            m = next((re.search(r"\*\*(\d+) de (\d+) REPLICA\*\*", l) for l in sec if "REPLICA**" in l), None)
            if m and m.group(1) == m.group(2):
                dias_ok += 1
            else:
                fallos.append(f)
                L.append(f"- {f}: " + (f"{m.group(1)} de {m.group(2)} replicaron." if m else "la réplica no corrió."))
                L += [f"  {l.strip()}" for l in sec if l.strip().startswith("- ") and ("NO " in l or "OJO" in l)][:4]
        L.append(f"- Días con todo replicando: **{dias_ok} de {len(datos)}**.")
        L.append("")

        # Vigilante
        L.append("## 2. Vigilante (cuentas en vivo)")
        alertas = []
        for f, secs in datos.items():
            for l in seccion(secs, "5. Vigilante"):
                if any(p in l for p in ("APAGAR", "AVISO", "DESVÍO", "falló")):
                    alertas.append(f"- {f}: {l.strip('- ').strip()}")
        if alertas:
            L += alertas
        else:
            sin = all(any("Sin cuentas en vivo" in l for l in seccion(s, "5. Vigilante")) for s in datos.values())
            L.append("- Sin cuentas en vivo esta semana." if sin else "- Sin avisos: las cuentas se mantuvieron lejos de los límites.")
        L.append("")

        # Ideas (último informe)
        L.append(f"## 3. Tus ideas (estado al {fechas[-1]})")
        L += [l for l in seccion(datos[fechas[-1]], "3. Tus ideas") if l.strip()]
        L.append("")

        # Criterio acumulado
        L.append("## 4. Lo que necesita tu criterio esta semana")
        cuenta = {}
        for secs in datos.values():
            for l in seccion(secs, "Lo que necesita tu criterio"):
                m = re.match(r"\d+\.\s+(.*)", l.strip())
                if m:
                    cuenta[m.group(1)] = cuenta.get(m.group(1), 0) + 1
        if cuenta:
            orden = sorted(cuenta.items(), key=lambda kv: (not kv[0].startswith("**APAGAR"), -kv[1]))
            L += [f"{n}. {t} _(apareció {c} de {len(datos)} días)_" for n, (t, c) in enumerate(orden, 1)]
        else:
            L.append("Nada pendiente.")
        L.append("")

    # Lección de la semana
    semana = hoy.isocalendar().week
    termino, expl, pregunta = GLOSARIO[semana % len(GLOSARIO)]
    L += ["## 5. Lección de la semana", f"**{termino}.** {expl}", "", f"Para pensar: {pregunta}", ""]

    ruta = RAIZ / "resultados" / f"informe_semanal_{hoy:%Y-%m-%d}.md"
    ruta.write_text("\n".join(L) + "\n", encoding="utf-8")
    CARPETA.mkdir(parents=True, exist_ok=True)
    with REGISTRO.open("a", encoding="utf-8") as f:
        f.write(f"{hoy:%Y-%m-%d %H:%M:%S}\tsemanal\t{len(diarios)} informes\t{ruta.relative_to(RAIZ)}\n")
    print(f"Informe semanal: {ruta.relative_to(RAIZ)} ({len(diarios)} informes diarios)")
    print(f"Lección de la semana: {termino}")
    sys.exit(0)


if __name__ == "__main__":
    main()
