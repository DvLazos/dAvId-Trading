# Riesgo · cesta10_williams_r · fase 07 · tamaño y riesgo · CRITERIO

> **SOLO EJERCICIO, ESTRATEGIA NO VALIDADA.** La ficha no tiene aprobadas las fases 04-06 (Fase 06 · Robustez (anexo: patrones y huella) · motor → NO APRUEBA). Estos números sirven para aprender y probar la tubería, no para operar.

> **Esta skill propone; no aprueba.** La fase 07 es de CRITERIO: el riesgo final lo decides tú, por escrito en la ficha. Nada de esto es una señal ni promete rentabilidad.

## Datos de partida
- Operaciones: 230 (archivo `resultados/cesta10_williams_r_operaciones.csv`, todo el periodo: incluye las de dentro de muestra, que suelen ser optimistas).
- Periodo: 13-08-2010 a 06-11-2026 (≈ 16,2 años, 14,2 operaciones por año).
- Ganadoras: 52 % · retorno medio por operación 6,05 %.
- Distancia al stop (lo que se pierde si salta): inferida de las salidas por stop: mediana 10,09 % con costes.
- Peor operación: -1,20 R (1 R = una pérdida completa de stop; más de 1 R significa hueco de precio).
- Límite de caída: 10 % (no existe MI_PLAN.md o no trae la caída: 10 % (supuesto)). Objetivo para la caída p95: 7 % (supuesto: 70 % del límite, margen de seguridad).
- Niveles de vigilancia (supuesto, hoja de ruta): aviso al 5 % y apagado al 8 % de caída.

**Palabras clave.** *Caída* = la peor bajada desde un máximo de la cuenta. *Monte Carlo* = barajar 10.000 veces el orden de las operaciones para ver otras historias posibles. *Percentil 95 (p95)* = el 95 % de las barajas cae menos que esto.

## 1. Fracción fija (un % del capital en riesgo por operación)
- **Propuesta máxima: 0,60 % de riesgo por operación.** Con 10.000 de capital (ejemplo) son 60 en riesgo por operación.
- Caída: mediana 4,4 % · p95 6,8 % · p99 8,2 % · peor baraja 12,8 % · orden real 11,5 %.
- Probabilidad de tocar el aviso (5 %): 32 % · de tocar el apagado (8 %): 1,3 %.
- Resultado acumulado de la muestra con ese tamaño: 125 % (el pasado no se repite).
- **Alerta:** en el orden real de la historia la caída fue 11,5 %, más que tu límite de 10 % y peor que el 100,0 % de las barajas. Señal de que las pérdidas llegan en racimos (varias operaciones a la vez caen juntas): barajar el orden rompe esos racimos y subestima la caída.
- **Propuesta prudente: 0,35 %**, el mayor tamaño con el que la caída p95 del Monte Carlo **y** la caída del orden real quedan bajo 7 %.
- **Ojo, operaciones a la vez:** hasta 9 posiciones abiertas al mismo tiempo. Si todas saltan juntas, la pérdida sería ≈ 5,4 % de golpe. El Monte Carlo trata las operaciones una tras otra, así que subestima ese riesgo cuando hay muchas a la vez.

Tabla corta (riesgo por operación → caída p95 · probabilidad de tocar el apagado):
- 0,25 % → 2,9 % · 0 %
- 0,50 % → 5,7 % · 0 %
- 0,75 % → 8,5 % · 8 %
- 1,00 % → 11,2 % · 36 %
- 1,50 % → 16,4 % · 92 %
- 2,00 % → 21,3 % · 100 %

## 2. Objetivo de volatilidad (tamaño que se ajusta al vaivén reciente)
- **Propuesta máxima: vaivén objetivo 0,7 % del capital por operación.** El tamaño de cada operación = 0,7 % ÷ desviación típica de las últimas 20 operaciones cerradas (sin mirar el futuro), con tope de 100 % del capital (sin apalancamiento, supuesto).
- Parte del capital que entra en cada operación: mediana 4 % (mín. 2 %, máx. 16 %).
- Caída: mediana 4,1 % · p95 6,4 % · p99 7,8 % · orden real 9,5 %.
- Probabilidad de tocar el aviso: 24 % · el apagado: 0,8 %.
- Resultado acumulado de la muestra: 93 %.

## Qué decides tú (fase 07 · CRITERIO)
1. ¿Qué riesgo por operación aceptas? Puede ser igual o **menor** que la propuesta, nunca mayor sin volver a correr esto.
2. ¿Confirmas los niveles de aviso (5 %) y apagado (8 %)?
3. Escríbelo en el bloque «Fase 07» de la ficha. Mientras METODO.md diga «umbral: se fija en el Reto», la fase 07 queda PENDIENTE.
4. Esta estrategia no está validada: el veredicto de la fase 07 es **NO APRUEBA / solo ejercicio**, aunque los números se vean bien.

## Supuestos
- Límite de caída 10 % (no existe MI_PLAN.md o no trae la caída: 10 % (supuesto)); objetivo p95 7 %; aviso 50 % y apagado 80 % del límite.
- Monte Carlo del orden, 10.000 barajas, semilla 42. Las operaciones se suman una tras otra (interés compuesto).
- Las operaciones del pasado representan a las futuras. Si la estrategia cambia de comportamiento, todo esto cambia.
- Arranque del objetivo de volatilidad con las primeras 20 operaciones (mira un poco el futuro solo al principio).

*Generado por `codigo/riesgo.py`. Determinista: mismo CSV, mismo resultado.*
