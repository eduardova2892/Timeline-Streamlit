import streamlit as st
st.set_page_config(layout="wide")
import json
import os
from datetime import date

import pandas as pd
import plotly.express as px


DATA_FILE = "data.json"

# ======================
# Funciones básicas
# ======================
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ======================
# UI principal
# ======================
st.title("📊 Timeline de Proyectos")

data = load_data()

# ======================
# Formulario de ingreso
# ======================
with st.expander("➕ Nueva tarea", expanded=False):

    with st.form("task_form_unico"):

        proyecto = st.text_input("Proyecto")
        consultor = st.text_input("Consultor")
        tarea = st.text_input("Tarea")
        subtarea = st.text_input("Subtarea (opcional)")

        responsable = st.text_input("Responsable")

        prioridad = st.selectbox("Prioridad", ["Alta", "Media", "Baja"])

        avance = st.slider("Avance (%)", 0, 100, 0)
        inicio = st.date_input("Fecha inicio")
        deadline = st.date_input("Fecha límite")

        link = st.text_input("Ruta o link documento")

        submitted = st.form_submit_button("Guardar")

        if submitted:
            nueva_tarea = {
                "proyecto": proyecto,
                "consultor": consultor,
                "tarea": tarea,
                "subtarea": subtarea,
                "responsable": responsable,
                "prioridad": prioridad,
                "avance": avance,
                "inicio": str(inicio),
                "deadline": str(deadline),
                "link": link.strip(),
                "comentarios": ""   # ✅ importante agregar
            }

            data.append(nueva_tarea)
            save_data(data)

            st.success("Tarea agregada ✅")

            # ✅ 🔥 CLAVE: recargar app
            st.rerun()

# ======================
# Mostrar tabla
# ======================
st.subheader("📋 Tareas registradas (editable)")

if len(data) > 0:
    df = pd.DataFrame(data)

    # Asegurar columnas clave
    columnas_deseadas = [
        "proyecto",
        "tarea",
        "consultor",
        "responsable",
        "inicio",
        "deadline",
        "avance",
        "prioridad"
    ]

    # Crear columnas si faltan (para evitar errores)
    for col in columnas_deseadas:
        if col not in df.columns:
            df[col] = ""

    # Reordenar columnas
    df = df[columnas_deseadas]

    # Convertir fechas
    df["inicio"] = pd.to_datetime(df["inicio"], errors="coerce").dt.date
    df["deadline"] = pd.to_datetime(df["deadline"], errors="coerce").dt.date

    # Editor tipo Excel

    df = df.sort_values(by="proyecto")
    df = df.reset_index(drop=True)
    edited_df = st.data_editor(
    df,
    use_container_width=True,
    hide_index=True,
    num_rows="dynamic",   # 🔥 clave → permite borrar filas
    column_config={
        "inicio": st.column_config.DateColumn("Fecha inicio"),
        "deadline": st.column_config.DateColumn("Deadline"),
        "avance": st.column_config.NumberColumn(
            "Avance (%)",
            min_value=0,
            max_value=100,
            step=1,
        ),
    }
)

    # Guardar cambios
    if st.button("💾 Guardar cambios"):
        updated = edited_df.copy()

        # Volver a string
        updated["inicio"] = updated["inicio"].astype(str)
        updated["deadline"] = updated["deadline"].astype(str)

        save_data(updated.to_dict(orient="records"))
        st.success("Cambios guardados ✅")

else:
    st.info("No hay tareas aún")


# =========================
# 📅 TIMELINE DE TAREAS
# =========================

from datetime import datetime

#ECHARTS BLOQUE (TEST)

echart_data = []

for i, row in df.iterrows():
    echart_data.append({
        "name": row["tarea"],
        "value": [
            i,
            str(row["inicio"]),
            str(row["deadline"]),
            row["avance"]
        ],
        "itemStyle": {
            "color": "#00c853" if row["avance"] == 100 else "#ff9800" if row["avance"] > 50 else "#d32f2f"
        }
    })



st.subheader("📅 Timeline de tareas")

if len(data) > 0:

    # =========================
    # 🔹 DATAFRAME BASE
    # =========================
    df = pd.DataFrame(data)

    df["inicio"] = pd.to_datetime(df["inicio"], errors="coerce")
    df["deadline"] = pd.to_datetime(df["deadline"], errors="coerce")

    df = df.dropna(subset=["inicio", "deadline"])

    # =========================
    # 🔹 RANGO REAL
    # =========================
    min_fecha = df["inicio"].min().date()
    max_fecha = df["deadline"].max().date()

    # =========================
    # 🔹 SESSION STATE (CLAVE)
    # =========================
    if "fecha_inicio" not in st.session_state:
        st.session_state.fecha_inicio = min_fecha

    if "fecha_fin" not in st.session_state:
        st.session_state.fecha_fin = max_fecha

    # =========================
    # 🔹 SELECTORES
    # =========================
    col1, col2 = st.columns(2)

    with col1:
        fecha_inicio_input = st.date_input(
            "Desde",
            value=st.session_state.fecha_inicio,
            min_value=min_fecha,
            max_value=max_fecha,
            key="filtro_inicio"
        )

    with col2:
        fecha_fin_input = st.date_input(
            "Hasta",
            value=st.session_state.fecha_fin,
            min_value=min_fecha,
            max_value=max_fecha,
            key="filtro_fin"
        )

    # ✅ actualizar session_state
    st.session_state.fecha_inicio = fecha_inicio_input
    st.session_state.fecha_fin = fecha_fin_input

    # =========================
    # 🔹 BOTÓN 30 DÍAS
    # =========================
    if st.button("Últimos 30 días"):
        st.session_state.fecha_fin = max_fecha
        st.session_state.fecha_inicio = max_fecha - pd.Timedelta(days=30)

    # =========================
    # 🔹 FILTRO CORRECTO
    # =========================
    df_filtrado = df[
        (df["deadline"].dt.date >= st.session_state.fecha_inicio) &
        (df["inicio"].dt.date <= st.session_state.fecha_fin)
    ]

    # =========================
    # 🔹 VALIDACIÓN
    # =========================
    
    df = df_filtrado.copy()

    if df.empty:
        st.warning("No hay tareas en ese rango de fechas")
        st.stop()   # ✅ corta ejecución


    else:
        df = df_filtrado

        # =========================
        # 🔹 ESTADO
        # =========================
        hoy_pd = pd.to_datetime(datetime.today())

        df["dias_restantes"] = (df["deadline"] - hoy_pd).dt.days

        df["estado"] = df.apply(
            lambda row: "Crítica" if row["dias_restantes"] <= 3 and row["avance"] < 100 else "Normal",
            axis=1
        )

        # =========================
        # 🔹 ORDENAR
        # =========================
        df = df.sort_values(by=["proyecto", "inicio"]).reset_index(drop=True)

        # =========================
        # 🔹 LABELS
        # =========================
        labels = []
        proyecto_anterior = None

        for _, row in df.iterrows():
            if row["proyecto"] != proyecto_anterior:
                label = "📁 " + row["proyecto"].upper() + "\n   └─ " + row["tarea"]
                proyecto_anterior = row["proyecto"]
            else:
                label = "   └─ " + row["tarea"]

            labels.append(label)

        df["proyecto_tarea"] = labels
    # =========================
    # 🔹 POSICIONES PARA LÍNEAS DE SEPARACIÓN
    # =========================
    line_positions = []

    for i in range(len(df)):
        if i == 0 or df.loc[i, "proyecto"] != df.loc[i - 1, "proyecto"]:
            line_positions.append(i)

    # =========================
    # 🔹 CREAR GRÁFICO
    # =========================
    fig = px.timeline(
        df,
        x_start="inicio",
        x_end="deadline",
        y="proyecto_tarea",
        color="avance",
        color_continuous_scale="RdYlGn"
    )

    fig.update_xaxes(
        range=[st.session_state.fecha_inicio, st.session_state.fecha_fin]
    )

    # ✅ Escala fija 0–100
    fig.update_coloraxes(cmin=0, cmax=100)

    # =========================
    # 🔹 LÍNEAS SEPARADORAS POR PROYECTO
    # =========================
    
    xmin = df["inicio"].min()
    xmax = df["deadline"].max()

    # 👇 extender un poco hacia ambos lados
    padding = (xmax - xmin) * 0.05

    xmin_ext = xmin - padding
    xmax_ext = xmax + padding

    
    
    for pos in line_positions:
        fig.add_shape(
            type="line",
            x0=xmin_ext,
            x1=xmax_ext,
            xref="x",
            y0=pos - 0.5,
            y1=pos - 0.5,
            yref="y",
            line=dict(
                color="rgba(200,200,200,0.4)",
                width=1.5,
                dash="dot"
            )
        )


    line=dict(
        color="rgba(200,200,200,0.4)",  # más suave
        width=1.5,
        dash="dot"
    )

    fig.update_xaxes(
    dtick="D1",  # o D7 si sigues con semanal
    tickformat="%d-%b<br>%a",   # 🔥 clave
    tickfont=dict(size=20)
)
                      
# =========================
# 🔹 LÍNEA "HOY"
# =========================
    from datetime import datetime

    today_date = datetime.today().date()

# 👉 poner en medio del día
    hoy = datetime.combine(datetime.today().date(), datetime.min.time())

    fig.add_vrect(
        x0=hoy - pd.Timedelta(hours=12),
        x1=hoy + pd.Timedelta(hours=12),
        fillcolor="red",
        opacity=0.2,
        line_width=0,
    )


    fig.add_annotation(
        x=hoy,
        y=1.02,
        xref="x",
        yref="paper",
        text="TODAY",
        showarrow=False,
        font=dict(size=16, color="red")
    )

    # =========================
    # 🔹 MARCAR TAREAS CRÍTICAS
    # =========================
    for _, row in df.iterrows():
        if row["estado"] == "Crítica":
            fig.add_scatter(
                x=[row["deadline"]],
                y=[row["proyecto_tarea"]],
                mode="markers+text",
                marker=dict(color="red", size=10),
                text=["⚠"],
                textposition="middle right",
                showlegend=False
            )

# ✅ MARCAR TAREAS COMPLETADAS

    for _, row in df.iterrows():
        if row["avance"] == 100:
            fig.add_scatter(
                x=[row["deadline"]],
                y=[row["proyecto_tarea"]],
                mode="text",
                text=["✅ Completado"],
                textposition="middle right",
                showlegend=False
            )


    # =========================
    # 🎨 ESTILO FINAL
    # =========================
    fig.update_yaxes(
        autorange="reversed",
        title="",
        tickfont=dict(size=18)
    )

    fig.update_layout(
        font=dict(size=18)
    )

    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("No hay tareas aún")


# DOCUMENTOS POR TAREA
st.subheader("📂 Documentos y comentarios por tarea")

if len(data) > 0:

    df_docs = pd.DataFrame(data)

    # Crear columna comentarios solo aquí si no existe
    if "comentarios" not in df_docs.columns:
        df_docs["comentarios"] = ""

    # Columnas que quieres mostrar
    columnas_docs = ["proyecto", "tarea", "responsable", "link", "comentarios"]

    for col in columnas_docs:
        if col not in df_docs.columns:
            df_docs[col] = ""

    df_docs = df_docs[columnas_docs]

# ✅ Editor SOLO para comentarios y links
edited_docs = st.data_editor(
    df_docs,
    use_container_width=True,
    column_config={
        "link": st.column_config.TextColumn("Ruta / Link documento"),
        "comentarios": st.column_config.TextColumn("Comentarios"),
    }
)

# ✅ GUARDAR (TODO VA DENTRO DEL BOTÓN)
if st.button("💾 Guardar comentarios / links"):

    # ✅ aquí se define correctamente
    updated_docs = edited_docs.copy()

    # ✅ data original
    merged_df = pd.DataFrame(data)

    # ✅ asegurar columnas
    for col in ["comentarios", "link"]:
        if col not in merged_df.columns:
            merged_df[col] = ""

    # ✅ actualizar correctamente
    for _, row in updated_docs.iterrows():

        mask = (
    (merged_df["proyecto"].astype(str).str.strip() == str(row["proyecto"]).strip()) &
    (merged_df["tarea"].astype(str).str.strip() == str(row["tarea"]).strip()) &
    (merged_df["responsable"].astype(str).str.strip() == str(row["responsable"]).strip())
)

        comentario = str(row.get("comentarios", "")).strip()
        link = str(row.get("link", "")).strip()

        if comentario and comentario.lower() != "nan":
            merged_df.loc[mask, "comentarios"] = comentario

        
        if link.lower() != "nan":
            merged_df.loc[mask, "link"] = link


    # ✅ guardar
    save_data(merged_df.to_dict(orient="records"))

    st.success("Comentarios y links guardados correctamente ✅")

st.subheader("🔗 Acceso directo a documentos")

for i, row in df_docs.iterrows():

    link = str(row.get("link", "")).strip()

    if link != "" and link.lower() != "nan":

        # ✅ convertir rutas locales
        if link.startswith("C:"):
            link = "file:///" + link.replace("\\", "/")

        st.link_button(
            f"📄 {row['proyecto']} - {row['tarea']}",
            link
        )
