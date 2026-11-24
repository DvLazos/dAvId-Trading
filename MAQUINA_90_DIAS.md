# MÁQUINA DE PRODUCCIÓN · plan de 90 días

> Del lunes 23-nov-2026 al viernes 20-feb-2027. Prioridad única: la vertical 3.
> El fondeo (vertical 1) y el capital propio (vertical 2) esperan al día 91: se conectan a una máquina que ya funciona.
> No promete rentabilidad. Los 4 números TIS no se bajan y ninguna fase se salta.

## Qué es «terminado» el día 90

- [ ] **Línea 01 → 06 automática.** Tú apruebas la fase 01; la máquina corre 02 a 06 y te deja cada veredicto listo para firmar.
- [ ] **Fase 07 propuesta y fase 08 en papel.** La skill riesgo propone el tamaño y la skill despliegue deja la lista de puesta en marcha (solo demo; el dinero real es de la vertical 2).
- [ ] **Universo sin sesgo obligatorio.** Ninguna cesta de acciones se prueba con la lista de hoy.
- [ ] **Trabajos automáticos instalados.** Informe diario de lunes a viernes y semanal cada lunes, sin que tú hagas nada.
- [ ] **Tú dominas la cueva.** Explicas el recorrido de una idea de punta a punta y sabes qué hacer si el informe dice NO REPLICA.

**Métricas del día 90**
- Al menos **4 ideas** recorrieron la línea (aprobadas o descartadas, da igual: descartar rápido también es producir).
- **Menos de 1 hora tuya por idea**, medida en el registro de la máquina.
- **8 informes semanales seguidos** llegaron solos.
- **100 % de réplica** en cada ronda diaria, o la causa explicada.

## Punto de partida (día 0, 17-nov)

Ya construido y probado: orquestador diario, réplica (8 de 8), estado de fichas, informe semanal, vigilante, skills riesgo, fondeo, universo y actualizar-datos, `requirements.txt`.
Falta: llenar el universo histórico, instalar el horario, un motor de backtest reutilizable, que el orquestador corra fases (hoy solo informa), la skill despliegue, MI_PLAN.md y los umbrales de las fases 05 a 08.

---

## Bloque 1 · días 1-30 · Cimientos (23-nov → 22-dic) · 10 h/semana

**Objetivo:** datos confiables, horario funcionando y un motor común.

- [ ] Semana 1 · `/objetivos` → `MI_PLAN.md`. Elegir la fuente del universo histórico.
- [ ] Semana 1 · Instalar el horario (`codigo/automatizacion/LEEME.md`) y dar acceso al Escritorio.
- [ ] Semana 2 · Llenar `datos/universo_ndx100_historico.csv` y pasar su control de calidad (`/universo`).
- [ ] Semana 2 · Fijar en `metodo/METODO.md` los umbrales de las fases 05 a 08 (CRITERIO: los decides tú).
- [ ] Semanas 3-4 · `codigo/motor/`: cargar datos, señales, backtest con costes 70/30, los 4 números, meseta y robustez, sacados de los scripts que ya existen.
- [ ] Semana 4 · Prueba de oro: el motor reproduce **exactamente** los números de cesta10 y nvda que hoy están en las fichas. Si no, el motor no se usa.

**Tus decisiones:** límites de MI_PLAN.md, fuente del universo, umbrales 05-08.
**Puerta del día 30:** el motor pasa la prueba de oro, el universo pasa su control y el informe diario llegó solo 10 días hábiles seguidos.

## Bloque 2 · días 31-60 · La línea corre sola (23-dic → 21-ene) · 8 h/semana

**Objetivo:** que una idea aprobada en la fase 01 llegue sola hasta la 06.

- [ ] `fichas/COLA.md`: la cola de ideas. Tú pones una idea con fase 01 aprobada; la máquina la toma.
- [ ] Receta por idea (`codigo/recetas/<activo>_<idea>.json`): la regla de la fase 03 escrita para el motor. El agente reglas la genera; tú no programas.
- [ ] El orquestador pasa de informar a **producir**: corre 02 → 06 en las ideas de la cola y escribe cada bloque en la ficha como «PENDIENTE DE TU FIRMA».
- [ ] Freno automático: si una fase no aprueba, la idea se para y te dice por qué. Nunca reintenta cambiando parámetros para pasar.
- [ ] Contador de variantes: cada intento sobre los mismos datos queda registrado (contra el sobreajuste).
- [ ] Piloto: la hipótesis honesta de la cesta, `fichas/ndx_top20_williams_r.md` (supuesto de nombre), de 01 a 06 con el universo sin sesgo.

**Tus decisiones:** aprobar la fase 01 del piloto; firmar o rechazar cada veredicto.
**Puerta del día 60:** el piloto recorrió 01 → 06 con menos de 1 hora tuya.

## Bloque 3 · días 61-90 · Escala y dominio (22-ene → 20-feb) · 6 h/semana

**Objetivo:** varias ideas por la línea y tú al mando con poco tiempo.

- [ ] La skill riesgo entra en la línea: toda idea que aprueba la 06 recibe su propuesta de fase 07.
- [ ] Skill `despliegue` (fase 08): lista de puesta en marcha, Pine Script con el agente programador y plan de demo. Sin dinero real.
- [ ] 3 ideas nuevas más por la cola (4 en total con el piloto).
- [ ] Informe semanal con «tus 3 decisiones de la semana» arriba de todo.
- [ ] `metodo/MANUAL_CUEVA.md` y `metodo/GLOSARIO.md`, incluido «qué hacer si algo falla».
- [ ] Simulacro: dejas la máquina una semana sin tocarla y lees solo el informe del lunes.

**Tus decisiones:** qué ideas entran a la cola; firmar 07 o no; qué sigue el día 91.
**Puerta del día 90:** las 4 métricas de arriba se cumplen.

---

## Tu semana tipo

- **Bloque 1 (10 h):** 1 h informe y decisiones · 2 h aprender · 5 h construir con los agentes · 2 h ideas.
- **Bloque 2 (8 h):** 1 h informe · 1 h aprender · 4 h construir · 2 h ideas.
- **Bloque 3 (6 h):** 1 h informe · 1 h aprender · 2 h construir · 2 h ideas.

## Lo que la máquina nunca hace sola

Aprobar una fase CRITERIO (01, 02, 07), cambiar el riesgo, cambiar una regla para que pase, operar, pagar un reto o pasar a real.

## Después del día 90

Días 91-180: vertical 2 (demo → real pequeño en Axi o Darwinex) y vertical 1 (simulador de fondeo con reglas reales → reto demo → reto pagado), como dice `MI_HOJA_DE_RUTA.md` desde su mes 4. Las dos usan la máquina terminada.

## Riesgos de estos 90 días

- **Universo sin fuente buena:** sin él, ninguna cesta es creíble. Mitigación: decidirlo la semana 1; si no hay fuente, trabajar con ideas de un solo activo (índices, forex) mientras tanto.
- **Motor que no replica:** se queda fuera hasta que reproduzca las fichas al centavo.
- **Automatizar falsos positivos:** la cola rápida aumenta las pruebas; el contador de variantes y el fuera de muestra intocable lo frenan.
- **Tu tiempo:** si una semana no llegas, la máquina sigue informando; se pierde avance, no control.
