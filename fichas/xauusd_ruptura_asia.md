# FICHA · Oro · ruptura del máximo de Asia
Regla: Compro oro (XAUUSD) cuando una vela de 15 min cierra por encima del máximo de Asia (00:00-07:00 UTC). Salgo al cierre de Nueva York (21:00 UTC). Stop: el mínimo de Asia. Horario: entradas de 07:00 a 20:45 UTC, una por día.
Por qué funcionaría: propuesta, confírmala: Londres y Nueva York toman la dirección que Asia dejó marcada y el precio sigue en esa dirección el resto del día.

## Fase 01 · AED · CRITERIO + DATOS
Agente / skill: skill aed (código: codigo/xauusd_ruptura_asia_aed.py)
Qué se hizo: idea del trader (24-nov-2026), copiada tal cual: «Compro oro cuando rompe el máximo de Asia. Salgo al cierre de Nueva York. Stop: el mínimo de Asia.» Sin pre-registro. Se midió, sin stop, el retorno desde la primera vela de 15 min que cierra sobre el máximo de Asia hasta las 21:00 UTC. Se comparó con la línea base: la misma hora en todos los días. El horizonte (hasta las 21:00 UTC) se fijó antes de medir. Solo se usó el 70 % más antiguo, hasta el 19-may-2025.
Resultado: 586 casos en 887 días (66 %). Casos +0,042 % frente a base +0,018 %. Ventaja bruta +0,025 %, menor que el coste de 0,040 %: neta −0,015 %. Placebo: 15,5 % de los sorteos la igualan. Años positivos: 2 de 5 (2024 y 2025). Contexto: 53 % de los casos suben hasta la salida y el 37 % toca el mínimo de Asia antes de salir. Las 4 condiciones: casos sí · ventaja no · placebo no · años no → 1/4.
Supuestos: Asia de 00:00 a 07:00 UTC. «Rompe» = cierre de una vela de 15 min por encima del máximo de Asia. Cierre de Nueva York = 21:00 UTC todo el año. Costes 0,02 % por lado (supuesto, METODO.md). Datos: Dukascopy bid, 15 min, APTA CON AVISOS (610 saltos grandes conservados, 9 velas faltantes sin rellenar). Se descartan los días incompletos (feriados y cierres anticipados). 1 idea probada sobre este CSV.
Veredicto: NO APRUEBA (falla la ventaja tras costes, el placebo y los años: 1/4)
Siguiente paso: volver a la fase 01 con una idea nueva; no se hacen las fases 02 a 08 con esta regla.
