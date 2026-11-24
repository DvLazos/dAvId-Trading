---
name: universo
description: Universo sin sesgo de supervivencia — qué acciones estaban en el Nasdaq-100 en cada fecha y cuáles eran las N mayores ese día, sin mirar el futuro. Úsala cuando el trader escriba /universo, arme una cesta de acciones, o una ficha elija acciones con la lista de hoy.
---
Eres el Director de la cueva (AGENTS.md) usando la skill UNIVERSO. Es una pieza de DATOS:
no es una fase, pero la fase 02 y la 04 de cualquier cesta de acciones dependen de ella.
Español latino, frases cortas, UNA pregunta por mensaje.

## Por qué existe
Lección de `cesta10_williams_r`: elegir las 10 mayores del QQQ de HOY para probar el pasado
infla los resultados. Hoy solo ves a las empresas que sobrevivieron y crecieron.
- **Sesgo de supervivencia**: olvidar a las que salieron del índice (quebraron, se compraron, cayeron).
- **Sesgo de selección**: elegir sabiendo quién ganó.
- **Mirar el futuro** (*look-ahead*): usar un dato que en la fecha X todavía no existía.
La solución: en cada fecha X, usar solo la lista de ese día y solo datos anteriores a X.

## Los archivos
- `datos/universo_ndx100_historico.csv` · el universo real. Columnas:
  `fecha_efectiva,ticker,accion,fuente` · `accion` es `alta` o `baja` · fechas AAAA-MM-DD.
  La primera tanda de filas es la **lista inicial**: todos los miembros en una fecha base, como `alta`.
  Después, cada cambio con su fuente. Las líneas que empiezan con `#` son comentarios.
- `datos/universo_ndx100_EJEMPLO.csv` · FICTICIO (tickers `EJ_...`). Solo para el autotest.
- `codigo/universo.py` · lee el archivo, lo valida y responde.

**Estado hoy: PENDIENTE.** El archivo histórico solo tiene la cabecera. Esta skill NO inventa
componentes: los pone el trader desde una fuente que él elige y verifica. Hasta que esté lleno,
toda cesta elegida con la lista de hoy lleva el aviso «sesgo de supervivencia».

## Comandos
```
python3 codigo/universo.py --autotest                       # prueba con el ejemplo ficticio
python3 codigo/universo.py --validar                        # revisa el archivo real
python3 codigo/universo.py --fecha 2022-10-12               # miembros ese día
python3 codigo/universo.py --fecha 2022-10-12 --top 10      # las 10 mayores ese día
python3 codigo/universo.py --fecha 2022-10-12 --top 10 --json   # para otros scripts
```
Desde Python: `from universo import cargar, top_n` (con `codigo/` en el path).

## Reglas de fechas (sin mirar el futuro)
- Un cambio vale desde el INICIO de su `fecha_efectiva`: la alta ya es miembro ese día; la baja ya no.
- Usa la fecha EFECTIVA (cuando entra o sale), nunca la del anuncio: el anuncio sale días antes,
  pero el índice no cambia hasta la fecha efectiva.
- El tamaño de cada acción en la fecha X se mide solo con velas ANTERIORES a X.

## Tamaño: el sustituto (supuesto)
Sin capitalización de mercado histórica, el «tamaño» es el promedio de **precio de cierre × volumen**
(dólares negociados por día) de las últimas 63 velas anteriores a X (≈ 3 meses; cambia con `--ventana`).
Lo saca de `datos/<TICKER>_1D.csv`. **(supuesto)**: las empresas más grandes suelen ser las más
negociadas, pero no siempre (una acción muy volátil puede negociarse más que una más grande).
Si un miembro no tiene CSV, sale en «sin datos» con un aviso: un ranking sin las empresas que
salieron del índice vuelve a tener sesgo. Baja sus datos con el agente datos (si el ticker ya no
cotiza, Yahoo puede no tenerlo: dilo, no lo inventes).

## Fuentes para llenar el archivo (el trader elige)
1. **Anuncios oficiales de Nasdaq** (sitio de Nasdaq y de Nasdaq Global Indexes, notas de prensa
   «to join the Nasdaq-100 Index»). La más fiable. Trae fecha de anuncio y fecha efectiva.
   Límite: hay que buscarlos uno por uno; la revisión anual es en diciembre, más los cambios sueltos.
2. **Tablas de cambios de Wikipedia** («Nasdaq-100», sección de cambios históricos). Rápida, gratis.
   Límite: la escriben voluntarios; puede faltar un cambio o tener la fecha del anuncio en vez de
   la efectiva. Úsala como borrador y verifica con la fuente 1.
3. **Datos de pago** (Norgate Data, CRSP, Compustat, Sharadar). Traen la lista histórica ya armada
   y las acciones que dejaron de cotizar. Límite: cuestan dinero; revisa la licencia.
Recomendación (supuesto): lista inicial al 2010-01-04 desde la fuente 2 o 3, y cada cambio
contrastado con la fuente 1. Anota en `fuente` de dónde salió cada fila (enlace o nombre + fecha).

## Cómo verificarlo (revisión de calidad)
1. `--validar` sin errores (no hay bajas de quien no estaba, ni altas dobles, ni fuentes vacías).
2. En 3 fechas al azar, cuenta miembros: deben ser unos 100 (algunas empresas tienen 2 clases, por
   ejemplo GOOGL y GOOG, así que puede haber 101-103).
3. Compara esas 3 fechas con una lista publicada de ese momento (archivo de Wikipedia de esa época
   en archive.org, o un informe del QQQ de ese trimestre).
4. Revisa la revisión anual de diciembre de 2 años: deben salir y entrar varias a la vez.
5. Cambios de nombre (FB → META): NO son baja + alta. Usa un solo ticker, el mismo nombre que tu
   archivo `datos/<TICKER>_1D.csv`, y anótalo en un comentario `#`.
Cuando pase estas 5 revisiones, el universo deja de estar PENDIENTE y la puerta del mes 1 de
MI_HOJA_DE_RUTA.md queda cumplida en esa parte.

## Uso en el método
- Fase 01: si la idea es una cesta de acciones, la regla dice «las N mayores del Nasdaq-100 en cada
  fecha de rebalanceo según `codigo/universo.py`», nunca una lista fija de hoy.
- Fase 04: el backtest llama a `top_n` en cada rebalanceo. Si el universo está PENDIENTE, la fase 04
  de una cesta queda PENDIENTE (o se anota el sesgo como supuesto grave en la ficha).

## Guardar en GitHub
`.gitignore` tiene `datos/**/*.csv`, así que el archivo del universo NO se sube. Pero no es un
precio tuyo: es una lista pública que conviene versionar (ver quién cambió qué fila).
Recomendación: añadir al final de `.gitignore` la línea `!datos/universo_*.csv` (el `!` hace una
excepción). Esta skill no edita `.gitignore`: lo decides tú. Si prefieres no tocarlo, guarda el
archivo en `activos/universo_ndx100_historico.csv` y usa `--archivo` con esa ruta.

Prohibido: inventar componentes o fechas, rellenar huecos de memoria, usar el archivo EJEMPLO para
un backtest, quitar el aviso de sesgo mientras el universo esté PENDIENTE.
