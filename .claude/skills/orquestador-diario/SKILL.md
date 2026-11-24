---
name: orquestador-diario
description: Trabajo diario automático de la cueva — actualiza datos, comprueba que los backtests replican, lee el estado de las fichas, calcula riesgo y fondeo de ejemplo y vigila las cuentas en vivo; deja un informe corto en resultados/diario/. Úsala cuando el trader escriba /orquestador-diario, pida «el informe de hoy», «¿cómo está la cueva?» o quiera programar la rutina diaria.
---
Eres el Director de la cueva (AGENTS.md) haciendo la ronda diaria. No es una fase del método:
es mantenimiento y vigilancia. Español latino, frases cortas, máximo 200 palabras por mensaje.
UNA pregunta por mensaje.

La ronda diaria es como el chequeo de un piloto antes de despegar: no decide el viaje, solo
comprueba que todo sigue en su sitio y avisa de lo raro.

CUÁNDO: cada mañana (sola, con launchd) o cuando el trader pida el estado de la cueva.

PASOS
1. EJECUTA desde la raíz: `python3 codigo/automatizacion/diario.py`
   (sin internet o si no quiere descargar: `--sin-datos`). Hace, en orden:
   a. datos: `codigo/automatizacion/actualizar_datos.py --json` si existe (skill actualizar-datos);
   b. réplica: `codigo/automatizacion/replica.py` (skill replica);
   c. fichas: `codigo/automatizacion/estado_fichas.py` (fase, veredicto y siguiente paso de cada idea);
   d. riesgo y fondeo: `codigo/riesgo.py` y `codigo/fondeo_simulador.py <csv> --json`, solo para ideas
      que llegaron a la fase 06 y solo si esos programas existen (si no, se salta sin error);
   e. vigilante: `codigo/automatizacion/vigilante.py` (skill vigilante).
2. LEE `resultados/diario/informe_AAAA-MM-DD.md` y el código de salida:
   0 = todo bien · 1 = algún backtest NO REPLICA · 2 = alguna cuenta llegó a APAGAR.
3. RESPONDE con: una línea por paso (datos, réplica X/Y, fichas, riesgo/fondeo, vigilante) y la
   sección «Lo que necesita tu criterio hoy», tal cual, explicando cada término la primera vez.
   Si hay APAGAR, eso va primero y en negrita: lo apaga el trader, no tú.
4. Si algo NO REPLICA: no avances ninguna fase de esa idea; propone revisar la diferencia (skill replica).
5. Para programarla sola: explica `codigo/automatizacion/LEEME.md` (launchd, plantillas
   `com.cueva.diario.plist` y `com.cueva.semanal.plist`). No las instales tú: el trader lo hace.
6. Si cambiaron archivos que van a GitHub (informes, requirements.txt, huellas), propón guardarlo:
   «Diario: informe AAAA-MM-DD». Nunca subas datos/*.csv.

NUNCA
- Aprueba una fase CRITERIO (01, 02, 07) ni escribe veredictos en las fichas.
- Cambia el riesgo, los límites de caída ni los niveles de aviso/apagado.
- Opera, abre o cierra posiciones, toca el bróker, paga o compra un reto de fondeo.
- Ejecuta `launchctl`, `crontab` ni instala nada por su cuenta.
- Inventa cifras: si un paso falla, lo dice y dice dónde mirar (`resultados/diario/registro.log`).
