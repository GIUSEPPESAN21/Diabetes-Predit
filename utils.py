# -*- coding: utf-8 -*-
from fpdf import FPDF
from datetime import datetime
import plotly.graph_objects as go

# --- CLASE PARA GENERACIÓN DE PDF ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Reporte de Riesgo de Diabetes', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(4)

    def chapter_body(self, body):
        self.set_font('Arial', '', 11)
        # Codificar el texto para FPDF que usa 'latin-1'
        body_encoded = body.encode('latin-1', 'replace').decode('latin-1')
        self.multi_cell(0, 6, body_encoded)
        self.ln()

def generar_pdf(datos_reporte):
    pdf = PDF()
    pdf.add_page()
    
    pdf.chapter_title('1. Datos del Paciente')
    fecha_reporte = datetime.now().strftime('%d/%m/%Y')
    info_paciente = (f"Fecha del reporte: {fecha_reporte}\n"
                     f"Edad: {datos_reporte['edad']} años\n"
                     f"Sexo: {datos_reporte['sexo']}\n"
                     f"IMC (Índice de Masa Corporal): {datos_reporte['imc']:.2f}\n"
                     f"Perímetro de cintura: {datos_reporte['cintura']} cm")
    pdf.chapter_body(info_paciente)
    
    pdf.chapter_title('2. Resultados del Cuestionario FINDRISC')
    resultados = (f"Puntaje Total: {datos_reporte['puntaje']} puntos\n"
                  f"Nivel de Riesgo: {datos_reporte['nivel_riesgo']}\n"
                  f"Estimación a 10 años: {datos_reporte['estimacion']}")
    pdf.chapter_body(resultados)
    
    pdf.chapter_title('3. Análisis y Recomendaciones por IA (Gemini)')
    pdf.chapter_body(datos_reporte['analisis_ia'])
    
    pdf.set_y(-40)
    pdf.set_font('Arial', 'I', 9)
    autor_info = ("Software desarrollado por:\n"
                  "Joseph Javier Sánchez Acuña: Ingeniero Industrial, Desarrollador de Aplicaciones Clínicas, Experto en Inteligencia Artificial.\n"
                  "Contacto: joseph.sanchez@uniminuto.edu.co")
    pdf.multi_cell(0, 5, autor_info, 0, 'C')
    
    return pdf.output(dest='S').encode('latin-1')


# --- FUNCIONES DE CÁLCULO ---
def calcular_puntaje_findrisc(edad, imc, cintura, sexo, actividad, frutas_verduras, hipertension, glucosa_alta, familiar_diabetes):
    score = 0
    if 45 <= edad <= 54: score += 2
    elif 55 <= edad <= 64: score += 3
    elif edad > 64: score += 4
    if 25 <= imc < 30: score += 1
    elif imc >= 30: score += 3
    if sexo == "Masculino":
        if 94 <= cintura <= 102: score += 3
        elif cintura > 102: score += 4
    elif sexo == "Femenino":
        if 80 <= cintura <= 88: score += 3
        elif cintura > 88: score += 4
    if actividad == "No": score += 2
    if frutas_verduras == "No todos los días": score += 1
    if hipertension == "Sí": score += 2
    if glucosa_alta == "Sí": score += 5
    if familiar_diabetes == "Sí: padres, hermanos o hijos": score += 5
    elif familiar_diabetes == "Sí: abuelos, tíos o primos": score += 3
    return score

def obtener_interpretacion_riesgo(score):
    if score < 7: return "Riesgo bajo", "1 de cada 100 personas desarrollará diabetes."
    elif 7 <= score <= 11: return "Riesgo ligeramente elevado", "1 de cada 25 personas desarrollará diabetes."
    elif 12 <= score <= 14: return "Riesgo moderado", "1 de cada 6 personas desarrollará diabetes."
    elif 15 <= score <= 20: return "Riesgo alto", "1 de cada 3 personas desarrollará diabetes."
    else: return "Riesgo muy alto", "1 de cada 2 personas desarrollará diabetes."

# --- FUNCIÓN DE GRÁFICO ---
def generar_grafico_riesgo(score):
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=score, domain={'x': [0, 1], 'y': [0, 1]}, title={'text': "<b>Nivel de Riesgo de Diabetes</b>"},
        gauge={'axis': {'range': [0, 25], 'tickwidth': 1, 'tickcolor': "darkblue"}, 'bar': {'color': "rgba(0,0,0,0.4)"}, 'bgcolor': "white", 'borderwidth': 2, 'bordercolor': "#cccccc",
               'steps': [{'range': [0, 6], 'color': '#28a745'}, {'range': [7, 11], 'color': '#a3d900'}, {'range': [12, 14], 'color': '#ffc107'}, {'range': [15, 20], 'color': '#fd7e14'}, {'range': [21, 25], 'color': '#dc3545'}],
               'threshold': {'line': {'color': "black", 'width': 4}, 'thickness': 0.85, 'value': score}}))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font={'color': "#333333", 'family': "Arial"})
    return fig
