"""Actualización diaria de los CSV de precios (skill actualizar-datos).

Para cada CSV de codigo/automatizacion/datos_config.json:
  1. lee la última fecha del CSV,
  2. descarga SOLO las velas nuevas (Yahoo Finance con yfinance),
  3. revisa la calidad (solape con la historia, duplicados, huecos, precios <= 0,
     máximo < mínimo, saltos grandes),
  4. si TODO pasa: guarda un respaldo en datos/crudos/ y AÑADE las filas nuevas al final.
     Nunca reescribe la historia. Si algo falla, no toca el archivo.
Registro: resultados/datos_actualizacion.log · Informe: resultados/datos_actualizacion_calidad.md

Uso:
    python3 codigo/automatizacion/actualizar_datos.py --simular        # sin red y sin escribir nada
    python3 codigo/automatizacion/actualizar_datos.py                  # actualiza de verdad
    python3 codigo/automatizacion/actualizar_datos.py --json           # para el orquestador diario
    python3 codigo/automatizacion/actualizar_datos.py --solo AAPL,MSFT

Códigos de salida: 0 todo bien · 1 algún archivo no se actualizó (revisar) ·
                   2 no se pudo empezar (falta yfinance o la configuración).
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

RAIZ = Path(__file__).resolve().parents[2]
CONFIG = Path(__file__).resolve().parent / "datos_config.json"
CRUDOS = RAIZ / "datos" / "crudos"
LOG = RAIZ / "resultados" / "datos_actualizacion.log"
INFORME = RAIZ / "resultados" / "datos_actualizacion_calidad.md"
COLUMNAS = ["fecha", "open", "high", "low", "close", "volume"]
NY = ZoneInfo("America/New_York")

SUPUESTOS = [
    "(supuesto) Días hábiles = lunes a viernes; los feriados de EE. UU. no se descuentan, así que "
    "un feriado puede aparecer como «1 vela pendiente» en --simular.",
    "(supuesto) Una vela diaria está completa después de las 16:30 de Nueva York; antes, la vela de "
    "hoy no se añade.",
    "(supuesto) Precios ajustados por splits y dividendos (auto_adjust de yfinance), igual que los CSV "
    "actuales. Si Yahoo reajusta la historia, el solape lo detecta y no se añade nada.",
]


# ------------------------------------------------------------------ utilidades
def rel(p: Path) -> str:
    try:
        return str(p.relative_to(RAIZ))
    except ValueError:
        return str(p)


def cargar_config(ruta: Path) -> dict:
    cfg = json.loads(ruta.read_text(encoding="utf-8"))
    if "archivos" not in cfg or not isinstance(cfg["archivos"], list):
        raise ValueError("datos_config.json no tiene la lista «archivos».")
    p = {"solape_velas": 5, "tolerancia_solape_pct": 0.5, "salto_max_pct": 25.0,
         "hueco_max_dias_habiles": 1, "hora_cierre_nueva_york": "16:30",
         "respaldos_max_por_archivo": 5}
    p.update(cfg.get("parametros", {}))
    cfg["parametros"] = p
    return cfg


def ultima_sesion_completa(ahora_ny: datetime, hora_cierre: str) -> date:
    hh, mm = (int(x) for x in hora_cierre.split(":"))
    d = ahora_ny.date()
    if d.weekday() >= 5 or ahora_ny.time() < time(hh, mm):
        d -= timedelta(days=1)
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d


def dias_habiles_entre(a: date, b: date) -> int:
    """Días lunes-viernes estrictamente después de a y hasta b (incluido)."""
    n, d = 0, a + timedelta(days=1)
    while d <= b:
        if d.weekday() < 5:
            n += 1
        d += timedelta(days=1)
    return n


def leer_cola(ruta: Path) -> tuple[list[str], list[list[str]], str]:
    """Devuelve cabecera, todas las filas (como texto) y el fin de línea del archivo."""
    crudo = ruta.read_bytes()
    fin = "\r\n" if b"\r\n" in crudo[:2000] else "\n"
    lineas = crudo.decode("utf-8").splitlines()
    cab = [c.strip() for c in lineas[0].split(",")]
    filas = [l.split(",") for l in lineas[1:] if l.strip()]
    return cab, filas, fin


def num(x: float) -> str:
    """Formato compacto sin notación científica (como los CSV actuales)."""
    s = f"{x:.6f}".rstrip("0").rstrip(".")
    return s if s else "0"


# ------------------------------------------------------------------ revisiones
def revisar(nuevas: list[dict], previa: dict | None, solape: list[tuple[str, float, float]],
            p: dict) -> list[str]:
    """Devuelve la lista de problemas. Lista vacía = pasa."""
    problemas = []
    # 1) Solape: las velas que ya tenías deben coincidir con lo que da Yahoo hoy.
    for f, viejo, nuevo in solape:
        dif = abs(nuevo - viejo) / viejo * 100 if viejo else 100.0
        if dif > p["tolerancia_solape_pct"]:
            problemas.append(
                f"El cierre del {f} cambió {dif:.2f} % (tu CSV {viejo:.4f} · Yahoo {nuevo:.4f}). Yahoo reajustó "
                "la historia (dividendo o split): hace falta volver a bajar el CSV completo con el "
                "agente datos. No se añade nada para no mezclar dos ajustes.")
            break
    # 2) Duplicados
    fechas = [r["fecha"] for r in nuevas]
    if len(fechas) != len(set(fechas)):
        problemas.append("Hay fechas duplicadas en las velas nuevas.")
    # 3) Velas imposibles
    for r in nuevas:
        o, h, l, c, v = r["open"], r["high"], r["low"], r["close"], r["volume"]
        if any(x != x for x in (o, h, l, c)):  # NaN
            problemas.append(f"{r['fecha']}: precio vacío.")
        elif min(o, h, l, c) <= 0:
            problemas.append(f"{r['fecha']}: precio en cero o negativo.")
        elif h < l:
            problemas.append(f"{r['fecha']}: máximo ({h}) menor que el mínimo ({l}).")
        elif h < max(o, c) * (1 - 1e-6) or l > min(o, c) * (1 + 1e-6):
            problemas.append(f"{r['fecha']}: apertura o cierre fuera del rango máximo-mínimo.")
        if v != v or v < 0:
            problemas.append(f"{r['fecha']}: volumen vacío o negativo.")
    # 4) Huecos y saltos (contra la vela anterior, incluida la última de tu CSV)
    anterior = previa
    for r in nuevas:
        if anterior:
            fa, fb = date.fromisoformat(anterior["fecha"]), date.fromisoformat(r["fecha"])
            if fb <= fa:
                problemas.append(f"{r['fecha']}: fecha fuera de orden.")
            faltan = dias_habiles_entre(fa, fb) - 1
            if faltan > p["hueco_max_dias_habiles"]:
                problemas.append(f"Hueco: faltan {faltan} días hábiles entre {fa} y {fb}.")
            if anterior["close"] > 0 and r["close"] == r["close"]:
                salto = abs(r["close"] / anterior["close"] - 1) * 100
                if salto > p["salto_max_pct"]:
                    problemas.append(
                        f"Salto de {salto:.1f} % el {r['fecha']} (límite {p['salto_max_pct']} %). Puede ser "
                        "real (resultados, noticia) o un error: míralo en el gráfico antes de aceptarlo.")
        anterior = r
    return problemas


# ------------------------------------------------------------------ descarga
def descargar_yahoo(ticker: str, desde: date) -> list[dict]:
    import yfinance as yf  # se importa aquí para que --simular no lo necesite

    df = yf.download(ticker, start=desde.isoformat(), end=(date.today() + timedelta(days=2)).isoformat(),
                     interval="1d", auto_adjust=True, actions=False, progress=False, threads=False)
    if df is None or df.empty:
        return []
    if getattr(df.columns, "nlevels", 1) > 1:  # columnas (Precio, Ticker)
        df = df.xs(ticker, axis=1, level=-1) if ticker in df.columns.get_level_values(-1) else df.droplevel(-1, axis=1)
    df = df.rename(columns=str.lower)
    filas = []
    for idx, r in df.iterrows():
        filas.append({
            "fecha": idx.date().isoformat() if hasattr(idx, "date") else str(idx)[:10],
            "open": float(r["open"]), "high": float(r["high"]), "low": float(r["low"]),
            "close": float(r["close"]),
            "volume": float(r["volume"]) if r["volume"] == r["volume"] else float("nan"),
        })
    return filas


# ------------------------------------------------------------------ un archivo
def procesar(entrada: dict, p: dict, ultima_sesion: date, simular: bool, sello: str) -> dict:
    ruta = RAIZ / entrada["archivo"]
    ticker = entrada["ticker"]
    res = {"archivo": entrada["archivo"], "ticker": ticker, "estado": "", "ultima_fecha": None,
           "velas_pendientes": 0, "velas_añadidas": 0, "problemas": [], "respaldo": None}
    if not ruta.exists():
        res.update(estado="ERROR", problemas=[f"No existe {entrada['archivo']}."])
        return res
    cab, filas, fin = leer_cola(ruta)
    if cab != COLUMNAS:
        res.update(estado="ERROR", problemas=[f"Cabecera inesperada {cab}; se esperaba {COLUMNAS}."])
        return res
    if not filas:
        res.update(estado="ERROR", problemas=["El CSV no tiene velas."])
        return res
    ultima = date.fromisoformat(filas[-1][0][:10])
    res["ultima_fecha"] = ultima.isoformat()
    pendientes = dias_habiles_entre(ultima, ultima_sesion)
    res["velas_pendientes"] = pendientes

    if pendientes == 0:
        res["estado"] = "AL_DIA"
        return res
    if simular:
        res["estado"] = "SE_ACTUALIZARIA"
        return res
    if entrada.get("fuente", "yahoo") != "yahoo":
        res.update(estado="ERROR", problemas=[f"Fuente «{entrada.get('fuente')}» aún no soportada (solo yahoo)."])
        return res

    # Descarga con solape: unas velas que ya tienes, para comprobar que la historia no cambió.
    n_sol = int(p["solape_velas"])
    desde = date.fromisoformat(filas[-n_sol][0][:10]) if len(filas) >= n_sol else ultima
    try:
        bajadas = descargar_yahoo(ticker, desde)
    except Exception as exc:  # red caída, ticker inexistente, cambios de Yahoo
        res.update(estado="ERROR", problemas=[f"La descarga falló: {type(exc).__name__}: {exc}"])
        return res
    if not bajadas:
        res.update(estado="SIN_VELAS_NUEVAS", problemas=["Yahoo no devolvió velas (¿feriado o sin conexión?)."])
        return res

    mias = {f[0][:10]: float(f[4]) for f in filas[-n_sol:]}
    solape = [(b["fecha"], mias[b["fecha"]], b["close"]) for b in bajadas if b["fecha"] in mias]
    nuevas = [b for b in bajadas
              if date.fromisoformat(b["fecha"]) > ultima and date.fromisoformat(b["fecha"]) <= ultima_sesion]
    if not solape:
        res["problemas"].append("No hay velas en común con tu CSV para comprobar el ajuste.")
    if not nuevas:
        res["estado"] = "SIN_VELAS_NUEVAS"
        return res
    u = filas[-1]
    previa = {"fecha": u[0][:10], "close": float(u[4])}
    res["problemas"] += revisar(nuevas, previa, solape, p)
    if res["problemas"]:
        res["estado"] = "RECHAZADO"
        res["velas_rechazadas"] = len(nuevas)
        return res

    # Respaldo ANTES de escribir
    CRUDOS.mkdir(parents=True, exist_ok=True)
    respaldo = CRUDOS / f"{ruta.stem}_respaldo_{sello}.csv"
    shutil.copy2(ruta, respaldo)
    res["respaldo"] = rel(respaldo)
    viejos = sorted(CRUDOS.glob(f"{ruta.stem}_respaldo_*.csv"))
    for v in viejos[:-int(p["respaldos_max_por_archivo"])]:
        v.unlink()

    # Añadir al final (modo "a": las filas viejas no se reescriben)
    tam_antes = ruta.stat().st_size
    with ruta.open("rb") as fh:
        fh.seek(-1, 2)
        termina_bien = fh.read(1) == b"\n"
    texto = "" if termina_bien else fin
    for r in nuevas:
        vol = int(round(r["volume"]))
        texto += ",".join([r["fecha"], num(r["open"]), num(r["high"]), num(r["low"]), num(r["close"]), str(vol)]) + fin
    with ruta.open("a", encoding="utf-8", newline="") as fh:
        fh.write(texto)

    # Comprobación: la historia quedó idéntica byte a byte y la última fecha es la esperada.
    with ruta.open("rb") as a, respaldo.open("rb") as b:
        iguales = a.read(tam_antes) == b.read()
    _, filas2, _ = leer_cola(ruta)
    if not iguales or filas2[-1][0][:10] != nuevas[-1]["fecha"]:
        shutil.copy2(respaldo, ruta)
        res.update(estado="ERROR", problemas=["La comprobación tras escribir falló; se restauró el respaldo."])
        return res
    res.update(estado="ACTUALIZADO", velas_añadidas=len(nuevas), ultima_fecha=nuevas[-1]["fecha"])
    return res


# ------------------------------------------------------------------ informe
def escribir_informe(resumen: dict) -> None:
    lineas = [f"# Actualización de datos · {resumen['fecha_hora']}", "",
              f"Estado general: **{resumen['estado']}** · última sesión esperada {resumen['ultima_sesion_esperada']}",
              f"Actualizados {resumen['conteo'].get('ACTUALIZADO', 0)} · al día {resumen['conteo'].get('AL_DIA', 0)} · "
              f"rechazados {resumen['conteo'].get('RECHAZADO', 0)} · errores {resumen['conteo'].get('ERROR', 0)}", ""]
    for r in resumen["archivos"]:
        extra = f" · +{r['velas_añadidas']} velas" if r["velas_añadidas"] else ""
        lineas.append(f"- {r['ticker']}: {r['estado']} (última {r['ultima_fecha']}){extra}")
        for pr in r["problemas"]:
            lineas.append(f"  - {pr}")
    lineas += ["", "Supuestos:"] + [f"- {s}" for s in SUPUESTOS]
    INFORME.parent.mkdir(parents=True, exist_ok=True)
    INFORME.write_text("\n".join(lineas) + "\n", encoding="utf-8")


def escribir_log(resumen: dict) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as fh:
        for r in resumen["archivos"]:
            pr = " | ".join(r["problemas"]).replace("\n", " ")
            fh.write(f"{resumen['fecha_hora']}\t{r['ticker']}\t{r['estado']}\tultima={r['ultima_fecha']}"
                     f"\tañadidas={r['velas_añadidas']}\t{pr}\n")
        fh.write(f"{resumen['fecha_hora']}\tRESUMEN\t{resumen['estado']}\t{json.dumps(resumen['conteo'], ensure_ascii=False)}\n")


# ------------------------------------------------------------------ main
def main() -> int:
    ap = argparse.ArgumentParser(description="Actualiza los CSV diarios sin reescribir la historia.")
    ap.add_argument("--simular", action="store_true", help="sin red y sin escribir: muestra qué se actualizaría")
    ap.add_argument("--json", action="store_true", help="salida en JSON (para el orquestador)")
    ap.add_argument("--config", type=Path, default=CONFIG)
    ap.add_argument("--solo", help="tickers separados por coma")
    a = ap.parse_args()

    ahora_ny = datetime.now(NY)
    resumen = {"modo": "simular" if a.simular else "real", "fecha_hora": ahora_ny.strftime("%Y-%m-%d %H:%M %Z"),
               "estado": "", "archivos": [], "conteo": {}, "supuestos": SUPUESTOS, "mensaje": ""}

    def salir(codigo: int) -> int:
        if a.json:
            print(json.dumps(resumen, ensure_ascii=False, indent=2))
        else:
            print(f"Actualización de datos · modo {resumen['modo']} · {resumen['fecha_hora']}")
            if resumen.get("ultima_sesion_esperada"):
                print(f"Última sesión completa esperada: {resumen['ultima_sesion_esperada']}")
            for r in resumen["archivos"]:
                info = {"AL_DIA": "al día", "SE_ACTUALIZARIA": f"faltan ~{r['velas_pendientes']} velas → se actualizaría",
                        "ACTUALIZADO": f"+{r['velas_añadidas']} velas", }.get(r["estado"], r["estado"])
                print(f"  {r['ticker']:<6} última {r['ultima_fecha']} · {info}")
                for pr in r["problemas"]:
                    print(f"         ! {pr}")
            if resumen["mensaje"]:
                print(resumen["mensaje"])
            print(f"Estado general: {resumen['estado']}")
            for s in SUPUESTOS:
                print(f"  {s}")
        return codigo

    try:
        cfg = cargar_config(a.config)
    except Exception as exc:
        resumen.update(estado="ERROR", mensaje=f"No pude leer la configuración {rel(a.config)}: {exc}")
        return salir(2)
    p = cfg["parametros"]
    ultima = ultima_sesion_completa(ahora_ny, p["hora_cierre_nueva_york"])
    resumen["ultima_sesion_esperada"] = ultima.isoformat()

    entradas = [e for e in cfg["archivos"] if e.get("activo", True)]
    if a.solo:
        quiero = {t.strip().upper() for t in a.solo.split(",")}
        entradas = [e for e in entradas if e["ticker"].upper() in quiero]

    hay_yf = importlib.util.find_spec("yfinance") is not None
    resumen["yfinance_instalado"] = hay_yf
    if not a.simular and not hay_yf:
        resumen.update(estado="SIN_YFINANCE", mensaje=(
            "Falta la librería yfinance. Instálala tú en el terminal de VS Code con: "
            "python3 -m pip install yfinance  · y vuelve a correr este script. No se tocó ningún archivo."))
        return salir(2)

    sello = ahora_ny.strftime("%Y%m%d_%H%M%S")
    for e in entradas:
        try:
            resumen["archivos"].append(procesar(e, p, ultima, a.simular, sello))
        except Exception as exc:
            resumen["archivos"].append({"archivo": e.get("archivo"), "ticker": e.get("ticker"), "estado": "ERROR",
                                        "ultima_fecha": None, "velas_pendientes": 0, "velas_añadidas": 0,
                                        "problemas": [f"{type(exc).__name__}: {exc}"], "respaldo": None})
    for r in resumen["archivos"]:
        resumen["conteo"][r["estado"]] = resumen["conteo"].get(r["estado"], 0) + 1

    malos = resumen["conteo"].get("RECHAZADO", 0) + resumen["conteo"].get("ERROR", 0)
    if a.simular:
        resumen["estado"] = "SIMULADO"
        resumen["mensaje"] = ("Simulación: no se usó internet ni se escribió ningún archivo."
                              + ("" if hay_yf else " Ojo: yfinance no está instalado; la actualización real no podrá correr."))
        return salir(1 if resumen["conteo"].get("ERROR") else 0)

    resumen["estado"] = "OK" if malos == 0 else "REVISAR"
    escribir_log(resumen)
    escribir_informe(resumen)
    resumen["mensaje"] = f"Registro: {rel(LOG)} · Informe: {rel(INFORME)}"
    return salir(0 if malos == 0 else 1)


if __name__ == "__main__":
    sys.exit(main())
