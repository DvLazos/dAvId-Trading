# Ficha técnica · SPY (ETF del S&P 500)

Fuente de datos: `datos/DatosSPY.csv` · velas diarias · 8,486 días · 29/01/1993 a 16/10/2026.

## Su personalidad: ¿tendencia o reversión a la media?

Mirando qué pasa un día después de una vela alcista o bajista:
- Después de un día **alcista**, el siguiente sube el 52.3 % de las veces.
- Después de un día **bajista**, el siguiente sube el 54.9 % de las veces.
- La línea base (sube cualquier día, sin condición) es 53.5 %.

Como después de una baja la probabilidad de subir (54.9 %) es más alta que la línea
base (53.5 %), y después de una subida es más baja (52.3 %), SPY tiene una **leve
tendencia a la reversión a la media en el corto plazo (día a día)**: tiende más a
«rebotar» después de una baja que a seguir cayendo. Es una huella débil, no una regla
de trading por sí sola — necesita pasar por la fase 02 (AED) de tu idea específica.

## Sus mejores y peores días de la semana

| Día | Retorno medio | % días al alza |
|---|---|---|
| Lunes | +0.057 % | 55.3 % |
| Martes | +0.070 % | 51.9 % |
| Miércoles | +0.060 % | 55.1 % |
| Jueves | +0.018 % | 53.3 % |
| Viernes | -0.002 % | 52.2 % |

Lunes a miércoles rinden algo mejor que jueves y viernes. La diferencia es pequeña:
es un patrón a vigilar, no una ventaja confirmada.

## Su volatilidad

- Rango diario promedio (alto-bajo / cierre), todo el historial: **1.29 %**.
- Rango diario promedio, últimos 2 años (2024 en adelante): **1.02 %** (más tranquilo
  que el promedio histórico).
- Peores días del historial: -10.94 % (16/03/2020), -9.84 % (15/10/2008), -9.57 %
  (12/03/2020) — todos en crisis (COVID, 2008).
- Mejores días: +14.52 % (13/10/2008), +11.69 % (28/10/2008), +10.50 % (09/04/2025).

## En qué horario se mueve más

**PENDIENTE.** El CSV que tengo (`datos/DatosSPY.csv`) es de velas **diarias**, no
tiene la hora de cada movimiento. Para saber en qué horario del día se mueve más
(por ejemplo, la primera hora de apertura vs. el cierre) necesito un CSV intradiario
(velas de 1 minuto, 5 minutos o 1 hora). Pídeselo al agente «datos» (o la skill
`/datos`) eligiendo Yahoo Finance o Alpaca con intervalo intradiario para SPY.

Lo que sí sé sin datos: SPY cotiza en NYSE Arca, sesión regular de **9:30 a 16:00
hora de Nueva York**, de lunes a viernes (fuera de festivos del mercado de EE.UU.).

## Qué lo mueve (contexto, no dato de mercado)

SPY replica el S&P 500, así que lo mueve lo que mueve a las 500 empresas más grandes
de EE.UU. en conjunto:
- Decisiones de tasas de interés de la Reserva Federal (reuniones del FOMC).
- Temporada de resultados trimestrales (earnings season).
- Datos macro de EE.UU.: inflación (CPI), empleo (nóminas no agrícolas), PIB.
- Apetito de riesgo global y eventos geopolíticos.
- Flujos grandes en fechas de vencimiento de opciones (quadruple witching).

## Lo que dice tu bróker

**PENDIENTE.** No sé con qué bróker o plataforma vas a operar SPY, así que no puedo
poner spread, comisión ni tamaño de contrato reales. Dime tu bróker cuando lo tengas
y completo esta sección — la necesitas antes de la fase 04 (el backtest usa estos
costos).

| Spread | Comisión | Tamaño del contrato | Horario del bróker |
|---|---|---|---|
| PENDIENTE | PENDIENTE | PENDIENTE | PENDIENTE |
