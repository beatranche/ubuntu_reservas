# functions/reportes.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from functions.data_utils import cargar_clientes
from sklearn.linear_model import LinearRegression

# ------------------- CONSTANTES Y CONFIG -------------------
EDAD_BINS   = [0, 18, 30, 45, 60, 120]
EDAD_LABELS = ['<18', '18‑30', '31‑45', '46‑60', '>60']
DOW_ORDER   = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']


# ===========================================================
#  PRE‑PROCESAMIENTO
# ===========================================================

def procesar_datos_clientes(df: pd.DataFrame) -> pd.DataFrame:
    """Limpia, tipa y enriquece el dataframe de clientes para los reportes.

    • Garantiza tipos Arrow‑compatibles (evita ArrowTypeError)
    • Elimina SettingWithCopyWarning usando copias explícitas y .loc
    """
    if df.empty:
        return df

    # -------- Trabajamos sobre copia profunda --------
    df = df.copy()

    # -------- Tipado base  --------
    df['ID']               = pd.to_numeric(df['ID'], errors='coerce').astype('Int64')
    df['Fecha Nacimiento'] = pd.to_datetime(df['Fecha Nacimiento'], dayfirst=True, errors='coerce')
    df['Fecha Actividad']  = pd.to_datetime(df['Fecha Actividad'],  dayfirst=True, errors='coerce')
    df['Precio']           = pd.to_numeric(df['Precio'],   errors='coerce')
    df['Personas']         = pd.to_numeric(df['Personas'], errors='coerce')

    # -------- Enriquecimiento --------
    # Edad (años cumplidos)
    df['Edad'] = ((pd.Timestamp.now() - df['Fecha Nacimiento']).dt.days // 365)

    # Ingresos por persona
    df['Ingresos por Persona'] = np.where(df['Personas'] > 0, df['Precio'] / df['Personas'], np.nan)

    # Filtrar edades razonables y copiar de nuevo para evitar SettingWithCopy
    df = df.loc[df['Edad'].between(1, 119)].copy()

    # Partes de la fecha de actividad
    df['Año']              = df['Fecha Actividad'].dt.year
    df['Mes']              = df['Fecha Actividad'].dt.month
    df['Día de la Semana'] = df['Fecha Actividad'].dt.day_name()
    df['Día del Mes']      = df['Fecha Actividad'].dt.day

    # Hora numérica (0‑23)
    df['Hora Inicio'] = (
        pd.to_datetime(df['Hora Inicio'], format='%H:%M', errors='coerce')
          .dt.hour
    )

    # Grupos de edad
    df['Grupo Edad'] = pd.cut(df['Edad'], bins=EDAD_BINS, labels=EDAD_LABELS, right=False)

    # Arrow friendliness: cualquier columna object -> string
    obj_cols = df.select_dtypes(['object']).columns
    df[obj_cols] = df[obj_cols].astype('string')

    return df


# ===========================================================
#  VISUALIZACIONES TEMPORALES
# ===========================================================

def generar_graficos_temporales(df: pd.DataFrame) -> None:
    if df.empty:
        st.warning("No hay datos para generar gráficos temporales")
        return

    col1, col2 = st.columns(2)

    # ---------- Reservas por mes ----------
    with col1:
        st.subheader("Reservas por Mes")
        reservas_por_mes = (
            df.groupby(['Año', 'Mes'])
              .size()
              .reset_index(name='Reservas')
        )
        reservas_por_mes['Fecha'] = pd.to_datetime(
            reservas_por_mes['Año'].astype(str) + '-' + reservas_por_mes['Mes'].astype(str) + '-01'
        )
        fig, ax = plt.subplots()
        sns.lineplot(data=reservas_por_mes, x='Fecha', y='Reservas', ax=ax)
        ax.set(title='Reservas por Mes', xlabel='Fecha', ylabel='Número de Reservas')
        plt.xticks(rotation=45)
        st.pyplot(fig)

        # ---------- Ingresos por día del mes ----------
        st.subheader("Ingresos por Día del Mes")
        ingresos_dia_mes = df.groupby('Día del Mes')['Precio'].sum()
        fig, ax = plt.subplots()
        ingresos_dia_mes.plot(kind='bar', ax=ax)
        ax.set(title='Ingresos Totales por Día del Mes', xlabel='Día del Mes', ylabel='Ingresos (€)')
        st.pyplot(fig)

    # ---------- Ingresos por día de la semana / reservas por hora ----------
    with col2:
        st.subheader("Ingresos por Día de la Semana")
        ingresos_dow = df.groupby('Día de la Semana')['Precio'].sum().reindex(DOW_ORDER)
        fig, ax = plt.subplots()
        ingresos_dow.plot(kind='bar', ax=ax)
        ax.set(title='Ingresos Totales por Día de la Semana', xlabel='Día', ylabel='Ingresos (€)')
        st.pyplot(fig)

        st.subheader("Reservas por Hora del Día")
        reservas_hora = df['Hora Inicio'].value_counts().sort_index()
        fig, ax = plt.subplots()
        reservas_hora.plot(kind='bar', ax=ax)
        ax.set(title='Reservas por Hora del Día', xlabel='Hora', ylabel='Número de Reservas')
        st.pyplot(fig)


# ===========================================================
#  VISUALIZACIONES DEMOGRÁFICAS
# ===========================================================

def generar_graficos_demograficos(df: pd.DataFrame) -> None:
    if df.empty:
        st.warning("No hay datos para generar gráficos demográficos")
        return

    st.header("👥 Análisis Demográfico y de Actividades")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Distribución por Sexo")
        sexo_count = df['Sexo'].value_counts()
        fig, ax = plt.subplots()
        ax.pie(sexo_count, labels=sexo_count.index, autopct='%1.1f%%')
        ax.set_title('Distribución por Sexo')
        st.pyplot(fig)

        st.subheader("Edad vs Precio")
        fig, ax = plt.subplots()
        sns.scatterplot(data=df, x='Edad', y='Precio', hue='Sexo', ax=ax)
        ax.set_title('Relación Edad vs Precio Pagado')
        st.pyplot(fig)

    with col2:
        st.subheader("Actividades Populares")
        actividad_count = df['Actividad'].value_counts().head(10)
        fig, ax = plt.subplots()
        actividad_count.plot(kind='bar', ax=ax)
        ax.set_title('Actividades Más Populares')
        ax.set_ylabel('Número de Reservas')
        plt.xticks(rotation=45)
        st.pyplot(fig)

        st.subheader("Ingresos por Ciudad")
        ingresos_ciudad = df.groupby('Ciudad')['Precio'].sum().nlargest(10)
        fig, ax = plt.subplots()
        ingresos_ciudad.plot(kind='bar', ax=ax)
        ax.set_title('Top 10 Ciudades por Ingresos')
        ax.set_ylabel('Ingresos (€)')
        plt.xticks(rotation=45)
        st.pyplot(fig)


# ===========================================================
#  PREDICCIONES
# ===========================================================

def generar_predicciones(df: pd.DataFrame) -> None:
    if df.empty:
        st.warning("No hay datos para generar predicciones")
        return

    st.header("🔮 Predicciones Futuras")
    st.subheader("Predicción de Actividad por Mes")

    # -------- Preparar datos --------
    df = df.copy()
    df['Fecha Registro'] = pd.to_datetime(df['Fecha Registro'], dayfirst=True, errors='coerce')
    df['Mes Registro'] = df['Fecha Registro'].dt.to_period('M')

    pred_df = (
        df.groupby(['Mes Registro', 'Actividad'])
          .agg(Precio=('Precio', 'sum'), Personas=('Personas', 'sum'), Reservas=('ID', 'count'))
          .reset_index()
    )
    pred_df['Mes Registro'] = pred_df['Mes Registro'].dt.to_timestamp()

    if pred_df.empty:
        st.warning("No hay suficientes datos para generar predicciones")
        return

    actividad = st.selectbox("Seleccionar actividad", pred_df['Actividad'].unique())
    act_df = pred_df[pred_df['Actividad'] == actividad].sort_values('Mes Registro')

    if len(act_df) < 2:
        st.warning("Se necesitan más datos para predecir esta actividad")
        return

    # -------- Modelo lineal simple --------
    X = np.arange(len(act_df)).reshape(-1, 1)
    y = act_df['Precio'].values
    model = LinearRegression().fit(X, y)

    # Predecir próximos 3 meses
    X_future = np.arange(len(act_df), len(act_df) + 3).reshape(-1, 1)
    y_future = model.predict(X_future)
    fechas_future = pd.date_range(start=act_df['Mes Registro'].max() + pd.DateOffset(months=1), periods=3, freq='MS')

    # -------- Unir histórico + predicción --------
    hist = pd.DataFrame({'Fecha': act_df['Mes Registro'], 'Precio': act_df['Precio'], 'Tipo': 'Histórico'})
    futu = pd.DataFrame({'Fecha': fechas_future,           'Precio': y_future,       'Tipo': 'Predicción'})
    full = pd.concat([hist, futu])

    fig, ax = plt.subplots(figsize=(8, 4))
    sns.lineplot(data=full, x='Fecha', y='Precio', hue='Tipo', style='Tipo', markers=True, dashes=False, ax=ax)
    ax.set_title(f'Ingresos de {actividad}: histórico + próximos 3 meses')
    ax.set_ylabel('Ingresos (€)')
    plt.xticks(rotation=45)
    st.pyplot(fig)

    st.subheader("Tabla de Predicciones")
    futu_out = futu.copy()
    futu_out['Mes'] = futu_out['Fecha'].dt.strftime('%B %Y')
    st.dataframe(futu_out[['Mes', 'Precio']].rename(columns={'Precio': 'Ingresos Predichos (€)'}))


# ===========================================================
#  TENDENCIAS POR EDAD
# ===========================================================

def generar_tendencias_edad(df: pd.DataFrame) -> None:
    if df.empty:
        st.warning("No hay datos para generar tendencias por edad")
        return

    st.subheader("Tendencias por Edad")
    fig, ax = plt.subplots()
    sns.boxplot(data=df, x='Grupo Edad', y='Ingresos por Persona', hue='Sexo', ax=ax)
    ax.set(title='Ingresos por Persona según Grupo de Edad y Sexo', xlabel='Grupo de Edad', ylabel='Ingresos por Persona (€)')
    st.pyplot(fig)


# ===========================================================
#  ORQUESTADOR PRINCIPAL
# ===========================================================

def generar_reportes() -> None:
    clientes_raw = cargar_clientes()

    if clientes_raw.empty:
        st.info("No hay datos de clientes disponibles. Ingrese datos en la pestaña 'Ingresar Datos de Clientes'.")
        return

    df = procesar_datos_clientes(clientes_raw)

    st.subheader("Datos de Clientes (procesados)")
    st.dataframe(df)

    st.header("📅 Análisis Temporal por Fecha de Actividad")
    generar_graficos_temporales(df)

    generar_graficos_demograficos(df)

    generar_predicciones(df)

    generar_tendencias_edad(df)