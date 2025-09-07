import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# Configuración de la página
st.set_page_config(page_title="Gastos Regionales Atacama", layout="wide")

st.title("Visualización de gastos de consejeros regionales - Región de Atacama")

# Se consume la API y guardamos la data en Cache para no estar consultando el API a cada selección
@st.cache_data
def cargar_datos():
    url = "https://datos.gob.cl/api/3/action/datastore_search"
    params = {
        "resource_id": "997347fc-feca-49ef-9888-e223e0fa12d6",
        "limit": 1000000
    }
    resp  = requests.get(url, params = params ) 
    records  = resp.json()["result"]["records"]
    df = pd.DataFrame( records)
    return df

df =  cargar_datos()

###Aseguramos que la data sea correcta para poder ser calculada 
df = df[df["GASTO TOTAL CONSEJERO"].notnull()]
df = df[df["GASTO TOTAL CONSEJERO"] != "GASTO TOTAL CONSEJERO"]
df["GASTO TOTAL CONSEJERO"] = (
    df["GASTO TOTAL CONSEJERO"]
    .str.replace(".", "", regex=False)
    .str.replace(",", ".", regex=False)
    .astype(float)
)

#### Limpiamos datos ya que vienen  gastos comunes como nombres de consejeros y el total tambien como nombre de consejero
patron_invalidos = r"(TOTAL|GASTOS COMUNES)"
df_invalidos = df[df["NOMBRE CONSEJERO"].str.upper().str.contains(patron_invalidos)]
df_validos = df[~df["NOMBRE CONSEJERO"].str.upper().str.contains(patron_invalidos)]

##### sacamos los Totales !!!!!!!
gasto_valido_total = df_validos["GASTO TOTAL CONSEJERO"].sum()
gasto_comunes = df_invalidos[df_invalidos["NOMBRE CONSEJERO"].str.upper() == "GASTOS COMUNES"]["GASTO TOTAL CONSEJERO"].sum()
gasto_total_registro = df_invalidos[df_invalidos["NOMBRE CONSEJERO"].str.upper() == "TOTAL"]["GASTO TOTAL CONSEJERO"].sum()



# generamos el selector en la web
opcion = st.selectbox("Selecciona el tipo de gráfico", ["Por consejeros", "Distribución del total de gastos generados"])
###### Nos permite indicar cual grafico mostrar 
### Gráfico de barras
if opcion == "Por consejeros":
    gastos_por_consejero = (
        df_validos.groupby("NOMBRE CONSEJERO")["GASTO TOTAL CONSEJERO"]
        .sum()
        .sort_values(ascending=False)
    )

    fig, ax = plt.subplots(figsize=(12, 6))
    gastos_por_consejero.plot(kind="bar", color="steelblue", ax=ax)
    ax.set_title("Gasto total por consejero regional (Región de Atacama)")
    ax.set_ylabel("Gasto CLP")
    ax.set_xlabel("Consejero")
    ax.set_xticklabels(gastos_por_consejero.index, rotation=45, ha="right")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}".replace(",", ".")))
    ax.grid(axis="y", linestyle="--", alpha=0.7)
    st.pyplot(fig)

#### Gráfico circular
elif opcion == "Distribución del total de gastos generados":
    labels = ["Gastos Consejeros", "Gastos comunes CORE"]
    values = [gasto_valido_total, gasto_comunes]
    colors = ["steelblue", "orange"]

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(
        values,
        labels=labels,
        colors=colors,
        autopct=lambda p: f"{p:.1f}%\n{int(p * sum(values) / 100):,}".replace(",", "."),
        startangle=90
    )
    ax.set_title("Distribución del gasto total: Consejeros vs Gastos Comunes")
    st.pyplot(fig)

  # Nos aseguramos que los valores mostrados sean visualmente entendible para los usuarios de Chile 
with st.expander("Auditoría de totales"):
    st.write(f"- Gasto total de consejeros: **{int(gasto_valido_total):,} CLP**".replace(",", "."))
    st.write(f"- Gasto declarado como 'GASTOS COMUNES': **{int(gasto_comunes):,} CLP**".replace(",", "."))
    st.write(f"- 'TOTAL de Gastos': **{int(gasto_total_registro):,} CLP**".replace(",", "."))