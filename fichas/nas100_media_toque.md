# FICHA · NAS100 · compra al tocar la SMA 200 (4H)
Regla: Compro el NAS100 (NDX) cuando el mínimo de una vela de 4H toca la SMA de 200 velas (el cierre de esa vela está por encima de la SMA, supuesto). Salgo cuando pasan 10 sesiones (20 velas de 4H, supuesto). Stop: ninguno (supuesto). Horario: velas de 4H del CSV (datos/NDX_4H.csv), entrada al precio de apertura de la vela siguiente (supuesto).
Por qué funcionaría: propuesta, confírmala (el trader pide que la media actúe como soporte dinámico en tendencia alcista).

## Fase 01 · Hipótesis · criterio
Agente / skill: director + skill escritor-hipotesis (sin agente hipotesis separado)
Qué se hizo: Se fijó la media como SMA de 200 velas de 4H (elección A del trader). Se definió "toca" como mínimo ≤ SMA ≤ máximo de la vela. Se fijó la salida por tiempo (10 sesiones = 20 velas).
Resultado: La regla es comprobable y no ambigua en entrada, salida y datos. No se probó nada todavía.
Supuestos: Compra solo si el cierre de la vela tocada está por encima de la SMA. Sin stop. Entrada a la apertura de la vela siguiente. Datos: TradingView, NASDAQ:NDX, 4H, solo horario regular, sin volumen.
Veredicto: APRUEBA (falta que confirmes el porqué de la ventaja)
Siguiente paso: Fase 02 (AED): comprobar si la compra al tocar la SMA 200 tiene ventaja estructural o es ruido, con datos del IS 2017-2021.

## Fase 02 · AED · criterio + datos
Agente / skill: director + skill aed (código: codigo/nas100_media_toque_aed.py)
Qué se hizo: Sin pre-registro. Se midió el retorno de cierre a cierre 1, 5 y 20 velas después de cada toque de la SMA 200 (4H), frente a todas las velas del IS 2017-2021 y frente a las velas sobre la SMA. Datos: datos/NDX_4H_2016_2021.csv (2016 solo para calentar la media; idéntico a datos/NDX_4H.csv en 2017-2021).
Resultado: A 20 velas (el horizonte de la regla), la señal da +0,91 % (42 velas de toque, 71 % positivas) frente a +1,02 % de una vela cualquiera y +0,87 % de las velas sobre la SMA: no supera la línea base. Si se toma una operación a la vez, quedan 16 señales independientes con +1,52 % de media (t≈1,19, no significativo). A 1 y 5 velas la señal sí va por encima (+0,17 % vs +0,05 %; +0,53 % vs +0,25 %). Por año: supera la base en 2018, 2019 y 2021; 2020 cae -5,8 % (toques antes de la caída del COVID); 2017 sin señales. Con 16 casos es una pista, no una conclusión. Huella: la misma regla en NVDA sí supera su base (ver fichas/nvda_media_toque.md).
Supuestos: SMA de 200 cierres; toque = mínimo ≤ SMA ≤ máximo con cierre sobre la SMA; retorno medido de cierre a cierre, sin costes; señales a menos de 20 velas de la anterior se descartan en el conteo independiente; no se miró nada posterior a 2021.
Veredicto: NO APRUEBA (no supera a la línea base a 20 velas y solo hay 16 operaciones posibles, lejos de las 30 que exige la fase 04)
Siguiente paso: Volver a la fase 01: cualquier cambio (horizonte, media) es una enmienda con fecha y se mide en datos no usados (2022 en adelante u otro activo).
