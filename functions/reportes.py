# functions/reportes.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from dateutil.relativedelta import relativedelta
from functions.data_utils import cargar_clientes
from sklearn.linear_model import LinearRegression

def procesar_datos_clientes(clientes_df):
    """Prepara los datos de clientes para análisis"""
    if clientes_df.empty:
        return pd.DataFrame()
    
    # Convertir tipos de datos
    clientes_df['Fecha Nacimiento'] = pd.to_datetime(clientes_df['Fecha Nacimiento'], dayfirst=True, errors='coerce')
    clientes_df['Fecha Actividad'] = pd.to_datetime(clientes_df['Fecha Actividad'], dayfirst=True, errors='coerce')
    clientes_df['Precio'] = pd.to_numeric(clientes_df['Precio'], errors='coerce')
    clientes_df['Personas'] = pd.to_numeric(clientes_df['Personas'], errors='coerce')
    
    # Calcular edad
    clientes_df['Edad'] = (datetime.now() - clientes_df['Fecha Nacimiento']).dt.days // 365
    
    # Calcular ingresos por persona
    clientes_df['Ingresos por Persona'] = clientes_df.apply(
        lambda row: row['Precio'] / row['Personas'] if row['Personas'] > 0 else 0,
        axis=1
    )
    
    # Filtrar edades razonables
    clientes_df = clientes_df[(clientes_df['Edad'] > 0) & (clientes_df['Edad'] < 120)]
    
    # Crear columnas para análisis temporal
    clientes_df['Año'] = clientes_df['Fecha Actividad'].dt.year
    clientes_df['Mes'] = clientes_df['Fecha Actividad'].dt.month
    clientes_df['Día de la Semana'] = clientes_df['Fecha Actividad'].dt.day_name()
    clientes_df['Día del Mes'] = clientes_df['Fecha Actividad'].dt.day
    
    # Convertir hora de inicio a formato numérico
    clientes_df['Hora Inicio'] = pd.to_datetime(clientes_df['Hora Inicio'], format='%H:%M', errors='coerce').dt.hour
    
    # Grupos de edad
    edad_bins = [0, 18, 30, 45, 60, 100]
    edad_labels = ['<18', '18-30', '31-45', '46-60', '>60']
    clientes_df['Grupo Edad'] = pd.cut(clientes_df['Edad'], bins=edad_bins, labels=edad_labels)
    
    return clientes_df

def generar_graficos_temporales(df):
    """Genera gráficos de análisis temporal"""
    if df.empty:
        st.warning("No hay datos para generar gráficos temporales")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Reservas por Mes")
        reservas_por_mes = df.groupby(['Año', 'Mes']).size().reset_index(name='Reservas')
        reservas_por_mes['Fecha'] = pd.to_datetime(reservas_por_mes['Año'].astype(str) + '-' + reservas_por_mes['Mes'].astype(str) + '-01')
        fig_temp1, ax_temp1 = plt.subplots()
        sns.lineplot(data=reservas_por_mes, x='Fecha', y='Reservas', ax=ax_temp1)
        ax_temp1.set_title('Reservas por Mes')
        ax_temp1.set_xlabel('Fecha')
        ax_temp1.set_ylabel('Número de Reservas')
        plt.xticks(rotation=45)
        st.pyplot(fig_temp1)
        
        st.subheader("Ingresos por Día del Mes")
        ingresos_dia_mes = df.groupby('Día del Mes')['Precio'].sum()
        fig_temp3, ax_temp3 = plt.subplots()
        ingresos_dia_mes.plot(kind='bar', ax=ax_temp3)
        ax_temp3.set_title('Ingresos Totales por Día del Mes')
        ax_temp3.set_xlabel('Día del Mes')
        ax_temp3.set_ylabel('Ingresos (€)')
        st.pyplot(fig_temp3)
    
    with col2:
        st.subheader("Ingresos por Día de la Semana")
        ingresos_dia_semana = df.groupby('Día de la Semana')['Precio'].sum()
        # Ordenar por días de la semana
        dias_ordenados = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        ingresos_dia_semana = ingresos_dia_semana.reindex(dias_ordenados)
        fig_temp2, ax_temp2 = plt.subplots()
        ingresos_dia_semana.plot(kind='bar', ax=ax_temp2)
        ax_temp2.set_title('Ingresos Totales por Día de la Semana')
        ax_temp2.set_xlabel('Día de la Semana')
        ax_temp2.set_ylabel('Ingresos (€)')
        st.pyplot(fig_temp2)
        
        st.subheader("Reservas por Hora del Día")
        reservas_por_hora = df['Hora Inicio'].value_counts().sort_index()
        fig_temp4, ax_temp4 = plt.subplots()
        reservas_por_hora.plot(kind='bar', ax=ax_temp4)
        ax_temp4.set_title('Reservas por Hora del Día')
        ax_temp4.set_xlabel('Hora del Día')
        ax_temp4.set_ylabel('Número de Reservas')
        st.pyplot(fig_temp4)

def generar_graficos_demograficos(df):
    """Genera gráficos de análisis demográfico"""
    if df.empty:
        st.warning("No hay datos para generar gráficos demográficos")
        return
    
    st.header("👥 Análisis Demográfico y de Actividades")
    col_demo1, col_demo2 = st.columns(2)
    
    with col_demo1:
        st.subheader("Distribución por Sexo")
        sexo_count = df['Sexo'].value_counts()
        fig1, ax1 = plt.subplots()
        ax1.pie(sexo_count, labels=sexo_count.index, autopct='%1.1f%%')
        st.pyplot(fig1)
        
        st.subheader("Edad vs Precio")
        fig3, ax3 = plt.subplots()
        sns.scatterplot(data=df, x='Edad', y='Precio', hue='Sexo', ax=ax3)
        ax3.set_title('Relación Edad vs Precio Pagado')
        st.pyplot(fig3)
    
    with col_demo2:
        st.subheader("Actividades Populares")
        actividad_count = df['Actividad'].value_counts().head(10)
        fig2, ax2 = plt.subplots()
        actividad_count.plot(kind='bar', ax=ax2)
        ax2.set_title('Actividades Más Populares')
        ax2.set_ylabel('Número de Reservas')
        plt.xticks(rotation=45)
        st.pyplot(fig2)
        
        st.subheader("Ingresos por Ciudad")
        ingresos_ciudad = df.groupby('Ciudad')['Precio'].sum().nlargest(10)
        fig4, ax4 = plt.subplots()
        ingresos_ciudad.plot(kind='bar', ax=ax4)
        ax4.set_title('Top 10 Ciudades por Ingresos')
        ax4.set_ylabel('Ingresos (€)')
        plt.xticks(rotation=45)
        st.pyplot(fig4)

def generar_predicciones(df):
    """Genera predicciones basadas en datos de clientes"""
    if df.empty:
        st.warning("No hay datos para generar predicciones")
        return
    
    st.header("🔮 Predicciones Futuras")
    st.subheader("Predicción de Actividad por Mes")
    
    # Preparar datos para predicción
    df['Fecha Registro'] = pd.to_datetime(df['Fecha Registro'], dayfirst=True)
    df['Mes'] = df['Fecha Registro'].dt.to_period('M')
    
    # Agrupar por mes y actividad
    predicciones_df = df.groupby(['Mes', 'Actividad']).agg({
        'Precio': 'sum',
        'Personas': 'sum',
        'ID': 'count'
    }).reset_index()
    predicciones_df['Mes'] = predicciones_df['Mes'].dt.to_timestamp()
    
    if predicciones_df.empty:
        st.warning("No hay suficientes datos para generar predicciones")
        return
    
    # Seleccionar actividad para predecir
    actividad_seleccionada = st.selectbox(
        "Seleccionar actividad para predicción",
        options=predicciones_df['Actividad'].unique()
    )
    
    # Filtrar datos para la actividad seleccionada
    datos_actividad = predicciones_df[predicciones_df['Actividad'] == actividad_seleccionada]
    
    if len(datos_actividad) > 1:
        # Modelo de predicción simple
        X = np.arange(len(datos_actividad)).reshape(-1, 1)
        y = datos_actividad['Precio'].values
        
        model = LinearRegression()
        model.fit(X, y)
        
        # Predecir próximos 3 meses
        X_future = np.arange(len(datos_actividad), len(datos_actividad) + 3).reshape(-1, 1)
        predicciones = model.predict(X_future)
        
        # Crear fechas futuras
        ultima_fecha = datos_actividad['Mes'].max()
        fechas_futuras = pd.date_range(
            start=ultima_fecha + pd.DateOffset(months=1),
            periods=3,
            freq='MS'
        )
        
        # Crear DataFrame para gráfico
        df_historico = pd.DataFrame({
            'Fecha': datos_actividad['Mes'],
            'Precio': datos_actividad['Precio'],
            'Tipo': 'Histórico'
        })
        
        df_prediccion = pd.DataFrame({
            'Fecha': fechas_futuras,
            'Precio': predicciones,
            'Tipo': 'Predicción'
        })
        
        df_completo = pd.concat([df_historico, df_prediccion])
        
        # Graficar
        fig5, ax5 = plt.subplots(figsize=(10, 5))
        sns.lineplot(data=df_completo, x='Fecha', y='Precio', hue='Tipo', style='Tipo', 
                    markers=True, dashes=False, ax=ax5)
        ax5.set_title(f'Predicción de Ingresos para {actividad_seleccionada}')
        ax5.set_ylabel('Ingresos (€)')
        ax5.grid(True)
        plt.xticks(rotation=45)
        st.pyplot(fig5)
        
        # Mostrar tabla de predicciones
        st.subheader("Detalles de Predicción")
        df_pred_detalle = df_prediccion.copy()
        df_pred_detalle['Mes'] = df_pred_detalle['Fecha'].dt.strftime('%B %Y')
        st.dataframe(df_pred_detalle[['Mes', 'Precio']].rename(columns={'Precio': 'Ingresos Predichos (€)'}))
    else:
        st.warning("Se necesitan más datos para generar predicciones para esta actividad")

def generar_tendencias_edad(df):
    """Genera gráfico de tendencias por edad"""
    if df.empty:
        st.warning("No hay datos para generar tendencias por edad")
        return
    
    st.subheader("Tendencias por Edad")
    fig6, ax6 = plt.subplots()
    sns.boxplot(
        data=df, 
        x='Grupo Edad', 
        y='Ingresos por Persona', 
        hue='Sexo',
        ax=ax6
    )
    ax6.set_title('Ingresos por Persona según Grupo de Edad y Sexo')
    ax6.set_xlabel('Grupo de Edad')
    ax6.set_ylabel('Ingresos por Persona (€)')
    st.pyplot(fig6)

def generar_reportes():
    """Función principal para generar todos los reportes"""
    clientes_df = cargar_clientes()
    
    if not clientes_df.empty:
        clientes_procesados = procesar_datos_clientes(clientes_df)
        st.subheader("Datos de Clientes")
        st.dataframe(clientes_procesados)
        
        st.header("📅 Análisis Temporal por Fecha de Actividad")
        generar_graficos_temporales(clientes_procesados)
        
        generar_graficos_demograficos(clientes_procesados)
        
        generar_predicciones(clientes_procesados)
        
        generar_tendencias_edad(clientes_procesados)
    else:
        st.info("No hay datos de clientes disponibles. Ingrese datos en la pestaña 'Ingresar Datos de Clientes'")