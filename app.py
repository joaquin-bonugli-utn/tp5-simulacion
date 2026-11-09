"""
app.py
======
Frontend de la simulación (TP 5 – Degustación H) hecho con Streamlit.

Cómo correrlo:
    pip install -r requirements.txt
    python -m streamlit run app.py

Este archivo SOLO se encarga de la interfaz: pedir parámetros, llamar a
simulacion.simular() y mostrar los resultados. Toda la lógica de la
simulación está en simulacion.py.
"""

import io
import math

import pandas as pd
import streamlit as st

import simulacion as sim

# ---------------------------------------------------------------------------
# Configuración general de la página
# ---------------------------------------------------------------------------
st.set_page_config(page_title="TP5 Simulación - Degustación H",
                   page_icon="🍷", layout="wide")

TITULO = "Grupo 18 - Trabajo Práctico 5"

st.markdown(
    f"<h2 style='text-align:center; color:#4a5568;'>{TITULO}</h2>"
    "<p style='text-align:center; color:#718096; margin-top:-10px;'>"
    "Simulación de eventos discretos · Degustación H (bodega + embutidos)</p>",
    unsafe_allow_html=True,
)

D = sim.PARAMETROS_DEFECTO   # atajo a los valores por defecto


# ---------------------------------------------------------------------------
# PANEL DE PARÁMETROS (queda siempre visible, también después de simular)
# ---------------------------------------------------------------------------
with st.expander("⚙️ PANEL DE CONFIGURACIÓN DE PARÁMETROS", expanded=True):

    # ----- 1. Simulación y visualización
    st.subheader("⏱️ 1. Simulación y visualización")
    c1, c2, c3, c4 = st.columns(4)
    tiempo_X = c1.number_input("Tiempo a simular X (min)", 1.0, 10_000_000.0,
                               D["tiempo_X"], step=100.0)
    max_iter = c2.number_input("Máx. iteraciones (N ≤ 100.000)", 1, 100_000,
                               D["max_iteraciones"], step=1000)
    mostrar_i = c3.number_input("Mostrar i iteraciones", 1, 2000, D["mostrar_i"])
    desde_j = c4.number_input("A partir de la hora j (min)", 0.0, 10_000_000.0,
                              D["desde_hora_j"], step=10.0)

    # ----- 2. Generador congruencial mixto (uno solo, compartido)
    st.subheader("🎲 2. Generador congruencial mixto (compartido por todas las variables)")
    st.caption("X(i) = (a · X(i-1) + c) mod m   ·   RND = X(i) / m")
    c1, c2, c3, c4 = st.columns(4)
    semilla = c1.number_input("Semilla X0", 0, 10**12, D["semilla"])
    a = c2.number_input("Constante multiplicativa a", 0, 10**12, D["a"])
    c = c3.number_input("Constante aditiva c", 0, 10**12, D["c"])
    m = c4.number_input("Módulo m", 1, 10**12, D["m"])

    # ----- 3. Ingreso vehicular (portón)
    st.subheader("🚗 3. Ingreso vehicular (portón con 2 operarios)")
    c1, c2, c3, c4 = st.columns(4)
    auto_media = c1.number_input("Llegada autos: cada (min)", 0.0, 10_000.0,
                                 D["auto_media"])
    auto_delta = c2.number_input("Llegada autos: ± (min)", 0.0, 10_000.0,
                                 D["auto_delta"])
    porton_media = c3.number_input("Acreditación portón: media exp. (min)",
                                   0.01, 10_000.0, D["porton_media"])
    estacionamiento = c4.number_input("Estacionar (min, constante)", 0.0,
                                      10_000.0, D["estacionamiento"])

    # ----- 4. Acceso peatonal
    st.subheader("🚶 4. Acceso peatonal")
    c1, c2, c3 = st.columns(3)
    peaton_dist = c1.selectbox(
        "Distribución del tiempo entre llegadas peatonales",
        sim.DISTRIBUCIONES_PEATON,
        index=sim.DISTRIBUCIONES_PEATON.index(D["peaton_dist"]),
        help="El enunciado dice 'un tiempo entre llegadas de 2.5 minutos' sin "
             "indicar distribución, por eso por defecto es constante. Se puede "
             "cambiar a exponencial negativa o uniforme.")
    peaton_media = c2.number_input("Tiempo entre llegadas peatonales (min)",
                                   0.01, 10_000.0, D["peaton_media"])
    peaton_delta = c3.number_input("± Δ (solo si es uniforme)", 0.0, 10_000.0,
                                   D["peaton_delta"],
                                   disabled=not peaton_dist.startswith("Uniforme"))
    c1, c2, c3, c4 = st.columns(4)
    porc_qr = c1.number_input("% con acreditación digital (QR)", 0.0, 100.0,
                              D["porc_qr"])
    escaneo_qr = c2.number_input("Escaneo QR (min, constante)", 0.0, 10_000.0,
                                 D["escaneo_qr"])
    recep_min = c3.number_input("Recepcionista: mínimo (min)", 0.0, 10_000.0,
                                D["recep_min"])
    recep_max = c4.number_input("Recepcionista: máximo (min)", 0.0, 10_000.0,
                                D["recep_max"])

    # ----- 5. Sala: expectativa e integración por Euler
    st.subheader("🍷 5. Sala de degustación: expectativa y Euler")
    st.caption("dE/dt = -k - E² / E0   ·   el invitado se retira cuando E llega a 0 "
               "(1 unidad de integración = 1 minuto)")
    cols = st.columns(6)
    exp_valores, exp_probs = [], []
    for idx, nombre in enumerate(D["exp_nombres"]):
        exp_valores.append(cols[2 * idx].number_input(
            f"E0 expectativa {nombre}", 0.01, 1_000_000.0,
            D["exp_valores"][idx], key=f"ev{idx}"))
        exp_probs.append(cols[2 * idx + 1].number_input(
            f"P({nombre})", 0.0, 1.0, D["exp_probs"][idx],
            step=0.0001, format="%.4f", key=f"ep{idx}"))
    c1, c2, _ = st.columns(3)
    euler_h = c1.number_input("Paso h de Euler", 0.0001, 10.0, D["euler_h"],
                              step=0.01, format="%.4f")
    euler_k = c2.number_input("Constante k de la ecuación (68)", 0.0, 1_000_000.0,
                              D["euler_k"])

# Diccionario con todos los parámetros (mismo formato que PARAMETROS_DEFECTO)
p = {
    "tiempo_X": float(tiempo_X), "max_iteraciones": int(max_iter),
    "mostrar_i": int(mostrar_i), "desde_hora_j": float(desde_j),
    "semilla": int(semilla), "a": int(a), "c": int(c), "m": int(m),
    "auto_media": auto_media, "auto_delta": auto_delta,
    "porton_media": porton_media, "estacionamiento": estacionamiento,
    "peaton_dist": peaton_dist, "peaton_media": peaton_media,
    "peaton_delta": peaton_delta, "porc_qr": porc_qr, "escaneo_qr": escaneo_qr,
    "recep_min": recep_min, "recep_max": recep_max,
    "exp_nombres": list(D["exp_nombres"]), "exp_valores": exp_valores,
    "exp_probs": exp_probs, "euler_h": euler_h, "euler_k": euler_k,
}


# ---------------------------------------------------------------------------
# Funciones auxiliares
# ---------------------------------------------------------------------------
COLUMNAS_TEXTO = {"Evento", "Tipo acred.", "Expectativa", "Op1 estado",
                  "Op2 estado", "QR estado", "Recep. estado"}
COLUMNAS_ENTERAS = {"Fila", "Cola portón", "Cola QR", "Cola recep.",
                    "Cant. estacionando", "Cant. en sala", "Cant. acreditados AP",
                    "Cant. inician atención AP", "Cant. salidas"}


def a_dataframe(filas, con_temporales=True):
    """Convierte las filas guardadas en una tabla de pandas."""
    nombres, planas = sim.filas_planas(filas, con_temporales)
    return pd.DataFrame(planas, columns=nombres)


def formato_columna(nombre):
    """Formato de cada columna del vector (RND con 4 decimales, etc.)."""
    if nombre in COLUMNAS_TEXTO or nombre.endswith(" Estado") or nombre.endswith(" Tipo"):
        return None
    if nombre in COLUMNAS_ENTERAS:
        return "%d"
    if nombre == "E0" or nombre.endswith(" E0"):
        return "%.0f"
    if nombre.startswith("%"):
        return "%.2f"
    return "%.4f"


def config_columnas(df, fijar=("Fila", "Evento", "Reloj")):
    """Arma la configuración de columnas: formatos y columnas ancladas."""
    cfg = {}
    for col in df.columns:
        fmt_ = formato_columna(col)
        kwargs = {}
        if col in fijar:
            kwargs["pinned"] = True
        try:
            if fmt_ is None:
                cfg[col] = st.column_config.TextColumn(col, **kwargs)
            else:
                cfg[col] = st.column_config.NumberColumn(col, format=fmt_, **kwargs)
        except TypeError:
            # Versiones viejas de Streamlit no tienen 'pinned'
            if fmt_ is None:
                cfg[col] = st.column_config.TextColumn(col)
            else:
                cfg[col] = st.column_config.NumberColumn(col, format=fmt_)
    return cfg


def fmt(x, dec=4):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "—"
    if isinstance(x, float):
        return f"{x:,.{dec}f}"
    return str(x)


def tabla_euler_df(tabla):
    return pd.DataFrame(tabla["filas"])[["i", "t(i)", "E(i)", "dE/dt",
                                          "t(i+1)", "E(i+1)"]]


def armar_excel(res, par):
    """Genera el Excel con el vector de estado, la última fila y las tablas de Euler."""
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        a_dataframe(res["filas_mostradas"]).to_excel(
            w, sheet_name="Vector de estado", index=False, freeze_panes=(1, 3))
        a_dataframe([res["ultima"]], False).to_excel(
            w, sheet_name="Última fila", index=False, freeze_panes=(1, 3))
        for E0, tabla in res["tablas_euler"].items():
            df = tabla_euler_df(tabla)
            df.to_excel(w, sheet_name=f"Euler E0={E0:g}", index=False,
                        startrow=2, freeze_panes=(3, 0))
            hoja = w.sheets[f"Euler E0={E0:g}"]
            hoja["A1"] = (f"Integración por Euler de dE/dt = -{tabla['k']:g} - E²/{E0:g}"
                          f"  ·  h = {tabla['h']:g}  ·  T permanencia = {tabla['T']:.4f} min")
        est = res["estimadores"]
        pd.DataFrame([
            ("Tiempo promedio de demora en el Acceso Peatonal (min)", est["prom_demora_ap"]),
            ("Porcentaje de tiempo libre de la recepcionista (%)", est["porc_libre_rec"]),
            ("Porcentaje de uso del dispositivo QR (%)", est["porc_uso_qr"]),
            ("Tiempo promedio de permanencia en el evento (min)", est["prom_permanencia"]),
            ("Tiempo promedio de espera en cola en el Acceso Peatonal (min)", est["prom_espera_ap"]),
            ("Reloj final (min)", est["reloj_final"]),
            ("Iteraciones", est["iteraciones"]),
            ("Motivo de fin", est["motivo"]),
        ], columns=["Resultado", "Valor"]).to_excel(w, sheet_name="Resultados", index=False)
        pd.DataFrame([(k, str(v)) for k, v in par.items()],
                     columns=["Parámetro", "Valor"]).to_excel(
            w, sheet_name="Parámetros", index=False)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# BOTÓN INICIAR SIMULACIÓN
# El resultado se guarda en st.session_state para que no se pierda cuando
# Streamlit vuelve a ejecutar el script (pasa cada vez que tocás algo).
# ---------------------------------------------------------------------------
_, centro, _ = st.columns([1, 2, 1])
if centro.button("🚀 INICIAR SIMULACIÓN", type="primary", width="stretch"):
    errores = sim.validar(p)
    if errores:
        for e in errores:
            st.error(e)
        st.session_state.pop("resultado", None)
    else:
        with st.spinner("Simulando..."):
            res = sim.simular(p)
            st.session_state["resultado"] = res
            st.session_state["params"] = p
            try:
                st.session_state["excel"] = armar_excel(res, p)
            except ImportError:
                st.session_state["excel"] = None

if "resultado" not in st.session_state:
    st.info("Configurá los parámetros y presioná **INICIAR SIMULACIÓN**.")
    st.stop()

res = st.session_state["resultado"]
par = st.session_state["params"]     # parámetros con los que se simuló
est = res["estimadores"]

if par != p:
    st.warning("Cambiaste parámetros después de simular: los resultados de abajo "
               "corresponden a la simulación anterior. Presioná INICIAR SIMULACIÓN "
               "para actualizarlos.")
else:
    st.success(f"Simulación calculada. {est['motivo']}.")


# ---------------------------------------------------------------------------
# PESTAÑAS DE RESULTADOS
# ---------------------------------------------------------------------------
tab_res, tab_vec, tab_ult, tab_euler, tab_mod = st.tabs(
    ["📊 Resultados", "📋 Vector de Estado", "🏁 Última Fila",
     "∫ Integración Euler", "🗺️ Modelo"])

# ===== 1) RESULTADOS =======================================================
with tab_res:
    st.header("📊 Resultados de la simulación")
    st.markdown(f"Reloj final: **{est['reloj_final']:,.4f} min** · "
                f"Iteraciones: **{est['iteraciones']:,}**")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Tiempo promedio de demora en el Acceso Peatonal",
              f"{fmt(est['prom_demora_ap'])} min")
    m2.metric("% de tiempo libre de la recepcionista",
              f"{fmt(est['porc_libre_rec'], 2)} %")
    m3.metric("% de uso del dispositivo QR", f"{fmt(est['porc_uso_qr'], 2)} %")
    m4.metric("Tiempo promedio de permanencia en el evento",
              f"{fmt(est['prom_permanencia'])} min")

    st.markdown("##### Fórmulas utilizadas")
    st.latex(r"\overline{Demora}_{AP} = \frac{\sum (\text{hora fin acreditación} - "
             r"\text{hora llegada})}{\text{cant. invitados acreditados en el AP}}")
    st.latex(r"\%\,Libre_{recep} = \frac{\sum \text{tiempo con recepcionista libre}}"
             r"{\text{reloj}} \cdot 100 \qquad "
             r"\%\,Uso_{QR} = \frac{\sum \text{tiempo con QR ocupado}}{\text{reloj}} \cdot 100")
    st.latex(r"\overline{Permanencia} = \frac{\sum (\text{hora salida de la sala} - "
             r"\text{hora llegada})}{\text{cant. invitados que se retiraron}}")

    st.divider()
    izq, der = st.columns(2)
    with izq:
        st.markdown("##### Datos complementarios")
        cola, periodo = res["periodo"]
        st.dataframe(pd.DataFrame([
            ("Motivo de fin", est["motivo"]),
            ("Invitados vehiculares llegados", f"{est['llegados_iv']:,}"),
            ("Invitados peatonales llegados", f"{est['llegados_ip']:,}"),
            ("  · con QR", f"{est['cant_qr']:,}"),
            ("  · presenciales (recepcionista)", f"{est['cant_presencial']:,}"),
            ("Invitados acreditados en el Acceso Peatonal", f"{est['acreditados_ap']:,}"),
            ("Invitados que se retiraron", f"{est['cant_salidas']:,}"),
            ("Invitados en el sistema al final", f"{est['en_sistema_al_final']:,}"),
            ("Tiempo promedio de espera en cola en el AP (solo cola)",
             f"{fmt(est['prom_espera_ap'])} min"),
            ("Números aleatorios usados", f"{est['rnd_usados']:,}"),
            ("Período del generador", f"{periodo:,} (empieza a repetirse después de {cola} número/s)"),
        ], columns=["Dato", "Valor"]), hide_index=True, width="stretch")
    with der:
        st.markdown("##### Parámetros con los que se simuló")
        st.dataframe(pd.DataFrame([(k, str(v)) for k, v in par.items()],
                                  columns=["Parámetro", "Valor"]),
                     hide_index=True, width="stretch", height=420)

# ===== 2) VECTOR DE ESTADO =================================================
with tab_vec:
    st.header("📋 Vector de Estado")
    filas = res["filas_mostradas"]
    if not filas:
        st.warning("No hay filas con reloj ≥ j (la hora j es mayor que el tiempo simulado).")
    else:
        st.markdown(
            f"Filas **{filas[0]['Fila']:,}** a **{filas[-1]['Fila']:,}** "
            f"(reloj {filas[0]['Reloj']:.4f} a {filas[-1]['Reloj']:.4f}). "
            "Solo se guardaron estas filas, no toda la simulación. "
            "**Hacé clic en el borde izquierdo de una fila para seleccionarla** y "
            "ver abajo el detalle de todos los objetos en ese instante.")

        with st.expander("Leyenda de estados de los objetos temporales"):
            l1, l2 = st.columns(2)
            l1.markdown("**IV = Invitado Vehicular** (llega en auto)\n\n" +
                        "\n".join(f"- `{k}`: {v}" for k, v in sim.ESTADOS_IV.items()))
            l2.markdown("**IP = Invitado Peatonal** (llega a pie)\n\n" +
                        "\n".join(f"- `{k}`: {v}" for k, v in sim.ESTADOS_IP.items()))

        con_temp = st.toggle("Mostrar objetos temporales (invitados)", value=True)
        df = a_dataframe(filas, con_temp)
        sel = st.dataframe(df, hide_index=True, width="stretch", height=560,
                           column_config=config_columnas(df),
                           on_select="rerun", selection_mode="single-row",
                           key="tabla_vector")

        if st.session_state.get("excel"):
            st.download_button("⬇️ Descargar vector de estado y tablas de Euler (Excel)",
                               st.session_state["excel"],
                               file_name="TP5_Degustacion_H_vector_estado.xlsx",
                               mime="application/vnd.openxmlformats-officedocument."
                                    "spreadsheetml.sheet")
        else:
            st.caption("Para exportar a Excel instalá openpyxl (pip install openpyxl).")

        # ----- Detalle de la fila seleccionada
        filas_sel = sel.selection.rows if sel is not None else []
        if filas_sel:
            r = filas[filas_sel[0]]
            st.subheader(f"🔎 Fila {r['Fila']} · {r['Evento']} · reloj = {r['Reloj']:.4f}")
            d1, d2, d3 = st.columns(3)
            with d1:
                st.markdown("**Objetos permanentes y colas**")
                st.dataframe(pd.DataFrame([
                    ("Operario 1", r["Op1 estado"], fmt(r["Fin acred. Op1"])),
                    ("Operario 2", r["Op2 estado"], fmt(r["Fin acred. Op2"])),
                    ("Dispositivo QR", r["QR estado"], fmt(r["Fin escaneo QR"])),
                    ("Recepcionista", r["Recep. estado"], fmt(r["Fin acred. recep."])),
                ], columns=["Objeto", "Estado", "Fin de atención"]),
                    hide_index=True, width="stretch")
                st.dataframe(pd.DataFrame([
                    ("Cola portón", r["Cola portón"]), ("Cola QR", r["Cola QR"]),
                    ("Cola recepcionista", r["Cola recep."]),
                    ("Estacionando", r["Cant. estacionando"]),
                    ("En la sala", r["Cant. en sala"]),
                ], columns=["Lugar", "Cantidad"]), hide_index=True, width="stretch")
            with d2:
                st.markdown("**Objetos temporales presentes**")
                temps = []
                for clase, _, nombre, atr in r["_temporales"]:
                    temps.append({
                        "Objeto": nombre,
                        "Estado": atr["Estado"],
                        "Tipo": atr.get("Tipo") or ("Auto" if clase == "IV" else ""),
                        "Hora llegada": fmt(atr["Hora llegada"]),
                        "Fin estac.": fmt(atr.get("Fin estac.")),
                        "E0": fmt(atr["E0"], 0),
                        "Fin degust.": fmt(atr["Fin degust."]),
                    })
                if temps:
                    st.dataframe(pd.DataFrame(temps), hide_index=True, width="stretch")
                else:
                    st.caption("No hay invitados en el sistema en este instante.")
            with d3:
                st.markdown("**Próximos eventos y estadísticas**")
                st.dataframe(pd.DataFrame([
                    ("Próx. llegada auto", fmt(r["Próx. lleg. auto"])),
                    ("Próx. llegada peatón", fmt(r["Próx. lleg. peatón"])),
                    ("Próx. fin estacionamiento", fmt(r["Próx. fin estac."])),
                    ("Próx. fin degustación", fmt(r["Próx. fin degust."])),
                    ("% tiempo libre recepcionista", fmt(r["% t libre recep."], 2)),
                    ("% uso QR", fmt(r["% uso QR"], 2)),
                    ("Prom. demora AP", fmt(r["Prom. demora AP"])),
                    ("Prom. permanencia", fmt(r["Prom. permanencia"])),
                ], columns=["Dato", "Valor"]), hide_index=True, width="stretch")
            if r["E0"] is not None:
                tabla = res["tablas_euler"][r["E0"]]
                with st.expander(f"∫ Integración usada en esta fila: E0 = {r['E0']:g} "
                                 f"({r['Expectativa']}) → T = {tabla['T']:.4f} min"):
                    st.dataframe(tabla_euler_df(tabla), hide_index=True,
                                 width="stretch", height=300)
        else:
            st.caption("Ninguna fila seleccionada.")

# ===== 3) ÚLTIMA FILA ======================================================
with tab_ult:
    st.header("🏁 Última Fila")
    ult = res["ultima"]
    st.info(f"Fila {ult['Fila']:,} · {ult['Evento']} · reloj = {ult['Reloj']:,.4f}. "
            "Es el estado que queda en memoria al terminar (sin objetos temporales).")
    df_u = a_dataframe([ult], False)
    st.dataframe(df_u, hide_index=True, width="stretch",
                 column_config=config_columnas(df_u))
    st.markdown("##### La misma fila en vertical")
    st.dataframe(pd.DataFrame([(k, fmt(ult.get(k))) for k in sim.COLUMNAS_FIJAS],
                              columns=["Columna", "Valor"]),
                 hide_index=True, width="stretch", height=500)

# ===== 4) INTEGRACIÓN EULER ================================================
with tab_euler:
    st.header("∫ Integración numérica por Euler")
    st.latex(r"\frac{dE}{dt} = -%g - \frac{E^2}{E_0} \qquad "
             r"E_{i+1} = E_i + h \cdot \frac{dE}{dt}\Big|_i \qquad t_{i+1} = t_i + h"
             % par["euler_k"])
    st.markdown(
        f"Paso **h = {par['euler_h']:g}**. Se integra desde E = E0 hasta que E ≤ 0 "
        "(el invitado se queda sin expectativa y se retira). El tiempo de permanencia "
        "es el t(i+1) de la última fila. Como el resultado solo depende de E0, hay "
        "**una tabla por cada valor posible de la expectativa**: en el vector de "
        "estado, la columna **E0** indica qué tabla se usó para cada invitado.")
    resumen = []
    for nombre, (E0, tabla) in zip(par["exp_nombres"], res["tablas_euler"].items()):
        exacta = sim.permanencia_exacta(E0, par["euler_k"]) if par["euler_k"] > 0 else None
        resumen.append({"Expectativa": nombre, "E0": E0,
                        "Pasos": len(tabla["filas"]),
                        "T por Euler (min)": tabla["T"],
                        "T exacto (analítico)": exacta})
    st.dataframe(pd.DataFrame(resumen), hide_index=True, width="stretch")
    st.caption("T exacto = (E0/√(k·E0))·arctan(E0/√(k·E0)); solo para comparar el error de Euler.")

    sub = st.tabs([f"E0 = {E0:g}" for E0 in res["tablas_euler"]])
    for t_, (E0, tabla) in zip(sub, res["tablas_euler"].items()):
        with t_:
            st.markdown(f"**E0 = {E0:g}** → T = **{tabla['T']:.4f} min**")
            st.dataframe(tabla_euler_df(tabla), hide_index=True, width="stretch",
                         height=450,
                         column_config={c: st.column_config.NumberColumn(c, format="%.4f")
                                        for c in ["t(i)", "E(i)", "dE/dt", "t(i+1)", "E(i+1)"]})

# ===== 5) MODELO ===========================================================
with tab_mod:
    st.header("🗺️ Modelo del sistema")
    st.graphviz_chart("""
    digraph {
        rankdir=LR;
        node [shape=box, style="rounded,filled", fillcolor="#eef2ff", fontname="Helvetica"];
        LA [label="Llegada auto\\nU(3;7)", shape=ellipse, fillcolor="#d1fae5"];
        LP [label="Llegada peatón\\ncada 2,5 min", shape=ellipse, fillcolor="#d1fae5"];
        CP [label="Cola portón", shape=cds, fillcolor="#fef3c7"];
        OP [label="Operario 1 / Operario 2\\nacreditación Exp(2)"];
        EST [label="Estacionamiento\\n3 min"];
        T [label="Tipo de acreditación\\n50 % QR / 50 % presencial", shape=diamond, fillcolor="#fff7ed"];
        CQ [label="Cola QR", shape=cds, fillcolor="#fef3c7"];
        QR [label="Dispositivo QR\\n0,5 min"];
        CR [label="Cola recepción", shape=cds, fillcolor="#fef3c7"];
        RE [label="Recepcionista\\nU(1;3)"];
        SALA [label="Sala de degustación\\nE0 ∈ {1000,1500,2000}\\nEuler: dE/dt = -68 - E²/E0", fillcolor="#fce7f3"];
        FIN [label="Salida", shape=doublecircle, fillcolor="#fee2e2"];
        LA -> CP -> OP -> EST -> SALA;
        LP -> T;
        T -> CQ [label="QR"]; CQ -> QR -> SALA;
        T -> CR [label="presencial"]; CR -> RE -> SALA;
        SALA -> FIN;
    }""")

    izq, der = st.columns(2)
    with izq:
        st.markdown("##### Variables aleatorias (transformada inversa)")
        st.dataframe(pd.DataFrame([
            ("Tiempo entre llegadas de autos", "Uniforme U(3;7)",
             f"{par['auto_media'] - par['auto_delta']:g} + "
             f"{2 * par['auto_delta']:g}·RND"),
            ("Tiempo de acreditación en el portón", "Exp. negativa (μ = 2)",
             f"-{par['porton_media']:g}·ln(1 - RND)"),
            ("Tiempo entre llegadas peatonales", par["peaton_dist"],
             {"Constante": f"{par['peaton_media']:g} (sin RND)",
              "Exponencial negativa": f"-{par['peaton_media']:g}·ln(1 - RND)"}.get(
                 par["peaton_dist"],
                 f"{par['peaton_media'] - par['peaton_delta']:g} + "
                 f"{2 * par['peaton_delta']:g}·RND")),
            ("Tipo de acreditación del peatón", "Bernoulli",
             f"RND < {par['porc_qr'] / 100:g} → QR ; si no → presencial"),
            ("Tiempo de acreditación de la recepcionista", "Uniforme U(1;3)",
             f"{par['recep_min']:g} + {par['recep_max'] - par['recep_min']:g}·RND"),
            ("Expectativa del invitado (E0)", "Discreta", "Ver tabla de rangos"),
            ("Tiempo de permanencia en la sala", "Euler (función de E0)",
             "Integración de dE/dt = -68 - E²/E0 hasta E ≤ 0"),
        ], columns=["Variable", "Distribución", "Fórmula"]),
            hide_index=True, width="stretch")
        st.markdown("##### Tabla de rangos de la expectativa")
        st.dataframe(pd.DataFrame(res["rangos_exp"]), hide_index=True,
                     width="stretch",
                     column_config={c: st.column_config.NumberColumn(c, format="%.4f")
                                    for c in ["P()", "RND desde", "RND hasta (<)"]})
    with der:
        st.markdown("##### Eventos")
        st.dataframe(pd.DataFrame([
            ("Llegada auto", "Crea un IV; si hay operario libre empieza la acreditación, si no va a la cola del portón."),
            ("Fin acred. portón Op1 / Op2", "El IV pasa a estacionar (3 min); el operario atiende al siguiente de la cola o queda libre."),
            ("Fin estacionamiento", "El IV entra a la sala: se genera su expectativa y su hora de salida."),
            ("Llegada peatón", "Crea un IP; se sortea QR o presencial; va al dispositivo/recepcionista o a su cola."),
            ("Fin escaneo QR", "El IP entra a la sala; el dispositivo atiende al siguiente o queda libre."),
            ("Fin acred. recepcionista", "El IP entra a la sala; la recepcionista atiende al siguiente o queda libre."),
            ("Fin degustación", "El invitado se retira; se acumula su tiempo de permanencia y se destruye el objeto."),
            ("Fin simulación (X)", "Corte en el instante X: se cierran los acumuladores de tiempo."),
        ], columns=["Evento", "Qué hace"]), hide_index=True, width="stretch")
        st.markdown("##### Colas")
        st.dataframe(pd.DataFrame([
            ("Cola portón", "2 (Op1 y Op2)", "FIFO", "Ilimitada"),
            ("Cola QR", "1 (dispositivo)", "FIFO", "Ilimitada"),
            ("Cola recepción", "1 (recepcionista)", "FIFO", "Ilimitada"),
        ], columns=["Cola", "Servidores", "Disciplina", "Capacidad"]),
            hide_index=True, width="stretch")
        st.caption("Si dos eventos ocurren en el mismo instante, primero se procesan "
                   "las salidas y fines de atención y después las llegadas.")
