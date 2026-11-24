# MI HOJA DE RUTA · 6 meses (borrador MVP)

> Borrador del 17-nov-2026. Periodo: diciembre 2026 a mayo 2027. Es TU plan: edítalo.
> Este documento organiza el trabajo. No promete rentabilidad ni da señales de compra o venta.
> Los 4 números TIS no se bajan nunca y ninguna fase se salta.
>
> **Cambio de prioridad (17-nov-2026):** los primeros 90 días (23-nov-2026 → 20-feb-2027) se dedican solo a la vertical 3, la máquina de producción. Ver `MAQUINA_90_DIAS.md`. Los meses de abajo se reordenan: fondeo y capital propio empiezan el día 91.

---

## 1. Punto de partida

**Tus respuestas (tal como las diste):**
- **Capital:** medio. Cuenta propia de 10.000 a 50.000 USD y un presupuesto de 500 a 1.500 USD al mes para retos de fondeo (*prop firms*: empresas que te prestan una cuenta si pasas un examen).
- **Ejecución en vivo:** TradingView (Pine Script) con alertas enviadas por *webhook* (un aviso automático por internet) a los brókers y a las cuentas de fondeo.
- **Fondeo:** los dos tipos. CFD y forex (tipo FTMO o The5ers: pérdida diaria máxima y pérdida total máxima, en MT5) y futuros (tipo Topstep o Apex: caída máxima «arrastrada», o *trailing drawdown*).
- **Tiempo:** 10 horas por semana hoy, 3 horas por semana al final (mes 6).
- **Caída máxima de tu cuenta propia antes de apagar todo:** 10 %. Es más estricta que el 20 % de TIS: la fase 07 tiene que dimensionar para ese 10 %.
- **Brókers:** Darwinex (solo como bróker, sin el programa de inversores DARWIN) y Axi.
- **Métrica principal de éxito:** «Máquina de producción». Una línea que lleve ideas de la fase 01 a la 08 casi sin ti. Tú solo pones criterio: hipótesis, aprobaciones y decisiones de riesgo.
- **Niveles:** 1/5 en trading sistemático y 2/5 en IA (MI_RETO.md).

**Estado real del repositorio hoy (honesto):**
- Hay 5 fichas. Ninguna estrategia está validada de punta a punta.
- `cesta10_williams_r` llegó a la fase 06 con 4/4, pero el anexo descubrió **sesgo de supervivencia y de selección** (elegir las acciones sabiendo cuáles subieron). En un universo sin ese sesgo, después de jul-2022, saca **3/4** (FB 1,17). Veredicto: NO APRUEBA. Hay que volver a la fase 01.
- `nvda_media_toque` falló la fase 04 (0/4). `nas100_media_toque` y `meta_williams_r` (diaria) fallaron la fase 02.
- Agentes que ya existen: director, objetivos, hipotesis, reglas, validador, datos, programador. Skills: aed, auditor, datos, escritor-hipotesis, objetivos, optimizar, robustez, validador-4de4, primer-uso, programador.
- **No existen**: fases 07 y 08, `MI_PLAN.md`, nada en `portafolio/` ni en `robots/`, ningún simulador de fondeo, ningún monitor en vivo.
- El código está en scripts sueltos por idea (`codigo/<activo>_<idea>.py`). Funciona, pero cada idea se rehace casi desde cero.
- Tus datos son CSV diarios de acciones grandes del Nasdaq, más NDX, NVDA y QQQ intradía. No hay lista histórica de componentes del índice (la pieza que evita el sesgo de supervivencia).

---

## 2. Visión a 6 meses: cómo se ve «terminado»

**Vertical 1 · Motor de fondeo**
- [ ] Un simulador (`codigo/fondeo_simulador.py`) que aplica las reglas de cada empresa (pérdida diaria, pérdida total, caída arrastrada, objetivo de ganancia, días mínimos) a las operaciones de un backtest.
- [ ] *Monte Carlo* (barajar miles de veces el orden de las operaciones) para estimar la **probabilidad de pasar** y el **costo esperado por cuenta fondeada**.
- [ ] Riesgo por operación ajustado a las reglas de cada empresa.
- [ ] Un tablero en vivo con *kill-switch* (interruptor que apaga todo) antes de tocar un límite.
- **Criterio medible:** al menos 1 reto hecho en demo o pagado **solo** si la estrategia pasó 01-07 y el simulador da una probabilidad de pasar que tú aceptaste por escrito.

**Vertical 2 · Capital propio profesional (cuenta propia, Axi, Darwinex)**
- [ ] Skill de fase 07: tamaño por fracción fija o por objetivo de volatilidad, correlación entre estrategias y tope de caída del 10 %.
- [ ] Skill de fase 08: demo → real pequeño → real completo, con reglas escritas para subir de etapa y para apagar.
- [ ] Monitor «vivo contra backtest» con alertas de desvío.
- **Criterio medible:** 1 estrategia validada 01-08 opera en real pequeño, con al menos 8 semanas de seguimiento y caída real dentro del límite.

**Vertical 3 · Máquina de producción y ecosistema de agentes**
- [ ] Un orquestador que lleva una idea de 01 a 06 llamando a los agentes y skills que ya tienes.
- [ ] Un universo sin sesgo de supervivencia como estándar para cualquier cesta de acciones.
- [ ] Ejecuciones programadas (*cron*: tareas automáticas con horario) y un informe semanal.
- **Criterio medible:** al menos 6 ideas nuevas pasan por la línea en el semestre, con menos de 1 hora tuya por idea, y el informe semanal llega solo cada lunes.

**Meta transversal · Que entiendas y domines tu cueva**
- [ ] `metodo/MANUAL_CUEVA.md`: cómo funciona todo, en lenguaje simple.
- [ ] `metodo/GLOSARIO.md`: cada término en una línea.
- [ ] Una «lección de la semana» dentro del informe semanal.
- **Criterio medible:** puedes explicar en voz alta el recorrido de una alerta, de la vela al bróker, y apagar todo tú solo en menos de 5 minutos.

---

## 3. Arquitectura

`[✓]` = existe hoy · `[ ]` = por construir

```
 TÚ (criterio)                                        TÚ (decides)
   │ ideas, aprobaciones, riesgo                          ▲
   ▼                                                      │
[✓] fichas/  ──►  ORQUESTADOR [ ]  ─────────────► INFORME SEMANAL [ ]
                    │                               (resultados/informe_AAAA-MM-DD.md)
                    ▼                                     ▲
   01 hipotesis [✓] → 02 aed [✓] → 03 reglas [✓]          │
   → 04 validador [✓] → 05 optimizar [✓] → 06 robustez [✓] │
                    │   (datos [✓] + universo sin sesgo [ ])│
                    ▼                                     │
   07 riesgo [ ]  +  fondeo simulador [ ]  + portafolio [ ]│
                    │                                     │
                    ▼                                     │
   programador [✓] → Pine Script en TradingView [ ]       │
                    │  alerta por webhook                 │
                    ▼                                     │
   PUENTE [ ]  (VPS: un ordenador en la nube 24 h)        │
     ├─► puente tipo PineConnector → MT5 → Axi / Darwinex / fondeo CFD
     └─► enrutador tipo TradersPost → Tradovate → fondeo de futuros
                    │                                     │
                    ▼                                     │
   VIGILANTE [ ]  (vivo contra backtest, límites, kill-switch) ┘
```

**Lectura simple:** tú traes la idea. La máquina la prueba (01-06). Si pasa, el agente de riesgo decide el tamaño y el simulador de fondeo calcula las probabilidades. Tú apruebas. El programador escribe el Pine Script. TradingView manda la alerta. El puente la convierte en una orden. El vigilante compara lo real con el backtest. Cada lunes recibes un informe y decides.

---

## 4. Mapa de agentes y skills

**Quién decide:** tú. **Quién ejecuta:** los agentes. Ningún agente aprueba una fase CRITERIO por ti.

**Ya existen**
- `director`: dirige la línea y dice en qué fase está cada idea.
- `objetivos` (+ skill): escribe `MI_PLAN.md`. Pendiente de usar.
- `hipotesis` + `escritor-hipotesis`: fase 01.
- skill `aed`: fase 02.
- `reglas`: fase 03, pseudocódigo.
- `validador` + `validador-4de4`: fase 04, los 4 números.
- skills `optimizar` y `robustez`: fases 05 y 06.
- `datos` (+ skill): descarga y limpia CSV.
- `programador` (+ skill): Pine Script y otras plataformas.
- skill `auditor`: tu historial convertido en 3 hipótesis.

**Por construir**
- skill + agente `riesgo` (fase 07): tamaño, correlación y tope del 10 %.
- skill `universo`: lista de componentes del índice en cada fecha (sin sesgo de supervivencia).
- skill + agente `fondeo`: simulador de reglas de empresas de fondeo y Monte Carlo.
- skill + agente `despliegue` (fase 08): demo → real pequeño → real, y lista de chequeo del puente.
- agente `vigilante`: monitor en vivo, desvíos y kill-switch.
- skill `portafolio`: combina estrategias y reparte el riesgo.
- skill `informe-semanal`: resume todo en una página para ti.
- `orquestador`: encadena 01 → 06 sin que tengas que pedir cada fase.

---

## 5. Plan mes a mes

### Mes 1 · diciembre 2026 · Cimientos · 10 h/semana
**Objetivo:** plan escrito, datos sin sesgo y fase 07 construida.
**Entregables:**
- [ ] `MI_PLAN.md` con el agente `objetivos` (primera tarea, semana 1).
- [ ] `.claude/skills/universo/SKILL.md` + `datos/universo_ndx100_historico.csv` (componentes del Nasdaq-100 por fecha). Fuente a elegir (supuesto: listas públicas de altas y bajas del índice, revisadas a mano).
- [ ] `codigo/universo.py`: devuelve «las N mayores en la fecha X», sin mirar el futuro.
- [ ] `.claude/skills/riesgo/SKILL.md` + `.claude/agents/riesgo.md` (fase 07).
- [ ] Umbrales de las fases 05-08 fijados en `metodo/METODO.md` (hoy dicen «se fija en el Reto» y bloquean la aprobación).
- [ ] `metodo/GLOSARIO.md` (primera versión).
**Tus decisiones de criterio:** límites de `MI_PLAN.md`; umbrales de 05-08; qué fuente de universo aceptas.
**Puerta para avanzar:** `MI_PLAN.md` existe, la skill de riesgo funciona sobre las operaciones de `cesta10_williams_r` como ejemplo, y el universo histórico pasa una revisión de calidad.

### Mes 2 · enero 2027 · MVP en demo · 9 h/semana
**Objetivo:** la primera cadena completa funcionando en demo (ver sección 6).
**Entregables:**
- [ ] Simulador de fondeo básico y skill `fondeo`.
- [ ] Skill `despliegue` (fase 08) y `robots/<activo>_<idea>_pine_estrategia.pine` con alertas.
- [ ] VPS y puente instalados, conectados a **una cuenta demo**.
- [ ] Primer `resultados/informe_2027-01-xx.md`.
- [ ] Nueva hipótesis honesta de la cesta: «la regla en las mayores del índice **en cada momento**» (fichas/ndx_top20_williams_r.md, supuesto de nombre), de 01 a 06 con el universo nuevo.
**Tus decisiones:** aprobar la fase 01 de la nueva hipótesis; elegir qué puente probar.
**Puerta:** una alerta de TradingView abre y cierra una operación en demo sin intervención, y el informe semanal llega.

### Mes 3 · febrero 2027 · Línea de producción · 7 h/semana
**Objetivo:** que las ideas pasen 01 → 06 solas.
**Entregables:**
- [ ] `codigo/motor/` con piezas reutilizables (cargar datos, backtest, 4 números, meseta, robustez). Los scripts por idea pasan a ser recetas cortas.
- [ ] `.claude/agents/orquestador.md` y una ejecución programada semanal (cron o rutinas programadas de Claude Code).
- [ ] 2 ideas nuevas pasadas por la línea.
- [ ] Informe: ¿MT5 nativo como alternativa? Comparar el puente de webhooks con un robot MQL5 que corre directo en MT5 (menos piezas, menos puntos de fallo). Solo se evalúa; no se impone.
- [ ] Lectura de reglas de 2 empresas de fondeo (ver sección 8).
**Tus decisiones:** aprobar o descartar las ideas en las fases CRITERIO; quedarte con webhooks o pasar a MT5 nativo.
**Puerta:** 2 ideas recorrieron 01-06 con menos de 1 hora tuya cada una.

### Mes 4 · marzo 2027 · Fondeo y real pequeño · 5 h/semana
**Objetivo:** primer dinero real, pequeño, solo si hay estrategia validada.
**Entregables:**
- [ ] Agente `vigilante`: compara vivo contra backtest y avisa si se acerca a un límite.
- [ ] `resultados/<activo>_<idea>_fondeo.md`: probabilidad de pasar y costo esperado por empresa.
- [ ] Si una estrategia aprobó 01-07: etapa «real pequeño» en Axi o Darwinex (supuesto: 10 % del riesgo final).
- [ ] Si además el simulador da probabilidades aceptables: primer reto **en demo** (gratuito o de prueba) de una empresa de fondeo.
**Tus decisiones:** cuánto riesgo real arriesgar; qué probabilidad de pasar te basta para pagar un reto.
**Puerta:** 4 semanas en real pequeño sin fallos técnicos graves, o la decisión escrita de seguir solo en demo.

### Mes 5 · abril 2027 · Portafolio y primer reto pagado · 4 h/semana
**Objetivo:** combinar estrategias y, si se cumplen las condiciones, el primer reto pagado.
**Entregables:**
- [ ] Skill `portafolio` y `portafolio/portafolio_2027-04.md` (reparto de riesgo y correlación).
- [ ] Tablero en vivo (`herramientas/tablero.html`, se abre con doble clic) con estado de cuentas y distancia a los límites.
- [ ] Primer reto pagado (dentro de tu presupuesto de 500-1.500 USD/mes), solo si el reto en demo salió bien.
**Tus decisiones:** pagar o no el reto; subir de etapa en cuenta propia.
**Puerta:** el portafolio, en simulación, se queda bajo el 10 % de caída en el percentil 95 de Monte Carlo.

### Mes 6 · mayo 2027 · Piloto automático · 3 h/semana
**Objetivo:** que tu trabajo sea solo criterio.
**Entregables:**
- [ ] `metodo/MANUAL_CUEVA.md` completo, incluido «qué hacer si algo falla».
- [ ] Revisión del semestre en `resultados/revision_semestre_2027-05.md`.
- [ ] `MI_PLAN.md` revisado con el agente `objetivos`.
**Tus decisiones:** qué sigue, qué se apaga, qué se escala.
**Puerta (éxito del semestre):** las ideas entran y salen de la línea con menos de 1 hora tuya; recibes el informe semanal; puedes apagar todo tú solo.

---

## 6. MVP · primeras 6 semanas (23-nov-2026 a 3-ene-2027)

**La rebanada mínima de punta a punta:** una estrategia → fase 07 → fase 08 en demo → alerta de TradingView → cuenta demo, más un simulador de fondeo básico y un informe semanal.

**Aviso honesto:** hoy no hay ninguna estrategia que haya aprobado 01-06. Por eso el MVP prueba la **tubería** con `cesta10_williams_r` (versión de oct-2022, la menos sesgada) marcada como **«estrategia de prueba, no validada»**. Solo demo, cero dinero real. La fase 07 de esa ficha seguirá NO APROBADA. En paralelo, la hipótesis honesta corre 01-06.

**Semana 1 · plan y datos**
- [ ] `/objetivos` → `MI_PLAN.md`.
- [ ] Elegir la fuente del universo histórico del Nasdaq-100.
- [ ] Primer borrador de `metodo/GLOSARIO.md`.

**Semana 2 · universo sin sesgo**
- [ ] Skill `universo` + `codigo/universo.py` + CSV de componentes por fecha.
- [ ] Ficha nueva de la hipótesis honesta (fase 01).

**Semana 3 · fase 07**
- [ ] Skill y agente `riesgo`: fracción fija (arriesgar un % fijo del capital por operación) y objetivo de volatilidad (ajustar el tamaño para que el movimiento esperado sea constante).
- [ ] Regla: el tamaño se elige para que la caída del percentil 95 de Monte Carlo quede bajo 10 % (tu límite) con margen (supuesto: apuntar a 7 %).
- [ ] Probarla con las operaciones de cesta10 → `resultados/cesta10_williams_r_riesgo.md`.

**Semana 4 · simulador de fondeo básico**
- [ ] `codigo/fondeo_simulador.py` con 2 perfiles genéricos: «CFD» (pérdida diaria y total fijas) y «futuros» (caída arrastrada). Los números los copias tú de las reglas vigentes.
- [ ] Salida: probabilidad de pasar, días medios y costo esperado por cuenta fondeada.

**Semana 5 · despliegue en demo**
- [ ] `/programador` → `robots/cesta10_williams_r_pine_estrategia.pine` con mensajes de alerta.
- [ ] Skill `despliegue` (fase 08) con lista de chequeo.
- [ ] VPS + puente + cuenta demo (MT5 de Axi o Darwinex). Una orden de prueba de punta a punta.
- [ ] Registro de cada alerta y cada orden en `resultados/cesta10_williams_r_vivo.csv`.

**Semana 6 · informe y repaso**
- [ ] Skill `informe-semanal` → `resultados/informe_2027-01-04.md`: fase de cada idea, operaciones demo contra backtest, alertas fallidas, lección de la semana.
- [ ] Prueba del kill-switch: apagar todo en menos de 5 minutos.
- [ ] Repaso contigo: ¿entiendes cada caja del diagrama?

---

## 7. Rutina semanal del trader

**Hoy (10 h/semana, mes 1)**
- 1 h · leer el informe y decidir (aprobar fases, riesgo).
- 2 h · aprender: glosario, manual, lección de la semana.
- 5 h · construir con los agentes (skills nuevas, universo, puente).
- 2 h · ideas nuevas para la fase 01.

**Mes 3 (7 h/semana)**
- 1 h informe y decisiones · 1 h aprender · 3 h construir · 2 h ideas.

**Final (3 h/semana, mes 6)**
- 1 h · lunes: leer el informe y decidir.
- 1 h · ideas nuevas y aprobaciones de fase 01.
- 30 min · revisar el tablero y las cuentas.
- 30 min · lección de la semana.

**Lo que hace la máquina sola:** descargar datos, correr 02-06 en ideas aprobadas, simular fondeo, vigilar las cuentas, avisar de desvíos, escribir el informe. **Lo que nunca hace sola:** aprobar una fase CRITERIO, cambiar el riesgo, pagar un reto o pasar a real.

---

## 8. Riesgos y límites

- **Tu límite del 10 %.** Se mide desde el máximo de la cuenta. Mitigación: la fase 07 dimensiona para ~7 % en el peor escenario razonable; el vigilante avisa al 5 % y apaga todo al 8 % (supuesto: tú confirmas estos niveles).
- **Fallos de alerta.** TradingView puede no enviar una alerta, el webhook puede perderse o el puente estar caído. Mitigación: registro de cada alerta, comparación diaria con las posiciones del bróker y aviso si no coinciden.
- **Latencia** (retraso entre la señal y la orden). Pesa poco en velas semanales y mucho en intradía. Mitigación: empezar con estrategias lentas; medir el deslizamiento real.
- **Puentes.** MT5 necesita un puente tipo PineConnector en un VPS. Los futuros necesitan un enrutador tipo TradersPost hacia Tradovate. Cada pieza es un punto de fallo y un costo mensual. Mitigación: evaluar MT5 nativo en el mes 3.
- **Reglas de las empresas de fondeo.** Muchas restringen o prohíben la automatización, el copiado de operaciones, los robots de terceros o usar la misma estrategia en varias cuentas. Algunas de futuros exigen cerrar todo antes del final de la sesión. Mitigación: **antes de comprar cualquier reto**, el agente `fondeo` resume las reglas vigentes en `activos/fondeo_<empresa>.md` y **tú las verificas** en la web oficial. Los ejemplos de este plan son genéricos.
- **Encaje de estilo.** Una estrategia semanal en acciones (como la cesta) encaja mal con retos de fondeo, que suelen ser en índices, forex o futuros y premian objetivos en pocas semanas. Puede que el fondeo necesite ideas propias más rápidas.
- **Sobreajuste** (que la regla se adapte al pasado y no al futuro). Lección de cesta10: el sesgo de selección infló un 4/4. Mitigación: universo sin sesgo obligatorio, datos fuera de muestra intocables, contar cuántas variantes se probaron.
- **Automatizar no es validar.** Una máquina rápida también produce falsos positivos rápido. Los 4 números y las fases no cambian.
- **Seguridad.** Nunca guardes claves, contraseñas ni números de cuenta en el repositorio. Usa `.env` fuera de GitHub.
- **Impuestos y regulación.** Operar con brókers extranjeros, CFD y cuentas de fondeo tiene efectos fiscales y legales que dependen de tu país. Consulta a un profesional antes de pasar a real.

---

## 9. Tus próximas 3 decisiones

1. **Hacer `MI_PLAN.md` esta semana** con el agente `objetivos` (confirma ahí el 10 % y los niveles de aviso y apagado).
2. **Elegir la fuente del universo histórico** del Nasdaq-100 para eliminar el sesgo de supervivencia.
3. **Elegir la primera cuenta demo del MVP:** MT5 de Axi o de Darwinex (y con ello, qué puente probar primero).
