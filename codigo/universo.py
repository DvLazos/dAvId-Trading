"""Universo sin sesgo de supervivencia (skill universo).

Responde dos preguntas SIN mirar el futuro:
  1) ¿Qué tickers estaban en el índice en la fecha X?
  2) ¿Cuáles eran las N mayores en la fecha X, usando solo datos hasta X?

Lee un archivo de cambios del índice (altas y bajas por fecha):
    fecha_efectiva,ticker,accion,fuente
    2015-12-21,EJEMPLO_A,alta,anuncio oficial Nasdaq 2015-12-11

No trae datos históricos de componentes: los rellena el trader desde una fuente que
él elige y verifica (ver .claude/skills/universo/SKILL.md). Mientras el archivo esté
vacío, el universo queda PENDIENTE.

Uso:
    python3 codigo/universo.py --autotest
    python3 codigo/universo.py --validar
    python3 codigo/universo.py --fecha 2022-10-12
    python3 codigo/universo.py --fecha 2022-10-12 --top 10 [--ventana 63] [--json]
    python3 codigo/universo.py --crear-plantillas
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ARCHIVO_HISTORICO = RAIZ / "datos" / "universo_ndx100_historico.csv"
ARCHIVO_EJEMPLO = RAIZ / "datos" / "universo_ndx100_EJEMPLO.csv"
CARPETA_PRECIOS = RAIZ / "datos"
COLUMNAS = ["fecha_efectiva", "ticker", "accion", "fuente"]

# Supuestos (se muestran en cada salida)
SUPUESTO_EFECTIVA = (
    "Un cambio vale desde el INICIO de su fecha_efectiva: una alta ya es miembro ese día; "
    "una baja ya no lo es ese día."
)
SUPUESTO_TAMANO = (
    "(supuesto) Tamaño = promedio de precio de cierre × volumen (dólares negociados) de las "
    "últimas N velas ANTERIORES a la fecha X, tomado de tus CSV datos/<TICKER>_1D.csv. "
    "No es la capitalización de mercado: es un sustituto porque no tienes esos datos."
)

EJEMPLO = """fecha_efectiva,ticker,accion,fuente
# EJEMPLO FICTICIO: tickers inventados para probar el script. NO son datos reales del Nasdaq-100.
2010-01-04,EJ_AAA,alta,EJEMPLO lista inicial ficticia
2010-01-04,EJ_BBB,alta,EJEMPLO lista inicial ficticia
2010-01-04,EJ_CCC,alta,EJEMPLO lista inicial ficticia
2010-01-04,EJ_DDD,alta,EJEMPLO lista inicial ficticia
2015-12-21,EJ_EEE,alta,EJEMPLO anuncio ficticio
2015-12-21,EJ_DDD,baja,EJEMPLO anuncio ficticio
2020-06-22,EJ_DDD,alta,EJEMPLO reingreso ficticio
2020-06-22,EJ_BBB,baja,EJEMPLO anuncio ficticio
"""


class ErrorUniverso(Exception):
    pass


@dataclass
class Universo:
    cambios: list[tuple[date, str, str, str]]
    archivo: Path
    avisos: list[str] = field(default_factory=list)

    @property
    def estado(self) -> str:
        return "PENDIENTE" if not self.cambios else "LISTO"

    def miembros_en(self, fecha: date) -> list[str]:
        """Tickers miembros en `fecha` usando solo cambios con fecha_efectiva <= fecha."""
        miembros: set[str] = set()
        for f, ticker, accion, _ in self.cambios:
            if f > fecha:
                break  # cambios ordenados: lo que sigue es futuro
            if accion == "alta":
                miembros.add(ticker)
            else:
                miembros.discard(ticker)
        return sorted(miembros)

    def primera_fecha(self) -> date | None:
        return self.cambios[0][0] if self.cambios else None


def _fecha(texto: str, linea: int) -> date:
    try:
        return date.fromisoformat(texto.strip())
    except ValueError as exc:
        raise ErrorUniverso(f"Línea {linea}: fecha «{texto}» no es AAAA-MM-DD.") from exc


def cargar(archivo: Path) -> Universo:
    """Lee y valida el archivo de cambios. Las líneas que empiezan con # son comentarios."""
    if not archivo.exists():
        raise ErrorUniverso(
            f"No existe {archivo.relative_to(RAIZ) if archivo.is_relative_to(RAIZ) else archivo}. "
            "Créalo con --crear-plantillas y rellénalo (ver la skill universo)."
        )
    with archivo.open(encoding="utf-8", newline="") as fh:
        lineas = [(i, l) for i, l in enumerate(fh.read().splitlines(), start=1)]
    utiles = [(i, l) for i, l in lineas if l.strip() and not l.lstrip().startswith("#")]
    if not utiles:
        raise ErrorUniverso("El archivo está vacío: falta la cabecera.")
    cab_i, cab = utiles[0]
    cabecera = [c.strip() for c in next(csv.reader([cab]))]
    if cabecera != COLUMNAS:
        raise ErrorUniverso(f"Línea {cab_i}: la cabecera debe ser {','.join(COLUMNAS)} y es {cab}.")

    cambios = []
    vistos = set()
    for i, l in utiles[1:]:
        fila = [c.strip() for c in next(csv.reader([l]))]
        if len(fila) != 4:
            raise ErrorUniverso(f"Línea {i}: se esperaban 4 columnas y hay {len(fila)}.")
        f_txt, ticker, accion, fuente = fila
        f = _fecha(f_txt, i)
        ticker = ticker.upper()
        accion = accion.lower()
        if not ticker:
            raise ErrorUniverso(f"Línea {i}: ticker vacío.")
        if accion not in ("alta", "baja"):
            raise ErrorUniverso(f"Línea {i}: accion debe ser alta o baja, no «{accion}».")
        if not fuente:
            raise ErrorUniverso(f"Línea {i}: falta la fuente. Cada cambio necesita su fuente para poder verificarlo.")
        clave = (f, ticker, accion)
        if clave in vistos:
            raise ErrorUniverso(f"Línea {i}: cambio duplicado ({f_txt} {ticker} {accion}).")
        vistos.add(clave)
        cambios.append((f, ticker, accion, fuente))

    # Orden: por fecha; el mismo día, primero bajas y luego altas (no cambia el resultado
    # si cada ticker aparece una vez por día, pero deja el orden fijo).
    cambios.sort(key=lambda c: (c[0], 0 if c[2] == "baja" else 1, c[1]))

    # Coherencia: no dar de baja a quien no está, ni de alta a quien ya está.
    universo = Universo(cambios, archivo)
    miembros: set[str] = set()
    for f, ticker, accion, _ in cambios:
        if accion == "alta":
            if ticker in miembros:
                raise ErrorUniverso(f"{f} {ticker}: alta de un ticker que ya era miembro.")
            miembros.add(ticker)
        else:
            if ticker not in miembros:
                raise ErrorUniverso(f"{f} {ticker}: baja de un ticker que no era miembro.")
            miembros.discard(ticker)
    if cambios:
        inicial = universo.miembros_en(cambios[0][0])
        if len(inicial) < 90 and "EJEMPLO" not in archivo.name.upper():
            universo.avisos.append(
                f"La lista inicial ({cambios[0][0]}) tiene {len(inicial)} tickers; el Nasdaq-100 tiene "
                "unos 100 (algunas empresas tienen 2 clases de acción). Revisa que esté completa."
            )
    return universo


def tamano_proxy(ticker: str, fecha: date, ventana: int, carpeta: Path) -> tuple[float | None, str]:
    """Promedio de cierre × volumen de las `ventana` velas con fecha < `fecha` (sin look-ahead)."""
    archivo = carpeta / f"{ticker}_1D.csv"
    if not archivo.exists():
        return None, f"sin CSV ({archivo.name})"
    filas = []
    with archivo.open(encoding="utf-8", newline="") as fh:
        lector = csv.DictReader(fh)
        if not {"fecha", "close", "volume"} <= set(lector.fieldnames or []):
            return None, f"{archivo.name} no tiene columnas fecha, close, volume"
        for r in lector:
            try:
                f = date.fromisoformat(r["fecha"][:10])
            except ValueError:
                continue
            if f >= fecha:
                break  # solo datos ANTERIORES a la fecha X (el CSV va en orden)
            try:
                filas.append(float(r["close"]) * float(r["volume"]))
            except (TypeError, ValueError):
                continue
    if len(filas) < ventana:
        return None, f"solo {len(filas)} velas antes de {fecha} (pide {ventana})"
    ultimas = filas[-ventana:]
    return sum(ultimas) / ventana, "ok"


def top_n(universo: Universo, fecha: date, n: int, ventana: int = 63,
          carpeta: Path = CARPETA_PRECIOS) -> dict:
    miembros = universo.miembros_en(fecha)
    medidos, sin_datos = [], []
    for t in miembros:
        valor, nota = tamano_proxy(t, fecha, ventana, carpeta)
        if valor is None:
            sin_datos.append({"ticker": t, "motivo": nota})
        else:
            medidos.append({"ticker": t, "dolares_dia": round(valor, 2)})
    medidos.sort(key=lambda d: (-d["dolares_dia"], d["ticker"]))
    avisos = []
    if sin_datos:
        avisos.append(
            f"{len(sin_datos)} de {len(miembros)} miembros sin datos suficientes: el ranking solo "
            "compara a los que tienen CSV. Si faltan empresas que luego salieron del índice, vuelve "
            "el sesgo de supervivencia. Baja sus datos con el agente datos."
        )
    return {
        "fecha": fecha.isoformat(),
        "n": n,
        "ventana_velas": ventana,
        "miembros": len(miembros),
        "top": medidos[:n],
        "sin_datos": sin_datos,
        "avisos": avisos,
        "supuesto": SUPUESTO_TAMANO,
    }


# ---------------------------------------------------------------- autotest
def autotest() -> int:
    fallos = []

    def comprobar(cond: bool, texto: str) -> None:
        print(("  OK    " if cond else "  FALLO ") + texto)
        if not cond:
            fallos.append(texto)

    print("AUTOTEST de codigo/universo.py (con datos FICTICIOS, no toca tus archivos)")
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        ejemplo = ARCHIVO_EJEMPLO if ARCHIVO_EJEMPLO.exists() else tmp / "universo_EJEMPLO.csv"
        if not ARCHIVO_EJEMPLO.exists():
            ejemplo.write_text(EJEMPLO, encoding="utf-8")
        print(f"Archivo de ejemplo: {ejemplo.name}")
        u = cargar(ejemplo)

        print("1) Miembros por fecha")
        comprobar(u.miembros_en(date(2009, 12, 31)) == [], "antes de la lista inicial no hay miembros")
        comprobar(u.miembros_en(date(2012, 1, 1)) == ["EJ_AAA", "EJ_BBB", "EJ_CCC", "EJ_DDD"], "2012: los 4 iniciales")
        comprobar(u.miembros_en(date(2015, 12, 18)) == ["EJ_AAA", "EJ_BBB", "EJ_CCC", "EJ_DDD"],
                  "el día antes de un cambio, el cambio aún no cuenta (sin mirar el futuro)")
        comprobar(u.miembros_en(date(2015, 12, 21)) == ["EJ_AAA", "EJ_BBB", "EJ_CCC", "EJ_EEE"],
                  "en la fecha efectiva: entra EJ_EEE y sale EJ_DDD")
        comprobar(u.miembros_en(date(2021, 1, 1)) == ["EJ_AAA", "EJ_CCC", "EJ_DDD", "EJ_EEE"],
                  "2021: EJ_DDD reingresó y EJ_BBB salió")

        print("2) Top N sin mirar el futuro")
        # Precios ficticios: EJ_CCC es la más negociada ANTES de 2018-01-01,
        # pero DESPUÉS tiene un volumen gigante que no debe influir en el ranking de esa fecha.
        precios = tmp / "precios"
        precios.mkdir()
        import datetime as dt
        dias = [date(2017, 9, 1) + dt.timedelta(days=i) for i in range(200)]
        dias = [d for d in dias if d.weekday() < 5]
        base = {"EJ_AAA": (10.0, 1_000), "EJ_CCC": (20.0, 2_000), "EJ_EEE": (5.0, 1_500)}
        for t, (px, vol) in base.items():
            with (precios / f"{t}_1D.csv").open("w", encoding="utf-8") as fh:
                fh.write("fecha,open,high,low,close,volume\n")
                for d in dias:
                    v = vol
                    if t == "EJ_AAA" and d >= date(2018, 1, 1):
                        v = 10_000_000  # salto de volumen en el FUTURO respecto a la fecha X
                    fh.write(f"{d},{px},{px},{px},{px},{v}\n")
        r = top_n(u, date(2018, 1, 1), 2, ventana=20, carpeta=precios)
        orden = [d["ticker"] for d in r["top"]]
        comprobar(orden == ["EJ_CCC", "EJ_AAA"], f"top 2 al 2018-01-01 = EJ_CCC, EJ_AAA (salió {orden})")
        comprobar(any(s["ticker"] == "EJ_BBB" for s in r["sin_datos"]),
                  "un miembro sin CSV queda en «sin datos» y genera aviso")
        r2 = top_n(u, date(2018, 3, 1), 1, ventana=20, carpeta=precios)
        comprobar([d["ticker"] for d in r2["top"]] == ["EJ_AAA"],
                  "en 2018-03-01 el volumen nuevo ya es pasado y EJ_AAA sube al primer puesto")
        r3 = top_n(u, date(2017, 9, 5), 2, ventana=20, carpeta=precios)
        comprobar(r3["top"] == [], "sin velas suficientes antes de la fecha no se inventa un ranking")

        print("3) Validación del archivo")
        casos = {
            "baja de quien no está": "2010-01-04,EJ_X,baja,f\n",
            "acción inválida": "2010-01-04,EJ_X,entra,f\n",
            "fuente vacía": "2010-01-04,EJ_X,alta,\n",
            "fecha mal escrita": "04/01/2010,EJ_X,alta,f\n",
        }
        for nombre, fila in casos.items():
            p = tmp / "malo.csv"
            p.write_text(",".join(COLUMNAS) + "\n" + fila, encoding="utf-8")
            try:
                cargar(p)
                comprobar(False, f"detecta: {nombre}")
            except ErrorUniverso:
                comprobar(True, f"detecta: {nombre}")
        p = tmp / "vacio.csv"
        p.write_text(",".join(COLUMNAS) + "\n", encoding="utf-8")
        comprobar(cargar(p).estado == "PENDIENTE", "archivo solo con cabecera = PENDIENTE")

    print()
    if fallos:
        print(f"AUTOTEST: {len(fallos)} FALLO(S)")
        return 1
    print("AUTOTEST: todo OK")
    return 0


def crear_plantillas() -> None:
    if ARCHIVO_HISTORICO.exists():
        print(f"Ya existe {ARCHIVO_HISTORICO.relative_to(RAIZ)}: no se toca.")
    else:
        ARCHIVO_HISTORICO.write_text(",".join(COLUMNAS) + "\n", encoding="utf-8")
        print(f"Creado {ARCHIVO_HISTORICO.relative_to(RAIZ)} (solo cabecera: universo PENDIENTE).")
    if ARCHIVO_EJEMPLO.exists():
        print(f"Ya existe {ARCHIVO_EJEMPLO.relative_to(RAIZ)}: no se toca.")
    else:
        ARCHIVO_EJEMPLO.write_text(EJEMPLO, encoding="utf-8")
        print(f"Creado {ARCHIVO_EJEMPLO.relative_to(RAIZ)} (ficticio, para el autotest).")


def main() -> int:
    ap = argparse.ArgumentParser(description="Universo del Nasdaq-100 sin sesgo de supervivencia.")
    ap.add_argument("--archivo", type=Path, default=ARCHIVO_HISTORICO, help="archivo de altas y bajas")
    ap.add_argument("--fecha", help="fecha X (AAAA-MM-DD)")
    ap.add_argument("--top", type=int, help="las N mayores en la fecha X")
    ap.add_argument("--ventana", type=int, default=63, help="velas para el tamaño (63 ≈ 3 meses)")
    ap.add_argument("--precios", type=Path, default=CARPETA_PRECIOS, help="carpeta con <TICKER>_1D.csv")
    ap.add_argument("--json", action="store_true", help="salida en JSON")
    ap.add_argument("--validar", action="store_true", help="solo valida el archivo")
    ap.add_argument("--autotest", action="store_true", help="prueba con el archivo de EJEMPLO")
    ap.add_argument("--crear-plantillas", action="store_true", help="crea cabecera y ejemplo si faltan")
    a = ap.parse_args()

    if a.autotest:
        return autotest()
    if a.crear_plantillas:
        crear_plantillas()
        return 0

    salida: dict = {"archivo": str(a.archivo), "supuesto_fecha": SUPUESTO_EFECTIVA}
    try:
        u = cargar(a.archivo)
    except ErrorUniverso as exc:
        salida.update(estado="ERROR", error=str(exc))
        print(json.dumps(salida, ensure_ascii=False, indent=2) if a.json else f"ERROR: {exc}")
        return 2
    salida.update(estado=u.estado, cambios=len(u.cambios), avisos=list(u.avisos))
    if "EJEMPLO" in a.archivo.name.upper():
        salida["avisos"].append("Estás usando el archivo de EJEMPLO (ficticio). No sirve para backtests.")

    if u.estado == "PENDIENTE":
        salida["mensaje"] = ("Universo PENDIENTE: el archivo solo tiene la cabecera. Rellénalo con altas y "
                             "bajas de una fuente verificada (skill universo). Hasta entonces, cualquier "
                             "cesta elegida con la lista de hoy tiene sesgo de supervivencia.")
    elif a.fecha:
        try:
            f = date.fromisoformat(a.fecha)
        except ValueError:
            print("ERROR: --fecha debe ser AAAA-MM-DD")
            return 2
        if u.primera_fecha() and f < u.primera_fecha():
            salida["avisos"].append(f"La fecha {f} es anterior al primer registro ({u.primera_fecha()}).")
        miembros = u.miembros_en(f)
        salida.update(fecha=f.isoformat(), miembros=miembros)
        if a.top:
            salida["ranking"] = top_n(u, f, a.top, a.ventana, a.precios)

    if a.json:
        print(json.dumps(salida, ensure_ascii=False, indent=2))
        return 0
    print(f"Universo: {salida['archivo']} · estado {salida['estado']} · {salida.get('cambios', 0)} cambios")
    for av in salida["avisos"]:
        print(f"AVISO: {av}")
    if "mensaje" in salida:
        print(salida["mensaje"])
    if "miembros" in salida:
        print(f"Miembros al {salida['fecha']} ({len(salida['miembros'])}): {', '.join(salida['miembros'])}")
        print(f"Regla de fechas: {SUPUESTO_EFECTIVA}")
    if "ranking" in salida:
        r = salida["ranking"]
        print(f"Top {r['n']} al {r['fecha']} (ventana {r['ventana_velas']} velas anteriores):")
        for i, d in enumerate(r["top"], 1):
            print(f"  {i:>2}. {d['ticker']:<8} {d['dolares_dia']:,.0f} USD/día")
        for s in r["sin_datos"]:
            print(f"  sin datos: {s['ticker']} ({s['motivo']})")
        for av in r["avisos"]:
            print(f"AVISO: {av}")
        print(r["supuesto"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
