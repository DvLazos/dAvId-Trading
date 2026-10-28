# Calidad de datos · datos/qqq_1h_alpaca.csv

Veredicto: **APTA CON AVISOS** para backtest

- Origen: datos/crudos/qqq_1h_alpaca.csv · mercado bolsa · temporalidad 1h · zona original UTC
- Fuente: Alpaca, feed IEX (datos de esa bolsa, no el mercado estadounidense consolidado); ajuste ALL por dividendos y splits.
- Desde 2021-10-29 13:00 hasta 2026-10-27 20:00 UTC · 5.0 años
- Velas: 10958 en el crudo → 10958 curadas (0.0% eliminadas)
- Velas faltantes: 0 (0.0%)
- Volumen: 0% en cero

## Avisos
- 42 saltos fuera de lo normal: revísalos en el gráfico (pueden ser reales).
- Revisión visual del trader: los saltos parecen movimientos reales; se conservan sin cambios. No se verificaron de forma independiente.

## Saltos para revisar (primeros 10)
- 2021-12-07 14:00 UTC
- 2022-01-24 20:00 UTC
- 2022-01-25 14:00 UTC
- 2022-01-26 14:00 UTC
- 2022-03-08 17:00 UTC
- 2022-03-09 14:00 UTC
- 2022-05-02 19:00 UTC
- 2022-05-05 13:00 UTC
- 2022-05-06 14:00 UTC
- 2022-05-12 14:00 UTC

Umbrales provisionales del Reto: NO APTA si se eliminó más del 5 %, faltan más del 5 % de las velas,
hay menos de 1 año o menos de 100 velas. Datos gratuitos: buenos para investigar, no iguales a datos de pago.
