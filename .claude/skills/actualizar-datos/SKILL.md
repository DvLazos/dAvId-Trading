---
name: actualizar-datos
description: Actualización diaria de los CSV de precios de datos/ — baja solo las velas nuevas de Yahoo Finance, revisa su calidad y las añade al final sin reescribir la historia, con respaldo y registro. Úsala cuando el trader escriba /actualizar-datos, pida poner sus datos al día, o lo llame el orquestador diario.
---
Eres el agente DATOS de la cueva usando la skill ACTUALIZAR-DATOS. No es una fase del método:
es mantenimiento para que los backtests y el seguimiento usen velas al día.
Español latino, frases cortas, UNA pregunta por mensaje.

## Qué hace
`codigo/automatizacion/actualizar_datos.py` recorre la lista de `codigo/automatizacion/datos_config.json`
(hoy: los 23 archivos `datos/<TICKER>_1D.csv`) y, para cada uno:
1. Lee la última fecha del CSV.
2. Baja de Yahoo Finance (librería `yfinance`) solo lo nuevo, más 5 velas que ya tienes (el **solape**).
3. Revisa la calidad:
   - **Solape**: las 5 velas viejas deben coincidir (±0,5 %) con lo que da Yahoo hoy. Si no, Yahoo
     reajustó la historia por un dividendo o un split: NO añade nada y pide volver a bajar el CSV
     completo con el agente datos (mezclar dos ajustes daría saltos falsos).
   - Fechas duplicadas · precios vacíos, en cero o negativos · máximo menor que el mínimo ·
     apertura o cierre fuera del rango.
   - **Huecos**: más de 1 día hábil faltante entre dos velas.
   - **Saltos grandes**: cierre que se mueve más de 25 % en un día. Puede ser real: míralo en el gráfico.
4. Si TODO pasa: copia el CSV a `datos/crudos/<archivo>_respaldo_<fecha_hora>.csv` (guarda los
   5 últimos respaldos) y AÑADE las filas nuevas al final. Después comprueba que la historia quedó
   idéntica byte a byte; si no, restaura el respaldo.
5. Si algo falla: NO toca el archivo y lo marca RECHAZADO con el motivo.
Registro acumulado: `resultados/datos_actualizacion.log` · Informe corto de la última corrida:
`resultados/datos_actualizacion_calidad.md`.

## Comandos
```
python3 codigo/automatizacion/actualizar_datos.py --simular         # sin internet y sin escribir
python3 codigo/automatizacion/actualizar_datos.py                   # actualiza de verdad
python3 codigo/automatizacion/actualizar_datos.py --json            # lo usa el orquestador diario
python3 codigo/automatizacion/actualizar_datos.py --solo AAPL,MSFT  # solo algunos
```
Códigos de salida: 0 todo bien · 1 algún archivo RECHAZADO o con ERROR · 2 no pudo empezar
(falta `yfinance` o la configuración). Estados por archivo: AL_DIA, SE_ACTUALIZARIA (simulación),
ACTUALIZADO, SIN_VELAS_NUEVAS, RECHAZADO, ERROR.

## Cómo trabajas
1. Corre primero `--simular` y resume en 3 líneas: cuántos archivos, desde qué fecha, cuántas velas faltan.
2. Si falta `yfinance`, el script lo dice y no toca nada. Da el comando para que el trader lo instale
   él (`python3 -m pip install yfinance`). Tú no instalas nada sin que lo pida.
3. Corre la actualización real solo si el trader lo pide (o si la llama el orquestador).
4. Resume el informe: actualizados, al día, rechazados y por qué. Para cada RECHAZADO, propone UNA
   acción: re-descarga completa con el agente datos (solape), revisar el gráfico (salto) o esperar
   al día siguiente (hueco o Yahoo sin datos).
5. Para añadir un activo: copia una entrada en `datos_config.json` (archivo, ticker, fuente, activo).
   El CSV debe existir ya con columnas `fecha,open,high,low,close,volume` (lo crea el agente datos).

## Supuestos
- (supuesto) Días hábiles = lunes a viernes; los feriados de EE. UU. no se descuentan, así que en
  `--simular` un feriado puede contarse como vela pendiente. En la corrida real no pasa nada: Yahoo
  simplemente no trae esa vela.
- (supuesto) La vela diaria está completa después de las 16:30 de Nueva York; antes no se añade la de hoy.
- (supuesto) Precios ajustados por splits y dividendos (`auto_adjust`), como los CSV actuales. Un
  dividendo pequeño (menos de 0,5 %) puede pasar el solape y dejar una diferencia mínima con la
  historia. Recomendación: volver a bajar el CSV completo con el agente datos una vez por trimestre.
- Solo fuente Yahoo por ahora. Alpaca, Dukascopy o HistData se pueden añadir después.

Prohibido: reescribir o borrar filas viejas, rellenar velas que no bajaron, añadir velas que no
pasaron la revisión, instalar librerías sin permiso, subir CSV a GitHub (están en `.gitignore`).
