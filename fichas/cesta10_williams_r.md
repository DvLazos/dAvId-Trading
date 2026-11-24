# FICHA · Cesta de 10 · Williams %R semanal sale de sobreventa y cruza −40
Regla: Compro cada una de las 10 mayores acciones del Nasdaq-100 (AAPL, NVDA, MSFT, GOOGL, AMZN, MU, AMD, TSLA, META, WMT) cuando su Williams %R de 14 semanas, después de haber bajado de −80, cruza −40 de abajo hacia arriba al cierre de la semana. Salgo al cierre de la semana 12 contando la de entrada. Stop: 10 % bajo el precio de entrada (supuesto). Horario: velas semanales; decisión al cierre del viernes, entrada a la apertura de la semana siguiente.
Por qué funcionaría: propuesta, confírmala (tras caídas fuertes muchos venden por miedo; cuando el precio recupera fuerza, quien compra en el giro gana lo que dejaron los que vendieron por pánico).

## Fase 01 · Hipótesis · criterio
Agente / skill: director + skill escritor-hipotesis
Qué se hizo: Enmienda del 8-nov-2026 a fichas/meta_williams_r.md (versión semanal), que se conserva: la misma señal se aplica a 10 acciones a la vez para tener operaciones suficientes. Las 10 son las de mayor peso en el QQQ el 8-nov-2026 (TipRanks), con Alphabet una sola vez (GOOGL).
Resultado: Regla medible en todos sus campos.
Supuestos: %R de 14 semanas. La señal armada no caduca. Salida por tiempo a 12 semanas (≈ 60 sesiones). Stop del 10 %. Una operación a la vez por acción. Datos diarios de TradingView (2010 a 6-nov-2026, ajustados por splits) agrupados en semanas de lunes a viernes.
Veredicto: APRUEBA (falta que confirmes el porqué)
Siguiente paso: Fase 02 (AED) solo antes del corte del 11-jul-2022.

## Fase 02 · AED · criterio + datos
Agente / skill: director + skill aed (código: codigo/cesta10_williams_r.py aed)
Qué se hizo: Sin pre-registro. Retorno 1, 4, 12 y 26 semanas tras la señal frente a cualquier semana de las 10 acciones, del 9-abr-2010 al 7-ene-2022, sin usar ningún precio posterior al 11-jul-2022. Datos: 9 CSV nuevos en datos/<TICKER>_1D.csv más META; sin huecos ni velas mal formadas; los saltos grandes coinciden con noticias o resultados.
Resultado: A 12 semanas, la señal da +9,19 % (156 señales, 68 % positivas) frente a +7,66 % de cualquier semana: +1,5 puntos (t≈1,04, no significativo). También supera la base a 1, 4 y 26 semanas. Supera la base en 9 de 10 acciones (falla TSLA) y en 10 de 13 años con señal. META ya se había mirado antes (sesgo).
Supuestos: Retornos de cierre a cierre, sin costes ni stop; la vela semanal se fecha el viernes.
Veredicto: APRUEBA (supera la base a 12 semanas en casi todas las acciones y años; ventaja pequeña)
Siguiente paso: Fase 03 (reglas) y fase 04 (backtest con costes y stop).

## Fase 03 · Reglas · motor
Agente / skill: director con el manual del agente reglas (.claude/agents/reglas.md)
Qué se hizo: Regla convertida en pseudocódigo sin código de plataforma.
Resultado: Pseudocódigo completo debajo; dos personas marcarían las mismas operaciones.
Supuestos: Los 8 de la lista de abajo.
Veredicto: APRUEBA (pseudocódigo sin huecos, con supuestos declarados)
Siguiente paso: Fase 04 (backtest) con OOS desde el 11-jul-2022.

```
DATOS: velas semanales (lunes a viernes) de AAPL, NVDA, MSFT, GOOGL, AMZN, MU, AMD, TSLA,
       META y WMT. Cada acción se trata por separado, con su propia cuenta del 10 % del capital.
CADA SEMANA, al cierre del viernes, para cada acción:
  1. MAXIMO14 = máximo más alto de las últimas 14 semanas (incluida esta).
     MINIMO14 = mínimo más bajo de las últimas 14 semanas (incluida esta).
     %R = (MAXIMO14 − cierre) ÷ (MAXIMO14 − MINIMO14) × −100.
  2. SI %R < −80 → la señal queda ARMADA.
  3. SI la señal está ARMADA Y el %R de la semana anterior ≤ −40 Y el %R de esta semana > −40:
       la señal se desarma.
       SI estoy fuera en esta acción:
         COMPRA a la apertura de la semana siguiente (SEMANA DE ENTRADA = semana 1).
         PRECIO DE ENTRADA = esa apertura. STOP = PRECIO DE ENTRADA × 0,90.
  4. MIENTRAS esté dentro, en cada semana nueva (empezando por la de entrada), en este orden:
       a. SI el mínimo de la semana ≤ STOP:
            SALGO al STOP (o a la apertura de la semana, si abrió por debajo del STOP).
       b. SI esta es la semana 12 contando desde la SEMANA DE ENTRADA:
            SALGO al cierre de esta semana.
  5. SI NO se cumple nada → no hago nada. FIN de la semana.
```
Supuestos: (1) %R con máximos y mínimos de 14 semanas incluida la actual. (2) La señal armada no caduca. (3) Las señales mientras estoy dentro se ignoran, pero desarman la señal. (4) Primero se comprueba el stop y después la salida por tiempo. (5) Costes: 0,05 % por lado (comisión + deslizamiento); son acciones muy líquidas. (6) 10 cuentas iguales (10 % del capital cada una), cada una con interés compuesto. (7) La semana de salida puede dar una señal nueva. (8) Si los datos se acaban antes de la semana 12, la operación se cierra al último cierre.

## Fase 04 · Backtest · motor
Agente / skill: director con la skill validador-4de4 (código: codigo/cesta10_williams_r.py backtest; operaciones en resultados/cesta10_williams_r_operaciones.csv)
Qué se hizo: Backtest con costes y stop. IS del 9-abr-2010 al 10-jul-2022 (≈ 74 %) y OOS del 11-jul-2022 al 6-nov-2026 (≈ 26 %), el corte fijado antes de mirar el OOS.
Resultado: OOS: factor de beneficio 1,99 ✓ · 68 operaciones ✓ · caída máxima −13,1 % ✓ · factor de beneficio sin la mejor 1,68 ✓ → 4/4. IS: 2,68 · 162 · −10,4 % · 2,50 → 4/4. Avisos: comprar y mantener la cesta multiplicó el capital por 4,59 en el OOS y la regla por 1,44, porque el capital solo estuvo invertido ≈ 24 % del tiempo; la ventaja depende de pocas operaciones grandes (sin las 5 mejores del OOS el factor de beneficio baja a 1,08; AMD aporta mucho); 35 de 68 operaciones OOS salieron por stop.
Supuestos: Los de la fase 03. Sesgo de selección: las 10 acciones se eligieron con datos de noviembre de 2026, sabiendo cuáles crecieron más; esto infla el IS y también el OOS. Es la quinta variante probada en la cueva sobre datos parecidos. La caída máxima es baja en parte porque el 76 % del capital está en efectivo.
Veredicto: APRUEBA (4/4 fuera de muestra, con los avisos de arriba)
Siguiente paso: Fase 05 (optimizar): comprobar que los vecinos de 14 semanas, −80, −40, 12 semanas y 10 % también funcionan.

## Fase 05 · Optimización · motor
Agente / skill: director con la skill optimizar (código: codigo/cesta10_williams_r_optimizar.py; mapa: resultados/cesta10_williams_r_meseta.png)
Qué se hizo: Rejilla de 2 parámetros que la regla ya tenía: nivel de disparo (−60 a −20, de 5 en 5) × semanas hasta la salida (6 a 18, de 2 en 2) = 63 combinaciones, solo dentro de muestra (datos cortados antes del 11-jul-2022), con los mismos costes y stop de la fase 04.
Resultado: MESETA. Los 8 vecinos de la combinación actual (−40, 12 semanas; FB 2,68 con 162 operaciones) tienen FB entre 2,37 y 3,22 (88 % a 120 % del actual) y más de 150 operaciones. Las 63 combinaciones tienen FB ≥ 1,3 y ≥ 138 operaciones. Se mantienen −40 y 12 semanas: no se cambia nada, así que no se vuelve a correr el OOS y los 4 números siguen 4/4 (fase 04). Aviso: el FB sube cuanto más tiempo se mantiene la acción (6 semanas ≈ 1,9; 18 semanas ≈ 3,4), lo que coincide con acciones que subieron mucho; parte de la meseta puede venir del sesgo de selección y no de la señal.
Supuestos: Parámetros probados elegidos por el director (el disparo es la idea del trader; la salida a 12 semanas era un supuesto). Fijos: %R de 14 semanas, armado en −80, stop 10 %. Vecinos inmediatos = las 8 casillas alrededor. Las operaciones que no caben enteras antes del corte no se cuentan.
Veredicto: APRUEBA (meseta, y los 4 números siguen 4/4 fuera de muestra)
Siguiente paso: Fase 06 (robustez): costes ×2, Monte Carlo, peores años y la cesta de las 10 mayores de julio de 2022 para medir el sesgo de selección.

## Fase 06 · Robustez · motor
Agente / skill: director con la skill robustez (código: codigo/cesta10_williams_r_robustez.py, semilla 42; gráficas: resultados/cesta10_williams_r_robustez.png)
Qué se hizo: La regla tal cual (fase 05), sin cambios. Las 4 pruebas del Reto sobre las 68 operaciones OOS (y años en todo el periodo), más una prueba extra del sesgo de selección: la misma regla en las 10 mayores del QQQ al 12-oct-2022 (AAPL, MSFT, AMZN, TSLA, GOOGL, META, NVDA, PEP, COST, AVGO; fuente: Insider Monkey, pesos al 12-oct-2022), con datos nuevos de PEP, COST y AVGO.
Resultado: a. Costes ×2: FB OOS 1,96 ✓ (pide ≥ 1,1). b. Monte Carlo del orden (1.000): caída del percentil 95 −11,3 % ✓ (pide < 30 %; la peor de 1.000, −15,3 %). c. Remuestreo (1.000): FB del percentil 5 = 1,16 ✓ (pide > 1; mediana 1,99). d. Años malos: 16 de 17 años ganan; sin el mejor año (2020) FB 2,22 ✓. Robustez 4/4. Único año perdedor: 2022 (20 operaciones, −187 % sumando retornos), justo al empezar el OOS. Extra, cesta de octubre de 2022: OOS 4/4 (FB 1,55 · 68 operaciones · caída −12,6 % · FB sin la mejor 1,36); el sesgo de selección explica parte de la ventaja (FB 1,99 → 1,55), pero no toda. Comprar y mantener esa cesta: ×3,50.
Supuestos: Costes base 0,05 % por lado, ×2 = 0,10 %. En el Monte Carlo cada operación usa el 10 % del capital, una tras otra (con más tamaño por operación la caída crece en proporción). El remuestreo del percentil 5 queda cerca del límite (1,16). Los umbrales son los provisionales del Reto. La lista de octubre de 2022 es 3 meses posterior al corte.
Veredicto: APRUEBA (4/4 de robustez y 4/4 en la cesta sin sesgo de hoy). Aprobar la fase 06 no valida la estrategia: faltan tamaño y riesgo (07) y puesta en marcha (08).
Siguiente paso: Fase 07 (tamaño y riesgo): todavía no hay agente ni skill; se construye durante el Reto, y antes conviene escribir MI_PLAN.md con /objetivos.

## Fase 06 · Robustez (anexo: patrones y huella) · motor
Agente / skill: director (código: codigo/cesta10_williams_r_patrones.py; operaciones de validación en resultados/cesta10_williams_r_validacion_operaciones.csv)
Qué se hizo: A pedido del trader, búsqueda de un patrón donde la regla funcione mejor. 4 patrones fijados antes de mirar (tendencia sobre/bajo la media de 40 semanas, caída desde el máximo de 52 semanas, semanas desde la sobreventa, amplitud de la caída en la cesta), medidos solo con operaciones anteriores al 11-jul-2022, con un criterio de elección fijado antes (≥ 30 operaciones, FB ≥ 1,25 × base y > 1,3; se elige uno). Validación única en 10 acciones nunca miradas: puestos 11 a 20 del QQQ al 12-oct-2022 (TMUS, CSCO, TXN, ADBE, AMGN, CMCSA, QCOM, HON, INTU, INTC). Además, la regla base en las 20 mayores del QQQ al 12-oct-2022, el universo sin sesgo de selección.
Resultado: Patrón elegido: caída del 15-30 % desde el máximo de 52 semanas (FB 3,72 con 33 operaciones en el descubrimiento). En la validación NO se sostiene: jul-2022 → nov-2026 da FB 0,42 con 24 operaciones (1/4); era azar. Hallazgo más importante: la regla base en las 10 acciones nuevas da 4/4 hasta jul-2022 (FB 1,64) pero 2/4 después (FB 0,88: pierde). En las 20 mayores de oct-2022, después del corte: FB 1,17 ✕ · 149 operaciones ✓ · caída −11,6 % ✓ · FB sin la mejor 1,09 ✓ → 3/4.
Supuestos: 10 grupos mirados en el descubrimiento (alguno sale bien por azar). TMUS tiene un salto de −31 % el 1-may-2013 (fusión con MetroPCS), posible artefacto de datos; no se quitó. La amplitud (P4) se mide con la cesta de hoy también en la validación.
Veredicto: NO APRUEBA (el patrón no se sostiene en datos nuevos, y en un universo sin sesgo de selección la regla base saca 3/4 después de jul-2022: su 4/4 dependía de haber elegido a las acciones que más subieron)
Siguiente paso: No pasar a la fase 07 con esta versión. Volver a la fase 01: la hipótesis honesta es «la regla en las mayores del índice en cada momento», y esa no pasa hoy.
