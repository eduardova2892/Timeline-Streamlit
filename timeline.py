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
st.subheader("➕ Nueva tarea")

with st.form("task_form"):

    proyecto = st.text_input("Proyecto")
    consultor = st.text_input("Consultor")
    tarea = st.text_input("Tarea")
    subtarea = st.text_input("Subtarea (opcional)")

    responsable = st.text_input("Responsable")

    prioridad = st.selectbox("Prioridad", ["Alta", "Media", "Baja"])

    avance = st.slider("Avance (%)", 0, 100, 0)
    inicio = st.date_input("Fecha inicio", value=date.today())
    deadline = st.date_input("Fecha límite", value=date.today())
    link = st.text_input("Ruta o link documento")

    # ✅ ESTE BOTÓN DEBE ESTAR AQUÍ DENTRO
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
            "link": link
        }

        data.append(nueva_tarea)
        save_data(data)
        st.success("Tarea agregada ✅")

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
    edited_df = st.data_editor(
    df,
    use_container_width=True,
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

st.subheader("📅 Timeline de tareas")

if len(data) > 0:

    df = pd.DataFrame(data)

    # =========================
    # 🔹 FORMATO DE FECHAS
    # =========================
    df["inicio"] = pd.to_datetime(df["inicio"], errors="coerce")
    df["deadline"] = pd.to_datetime(df["deadline"], errors="coerce")

    # =========================
    # 🔹 ESTADO (CRÍTICO / NORMAL)
    # =========================
    hoy_pd = pd.to_datetime(datetime.today())

    df["dias_restantes"] = (df["deadline"] - hoy_pd).dt.days

    def estado_tarea(row):
        if row["dias_restantes"] <= 3 and row["avance"] < 100:
            return "Crítica"
        else:
            return "Normal"

    df["estado"] = df.apply(estado_tarea, axis=1)

    # =========================
    # 🔹 ORDENAR
    # =========================
    df = df.sort_values(by=["proyecto", "inicio"]).reset_index(drop=True)

    # =========================
    # 🔹 FORMATO VISUAL PROYECTO → TAREA
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
    

    # ✅ Guardar cambios
    if st.button("💾 Guardar comentarios / links"):

        updated_docs = edited_docs.copy()
        full_df = pd.DataFrame(data)

        # Asegurar columna
        if "comentarios" not in full_df.columns:
            full_df["comentarios"] = ""

        # ✅ actualizar SOLO esos campos
        full_df["comentarios"] = updated_docs["comentarios"]
        full_df["link"] = updated_docs["link"]

        save_data(full_df.to_dict(orient="records"))

        st.success("Comentarios y links actualizados ✅")

st.subheader("🔗 Acceso directo a documentos")

for i, row in df_docs.iterrows():
    if row["link"]:

        link = row["link"]

        # ✅ convertir rutas locales en formato válido
        if link.startswith("C:"):
            link = "file:///" + link.replace("\\", "/")

        st.link_button(
            f"📄 {row['proyecto']} - {row['tarea']}",
            link
        )

