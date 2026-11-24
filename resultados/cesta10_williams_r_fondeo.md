# Fondeo · cesta10_williams_r · simulador de retos

> **Ningún reto se compra si la estrategia no aprobó las fases 01 a 07** y tú no aceptaste por escrito la probabilidad de pasar. Este informe propone; tú decides.

> **SOLO EJERCICIO, ESTRATEGIA NO VALIDADA** (sin bloque: fase 07 · Fase 06 · Robustez (anexo: patrones y huella) · motor → NO APRUEBA). Sirve para aprender a usar el simulador.

> **Los números de los perfiles son EJEMPLOS** (`codigo/fondeo_perfiles.json`). Cópialos de las reglas oficiales vigentes de cada empresa antes de sacar conclusiones.

## Datos de partida
- 230 operaciones de `resultados/cesta10_williams_r_operaciones.csv` · 0,27 por semana · duración mediana 77 días.
- Riesgo = distancia al stop (inferida de las salidas por stop: mediana 10,09 % con costes). 1 R = perder un stop completo.
- Riesgo por operación de referencia: 0,50 % de la cuenta inicial (supuesto), fijo (sin interés compuesto).
- Monte Carlo: 10.000 intentos, semilla 42. Cada día se sortea cuántas operaciones cierran (copiando los días reales del backtest, también los vacíos) y qué resultado tiene cada una.

## Encaje con el fondeo: POBRE
- pocas operaciones: 0,27 por semana. Un reto suele pedir llegar al objetivo en pocas semanas.
- duración mediana de 77 días naturales: deja posiciones abiertas de noche y el fin de semana, algo que muchas empresas limitan o prohíben. Además, la empresa mide la pérdida diaria con lo abierto (flotante) y este simulador solo ve operaciones cerradas: la realidad sería peor.
- Los retos de fondeo suelen operarse en índices, forex o futuros y premian llegar al objetivo en pocas semanas. Una estrategia semanal en acciones encaja mal: el fondeo probablemente necesite ideas propias más rápidas.

**Palabras clave.** *Objetivo*: ganancia que hay que alcanzar para pasar. *Pérdida diaria / total*: si la cuenta baja eso, el reto se pierde. *Caída arrastrada (trailing)*: el límite de pérdida sube con el máximo de la cuenta. *Consistencia*: el mejor día no puede ser más de cierto % de la ganancia total.

## Perfil «cfd_generico» (EJEMPLO, no es una empresa real)
- Reto genérico de CFD (índices/forex) en una fase: pérdida diaria y pérdida total fijas.
- Reglas usadas: cuenta 100.000 · objetivo 8,0 % · pérdida diaria 5,0 % · pérdida total 10,0 % (fija) · 4 días mínimos con operaciones · costo 500 (pago único).
- Plazo: 260 días hábiles (supuesto: el perfil no trae límite).
- **Con 0,50 % por operación:** pasa 17,7 % · falla 0,0 % · no termina a tiempo 82,3 %.
- Cuando pasa: mediana de 183 días hábiles y 12 operaciones.
- Costo medio por intento 500 → **costo esperado por cuenta fondeada: 2.826** (costo por intento ÷ probabilidad de pasar).

Rejilla de riesgo por operación → pasa · falla · no termina · costo por fondeada:
- 0,25 % → 0,9 % · 0,0 % · 99,1 % · 56.180
- 0,50 % → 17,7 % · 0,0 % · 82,3 % · 2.826
- 0,75 % → 38,0 % · 0,0 % · 62,0 % · 1.318
- 1,00 % → 52,0 % · 0,1 % · 47,9 % · 961
- 1,25 % → 61,7 % · 0,7 % · 37,7 % · 811
- 1,50 % → 68,4 % · 1,6 % · 30,0 % · 731
- 2,00 % → 74,1 % · 6,5 % · 19,3 % · 674
- 2,50 % → 74,4 % · 13,9 % · 11,7 % · 672
- 3,00 % → 72,5 % · 20,1 % · 7,4 % · 690

**Riesgo que maximiza la probabilidad de pasar en la rejilla: 2,50 %** (pasa 74,4 %, falla 13,9 %). Ojo: más riesgo también acerca la pérdida máxima; en una cuenta fondeada real el riesgo suele tener que bajar. Nunca uses más riesgo que el que aceptaste en la fase 07 (`resultados/<idea>_riesgo.md`) solo para pasar más rápido.

## Perfil «futuros_generico» (EJEMPLO, no es una empresa real)
- Evaluación genérica de futuros: caída arrastrada (trailing) sobre el saldo de cierre, cuota mensual y regla de consistencia opcional.
- Reglas usadas: cuenta 50.000 · objetivo 6,0 % · caída arrastrada 4,0 % · 5 días mínimos con operaciones · consistencia: mejor día ≤ 50 % de la ganancia · costo 150 (cada mes).
- Plazo: 260 días hábiles (supuesto: el perfil no trae límite).
- **Con 0,50 % por operación:** pasa 23,7 % · falla 1,0 % · no termina a tiempo 75,3 %.
- Cuando pasa: mediana de 185 días hábiles y 12 operaciones.
- Por qué falla: caída arrastrada 100 %.
- Costo medio por intento 1.801 → **costo esperado por cuenta fondeada: 7.599** (costo por intento ÷ probabilidad de pasar).

Rejilla de riesgo por operación → pasa · falla · no termina · costo por fondeada:
- 0,25 % → 4,2 % · 0,0 % · 95,9 % · 46.540
- 0,50 % → 23,7 % · 1,0 % · 75,3 % · 7.599
- 0,75 % → 34,7 % · 6,0 % · 59,3 % · 4.820
- 1,00 % → 38,8 % · 16,2 % · 45,1 % · 3.927
- 1,25 % → 40,0 % · 21,5 % · 38,5 % · 3.614
- 1,50 % → 39,4 % · 29,1 % · 31,6 % · 3.371
- 2,00 % → 34,9 % · 43,3 % · 21,8 % · 3.147
- 2,50 % → 34,7 % · 44,3 % · 21,0 % · 3.116
- 3,00 % → 34,0 % · 46,2 % · 19,8 % · 3.085

**Riesgo que maximiza la probabilidad de pasar en la rejilla: 1,25 %** (pasa 40,0 %, falla 21,5 %). Ojo: más riesgo también acerca la pérdida máxima; en una cuenta fondeada real el riesgo suele tener que bajar. Nunca uses más riesgo que el que aceptaste en la fase 07 (`resultados/<idea>_riesgo.md`) solo para pasar más rápido.

## Antes de comprar cualquier reto (lista corta; la completa está en la skill fondeo)
- [ ] La estrategia aprobó las fases 01 a 07.
- [ ] Leíste en la web oficial, con fecha, si permiten: robots/EA, copiar operaciones, webhooks/puentes, VPS, dejar posiciones de noche y fin de semana, operar noticias, y la misma estrategia en varias cuentas.
- [ ] Copiaste las reglas a un perfil propio y volviste a correr este simulador.
- [ ] Aceptaste por escrito la probabilidad de pasar y el costo esperado.

## Supuestos
- Los perfiles son ejemplos, no reglas reales.
- La pérdida diaria y la caída arrastrada se miden con operaciones cerradas (las empresas suelen usar el flotante: la realidad es más dura). El arrastre se actualiza con el saldo de cierre del día.
- Días con operación = días en que cierra al menos una operación. Riesgo fijo sobre la cuenta inicial.
- Las operaciones y los días del backtest representan a los futuros (remuestreo con reemplazo, sin racimos). Se usan todas las operaciones del CSV, también las de dentro de muestra, que suelen ser optimistas.

*Generado por `codigo/fondeo_simulador.py`. Determinista: mismo CSV y mismos perfiles, mismo resultado.*
