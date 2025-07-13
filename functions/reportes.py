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
#  NUEVOS ANÁLISIS SOLICITADOS
# ===========================================================

def analizar_actividades_por_procedencia_edad(df: pd.DataFrame) -> None:
    """Analiza qué actividades se realizan más por procedencia y edad."""
    if df.empty:
        st.warning("No hay datos para analizar actividades por procedencia y edad")
        return

    st.header("🌍 Actividades por Procedencia y Edad")
    
    # Análisis por procedencia (ciudad)
    st.subheader("Actividades más populares por Ciudad")
    actividades_ciudad = df.groupby(['Ciudad', 'Actividad']).size().reset_index(name='Cantidad')
    
    # Top 5 ciudades por volumen de actividades
    top_ciudades = df['Ciudad'].value_counts().head(5).index
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    axes = axes.flatten()
    
    for i, ciudad in enumerate(top_ciudades):
        if i < 5:
            ciudad_data = actividades_ciudad[actividades_ciudad['Ciudad'] == ciudad].nlargest(5, 'Cantidad')
            if not ciudad_data.empty:
                axes[i].bar(ciudad_data['Actividad'], ciudad_data['Cantidad'])
                axes[i].set_title(f'Top Actividades en {ciudad}')
                axes[i].tick_params(axis='x', rotation=45)
    
    # Heatmap general
    pivot_ciudad = df.groupby(['Ciudad', 'Actividad']).size().unstack(fill_value=0)
    top_actividades = df['Actividad'].value_counts().head(10).index
    pivot_ciudad_top = pivot_ciudad[top_actividades].head(10)
    
    axes[5].imshow(pivot_ciudad_top.values, cmap='YlOrRd', aspect='auto')
    axes[5].set_title('Heatmap: Ciudades vs Actividades')
    axes[5].set_xticks(range(len(top_actividades)))
    axes[5].set_xticklabels(top_actividades, rotation=45)
    axes[5].set_yticks(range(len(pivot_ciudad_top.index)))
    axes[5].set_yticklabels(pivot_ciudad_top.index)
    
    plt.tight_layout()
    st.pyplot(fig)
    
    # Análisis por grupo de edad
    st.subheader("Actividades más populares por Grupo de Edad")
    actividades_edad = df.groupby(['Grupo Edad', 'Actividad']).size().reset_index(name='Cantidad')
    
    fig, ax = plt.subplots(figsize=(12, 8))
    pivot_edad = df.groupby(['Grupo Edad', 'Actividad']).size().unstack(fill_value=0)
    top_actividades_edad = df['Actividad'].value_counts().head(8).index
    pivot_edad_top = pivot_edad[top_actividades_edad]
    
    sns.heatmap(pivot_edad_top, annot=True, fmt='d', cmap='Blues', ax=ax)
    ax.set_title('Heatmap: Actividades por Grupo de Edad')
    ax.set_xlabel('Actividad')
    ax.set_ylabel('Grupo de Edad')
    st.pyplot(fig)
    
    # Tabla resumen
    st.subheader("Resumen por Procedencia y Edad")
    resumen = df.groupby(['Ciudad', 'Grupo Edad', 'Actividad']).agg({
        'ID': 'count',
        'Precio': 'sum'
    }).rename(columns={'ID': 'Reservas', 'Precio': 'Ingresos'}).reset_index()
    
    resumen_top = resumen.nlargest(20, 'Reservas')
    st.dataframe(resumen_top)


def analizar_dias_semana_actividades(df: pd.DataFrame) -> None:
    """Analiza qué día de la semana se realizan más actividades."""
    if df.empty:
        st.warning("No hay datos para analizar días de la semana")
        return

    st.header("📅 Análisis de Días de la Semana")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Actividades por Día de la Semana")
        actividades_dow = df.groupby('Día de la Semana').size().reindex(DOW_ORDER)
        
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(actividades_dow.index, actividades_dow.values, color='skyblue')
        ax.set_title('Número de Actividades por Día de la Semana')
        ax.set_xlabel('Día de la Semana')
        ax.set_ylabel('Número de Actividades')
        
        # Destacar el día con más actividades
        max_idx = actividades_dow.values.argmax()
        bars[max_idx].set_color('orange')
        
        plt.xticks(rotation=45)
        st.pyplot(fig)
        
        # Mostrar estadísticas
        dia_mas_activo = actividades_dow.index[max_idx]
        st.metric("Día más activo", dia_mas_activo, f"{actividades_dow.values[max_idx]} actividades")
    
    with col2:
        st.subheader("Ingresos por Día de la Semana")
        ingresos_dow = df.groupby('Día de la Semana')['Precio'].sum().reindex(DOW_ORDER)
        
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(ingresos_dow.index, ingresos_dow.values, color='lightgreen')
        ax.set_title('Ingresos por Día de la Semana')
        ax.set_xlabel('Día de la Semana')
        ax.set_ylabel('Ingresos (€)')
        
        # Destacar el día con más ingresos
        max_idx = ingresos_dow.values.argmax()
        bars[max_idx].set_color('darkgreen')
        
        plt.xticks(rotation=45)
        st.pyplot(fig)
        
        dia_mas_rentable = ingresos_dow.index[max_idx]
        st.metric("Día más rentable", dia_mas_rentable, f"{ingresos_dow.values[max_idx]:.2f} €")
    
    # Análisis detallado por actividad y día
    st.subheader("Actividades Específicas por Día")
    actividad_dia = df.groupby(['Actividad', 'Día de la Semana']).size().unstack(fill_value=0)
    actividad_dia_top = actividad_dia.loc[df['Actividad'].value_counts().head(5).index]
    
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.heatmap(actividad_dia_top, annot=True, fmt='d', cmap='YlOrRd', ax=ax)
    ax.set_title('Heatmap: Actividades por Día de la Semana')
    st.pyplot(fig)


def analizar_ingresos_mensuales_comparativa(df: pd.DataFrame) -> None:
    """Analiza ingresos por mes y comparativa con otros años."""
    if df.empty:
        st.warning("No hay datos para analizar ingresos mensuales")
        return

    st.header("💰 Ingresos Mensuales y Comparativa Anual")
    
    # Preparar datos mensuales
    ingresos_mensuales = df.groupby(['Año', 'Mes']).agg({
        'Precio': 'sum',
        'ID': 'count'
    }).rename(columns={'ID': 'Reservas'}).reset_index()
    
    # Crear columna de fecha para facilitar visualización
    ingresos_mensuales['Fecha'] = pd.to_datetime(
        ingresos_mensuales['Año'].astype(str) + '-' + 
        ingresos_mensuales['Mes'].astype(str) + '-01'
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Evolución de Ingresos Mensuales")
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Línea por año
        años = sorted(ingresos_mensuales['Año'].unique())
        for año in años:
            data_año = ingresos_mensuales[ingresos_mensuales['Año'] == año]
            ax.plot(data_año['Mes'], data_año['Precio'], marker='o', label=f'{año}')
        
        ax.set_title('Ingresos Mensuales por Año')
        ax.set_xlabel('Mes')
        ax.set_ylabel('Ingresos (€)')
        ax.legend()
        ax.grid(True, alpha=0.3)
        st.pyplot(fig)
    
    with col2:
        st.subheader("Comparativa Anual")
        ingresos_anuales = df.groupby('Año')['Precio'].sum()
        
        fig, ax = plt.subplots(figsize=(8, 6))
        bars = ax.bar(ingresos_anuales.index, ingresos_anuales.values, color='lightblue')
        ax.set_title('Ingresos Totales por Año')
        ax.set_xlabel('Año')
        ax.set_ylabel('Ingresos (€)')
        
        # Destacar el mejor año
        if len(ingresos_anuales) > 1:
            max_idx = ingresos_anuales.values.argmax()
            bars[max_idx].set_color('gold')
        
        st.pyplot(fig)
        
        # Mostrar crecimiento año a año
        if len(ingresos_anuales) > 1:
            crecimiento = ingresos_anuales.pct_change().dropna() * 100
            st.subheader("Crecimiento Anual (%)")
            for año, crecimiento_pct in crecimiento.items():
                color = "green" if crecimiento_pct > 0 else "red"
                st.markdown(f"**{año}**: <span style='color:{color}'>{crecimiento_pct:.1f}%</span>", 
                          unsafe_allow_html=True)
    
    # Análisis estacional
    st.subheader("Análisis Estacional")
    estacional = df.groupby('Mes').agg({
        'Precio': ['sum', 'mean'],
        'ID': 'count'
    }).round(2)
    
    estacional.columns = ['Ingresos Totales', 'Ingresos Promedio', 'Reservas']
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # Ingresos por mes (promedio entre años)
    ax1.bar(estacional.index, estacional['Ingresos Totales'], color='lightcoral')
    ax1.set_title('Ingresos Totales por Mes (Todos los Años)')
    ax1.set_xlabel('Mes')
    ax1.set_ylabel('Ingresos (€)')
    
    # Reservas por mes
    ax2.bar(estacional.index, estacional['Reservas'], color='lightsteelblue')
    ax2.set_title('Número de Reservas por Mes')
    ax2.set_xlabel('Mes')
    ax2.set_ylabel('Reservas')
    
    plt.tight_layout()
    st.pyplot(fig)
    
    # Tabla resumen
    st.subheader("Resumen Mensual")
    meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
             'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    estacional['Mes'] = [meses[i-1] for i in estacional.index]
    st.dataframe(estacional[['Mes', 'Ingresos Totales', 'Ingresos Promedio', 'Reservas']])


def analizar_actividades_por_sexo(df: pd.DataFrame) -> None:
    """Analiza actividades por sexo."""
    if df.empty:
        st.warning("No hay datos para analizar actividades por sexo")
        return

    st.header("⚧ Actividades por Sexo")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Distribución General por Sexo")
        sexo_counts = df['Sexo'].value_counts()
        
        fig, ax = plt.subplots(figsize=(8, 6))
        colors = ['lightpink', 'lightblue', 'lightgreen']
        wedges, texts, autotexts = ax.pie(sexo_counts.values, labels=sexo_counts.index, 
                                         autopct='%1.1f%%', colors=colors[:len(sexo_counts)])
        ax.set_title('Distribución de Clientes por Sexo')
        st.pyplot(fig)
        
        # Estadísticas por sexo
        st.subheader("Estadísticas por Sexo")
        stats_sexo = df.groupby('Sexo').agg({
            'Precio': ['sum', 'mean'],
            'ID': 'count',
            'Edad': 'mean'
        }).round(2)
        
        stats_sexo.columns = ['Ingresos Totales', 'Gasto Promedio', 'Reservas', 'Edad Promedio']
        st.dataframe(stats_sexo)
    
    with col2:
        st.subheader("Actividades Favoritas por Sexo")
        
        # Top 3 actividades por cada sexo
        sexos = df['Sexo'].unique()
        fig, axes = plt.subplots(len(sexos), 1, figsize=(10, 4*len(sexos)))
        if len(sexos) == 1:
            axes = [axes]
        
        for i, sexo in enumerate(sexos):
            sexo_data = df[df['Sexo'] == sexo]
            top_actividades = sexo_data['Actividad'].value_counts().head(5)
            
            axes[i].bar(top_actividades.index, top_actividades.values, 
                       color='lightpink' if sexo == 'Femenino' else 'lightblue')
            axes[i].set_title(f'Top Actividades - {sexo}')
            axes[i].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        st.pyplot(fig)
    
    # Análisis cruzado: Actividades por sexo y edad
    st.subheader("Actividades por Sexo y Grupo de Edad")
    
    # Heatmap de actividades por sexo
    actividades_sexo = df.groupby(['Sexo', 'Actividad']).size().unstack(fill_value=0)
    top_actividades_sexo = df['Actividad'].value_counts().head(8).index
    actividades_sexo_top = actividades_sexo[top_actividades_sexo]
    
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.heatmap(actividades_sexo_top, annot=True, fmt='d', cmap='RdYlBu', ax=ax)
    ax.set_title('Heatmap: Actividades por Sexo')
    st.pyplot(fig)
    
    # Análisis por sexo y edad
    st.subheader("Preferencias por Sexo y Edad")
    sexo_edad_actividad = df.groupby(['Sexo', 'Grupo Edad', 'Actividad']).size().reset_index(name='Cantidad')
    
    # Crear gráfico de barras agrupadas
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Usar solo las top 5 actividades para claridad
    top_5_actividades = df['Actividad'].value_counts().head(5).index
    data_filtered = sexo_edad_actividad[sexo_edad_actividad['Actividad'].isin(top_5_actividades)]
    
    pivot_data = data_filtered.pivot_table(
        index=['Sexo', 'Grupo Edad'], 
        columns='Actividad', 
        values='Cantidad', 
        fill_value=0
    )
    
    pivot_data.plot(kind='bar', ax=ax, width=0.8)
    ax.set_title('Actividades por Sexo y Grupo de Edad (Top 5)')
    ax.set_xlabel('Sexo - Grupo de Edad')
    ax.set_ylabel('Cantidad de Reservas')
    ax.legend(title='Actividad', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.xticks(rotation=45)
    plt.tight_layout()
    st.pyplot(fig)


# ===========================================================
#  VISUALIZACIONES TEMPORALES (ORIGINAL)
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
#  VISUALIZACIONES DEMOGRÁFICAS (ORIGINAL)
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
#  PREDICCIONES (ORIGINAL)
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
#  TENDENCIAS POR EDAD (ORIGINAL)
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

    st.title("📊 Dashboard de Análisis de Clientes")
    st.subheader("Datos de Clientes (procesados)")
    st.dataframe(df)

    # Crear pestañas para organizar los análisis
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📅 Análisis Temporal", 
        "🌍 Procedencia y Edad",
        "📆 Días de la Semana", 
        "💰 Ingresos Mensuales",
        "⚧ Actividades por Sexo",
        "🔮 Predicciones"
    ])
    
    with tab1:
        st.header("📅 Análisis Temporal por Fecha de Actividad")
        generar_graficos_temporales(df)
        generar_graficos_demograficos(df)
        generar_tendencias_edad(df)
    
    with tab2:
        # NUEVA FUNCIONALIDAD: Actividades por procedencia y edad
        analizar_actividades_por_procedencia_edad(df)
    
    with tab3:
        # NUEVA FUNCIONALIDAD: Días de la semana más activos
        analizar_dias_semana_actividades(df)
    
    with tab4:
        # NUEVA FUNCIONALIDAD: Ingresos mensuales y comparativa anual
        analizar_ingresos_mensuales_comparativa(df)
    
    with tab5:
        # NUEVA FUNCIONALIDAD: Actividades por sexo
        analizar_actividades_por_sexo(df)
    
    with tab6:
        generar_predicciones(df)