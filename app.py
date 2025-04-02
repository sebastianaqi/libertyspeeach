from docx import Document
from langchain_openai import ChatOpenAI
import pandas as pd
import numpy as np
import os
from openai import OpenAI
import streamlit as st
from tools.tratamientos import text_to_word
from langchain.agents.agent_types import AgentType
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent


# Título del aplicativo
st.set_page_config(page_title="Consulta Speeach Liberty", layout="centered", )
st.title('Consulta Speeach Liberty')


# Cargar datos
df_global:pd.DataFrame = pd.read_pickle("./data/df_fin_streamlit.pkl")
st.sidebar.title("Filtros")
fecha_minima = df_global['DATE'].min()
fecha_max = df_global['DATE'].max()
fecha_seleccionada = st.sidebar.date_input(
    "Selecciona una fecha", 
    min_value= fecha_minima,
    max_value= fecha_max,
    value=fecha_minima
)


opciones_linea = df_global['SERVICE_LINE'].dropna().unique().tolist()
linea_seleccionada = st.sidebar.selectbox("Selecciona una línea de servicio", opciones_linea)


if "df" not in st.session_state:
    st.session_state.df = None

if st.sidebar.button("Aplicar Filtro"):
    fecha = fecha_seleccionada.strftime('%Y-%m-%d')
    with st.spinner("Cargando datos..."):
        df:pd.DataFrame = df_global[df_global['SERVICE_LINE'] == linea_seleccionada]
        df['DATE'] = pd.to_datetime(df['DATE'])
        df = df[df['DATE'] >=  pd.Timestamp(fecha)]
        st.session_state.df = df
    st.success("Datos cargados correctamente")
if st.session_state.df is not None:
    st.dataframe(st.session_state.df)
else:
    st.info("Selecciona una fecha y haz clic en 'Aplicar Filtro'")




ini_promp = """
Eres un analista experto en comportamiento del cliente y redacción de reportes ejecutivos.
Tengo las siguientes transcripciones de llamadas realizadas a clientes como parte de una campaña de renovación con la empresa Mas Móvil. Esta campaña está pasando por una crisis y necesito un análisis detallado.
Por favor, analiza el contenido de las conversaciones con los siguientes elementos:
"""

fin_promp = """
Redacta el contenido en un estilo claro, profesional y orientado a toma de decisiones, usando títulos y subtítulos tipo Markdown.
 **reporte en formato tipo Markdown**
"""



prompt_default = f"""
1. **Resumen ejecutivo:** visión general de la situación encontrada en las llamadas.
2. **Causas frecuentes de no venta:** razones mencionadas o inferidas por las que el cliente no renovó el servicio.
3. **Motivos de venta exitosa:** factores que influyeron en los casos donde sí se logró la renovación.
4. **Disgustos frecuentes del cliente:** quejas, molestias o incomodidades manifestadas.
5. **Problemas detectados en la operación o gestión del servicio:** errores comunes, fallas del sistema, problemas del agente u oferta.
6. **Recomendaciones para mejorar la tasa de renovación.**
"""





# Sección para generar reporte
st.markdown("---")
st.subheader("Generar reporte")

texto_reporte = st.text_area("Escribe tu consulta aquí:", 
                             value= ini_promp+ "\n\n"+ prompt_default, height= 500)
if st.button(key="reporte", label= "generar reporte")  and st.session_state.df is not None:
    
    new_text =  ini_promp + "\n" + texto_reporte + "\n" + fin_promp

    df_aux = st.session_state.df 
    sample_transcripts = df_aux['TRANSCRIPT'].dropna().sample(len(df_aux)).tolist()    
    joined_transcripts = "\n\n".join(sample_transcripts)
        
    if len(joined_transcripts) > 200000:
        joined_transcripts = joined_transcripts[0:200000]
    
    prompt2 = f"""
    Transcripciones:\n
    {joined_transcripts}
    """

    client = OpenAI()
    completion = client.chat.completions.create(
        model="gpt-4o-mini",  # o "gpt-3.5-turbo"
        messages=[
            {"role": "user", "content": new_text + "\n" + prompt2 }
        ],
        temperature=0.3
    )
    
    text_to_word(text= completion.choices[0].message.content ,output_filename = "renovacion23.docx" )
    with open("renovacion23.docx", "rb") as file:
        st.download_button(
            label="Descargar reporte",
            data=file,
            file_name="reporte_renovacion.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )




# Entrada de texto para la consulta
st.markdown("---")
st.subheader("Consulta sobre el DataFrame")
pregunta_usuario = st.text_area("Haz una pregunta sobre los datos cargados")

if st.button("Consultar agente") and st.session_state.df is not None:
    with st.spinner("Consultando al agente..."):
        df = st.session_state.df

        # Crear el agente
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        agent = create_pandas_dataframe_agent(
            llm=llm,
            df=df,
            verbose=False,
            agent_type=AgentType.OPENAI_FUNCTIONS,
            handle_parsing_errors=True,
            allow_dangerous_code=True,
            max_iterations=10
        )

        # Ejecutar consulta
        try:
            respuesta = agent.run(pregunta_usuario)
            st.markdown("### Respuesta del agente")
            st.write(respuesta)
        except Exception as e:
            st.error(f"Error al procesar la consulta: {str(e)}")
else:
    st.info("Escribe tu pregunta y asegúrate de haber cargado datos con 'Aplicar Filtro'")



# Entrada de texto para enviar consulta
# st.markdown("---")
# st.subheader("Consulta personalizada")
# texto_usuario = st.text_area("Escribe tu consulta aquí:")

# if st.button("Enviar Consulta") and st.session_state.df is not None:
#     st.write("Texto recibido:", texto_usuario)
#     # Aquí puedes agregar la lógica para enviar este texto a tu backend o modelo
#     import pandas as pd
#     import lotus
#     from lotus.models import SentenceTransformersRM, LM
#     # Configurar los modelos
#     lm = LM(model="gpt-4o-mini")  # o "gpt-3.5-turbo"
#     rm = SentenceTransformersRM(model="intfloat/e5-base-v2")

#     lotus.settings.configure(lm=lm, rm=rm)

#     # Cargar tus datos (asegúrate que la columna se llame 'transcripcion')
#     df = st.session_state.df
#     df2 = df.dropna(subset=["TRANSCRIPT"])

#     # Aplicar filtro semántico: solo llamadas con sentimiento negativo
#     llamadas_negativas = df2.sem_filter(
#         "{TRANSCRIPT}" + texto_usuario
#     )
#     st.dataframe(llamadas_negativas)