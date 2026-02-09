import matplotlib.pyplot as plt
import base64
from io import BytesIO
import seaborn as sns

def get_graph():
    buffer = BytesIO()
    # bbox_inches='tight' recorta los márgenes blancos sobrantes
    plt.savefig(buffer, format='png', bbox_inches='tight')
    buffer.seek(0)
    image_png = buffer.getvalue()
    graph = base64.b64encode(image_png)
    graph = graph.decode('utf-8')
    buffer.close()
    return graph

def get_plot(x, y, title, xlabel, ylabel, plot_type='bar', color='viridis'):
    plt.switch_backend('AGG') # Motor gráfico sin interfaz (necesario para Django)
    
    # Ajustamos el tamaño según el tipo de gráfico
    if plot_type == 'pie':
         plt.figure(figsize=(8, 6))
    else:
         plt.figure(figsize=(10, 5))
    
    if plot_type == 'bar':
        # Gráfico de Barras (Usamos Seaborn)
        # hue=x evita advertencias futuras de la librería
        sns.barplot(x=x, y=y, palette=color, hue=x, legend=False)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        
    elif plot_type == 'pie':
        # --- SOLUCIÓN DE COLORES ---
        # Definimos una lista manual de colores que contrastan mucho entre sí
        # [Azul fuerte, Naranja, Verde, Rojo, Morado, Café, Rosa, Gris]
        colores_contrastados = ['#3B82F6', '#F59E0B', '#10B981', '#EF4444', '#8B5CF6', '#D97706', '#EC4899', '#6B7280']
        
        plt.pie(x, 
                labels=y, 
                autopct='%1.1f%%', 
                colors=colores_contrastados, # <--- Aquí aplicamos los colores fijos
                startangle=140,
                wedgeprops={'edgecolor': 'white', 'linewidth': 1}) # Borde blanco elegante

    plt.title(title, fontsize=14, fontweight='bold', pad=20)
    plt.tight_layout()
    
    graph = get_graph()
    plt.close() # Cerramos la figura para liberar memoria
    return graph