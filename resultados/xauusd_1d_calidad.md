# Calidad de datos · XAUUSD diario

- Archivo: datos/XAUUSD_1D.csv
- Fuente: TradingView, símbolo OANDA:XAUUSD (oro contra dólar, CFD de OANDA), velas de 1 día.
- Descargado: 2026-11-24, conector TradingView MCP.
- Pedidas: 840 velas. Guardadas: 839. Se quitó la última vela (2026-11-24) porque estaba sin cerrar.
- Periodo: 2023-08-24 a 2026-11-23.
- Columnas: fecha, open, high, low, close, volume.
- Fecha: es el día de la sesión. La vela abre a las 17:00 de Nueva York del día anterior y cierra a las 17:00 del día de la fecha.
- Volumen: son ticks del CFD de OANDA (cambios de precio), no contratos reales. No sirve como volumen del mercado.

## Comprobaciones
- Se cuadró con el resumen de TradingView: primera apertura, último cierre, máximo, mínimo y volumen total coinciden.
- Fechas repetidas: 0. Velas en fin de semana: 0. Huecos de más de 4 días: 0.
- Velas incoherentes (máximo menor que apertura o cierre, etc.): 0. Valores vacíos: 0.
- Movimientos de más del 5 % en un día: 3. Se conservan; revísalos en el gráfico.
  - 2025-10-21 · −5,3 %
  - 2026-01-30 · −8,8 %
  - 2026-02-03 · +6,1 %

## Límites
- 839 velas son unos 3,3 años. Para el 70/30 quedan unas 250 velas fuera de muestra (unos 12 meses).
- En velas diarias no se ven las sesiones de Asia, Londres y Nueva York. Para medir la ruptura del máximo de Asia hace falta un CSV de 15 minutos o 1 hora.
