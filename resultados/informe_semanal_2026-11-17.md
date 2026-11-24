# Informe semanal · 2026-11-17

> Resumen de la semana para que tú decidas. Lo escribe codigo/automatizacion/semanal.py a partir de los informes diarios. No aprueba fases, no cambia el riesgo, no opera.

Informes leídos: 1 (del 2026-11-17 al 2026-11-17).

## 1. Réplica de los backtests
- Días con todo replicando: **1 de 1**.

## 2. Vigilante (cuentas en vivo)
- Sin cuentas en vivo esta semana.

## 3. Tus ideas (estado al 2026-11-17)
- **cesta10_williams_r** · Fase 06 · Robustez (anexo: patrones y huella) · motor → **NO APRUEBA**.
  - Siguiente paso: No pasar a la fase 07 con esta versión. Volver a la fase 01: la hipótesis honesta es «la regla en las mayores del índice en cada momento», y esa no pasa hoy.
- **meta_williams_r** · Fase 02 · AED (versión semanal) · criterio + datos → **APRUEBA**.
  - Siguiente paso: Antes de la fase 04, ampliar la regla a varias acciones: con una sola acción en semanal saldrían unas 5 operaciones fuera de muestra, lejos de las 30.
- **nas100_media_toque** · Fase 02 · AED · criterio + datos → **NO APRUEBA**.
  - Siguiente paso: Volver a la fase 01: cualquier cambio (horizonte, media) es una enmienda con fecha y se mide en datos no usados (2022 en adelante u otro activo).
- **nvda_media_toque** · Fase 04 · Backtest · motor → **NO APRUEBA**.
  - Siguiente paso: Nueva hipótesis (fase 01) con stop, probada en otras acciones que no se hayan mirado.

## 4. Lo que necesita tu criterio esta semana
1. cesta10_williams_r: lo siguiente es la fase 01, que es CRITERIO (la decides tú; la máquina no avanza sola). _(apareció 1 de 1 días)_
2. nas100_media_toque: lo siguiente es la fase 01, que es CRITERIO (la decides tú; la máquina no avanza sola). _(apareció 1 de 1 días)_
3. nvda_media_toque: lo siguiente es la fase 01, que es CRITERIO (la decides tú; la máquina no avanza sola). _(apareció 1 de 1 días)_

## 5. Lección de la semana
**Fracción fija.** Arriesgar el mismo % de la cuenta en cada operación (por ejemplo, 0,5 %). Al crecer la cuenta, crece el tamaño.

Para pensar: ¿Cuánto perderías en 10 operaciones perdedoras seguidas con tu fracción?

