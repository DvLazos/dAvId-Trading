"""Estado de las fichas · ¿en qué fase está cada idea?

Lee fichas/*.md (salta las que empiezan por EJEMPLO) y, para cada idea, saca:
  - la ÚLTIMA fase trabajada (el último bloque «## Fase 0X ...» de la ficha, en orden de archivo,
    porque un anexo o una versión nueva puede venir después y es lo más reciente),
  - su veredicto (APRUEBA · NO APRUEBA · PENDIENTE) y su «Siguiente paso»,
  - la fase más alta a la que llegó (aunque después la tumbara un anexo).
Solo LEE: nunca cambia una ficha ni aprueba nada.

Uso (desde la raíz del repositorio):
  python3 codigo/automatizacion/estado_fichas.py          # resumen en pantalla
  python3 codigo/automatizacion/estado_fichas.py --json   # para diario.py
"""
import argparse
import json
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent.parent
FICHAS = RAIZ / "fichas"
TIPOS = {1: "CRITERIO", 2: "CRITERIO + DATOS", 3: "MOTOR", 4: "MOTOR", 5: "MOTOR", 6: "MOTOR",
         7: "CRITERIO", 8: "DOCUMENTACIÓN"}
RX_FASE = re.compile(r"^##\s*Fase\s*0?(\d)\s*·\s*(.+?)\s*$")


def campo(lineas, nombre):
    for l in lineas:
        if l.lower().startswith(nombre.lower() + ":"):
            return l.split(":", 1)[1].strip()
    return ""


def veredicto_corto(texto):
    t = texto.upper()
    for v in ("NO APRUEBA", "APRUEBA", "PENDIENTE"):
        if t.startswith(v):
            return v
    return "SIN VEREDICTO"


def leer_ficha(ruta):
    lineas = ruta.read_text(encoding="utf-8").splitlines()
    titulo = next((l.lstrip("# ").replace("FICHA · ", "").strip() for l in lineas if l.startswith("# ")), ruta.stem)
    bloques = []
    for i, l in enumerate(lineas):
        m = RX_FASE.match(l)
        if not m:
            continue
        fin = next((j for j in range(i + 1, len(lineas)) if lineas[j].startswith("## ")), len(lineas))
        cuerpo = lineas[i + 1:fin]
        partes = [p.strip() for p in m.group(2).split("·")]
        ver = campo(cuerpo, "Veredicto")
        bloques.append({
            "fase": int(m.group(1)),
            "nombre": partes[0],
            "encabezado": l.lstrip("# ").strip(),
            "veredicto": veredicto_corto(ver),
            "veredicto_texto": ver,
            "siguiente_paso": campo(cuerpo, "Siguiente paso"),
            "resultado": campo(cuerpo, "Resultado"),
        })
    idea = {"idea": ruta.stem, "archivo": str(ruta.relative_to(RAIZ)), "titulo": titulo, "bloques": len(bloques)}
    if not bloques:
        idea.update(fase=0, fase_nombre="sin fases", veredicto="SIN VEREDICTO", siguiente_paso="Fase 01 (hipótesis).",
                    fase_maxima=0, tipo="")
        return idea
    u = bloques[-1]
    idea.update(fase=u["fase"], fase_nombre=u["encabezado"], tipo=TIPOS.get(u["fase"], ""),
                veredicto=u["veredicto"], veredicto_texto=u["veredicto_texto"],
                siguiente_paso=u["siguiente_paso"], fase_maxima=max(b["fase"] for b in bloques),
                fases=[{"fase": b["fase"], "encabezado": b["encabezado"], "veredicto": b["veredicto"]} for b in bloques])
    # ¿Qué le toca a la siguiente fase? Si es CRITERIO, la decide el trader.
    proxima = u["fase"] + 1 if u["veredicto"] == "APRUEBA" else u["fase"]
    if u["veredicto"] == "NO APRUEBA" and "fase 01" in u["siguiente_paso"].lower():
        proxima = 1
    idea["proxima_fase"] = proxima
    idea["proxima_es_criterio"] = TIPOS.get(proxima, "").startswith("CRITERIO")
    return idea


def estado():
    return [leer_ficha(p) for p in sorted(FICHAS.glob("*.md")) if not p.name.upper().startswith("EJEMPLO")]


def main():
    ap = argparse.ArgumentParser(description="Fase y veredicto de cada ficha (solo lectura).")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    ideas = estado()
    if a.json:
        print(json.dumps(ideas, ensure_ascii=False, indent=1))
        return
    print(f"ESTADO DE LAS FICHAS · {len(ideas)} ideas\n")
    for i in ideas:
        print(f"{i['idea']}")
        print(f"  Última fase: {i['fase_nombre']} → {i['veredicto']}"
              + (f" (llegó hasta la fase {i['fase_maxima']:02d})" if i["fase_maxima"] > i["fase"] else ""))
        print(f"  Siguiente paso: {i['siguiente_paso']}\n")


if __name__ == "__main__":
    main()
