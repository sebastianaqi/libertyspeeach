from docx import Document
import streamlit as st
import pandas as pd
import numpy as np
from tools.consultas import ejecutar_consulta_segura, ENGINE_DS
import os
from openai import OpenAI
import pandas as pd



def text_to_word(text, output_filename="output.docx"):
    doc = Document()
    lines = text.split("\n")
    
    for line in lines:
        stripped = line.strip()

        if stripped.startswith("# "):  # Encabezado nivel 1
            doc.add_heading(stripped[2:].replace("**", ""), level=1)
        elif stripped.startswith("## "):  # Encabezado nivel 2
            doc.add_heading(stripped[3:].replace("**", ""), level=2)
        elif stripped.startswith("### "):  # Encabezado nivel 3
            doc.add_heading(stripped[4:].replace("**", ""), level=3)
        elif stripped.startswith("- "):  # Lista
            doc.add_paragraph(stripped[2:].replace("**", ""), style="List Bullet")
        elif stripped.startswith("**") and stripped.endswith("**"):  # Negrita
            paragraph = doc.add_paragraph()
            run = paragraph.add_run(stripped[2:-2])
            run.bold = True
        elif stripped.startswith("```"):  # Bloque de código
            continue  # Podrías agregar soporte para bloques si lo deseas
        elif stripped:
            doc.add_paragraph(stripped.replace("**", ""))
    
    doc.save(output_filename)
    print(f"✅ Documento guardado como {output_filename}")

print(f"ESTA ES LA RUTA {os.getcwd()} "  )
# Título del aplicativo
st.set_page_config(page_title="Consulta Speeach Liberty renovaciones", layout="wide")
st.title('Consulta Speeach Liberty renovaciones')

st.sidebar.title("Filtros")
fecha_seleccionada = st.sidebar.date_input("Selecciona una fecha", pd.to_datetime("2025-03-01"))
fecha_seleccionada = pd.to_datetime(fecha_seleccionada)  # Asegura datetime completo

if "df" not in st.session_state:
    st.session_state.df = None

if st.sidebar.button("Aplicar Filtro"):
    #import lotus
    #from lotus.models import SentenceTransformersRM, LM

    fecha = fecha_seleccionada.strftime('%Y-%m-%d')
    print(fecha)
    query = f'''
    SELECT * FROM [DS].[dbo].[tbl_Speech_resumen_call] 
    WHERE [CAMPAIGN] ='LIBERTY' 
    AND TRY_CONVERT(date, [DATE]) >= '{fecha}' 
    AND [SERVICE_LINE] = 'Renovaciones'
    '''

    with st.spinner("Cargando datos..."):
        #st.session_state.df = ejecutar_consulta_segura(query=query, engine=ENGINE_DS)
        df:pd.DataFrame = pd.read_pickle("./data/tabla_speeach_liberty.pkl")
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
Por favor, analiza el contenido de las conversaciones y genera un **reporte en formato tipo Markdown** con los siguientes elementos:
"""

fin_promp = """
Redacta el contenido en un estilo claro, profesional y orientado a toma de decisiones, usando títulos y subtítulos tipo Markdown.
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
texto_reporte = st.text_area("Escribe tu consulta aquí:", value=prompt_default, height= 500)
if st.button(key="reporte", label= "generar reporte")  and st.session_state.df is not None:
    
    new_text =  ini_promp + "\n" + texto_reporte + "\n" + fin_promp
    print(new_text)
    df_aux = st.session_state.df 
    if len(df_aux) >= 100:
        sample_transcripts = df_aux['TRANSCRIPT'].dropna().sample(100).tolist()
    else: 
        sample_transcripts = df_aux['TRANSCRIPT'].dropna().sample(len(df_aux)).tolist()
    
    joined_transcripts = "\n\n".join(sample_transcripts)
    joined_transcripts = joined_transcripts[0:2000]
    prompt2 = f"""
    Transcripciones:\n
    {joined_transcripts}
    """
    print( new_text + "\n" + prompt2)
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








# Entrada de texto para enviar consulta
st.markdown("---")
st.subheader("Consulta personalizada")
texto_usuario = st.text_area("Escribe tu consulta aquí:")

if st.button("Enviar Consulta") and st.session_state.df is not None:
    st.write("Texto recibido:", texto_usuario)
    # Aquí puedes agregar la lógica para enviar este texto a tu backend o modelo
    import pandas as pd
    import lotus
    from lotus.models import SentenceTransformersRM, LM
    # Configurar los modelos
    lm = LM(model="gpt-4o-mini")  # o "gpt-3.5-turbo"
    rm = SentenceTransformersRM(model="intfloat/e5-base-v2")

    lotus.settings.configure(lm=lm, rm=rm)

    # Cargar tus datos (asegúrate que la columna se llame 'transcripcion')
    df = st.session_state.df
    df2 = df.dropna(subset=["TRANSCRIPT"])

    # Aplicar filtro semántico: solo llamadas con sentimiento negativo
    llamadas_negativas = df2.sem_filter(
        "{TRANSCRIPT}" + texto_usuario
    )
    st.dataframe(llamadas_negativas)