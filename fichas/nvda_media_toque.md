# FICHA · NVDA · compra al tocar la SMA 200 (4H)
Regla: Compro NVDA cuando el mínimo de una vela de 4H toca la SMA de 200 velas (el cierre de esa vela está por encima de la SMA, supuesto). Salgo cuando pasan 10 sesiones (20 velas de 4H, supuesto). Stop: ninguno (supuesto). Horario: velas de 4H del CSV (datos/NVDA_4H_2016_2021.csv), entrada al precio de apertura de la vela siguiente (supuesto).
Por qué funcionaría: propuesta, confírmala (la media 200 actuaría como soporte dinámico en una acción con tendencia alcista fuerte).

## Fase 01 · Hipótesis · criterio
Agente / skill: director + skill escritor-hipotesis
Qué se hizo: Misma regla que fichas/nas100_media_toque.md, sin cambiar nada, aplicada a NVDA por decisión del trader después de que NAS100 no aprobara la fase 02.
Resultado: Regla comprobable, idéntica a la de NAS100. Es una idea nueva: se eligió el activo después de ver el resultado de NAS100.
Supuestos: Compra solo si el cierre de la vela tocada está por encima de la SMA. Sin stop. Entrada a la apertura de la vela siguiente. Datos: TradingView, NASDAQ:NVDA, 4H, solo horario regular, precios ajustados por splits (no por dividendos, que en NVDA son mínimos).
Veredicto: APRUEBA (falta que confirmes el porqué de la ventaja)
Siguiente paso: Fase 02 (AED) con el IS 2017-2021.

## Fase 02 · AED · criterio + datos
Agente / skill: director + skill aed (código: codigo/nas100_media_toque_aed.py datos/NVDA_4H_2016_2021.csv)
Qué se hizo: Sin pre-registro. Retorno de cierre a cierre 1, 5 y 20 velas después de cada toque de la SMA 200 (4H), frente a todas las velas y frente a las velas sobre la SMA, IS 2017-2021 (2016 solo para calentar la media). Datos: 3.013 velas, sin huecos ni velas mal formadas; dos saltos grandes (11-nov-2016 +17 %, 16-nov-2018 −19 %) que coinciden con resultados trimestrales.
Resultado: A 20 velas, la señal da +5,88 % (57 velas de toque, 84 % positivas) frente a +2,35 % de una vela cualquiera y +2,12 % de las velas sobre la SMA. Una operación a la vez: 19 señales, +3,55 % de media (t≈1,62, no significativo al 95 %). Supera la base en 4 de 5 años (falla 2019). A 1 vela no hay ventaja. Con 19 casos es una pista, no una conclusión. Alerta: NVDA se eligió sabiendo que fue una de las acciones que más subió en 2017-2021 (sesgo de elegir mirando atrás).
Supuestos: SMA de 200 cierres; toque = mínimo ≤ SMA ≤ máximo con cierre sobre la SMA; retorno de cierre a cierre, sin costes; los dos saltos son reales (resultados trimestrales); no se miró nada posterior a 2021.
Veredicto: APRUEBA (supera a la línea base a 20 velas en 4 de 5 años; solo 19 casos, la prueba real será 2022 en adelante)
Siguiente paso: Fase 03 (reglas): pseudocódigo con los supuestos de una operación a la vez, salida al cierre de la vela 20 y costes.

## Fase 03 · Reglas · motor
Agente / skill: director con el manual del agente reglas (.claude/agents/reglas.md)
Qué se hizo: Se convirtió la regla en pseudocódigo paso a paso, sin código de plataforma, cerrando los huecos con supuestos.
Resultado: Pseudocódigo completo debajo. Dos personas marcarían las mismas operaciones.
Supuestos: Los 7 de la lista de abajo.
Veredicto: APRUEBA (pseudocódigo sin huecos, con supuestos declarados)
Siguiente paso: Fase 04 (backtest) con costes, IS 2017-2021 y OOS 2022 en adelante.

```
DATOS: velas de 4H de NVDA (NASDAQ:NVDA, TradingView), solo horario regular,
       hora de Nueva York. Dos velas por día: 9:30 y 13:30.
CADA VELA, a su cierre:
  1. SMA200 = media de los cierres de las últimas 200 velas (incluida esta).
  2. SI estoy fuera Y mínimo de esta vela ≤ SMA200 ≤ máximo de esta vela
     Y cierre de esta vela > SMA200:
       esta vela es la VELA DE SEÑAL.
       COMPRA a la apertura de la vela siguiente (VELA DE ENTRADA = vela 1).
  3. MIENTRAS esté dentro, en cada vela nueva, en este orden:
       a. SI esta vela es la vela 20 contando desde la VELA DE ENTRADA:
          SALGO al cierre de esta vela. Ve al paso 2 con esta misma vela.
       b. SI aparece otra señal → se ignora.
  4. SI NO se cumple nada → no hago nada. FIN de la vela.
```
Supuestos: (1) La SMA se calcula con cierres; 2016 se usa solo para calentarla. (2) Una sola operación a la vez. (3) Sin stop, porque la regla no lo trae. (4) La vela de salida puede dar una señal nueva. (5) Costes: 0,05 % por lado (comisión + deslizamiento), 0,10 % ida y vuelta; NVDA es muy líquida y el diferencial suele ser de un centavo, así que es una cifra prudente. (6) Todo el capital en cada operación, sin apalancamiento. (7) Una operación que no llegue a 20 velas al final de los datos se cierra al último cierre.

## Fase 04 · Backtest · motor
Agente / skill: director con la skill validador-4de4 (código: codigo/nvda_media_toque_backtest.py; operaciones en resultados/nvda_media_toque_operaciones.csv)
Qué se hizo: Backtest con costes sobre datos/NVDA_4H_2016_2026.csv (5.438 velas hasta el 6-nov-2026, último día con mercado). Dos cortes: el del trader (IS 2017-2021 / OOS 2022-2026) y el del método (70 % / 30 %, corte el 20-nov-2023).
Resultado: OOS del trader: 28 operaciones, FB 1,08 ✕, 28 operaciones ✕, caída máxima −53,1 % ✕, FB sin la mejor 0,94 ✕ → 0/4. En 2022 (mercado bajista) 6 operaciones sumaron −53,7 %. OOS 70/30 del método: 19 operaciones, FB 2,77 ✓, 19 ✕, caída −24,7 % ✕, FB sin la mejor 2,30 ✓ → 2/4. IS 2017-2021: 2/4 (20 operaciones, caída −22,8 %). Comprar y mantener ganó en todos los tramos.
Supuestos: Los de la fase 03. Salto del 25-may-2023 (+26 %) por resultados trimestrales, dado por real. El OOS ya se usó: cualquier cambio a la regla necesita datos nuevos. Revisión posterior: la definición de «toque» no exigía venir desde arriba de la SMA, así que 22 de 48 operaciones (12 de 28 en el OOS, 5 de 6 en 2022) fueron cruces desde abajo, no retrocesos; además se corrigió un filtro de fechas que no cambió ningún número. La caída máxima medida con mínimos dentro de la vela es −53,6 % (con cierres, −53,1 %).
Veredicto: NO APRUEBA (0/4 en el OOS del trader, 2/4 en el del método: fallan las 30 operaciones y la caída máxima)
Siguiente paso: Nueva hipótesis (fase 01) con stop, probada en otras acciones que no se hayan mirado.
