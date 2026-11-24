"""AED · fase 01 · xauusd_ruptura_asia (método TIS).

Idea del trader (24-nov-2026): «Compro oro cuando rompe el máximo de Asia. Salgo al cierre de
Nueva York. Stop: el mínimo de Asia.»
Qué se mide (sin stop, la AED mide el comportamiento, no la regla):
  tras la primera vela de 15 min que CIERRA por encima del máximo de Asia (00:00-07:00 UTC),
  entre 07:00 y 20:45 UTC, ¿el precio sube más de lo normal hasta el cierre de las 21:00 UTC?
Horizonte elegido ANTES de medir: hasta el cierre de la vela de 20:45 UTC (salida 21:00 UTC).
Línea base: en todos los días, desde la vela de la misma hora hasta las 21:00 UTC.
Solo el 70 % más antiguo. Costes 0,02 % por lado (supuesto, METODO.md).
Uso: python codigo/xauusd_ruptura_asia_aed.py
"""
import numpy as np
import pandas as pd

CSV = 'datos/xauusd_15m_dukascopy.csv'
COSTE = 2 * 0.0002            # ida y vuelta
ASIA_FIN = 7 * 60             # minutos UTC
ULTIMA = 20 * 60 + 45         # vela de salida (cierra a las 21:00 UTC)

df = pd.read_csv(CSV, parse_dates=['fecha'])
df['dia'] = df.fecha.dt.tz_convert('UTC').dt.date
df['min'] = df.fecha.dt.hour * 60 + df.fecha.dt.minute
corte = df.fecha.iloc[int(len(df) * 0.7)]
print(f'CSV: {len(df)} velas, {df.fecha.iloc[0]} a {df.fecha.iloc[-1]}')
print(f'Corte 70/30: {corte} (el 30 % posterior no se mira)')
df = df[df.fecha < corte]

filas = []   # una fila por día: retorno desde cada vela hasta la salida + el caso, si lo hubo
for dia, g in df.groupby('dia'):
    if pd.Timestamp(dia).weekday() >= 5:
        continue
    asia = g[g['min'] < ASIA_FIN]
    sesion = g[(g['min'] >= ASIA_FIN) & (g['min'] <= ULTIMA)]
    if len(asia) < 14 or len(sesion) < 28 or sesion['min'].iloc[-1] != ULTIMA:
        continue                          # día incompleto (feriado, cierre anticipado, hueco)
    salida = sesion.close.iloc[-1]
    ret = (salida / sesion.close - 1).values
    hi, lo = asia.high.max(), asia.low.min()
    rompe = (sesion.close > hi).values
    if rompe[:-1].any():
        i = int(np.argmax(rompe[:-1]))   # la vela de salida no puede ser la de entrada
    else:
        i = None
    caso = None
    if i is not None:
        resto = sesion.iloc[i + 1:]
        caso = dict(dia=dia, min=int(sesion['min'].iloc[i]), ret=ret[i],
                    ret1=sesion.close.iloc[min(i + 1, len(sesion) - 1)] / sesion.close.iloc[i] - 1,
                    ret5=sesion.close.iloc[min(i + 5, len(sesion) - 1)] / sesion.close.iloc[i] - 1,
                    toca_stop=bool((resto.low <= lo).any()), riesgo=(sesion.close.iloc[i] - lo) / sesion.close.iloc[i])
    filas.append(dict(dia=dia, año=pd.Timestamp(dia).year,
                      tabla=dict(zip(sesion['min'].values, ret)), caso=caso))

dias = pd.DataFrame(filas)
base = pd.DataFrame(list(dias.tabla)).set_index(dias.index)   # retorno hasta la salida, por hora de entrada
base['año'] = dias['año']
casos = pd.DataFrame([c for c in dias.caso if c is not None])
casos['año'] = [pd.Timestamp(d).year for d in casos.dia]

linea_global = base.drop(columns='año').mean()
linea_año = base.groupby('año').mean()
casos['base'] = [linea_global[m] for m in casos['min']]
casos['exceso'] = casos.ret - casos.base

n = len(casos)
ventaja = casos.exceso.mean()
print(f'\nDías válidos: {len(dias)} · casos (rupturas): {n} ({n / len(dias):.0%} de los días)')
print(f'Retorno medio de los casos hasta las 21:00: {casos.ret.mean():+.3%}')
print(f'Línea base (misma hora, todos los días):     {casos.base.mean():+.3%}')
print(f'Ventaja bruta: {ventaja:+.3%} · coste ida y vuelta: {COSTE:.3%} · neta: {ventaja - COSTE:+.3%}')
print(f'Casos que suben hasta la salida: {(casos.ret > 0).mean():.0%}')
print(f'Contexto · 1 vela: {casos.ret1.mean():+.3%} · 5 velas: {casos.ret5.mean():+.3%}')
print(f'Contexto stop · tocan el mínimo de Asia antes de salir: {casos.toca_stop.mean():.0%} · '
      f'distancia media al stop: {casos.riesgo.mean():.2%}')

# placebo: tantas entradas al azar (día y hora entre 07:00 y 20:30) como casos, sin reemplazo
rng = np.random.default_rng(42)
mat = base.drop(columns=['año', ULTIMA]).values
exc = mat - linea_global.drop(ULTIMA).values
validas = np.argwhere(~np.isnan(exc))
sorteos = np.array([exc[tuple(validas[rng.choice(len(validas), n, replace=False)].T)].mean() for _ in range(1000)])
p = (sorteos >= ventaja).mean()
print(f'Placebo: {p:.1%} de 1.000 sorteos iguala o supera la ventaja')

print('\nPor año (casos frente a la misma hora del mismo año, menos coste):')
pos = tot = 0
for año, g in casos.groupby('año'):
    neta = (g.ret - [linea_año.loc[año, m] for m in g['min']]).mean() - COSTE
    if len(g) >= 5:
        tot += 1
        pos += neta > 0
    print(f'  {año}: {len(g):3d} casos · neta {neta:+.3%}')

c1, c2, c3, c4 = n >= 30, ventaja > COSTE, p < 0.05, tot > 0 and pos >= tot / 2
print(f'\nCasos ≥ 30: {c1} · Ventaja > coste: {c2} · Placebo < 5 %: {c3} · Años {pos}/{tot}: {c4}')
print(f'Veredicto: {sum([c1, c2, c3, c4])}/4 → {"APRUEBA" if all([c1, c2, c3, c4]) else "NO APRUEBA"}')
