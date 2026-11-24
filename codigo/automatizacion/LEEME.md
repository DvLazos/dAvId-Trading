# codigo/automatizacion/ · la cueva trabaja sola cada mañana

Aquí vive la parte automática de la cueva: programas que corren solos, revisan que todo siga en
orden y te dejan un informe corto. **Solo informan.** Nunca aprueban una fase, nunca cambian tu
riesgo, nunca operan y nunca compran un reto de fondeo. Tú decides.

## Qué hay

| Archivo | Qué hace |
|---|---|
| `diario.py` | El trabajo diario (orquestador). Datos → réplica → fichas → riesgo y fondeo → vigilante. Escribe `resultados/diario/informe_AAAA-MM-DD.md` y `resultados/diario/registro.log`. |
| `replica.py` | Vuelve a correr los backtests en una carpeta temporal y comprueba que dan **exactamente** lo mismo (byte a byte) y que las cifras coinciden con las fichas. Guarda las huellas de tus CSV en `resultados/huellas_datos.json` y escribe `requirements.txt`. |
| `estado_fichas.py` | Lee `fichas/*.md` y dice en qué fase está cada idea, su veredicto y el siguiente paso. |
| `vigilante.py` | Si existe `resultados/<idea>_vivo.csv`, compara lo real con el backtest y mide la caída: aviso al 5 %, APAGAR al 8 %. |
| `semanal.py` | Junta los 7 últimos informes diarios en `resultados/informe_semanal_AAAA-MM-DD.md`, con la lección de la semana. |
| `com.cueva.diario.plist` | Plantilla para que el Mac corra `diario.py` de lunes a viernes a las 07:00. **No está instalada.** |
| `com.cueva.semanal.plist` | Plantilla para `semanal.py` cada lunes a las 07:30. **No está instalada.** |
| `actualizar_datos.py`, `datos_config.json` | Los usa la skill actualizar-datos (paso a del diario). |

## Probarlo a mano (primero siempre esto)

Abre la Terminal y escribe:

```
cd /Users/david/Desktop/dAvId-Trading
python3 codigo/automatizacion/diario.py --sin-datos
python3 codigo/automatizacion/semanal.py
```

`--sin-datos` no descarga nada (sirve sin internet). Tarda menos de un minuto. Luego abre
`resultados/diario/informe_<fecha de hoy>.md`.

**Código de salida** (un número que el programa devuelve al terminar; lo ves con `echo $?`):
0 = todo bien · 1 = algún backtest NO REPLICA · 2 = alguna cuenta llegó al nivel de APAGAR.

## Palabras que vas a ver

- **Réplica**: volver a correr un backtest y obtener lo mismo. Si no replica, la cifra de la ficha ya no es de fiar.
- **Huella (sha256)**: una firma de 64 letras que cambia si cambia un solo byte del archivo.
- **CSV ampliado**: solo se añadieron días nuevos al final. Es normal; la réplica recorta la copia y sigue siendo exacta.
- **CSV modificado**: cambió la historia. No es normal. Los scripts que lo usan salen «NO COMPARABLE».
  Si aceptas los datos nuevos (es tu criterio): `python3 codigo/automatizacion/replica.py --nueva-base`.
- **requirements.txt**: la lista de versiones exactas de Python y sus librerías con las que todo replica.
  Para instalar las mismas en otro equipo: `python3 -m pip install -r requirements.txt`.

## Programarlo en tu Mac (launchd)

**launchd** es el «reloj» de macOS: corre programas a la hora que le digas, aunque no tengas la
Terminal abierta. Las dos plantillas ya traen la ruta de tu repositorio
(`/Users/david/Desktop/dAvId-Trading`) y de tu Python
(`/Library/Frameworks/Python.framework/Versions/3.15/bin/python3`). Si cambias de carpeta o de
Python, edita esas rutas dentro de los `.plist`.

**Instalar** (copias las plantillas a tu carpeta de agentes y las cargas):

```
cp /Users/david/Desktop/dAvId-Trading/codigo/automatizacion/com.cueva.diario.plist ~/Library/LaunchAgents/
cp /Users/david/Desktop/dAvId-Trading/codigo/automatizacion/com.cueva.semanal.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.cueva.diario.plist
launchctl load ~/Library/LaunchAgents/com.cueva.semanal.plist
```

**Comprobar** que están cargadas: `launchctl list | grep cueva` (salen dos líneas).
**Probar ya**, sin esperar a las 07:00: `launchctl start com.cueva.diario`.
Lo que imprime queda en `resultados/diario/launchd_diario.log`.

**Desinstalar** (deja de correr solo; no borra tus informes):

```
launchctl unload ~/Library/LaunchAgents/com.cueva.diario.plist
launchctl unload ~/Library/LaunchAgents/com.cueva.semanal.plist
rm ~/Library/LaunchAgents/com.cueva.diario.plist ~/Library/LaunchAgents/com.cueva.semanal.plist
```

**Avisos importantes**
- El Mac tiene que estar encendido. Si está dormido a las 07:00, launchd lo corre al despertar.
- Tu repositorio está en el **Escritorio**, una carpeta protegida de macOS. La primera vez puede
  fallar con «Operation not permitted». Arreglo: Ajustes del Sistema → Privacidad y seguridad →
  Acceso total al disco → añade el `python3` de arriba (o mueve el repositorio fuera del Escritorio
  y cambia las rutas de los `.plist`).
- Si cambias un `.plist`, haz `unload` y `load` otra vez para que launchd lo relea.
- Si no quieres descargar datos cada mañana, añade `<string>--sin-datos</string>` debajo de la línea de `diario.py`.

## La alternativa: rutinas programadas de Claude Code (/schedule)

launchd solo corre programas de Python: no piensa. Cuando el trabajo necesita un **agente** (leer el
informe y escribirte un resumen, pedir al Director que revise por qué algo NO REPLICA, preparar la
fase siguiente), usa una **rutina programada** de Claude Code: escribe `/schedule` en Claude Code y
pídele, por ejemplo, «cada lunes a las 08:00, usa la skill informe-semanal y resúmeme las
decisiones que tengo pendientes». Ojo: esas rutinas corren en la nube, con una copia del
repositorio de GitHub; tus CSV de `datos/` no se suben a GitHub, así que allí la réplica no puede
correr. Reparto recomendado: **launchd en tu Mac** para lo que usa tus datos (diario y semanal) y
**/schedule** para leer los informes que ya subiste y ayudarte a decidir.

## Supuestos (puedes cambiarlos)

- Niveles del vigilante: aviso 5 % y APAGAR 8 % (50 % y 80 % de tu límite del 10 %, de MI_HOJA_DE_RUTA.md). Si MI_PLAN.md trae otro límite, se usa ese.
- Formato de `resultados/<idea>_vivo.csv`: una fila por operación cerrada con `fecha` y `equity` (valor de la cuenta) o `ret_cuenta` (variación de la cuenta) o `ret` (retorno de la operación, como en el backtest) con `fraccion` (parte de la cuenta usada; si falta, toda la cuenta: prudente).
- Riesgo y fondeo se calculan para las ideas que llegaron a la fase 06, aunque su veredicto final sea NO APRUEBA (se marcan «solo ejercicio»).
- Para añadir un backtest a la réplica: copia una entrada de la lista `SCRIPTS` en `replica.py`.
