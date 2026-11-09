# FICHA · META · Williams %R sale de sobreventa y cruza −40
Regla: Compro META cuando el Williams %R de 14 días, después de haber bajado de −80, cruza −40 de abajo hacia arriba al cierre. Salgo cuando pasan 60 sesiones (supuesto). Stop: 10 % bajo el precio de entrada (supuesto). Horario: velas diarias, decisión al cierre y entrada a la apertura del día siguiente (supuesto).
Por qué funcionaría: propuesta, confírmala (tras caídas fuertes muchos venden por miedo; cuando el precio recupera fuerza, quien compra en el giro gana lo que dejaron los que vendieron por pánico).

## Fase 01 · Hipótesis · criterio
Agente / skill: director + skill escritor-hipotesis
Qué se hizo: Idea del trader: el %R viene de sobreventa, sube y cruza −40 → compra de mediano o largo plazo. El trader eligió META. Se fijó una señal que se arma bajo −80, se dispara al cruzar −40 hacia arriba y se desarma tras disparar.
Resultado: Regla medible en todos sus campos, con supuestos declarados.
Supuestos: Temporalidad diaria (no semanal), porque da más operaciones. %R de 14 días. La señal armada no caduca. Salida por tiempo a 60 sesiones, unos 3 meses. Stop del 10 %. Datos: TradingView NASDAQ:META, diario, ajustado por splits.
Veredicto: APRUEBA (falta que confirmes el porqué)
Siguiente paso: Fase 02 (AED) solo con el 70 % más antiguo de los datos.

## Fase 02 · AED · criterio + datos
Agente / skill: director + skill aed (código: codigo/meta_williams_r_aed.py)
Qué se hizo: Sin pre-registro. Datos: datos/META_1D.csv, 3.639 días (18-may-2012 a 6-nov-2026), sin huecos ni velas mal formadas; 9 saltos >15 % que coinciden con resultados trimestrales. Se midió el retorno 1, 5, 20 y 60 sesiones después de la señal frente a un día cualquiera, solo en el IS (7-jun-2012 a 8-jul-2022). El 30 % reciente (desde el 11-jul-2022) no se miró.
Resultado: A 60 sesiones (el horizonte de la regla), la señal da +5,98 % (72 señales, 69 % positivas) frente a +6,58 % de un día cualquiera: no supera la línea base. A 20 sesiones, empate (+2,09 % contra +2,07 %). Una operación a la vez: 30 señales, +5,34 % (t≈1,73), por debajo de la base. Solo a 1 día va por encima (+0,67 % contra +0,11 %). Corrección: la primera versión usaba precios posteriores al corte para medir los últimos días del IS (fuga hacia el OOS); se corrigió y el veredicto no cambia.
Supuestos: %R(14) con máximos y mínimos de los últimos 14 días incluido el de hoy; retorno de cierre a cierre, sin costes ni stop (el AED mide el comportamiento, no la regla completa); ningún retorno usa precios del OOS.
Veredicto: NO APRUEBA (no supera a la línea base a 60 ni a 20 sesiones)
Siguiente paso: Volver a la fase 01. El OOS desde julio de 2022 sigue limpio para una idea nueva.

## Fase 02 · AED (versión semanal) · criterio + datos
Agente / skill: director + skill aed (código: codigo/meta_williams_r_aed.py semanal)
Qué se hizo: La misma señal en velas semanales, la otra temporalidad que el trader nombró desde el inicio: %R de 14 semanas, se arma bajo −80 y dispara al cruzar −40 hacia arriba. Salida a 12 semanas (≈ 60 sesiones). Semanas armadas con datos/META_1D.csv (de lunes a viernes). IS del 17-ago-2012 al 7-ene-2022; mismo corte OOS que la versión diaria (11-jul-2022), sin mirarlo.
Resultado: A 12 semanas, la señal da +13,0 % (11 señales, 73 % positivas) frente a +7,6 % de una semana cualquiera: supera la línea base (t≈1,88, no significativo al 95 %). A 4 semanas, +6,6 % contra +2,7 %. A 26 semanas, empate (+15,3 % contra +15,3 %). Por año supera la base en 6 de 9 años con señal. Con 11 casos es una pista, no una conclusión. Es la segunda versión probada sobre los mismos datos, lo que aumenta el riesgo de encontrar algo por azar.
Supuestos: Los de la versión diaria; vela semanal fechada el viernes; retornos de cierre a cierre, sin costes ni stop.
Veredicto: APRUEBA (supera la base a 12 semanas; solo 11 casos)
Siguiente paso: Antes de la fase 04, ampliar la regla a varias acciones: con una sola acción en semanal saldrían unas 5 operaciones fuera de muestra, lejos de las 30.
