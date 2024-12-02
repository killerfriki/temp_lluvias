import requests
import pdfplumber
import pandas as pd
from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import io
import os


# Base URLs para los archivos PDF de lluvias y temperaturas máximas
url_base_rainfall = "https://smn.conagua.gob.mx/tools/DATA/Climatolog%C3%ADa/Pron%C3%B3stico%20clim%C3%A1tico/Temperatura%20y%20Lluvia/PREC/"
url_base_temp = "https://smn.conagua.gob.mx/tools/DATA/Climatolog%C3%ADa/Pron%C3%B3stico%20clim%C3%A1tico/Temperatura%20y%20Lluvia/TMAX/"

# Lista de estados con nombres compuestos
composite_states = [
    "Baja California", "Ciudad de México", "Estado de México", "San Luis Potosí",
    "Baja California Sur", "Nuevo León", "Quintana Roo"
]

# Función para obtener y procesar datos desde los PDFs
def obtener_datos_pronostico(url_base):
    all_data = []
    for year in range(2000, 2025):
        # Generar URL y realizar la solicitud GET
        url = f"{url_base}{year}.pdf"
        response = requests.get(url)
        if response.status_code == 200:
            with pdfplumber.open(io.BytesIO(response.content)) as pdf:
                page = pdf.pages[0]
                text = page.extract_text()
                lines = text.split('\n')
                for line in lines:
                    if any(char.isdigit() for char in line):
                        row = line.split()
                        if len(row) == 14:
                            row.append(year)
                            all_data.append(row)
                        elif len(row) > 14:
                            estado = " ".join(row[:2])
                            if estado in composite_states:
                                row = [estado] + row[2:]
                            else:
                                estado = " ".join(row[:3])
                                row = [estado] + row[3:]
                            row.append(year)
                            if len(row) == 15:
                                all_data.append(row)

    columns = ["Estado", "Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic", "Anual", "Año"]
    df = pd.DataFrame(all_data, columns=columns)
    for col in columns[1:-1]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df.loc[df['Año'] == 2024, ['Nov', 'Dic']] = None
    return df

# Obtener datos de lluvias y temperaturas
df_rainfall = obtener_datos_pronostico(url_base_rainfall)
df_temp = obtener_datos_pronostico(url_base_temp)

# Preparar datos de lluvias para Ciudad de México
df_CDMX_rain = df_rainfall[df_rainfall['Estado'] == 'Ciudad de México']
df_CDMX_rain = df_CDMX_rain.drop(columns=['Anual', 'Estado'], errors='ignore')
df_CDMX_rain_long = df_CDMX_rain.melt(id_vars=['Año'], var_name='Mes', value_name='Cantidad de Lluvia')

# Agregar datos de noviembre y diciembre como promedio histórico
meses_numericos = {'Ene': 1, 'Feb': 2, 'Mar': 3, 'Abr': 4, 'May': 5, 'Jun': 6, 'Jul': 7, 'Ago': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dic': 12}
nov_avg_rain = df_CDMX_rain_long[(df_CDMX_rain_long['Mes'] == 'Nov') & (df_CDMX_rain_long['Año'] < 2024)]['Cantidad de Lluvia'].mean()
dic_avg_rain = df_CDMX_rain_long[(df_CDMX_rain_long['Mes'] == 'Dic') & (df_CDMX_rain_long['Año'] < 2024)]['Cantidad de Lluvia'].mean()
df_CDMX_rain_long = pd.concat([df_CDMX_rain_long, pd.DataFrame({'Año': [2024, 2024], 'Mes': ['Nov', 'Dic'], 'Cantidad de Lluvia': [nov_avg_rain, dic_avg_rain]})], ignore_index=True)

# Agregar nuevos datos de lluvias para 2024
df_2024_new_rain = pd.DataFrame({
    'Año': [2024] * 10, 
    'Mes': ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct'], 
    'Cantidad de Lluvia': [0.5, 13.2, 0.1, 9.1, 34.6, 104.4, 145.8, 234.6, 159.6, 45.5]
})
df_CDMX_rain_long = pd.concat([df_CDMX_rain_long, df_2024_new_rain], ignore_index=True)
df_CDMX_rain_long['Mes_Num'] = df_CDMX_rain_long['Mes'].map(meses_numericos)

# Preparar datos de temperaturas máximas para Ciudad de México
df_CDMX_temp = df_temp[df_temp['Estado'] == 'Ciudad de México']
df_CDMX_temp = df_CDMX_temp.drop(columns=['Anual', 'Estado'], errors='ignore')
df_CDMX_temp_long = df_CDMX_temp.melt(id_vars=['Año'], var_name='Mes', value_name='Temperatura Máxima')

# Agregar datos de noviembre y diciembre como promedio histórico
nov_avg_temp = df_CDMX_temp_long[(df_CDMX_temp_long['Mes'] == 'Nov') & (df_CDMX_temp_long['Año'] < 2024)]['Temperatura Máxima'].mean()
dic_avg_temp = df_CDMX_temp_long[(df_CDMX_temp_long['Mes'] == 'Dic') & (df_CDMX_temp_long['Año'] < 2024)]['Temperatura Máxima'].mean()
df_CDMX_temp_long = pd.concat([df_CDMX_temp_long, pd.DataFrame({'Año': [2024, 2024], 'Mes': ['Nov', 'Dic'], 'Temperatura Máxima': [nov_avg_temp, dic_avg_temp]})], ignore_index=True)

# Agregar nuevos datos de temperaturas máximas para 2024
df_2024_new_temp = pd.DataFrame({
    'Año': [2024] * 10, 
    'Mes': ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct'], 
    'Temperatura Máxima': [23.6, 25.6, 28.4, 28.4, 31.1, 32.8, 24.7, 25.2, 24.3, 22.4]
})
df_CDMX_temp_long = pd.concat([df_CDMX_temp_long, df_2024_new_temp], ignore_index=True)
df_CDMX_temp_long['Mes_Num'] = df_CDMX_temp_long['Mes'].map(meses_numericos)

# Crear la aplicación Dash
app = Dash(__name__)
app.layout = html.Div([
    html.H1("Dashboard de Clima en Ciudad de México"),
    dcc.Dropdown(
        id='year-dropdown',
        options=[{'label': str(year), 'value': year} for year in sorted(df_CDMX_rain_long['Año'].unique())],
        value=sorted(df_CDMX_rain_long['Año'].unique()),
        multi=True,
        placeholder="Seleccione los años a visualizar"
    ),
    dcc.Graph(id='rainfall-graph'),
    dcc.Graph(id='temperature-graph')
])

# Callback para actualizar gráficos
@app.callback(
    [Output('rainfall-graph', 'figure'),
     Output('temperature-graph', 'figure')],
    Input('year-dropdown', 'value')
)
def update_graphs(selected_years):
    # Filtrar datos
    rain_filtered = df_CDMX_rain_long[df_CDMX_rain_long['Año'].isin(selected_years)]
    temp_filtered = df_CDMX_temp_long[df_CDMX_temp_long['Año'].isin(selected_years)]

    # Gráfico de lluvias
    rain_fig = px.line(
        rain_filtered, 
        x='Mes_Num', 
        y='Cantidad de Lluvia', 
        color='Año', 
        labels={'Mes_Num': 'Mes', 'Cantidad de Lluvia': 'Cantidad de Lluvia (mm)'},
        title="Registro de Lluvias Mensuales"
    )
    rain_fig.update_xaxes(tickvals=list(meses_numericos.values()), ticktext=list(meses_numericos.keys()))
    rain_fig.update_layout(xaxis_title="Mes", yaxis_title="Cantidad de Lluvia (mm)")

    # Gráfico de temperaturas
    temp_fig = px.line(
        temp_filtered, 
        x='Mes_Num', 
        y='Temperatura Máxima', 
        color='Año', 
        labels={'Mes_Num': 'Mes', 'Temperatura Máxima': 'Temperatura Máxima (°C)'},
        title="Registro de Temperaturas Máximas Mensuales"
    )
    temp_fig.update_xaxes(tickvals=list(meses_numericos.values()), ticktext=list(meses_numericos.keys()))
    temp_fig.update_layout(xaxis_title="Mes", yaxis_title="Temperatura Máxima (°C)")

    return rain_fig, temp_fig

if __name__ == '__main__':
    # Usa el puerto proporcionado por Render, o 8050 si no está disponible
    app.run_server(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8050)))
