"""Réplica · ¿mis resultados se pueden repetir hoy, byte a byte?

Qué hace (en este orden):
  1. HUELLAS DE DATOS. Calcula la huella sha256 (una "firma" de 64 letras que cambia si cambia
     un solo byte) de cada datos/*.csv y la compara con resultados/huellas_datos.json.
     La primera vez crea esa base. Después avisa de CSV nuevos, faltantes, AMPLIADOS (solo se
     añadieron filas al final: la base sigue intacta dentro del archivo) o MODIFICADOS (cambió
     la historia).
  2. RE-EJECUCIÓN. Copia codigo/ y datos/ a una carpeta temporal y corre ahí cada script de la
     lista SCRIPTS (los que respaldan las fichas). Si un CSV solo se amplió, la copia temporal se
     recorta al tamaño de la base, así la réplica sigue siendo exacta.
     resultados/ NO se toca: los scripts escriben en la carpeta temporal.
  3. COMPARACIÓN. Cada archivo que el script escribe se compara byte a byte con el de
     resultados/. Lo que imprime en pantalla se compara con su huella guardada. Y algunas cifras
     clave se comparan con las líneas «Resultado:» de las fichas.
  4. VEREDICTO por script: REPLICA · NO REPLICA · NO COMPARABLE (cambió la historia de sus datos).
  5. requirements.txt en la raíz con las versiones exactas instaladas de lo que importa codigo/.

Seguridad: antes de empezar guarda una copia de resultados/; si al final algún archivo original
cambió (no debería), lo restaura y lo dice.

Uso (desde la raíz del repositorio):
  python3 codigo/automatizacion/replica.py            # informe en pantalla
  python3 codigo/automatizacion/replica.py --json     # resumen en JSON (lo usa diario.py)
  python3 codigo/automatizacion/replica.py --nueva-base
        # acepta los datos de hoy como nueva base. Es una decisión TUYA (criterio):
        # las cifras de las fichas pueden dejar de coincidir.
Código de salida: 0 si todo replica (o solo hay NO COMPARABLE), 1 si algún script NO REPLICA.
Solo usa la biblioteca estándar de Python. No usa internet.
"""
import argparse
import ast
import difflib
import hashlib
import importlib.metadata as md
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent.parent
DATOS = RAIZ / "datos"
RESULTADOS = RAIZ / "resultados"
HUELLAS = RESULTADOS / "huellas_datos.json"
TIEMPO_MAX = 900  # segundos por script

# ---------------------------------------------------------------------------------------------
# Scripts que respaldan las fichas. Para añadir uno: copia una entrada.
#   salidas  = archivos de resultados/ que el script escribe (se comparan byte a byte)
#   cifras   = (qué es, regex sobre lo que imprime, ficha, inicio del bloque, regex en la ficha)
#              Las dos regex capturan UN número en el grupo 1. Tolerancia: el redondeo de la ficha.
# ---------------------------------------------------------------------------------------------
C10 = "fichas/cesta10_williams_r.md"
NVDA = "fichas/nvda_media_toque.md"
META = "fichas/meta_williams_r.md"
SCRIPTS = [
    dict(id="cesta10_williams_r.py aed", args=["codigo/cesta10_williams_r.py", "aed"], salidas=[],
         cifras=[
             ("señales (n)", r"Señal %R \(cesta\)\s+n=\s*(\d+)", C10, "## Fase 02", r"\((\d+) señales"),
             ("retorno a 12 semanas", r"Señal %R \(cesta\).*?r12 ([+-][\d.]+)%", C10, "## Fase 02", r"la señal da ([+-][\d,]+) %"),
             ("base a 12 semanas", r"Cualquier semana \(base\).*?r12 ([+-][\d.]+)%", C10, "## Fase 02", r"frente a ([+-][\d,]+) % de cualquier"),
             ("t", r"t≈([\d.]+)", C10, "## Fase 02", r"t≈([\d,]+)"),
         ]),
    dict(id="cesta10_williams_r.py backtest", args=["codigo/cesta10_williams_r.py", "backtest"],
         salidas=["resultados/cesta10_williams_r_operaciones.csv"],
         cifras=[
             ("OOS factor de beneficio", r"FUERA DE MUESTRA.*?Factor de beneficio ≥ 1,3: ([\d.]+)", C10, "## Fase 04", r"OOS: factor de beneficio ([\d,]+)"),
             ("OOS operaciones", r"FUERA DE MUESTRA.*?Al menos 30 operaciones: (\d+)", C10, "## Fase 04", r"OOS: factor de beneficio [\d,]+ \S+ · (\d+) operaciones"),
             ("OOS caída máxima", r"FUERA DE MUESTRA.*?Caída máxima < 20 %: (-[\d.]+) %", C10, "## Fase 04", r"OOS:.*?caída máxima (-[\d,]+) %"),
             ("OOS FB sin la mejor", r"FUERA DE MUESTRA.*?FB sin la mejor > 1: ([\d.]+)", C10, "## Fase 04", r"OOS:.*?sin la mejor ([\d,]+)"),
             ("IS factor de beneficio", r"DENTRO DE MUESTRA.*?Factor de beneficio ≥ 1,3: ([\d.]+)", C10, "## Fase 04", r"IS: ([\d,]+) ·"),
             ("IS operaciones", r"DENTRO DE MUESTRA.*?Al menos 30 operaciones: (\d+)", C10, "## Fase 04", r"IS: [\d,]+ · (\d+) ·"),
             ("IS caída máxima", r"DENTRO DE MUESTRA.*?Caída máxima < 20 %: (-[\d.]+) %", C10, "## Fase 04", r"IS: [\d,]+ · \d+ · (-[\d,]+) %"),
         ]),
    dict(id="cesta10_williams_r_optimizar.py", args=["codigo/cesta10_williams_r_optimizar.py"],
         salidas=["resultados/cesta10_williams_r_meseta.png"],
         cifras=[
             ("FB combinación actual", r"Combinación actual:.*?FB ([\d.]+),", C10, "## Fase 05", r"12 semanas; FB ([\d,]+) con"),
             ("operaciones combinación actual", r"Combinación actual:.*?FB [\d.]+, (\d+) operaciones", C10, "## Fase 05", r"FB [\d,]+ con (\d+) operaciones"),
             ("combinaciones que cumplen", r"toda la rejilla.*?: (\d+) de 63", C10, "## Fase 05", r"Las (\d+) combinaciones tienen"),
         ]),
    dict(id="cesta10_williams_r_robustez.py", args=["codigo/cesta10_williams_r_robustez.py"],
         salidas=["resultados/cesta10_williams_r_robustez.png"],
         cifras=[
             ("costes ×2: FB", r"Costes ×2.*?FB ([\d.]+)", C10, "## Fase 06 · Robustez · motor", r"Costes ×2: FB OOS ([\d,]+)"),
             ("Monte Carlo: caída p95", r"caída p95 < 30 %: p95 (-[\d.]+) %", C10, "## Fase 06 · Robustez · motor", r"percentil 95 (-[\d,]+) %"),
             ("remuestreo: FB p5", r"FB p5 > 1: p5 ([\d.]+)", C10, "## Fase 06 · Robustez · motor", r"percentil 5 = ([\d,]+)"),
             ("años que ganan", r"(\d+) de 17 años ganan", C10, "## Fase 06 · Robustez · motor", r"(\d+) de 17 años ganan"),
             ("FB sin el mejor año", r"sin 2020: FB ([\d.]+)", C10, "## Fase 06 · Robustez · motor", r"sin el mejor año \(2020\) FB ([\d,]+)"),
             ("cesta oct-2022: FB", r"Extra.*?FB ≥ 1,3: ([\d.]+)", C10, "## Fase 06 · Robustez · motor", r"OOS 4/4 \(FB ([\d,]+)"),
             ("cesta oct-2022: caída", r"Extra.*?Caída máxima < 20 %: (-[\d.]+)", C10, "## Fase 06 · Robustez · motor", r"caída (-[\d,]+) % · FB sin la mejor"),
             ("cesta oct-2022: FB sin la mejor", r"Extra.*?FB sin la mejor > 1: ([\d.]+)", C10, "## Fase 06 · Robustez · motor", r"FB sin la mejor ([\d,]+)\)"),
         ]),
    dict(id="cesta10_williams_r_patrones.py", args=["codigo/cesta10_williams_r_patrones.py"],
         salidas=["resultados/cesta10_williams_r_validacion_operaciones.csv"],
         cifras=[
             ("patrón: operaciones", r"caída 15-30 %\s+n=\s*(\d+)", C10, "## Fase 06 · Robustez (anexo", r"FB [\d,]+ con (\d+) operaciones en el descubrimiento"),
             ("patrón: FB descubrimiento", r"caída 15-30 %\s+n=\s*\d+\s+FB\s+([\d.]+)", C10, "## Fase 06 · Robustez (anexo", r"\(FB ([\d,]+) con \d+ operaciones en el descubrimiento"),
             ("patrón: FB validación", r"Regla \+ patrón.*?jul-2022 → nov-2026: \S+ FB ([\d.]+)", C10, "## Fase 06 · Robustez (anexo", r"da FB ([\d,]+) con 24"),
             ("10 nuevas antes del corte: FB", r"Regla base, sin patrón:.*?2010 → jul-2022: \S+ FB ([\d.]+)", C10, "## Fase 06 · Robustez (anexo", r"hasta jul-2022 \(FB ([\d,]+)\)"),
             ("10 nuevas después del corte: FB", r"Regla base, sin patrón:.*?jul-2022 → nov-2026: \S+ FB ([\d.]+)", C10, "## Fase 06 · Robustez (anexo", r"después \(FB ([\d,]+): pierde"),
         ]),
    dict(id="nvda_media_toque_backtest.py", args=["codigo/nvda_media_toque_backtest.py"],
         salidas=["resultados/nvda_media_toque_operaciones.csv"],
         cifras=[
             ("OOS trader: operaciones", r"OOS del trader\).*?Operaciones: (\d+)", NVDA, "## Fase 04", r"OOS del trader: (\d+) operaciones"),
             ("OOS trader: FB", r"OOS del trader\).*?Factor de beneficio ≥ 1,3: ([\d.]+)", NVDA, "## Fase 04", r"OOS del trader: \d+ operaciones, FB ([\d,]+)"),
             ("OOS trader: caída", r"OOS del trader\).*?Caída máxima < 20 %: (-[\d.]+)", NVDA, "## Fase 04", r"OOS del trader:.*?caída máxima (-[\d,]+) %"),
             ("OOS trader: FB sin la mejor", r"OOS del trader\).*?FB sin la mejor operación > 1: ([\d.]+)", NVDA, "## Fase 04", r"OOS del trader:.*?FB sin la mejor ([\d,]+)"),
             ("OOS 70/30: FB", r"OOS 30 % del método.*?Factor de beneficio ≥ 1,3: ([\d.]+)", NVDA, "## Fase 04", r"OOS 70/30 del método: \d+ operaciones, FB ([\d,]+)"),
             ("OOS 70/30: caída", r"OOS 30 % del método.*?Caída máxima < 20 %: (-[\d.]+)", NVDA, "## Fase 04", r"OOS 70/30 del método:.*?caída (-[\d,]+) %"),
             ("IS: caída", r"DENTRO DE MUESTRA.*?Caída máxima < 20 %: (-[\d.]+)", NVDA, "## Fase 04", r"IS 2017-2021: \d/4 \(\d+ operaciones, caída (-[\d,]+) %"),
         ]),
    dict(id="meta_williams_r_aed.py semanal", args=["codigo/meta_williams_r_aed.py", "semanal"], salidas=[],
         cifras=[
             ("señales (n)", r"Señal %R\s+n=\s*(\d+)", META, "## Fase 02 · AED (versión semanal)", r"\((\d+) señales"),
             ("retorno a 12 semanas", r"Señal %R.*?r12 ([+-][\d.]+)%", META, "## Fase 02 · AED (versión semanal)", r"la señal da ([+-][\d,]+) %"),
             ("base a 12 semanas", r"Todos los días \(base\).*?r12 ([+-][\d.]+)%", META, "## Fase 02 · AED (versión semanal)", r"frente a ([+-][\d,]+) % de una semana"),
             ("t", r"t≈([\d.]+)", META, "## Fase 02 · AED (versión semanal)", r"t≈([\d,]+)"),
         ]),
    dict(id="nas100_media_toque_aed.py (NVDA)", args=["codigo/nas100_media_toque_aed.py", "datos/NVDA_4H_2016_2021.csv"], salidas=[],
         cifras=[
             ("velas de toque (n)", r"Toque SMA200 \(señal\)\s+n=\s*(\d+)", NVDA, "## Fase 02", r"\((\d+) velas de toque"),
             ("retorno a 20 velas", r"Toque SMA200.*?r20: media ([+-][\d.]+)%", NVDA, "## Fase 02", r"la señal da ([+-][\d,]+) %"),
             ("base a 20 velas", r"Todas las velas \(base\).*?r20: media ([+-][\d.]+)%", NVDA, "## Fase 02", r"frente a ([+-][\d,]+) % de una vela"),
             ("señales independientes", r"Señales independientes.*?n=(\d+)", NVDA, "## Fase 02", r"Una operación a la vez: (\d+) señales"),
             ("t", r"t≈([\d.]+)", NVDA, "## Fase 02", r"t≈([\d,]+)"),
         ]),
]

# Envoltorio: corre el script como si fuera "python3 script args" y apunta qué CSV lee y qué
# archivos escribe (con los "audit hooks" de Python, que avisan de cada open()).
ENVOLTORIO = r"""
import sys, os, json, runpy, atexit
_reg = {"lee": set(), "escribe": set()}
_listo = [False]
def _hook(ev, a):
    if _listo[0] or ev != "open" or not a:
        return
    p = a[0]
    if not isinstance(p, (str, bytes, os.PathLike)):
        return
    try:
        p = os.path.abspath(os.fsdecode(p))
    except Exception:
        return
    modo = a[1] if len(a) > 1 and isinstance(a[1], str) else "r"
    if any(c in modo for c in "wax+"):
        _reg["escribe"].add(p)
    elif p.endswith(".csv"):
        _reg["lee"].add(p)
def _fin():
    _listo[0] = True
    with open(os.environ["REPLICA_REGISTRO"], "w") as f:
        json.dump({k: sorted(v) for k, v in _reg.items()}, f)
atexit.register(_fin)
sys.addaudithook(_hook)
sys.argv = sys.argv[1:]
runpy.run_path(sys.argv[0], run_name="__main__")
"""


# ------------------------------------------- utilidades -------------------------------------

def sha256(ruta, limite=None):
    h = hashlib.sha256()
    leidos = 0
    with open(ruta, "rb") as f:
        while True:
            n = 1 << 20 if limite is None else min(1 << 20, limite - leidos)
            if n <= 0:
                break
            b = f.read(n)
            if not b:
                break
            h.update(b)
            leidos += len(b)
    return h.hexdigest()


def rel(p):
    try:
        return str(Path(p).resolve().relative_to(RAIZ))
    except ValueError:
        return str(p)


def cargar_huellas():
    if HUELLAS.exists():
        return json.loads(HUELLAS.read_text(encoding="utf-8"))
    return None


def guardar_huellas(h):
    HUELLAS.write_text(json.dumps(h, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def huellas_actuales():
    out = {}
    for p in sorted(DATOS.rglob("*.csv")):
        if "__pycache__" in p.parts:
            continue
        out[rel(p)] = {"sha256": sha256(p), "bytes": p.stat().st_size}
    return out


def comparar_datos(base, hoy):
    """Estado de cada CSV frente a la base: igual, ampliado, modificado, nuevo, falta."""
    estado = {}
    for k, v in hoy.items():
        b = base.get(k)
        if b is None:
            estado[k] = "nuevo"
        elif b["sha256"] == v["sha256"]:
            estado[k] = "igual"
        elif v["bytes"] > b["bytes"] and sha256(RAIZ / k, b["bytes"]) == b["sha256"]:
            estado[k] = "ampliado"
        else:
            estado[k] = "modificado"
    for k in base:
        if k not in hoy:
            estado[k] = "falta"
    return estado


def limpiar(txt):
    """'1,04,' → '1.04' (la coma decimal de las fichas y la puntuación final fuera)."""
    return txt.rstrip(".,").replace("−", "-").replace(",", ".").replace("+", "")


def numero(txt):
    return float(limpiar(txt))


def decimales(txt):
    t = limpiar(txt)
    return len(t.split(".")[1]) if "." in t else 0


def bloque_ficha(texto, inicio):
    """Texto del primer bloque de la ficha cuyo encabezado empieza por `inicio`."""
    lineas = texto.splitlines()
    for i, l in enumerate(lineas):
        if l.startswith(inicio):
            fin = next((j for j in range(i + 1, len(lineas)) if lineas[j].startswith("## ")), len(lineas))
            return "\n".join(lineas[i:fin])
    return None


def revisar_cifras(salida, cifras):
    res = []
    for que, rx_out, ficha, inicio, rx_ficha in cifras:
        r = {"que": que, "ficha": ficha}
        m1 = re.search(rx_out, salida, re.S)
        ruta = RAIZ / ficha
        bloque = bloque_ficha(ruta.read_text(encoding="utf-8").replace("−", "-"), inicio) if ruta.exists() else None
        m2 = re.search(rx_ficha, bloque) if bloque else None
        if not m1:
            r.update(estado="aviso", detalle="el script ya no imprime esta cifra")
        elif not m2:
            r.update(estado="aviso", detalle=f"no se encontró en la ficha (bloque «{inicio}»); ¿se editó?")
        else:
            a, b = numero(m1.group(1)), numero(m2.group(1))
            tol = 0.5 * 10 ** -decimales(m2.group(1)) + 0.5 * 10 ** -decimales(m1.group(1)) + 1e-9
            ok = abs(a - b) <= tol
            r.update(estado="ok" if ok else "distinta", script=m1.group(1), en_ficha=m2.group(1))
        res.append(r)
    return res


def diferencia_texto(a, b, nombre, max_lineas=12):
    try:
        la = a.read_text(encoding="utf-8").splitlines()
        lb = b.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return [f"{nombre}: archivo binario distinto ({a.stat().st_size} → {b.stat().st_size} bytes)"]
    d = list(difflib.unified_diff(la, lb, "original", "hoy", lineterm="", n=0))
    if len(d) > max_lineas:
        d = d[:max_lineas] + [f"... ({len(d) - max_lineas} líneas más)"]
    return d


# --------------------------------------- requirements.txt -----------------------------------

def escribir_requirements():
    """Fija las versiones instaladas de todo lo que importa codigo/ (y sus dependencias)."""
    externos = set()
    for p in (RAIZ / "codigo").rglob("*.py"):
        try:
            arbol = ast.parse(p.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            continue
        for n in ast.walk(arbol):
            if isinstance(n, ast.Import):
                externos |= {a.name.split(".")[0] for a in n.names}
            elif isinstance(n, ast.ImportFrom) and n.module and n.level == 0:
                externos.add(n.module.split(".")[0])
    locales = {p.stem for p in (RAIZ / "codigo").rglob("*.py")}
    externos = {m for m in externos if m not in sys.stdlib_module_names and m not in locales}
    mod_a_dist = md.packages_distributions()
    directas, faltan = set(), []
    for m in sorted(externos):
        dists = mod_a_dist.get(m)
        if dists:
            directas.add(dists[0])
        else:
            faltan.append(m)

    def nombre_req(req):
        return re.split(r"[\s<>=!~;\[(]", req, maxsplit=1)[0]

    todas, cola = {}, list(directas)
    while cola:
        d = cola.pop()
        clave = d.lower().replace("_", "-")
        if clave in todas:
            continue
        try:
            dist = md.distribution(d)
        except md.PackageNotFoundError:
            continue
        todas[clave] = (dist.metadata["Name"], dist.version)
        for req in dist.requires or []:
            if "extra ==" in req:
                continue
            cola.append(nombre_req(req))
    directas_l = {d.lower().replace("_", "-") for d in directas}
    L = [
        "# Versiones exactas con las que se replicaron los backtests de la cueva.",
        f"# Python {platform.python_version()} ({platform.system()} {platform.machine()})",
        f"# Generado por codigo/automatizacion/replica.py el {datetime.now():%Y-%m-%d}.",
        "# Instalar igual: python3 -m pip install -r requirements.txt",
        "",
        "# Importadas directamente por codigo/",
    ]
    L += [f"{n}=={v}" for k, (n, v) in sorted(todas.items()) if k in directas_l]
    L += ["", "# Dependencias de las anteriores (también influyen en el resultado, p. ej. los PNG)"]
    L += [f"{n}=={v}" for k, (n, v) in sorted(todas.items()) if k not in directas_l]
    if faltan:
        L += ["", "# Importadas en codigo/ pero NO instaladas aquí (no se fijan): " + ", ".join(faltan)]
    texto = "\n".join(L) + "\n"
    ruta = RAIZ / "requirements.txt"
    previo = ruta.read_text(encoding="utf-8") if ruta.exists() else None
    # La fecha cambia cada día: solo reescribe si cambió algo además de la fecha.
    sin_fecha = lambda t: re.sub(r"el \d{4}-\d{2}-\d{2}", "", t or "")
    if sin_fecha(previo) != sin_fecha(texto):
        ruta.write_text(texto, encoding="utf-8")
        return "actualizado"
    return "sin cambios"


# ------------------------------------------- principal --------------------------------------

def respaldar_resultados(destino):
    copia = {}
    for p in RESULTADOS.rglob("*"):
        if p.is_file() and "diario" not in p.relative_to(RESULTADOS).parts:
            r = p.relative_to(RESULTADOS)
            (destino / r).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, destino / r)
            copia[str(r)] = sha256(p)
    return copia


def restaurar_si_cambio(copia, respaldo, ignorar):
    restaurados = []
    for r, h in copia.items():
        p = RESULTADOS / r
        if r in ignorar:
            continue
        if not p.exists() or sha256(p) != h:
            shutil.copy2(respaldo / r, p)
            restaurados.append(r)
    return restaurados


def correr(nueva_base=False):
    hoy = huellas_actuales()
    base = cargar_huellas()
    primera = base is None
    if primera or nueva_base:
        base = {"creado": datetime.now().isoformat(timespec="seconds"), "datos": hoy,
                "salidas": (base or {}).get("salidas", {}) if not nueva_base else {}}
    estado_datos = comparar_datos(base["datos"], hoy)

    informe = {"fecha": datetime.now().isoformat(timespec="seconds"), "primera_vez": primera,
               "nueva_base": nueva_base, "python": platform.python_version(), "scripts": [],
               "datos": {k: v for k, v in estado_datos.items() if v != "igual"}, "restaurados": []}

    with tempfile.TemporaryDirectory(prefix="cueva_replica_") as tmp:
        tmp = Path(tmp)
        respaldo = tmp / "respaldo_resultados"
        copia = respaldar_resultados(respaldo)
        trabajo = tmp / "repo"
        shutil.copytree(RAIZ / "codigo", trabajo / "codigo", ignore=shutil.ignore_patterns("__pycache__", "automatizacion"))
        shutil.copytree(DATOS, trabajo / "datos", ignore=shutil.ignore_patterns("__pycache__", "*.py"))
        (trabajo / "resultados").mkdir()
        # CSV ampliados: se recortan al tamaño de la base para replicar exactamente.
        for k, e in estado_datos.items():
            if e == "ampliado":
                with open(trabajo / k, "r+b") as f:
                    f.truncate(base["datos"][k]["bytes"])
        envoltorio = tmp / "envoltorio.py"
        envoltorio.write_text(ENVOLTORIO, encoding="utf-8")

        for s in SCRIPTS:
            r = {"id": s["id"], "archivos": [], "diferencias": [], "cifras": []}
            registro = tmp / "registro.json"
            if registro.exists():
                registro.unlink()
            env = dict(os.environ, REPLICA_REGISTRO=str(registro), MPLBACKEND="Agg", PYTHONHASHSEED="0")
            t0 = datetime.now()
            try:
                p = subprocess.run([sys.executable, str(envoltorio), *s["args"]], cwd=trabajo, env=env,
                                   capture_output=True, text=True, timeout=TIEMPO_MAX)
                salida, codigo, error = p.stdout, p.returncode, p.stderr
            except subprocess.TimeoutExpired:
                salida, codigo, error = "", -1, f"tardó más de {TIEMPO_MAX} s"
            r["segundos"] = round((datetime.now() - t0).total_seconds(), 1)
            reg = json.loads(registro.read_text()) if registro.exists() else {"lee": [], "escribe": []}
            leidos = sorted({str(Path(x).resolve().relative_to(trabajo.resolve())) for x in reg["lee"]
                             if Path(x).resolve().is_relative_to(trabajo.resolve() / "datos")})
            r["datos_leidos"] = leidos
            cambios = {d: estado_datos.get(d, "nuevo") for d in leidos if estado_datos.get(d, "nuevo") != "igual"}
            r["datos_cambiados"] = cambios

            if any(v in ("modificado", "falta") for v in cambios.values()):
                r["veredicto"] = "NO COMPARABLE"
                r["diferencias"].append("cambió la historia de sus datos: " +
                                        ", ".join(f"{k} ({v})" for k, v in cambios.items()))
                if codigo != 0:
                    r["diferencias"].append("además el script falló con esos datos: " + (error.strip().splitlines() or ["?"])[-1])
                informe["scripts"].append(r)
                continue
            if codigo != 0:
                r["veredicto"] = "NO REPLICA"
                r["diferencias"].append(f"el script falló (código {codigo}): " + (error.strip().splitlines() or ["?"])[-1])
                informe["scripts"].append(r)
                continue

            escritos = {str(Path(x).resolve().relative_to(trabajo.resolve())) for x in reg["escribe"]
                        if Path(x).resolve().is_relative_to(trabajo.resolve() / "resultados")}
            iguales = True
            for sal in sorted(set(s["salidas"]) | escritos):
                nuevo, original = trabajo / sal, RAIZ / sal
                if not nuevo.exists():
                    r["archivos"].append({"archivo": sal, "estado": "no se generó"})
                    iguales = False
                elif not original.exists():
                    r["archivos"].append({"archivo": sal, "estado": "sin original en resultados/"})
                    iguales = False
                elif sha256(nuevo) == sha256(original):
                    r["archivos"].append({"archivo": sal, "estado": "idéntico"})
                else:
                    r["archivos"].append({"archivo": sal, "estado": "DISTINTO"})
                    r["diferencias"] += diferencia_texto(original, nuevo, sal)
                    iguales = False

            h_out = hashlib.sha256(salida.encode("utf-8")).hexdigest()
            h_base = base["salidas"].get(s["id"])
            if h_base is None:
                r["pantalla"] = "sin huella previa"
            elif h_base == h_out:
                r["pantalla"] = "idéntica"
            else:
                r["pantalla"] = "DISTINTA"
                iguales = False
                r["diferencias"].append("lo que imprime en pantalla cambió respecto de la base")

            r["cifras"] = revisar_cifras(salida, s["cifras"])
            if any(c["estado"] == "distinta" for c in r["cifras"]):
                iguales = False
                r["diferencias"] += [f"cifra «{c['que']}»: script {c['script']} · ficha {c['en_ficha']}"
                                     for c in r["cifras"] if c["estado"] == "distinta"]
            r["veredicto"] = "REPLICA" if iguales else "NO REPLICA"
            if iguales and h_base is None:
                base["salidas"][s["id"]] = h_out
            informe["scripts"].append(r)

        # Red de seguridad: resultados/ tiene que quedar igual que al empezar.
        informe["restaurados"] = restaurar_si_cambio(copia, respaldo, ignorar={"huellas_datos.json"})

    if primera or nueva_base or any(s["veredicto"] == "REPLICA" for s in informe["scripts"]):
        guardar_huellas(base)
    informe["requirements"] = escribir_requirements()
    informe["ok"] = all(s["veredicto"] != "NO REPLICA" for s in informe["scripts"])
    return informe


def imprimir(inf):
    print(f"RÉPLICA · {inf['fecha']} · Python {inf['python']}")
    if inf["primera_vez"]:
        print("Primera vez: se creó la base de huellas en resultados/huellas_datos.json")
    if inf["nueva_base"]:
        print("Se aceptaron los datos de hoy como NUEVA BASE (decisión del trader).")
    if inf["datos"]:
        print("Datos que cambiaron desde la base:")
        for k, v in sorted(inf["datos"].items()):
            print(f"  · {k}: {v}")
    else:
        print("Datos: todos los CSV de datos/ son idénticos a la base.")
    print()
    for s in inf["scripts"]:
        ok_c = sum(c["estado"] == "ok" for c in s["cifras"])
        extra = f" · cifras de la ficha {ok_c}/{len(s['cifras'])}" if s["cifras"] else ""
        print(f"{s['veredicto']:<14} {s['id']}  ({s['segundos']} s{extra})")
        for a in s["archivos"]:
            print(f"    {a['archivo']}: {a['estado']}")
        for c in s["cifras"]:
            if c["estado"] == "aviso":
                print(f"    aviso: {c['que']}: {c['detalle']}")
        for d in s["diferencias"]:
            print(f"    {d}")
    if inf["restaurados"]:
        print("\n¡OJO! Se restauraron en resultados/: " + ", ".join(inf["restaurados"]))
    print(f"\nrequirements.txt: {inf['requirements']}")
    n = sum(s["veredicto"] == "REPLICA" for s in inf["scripts"])
    print(f"Resumen: {n}/{len(inf['scripts'])} REPLICA · {'OK' if inf['ok'] else 'HAY SCRIPTS QUE NO REPLICAN'}")


def main():
    ap = argparse.ArgumentParser(description="Comprueba que los backtests se repiten byte a byte.")
    ap.add_argument("--json", action="store_true", help="imprime el resumen en JSON")
    ap.add_argument("--nueva-base", action="store_true", help="acepta los datos de hoy como base (decisión del trader)")
    a = ap.parse_args()
    os.chdir(RAIZ)
    inf = correr(nueva_base=a.nueva_base)
    if a.json:
        print(json.dumps(inf, ensure_ascii=False, indent=1))
    else:
        imprimir(inf)
    sys.exit(0 if inf["ok"] else 1)


if __name__ == "__main__":
    main()
