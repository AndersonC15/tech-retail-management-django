import pandas as pd
from django.shortcuts import render
from pymongo import MongoClient
from .utils import get_plot

from inventario.models import Producto, Sucursal 

def dashboard_ventas(request):

    # 1. OBTENER DATOS DE MONGODB (Ventas Históricas)
    client = MongoClient('mongodb://localhost:27017/')
    db = client['nextgen_ventas'] 
    collection = db['ventas']
    
    # Traemos todas las ventas
    ventas_mongo = list(collection.find())
    
    # Convertimos a DataFrame
    df_ventas = pd.DataFrame(ventas_mongo)
    
    # 2. PROCESAMIENTO DE DATOS (PANDAS)
    grafica_productos = None
    grafica_clientes = None
    grafica_sucursales = None
    
    tabla_top_sucursal = [] 
    
    if not df_ventas.empty:
        lista_procesada = []
        for venta in ventas_mongo:
            # Intentamos obtener el nombre de la sucursal. 
            sucursal_data = venta.get('sucursal', 'Desconocida')
            if isinstance(sucursal_data, dict):
                sucursal_nombre = sucursal_data.get('nombre', 'Desconocida')
            else:
                sucursal_nombre = str(sucursal_data)

            cliente_nombre = venta.get('cliente', 'Anónimo')
            
            # Procesamos los items
            for item in venta.get('items', []):
                lista_procesada.append({
                    'sucursal': sucursal_nombre,
                    'cliente': cliente_nombre,
                    'producto': item.get('nombre', 'Producto X'),
                    'cantidad': int(item.get('cantidad', 1)),
                    'subtotal': float(item.get('subtotal', 0))
                })
        
        df_items = pd.DataFrame(lista_procesada)

        if not df_items.empty:
            # 1. Top Productos Globales
            top_prod = df_items.groupby('producto')['cantidad'].sum().nlargest(5).reset_index()
            grafica_productos = get_plot(top_prod['cantidad'], top_prod['producto'], 
                                        'Top 5 Productos Globales', 'Cantidad', '', 'bar', 'viridis')

            # 2. Top Clientes
            # Aseguramos que 'total' sea numérico
            if 'total' in df_ventas.columns:
                df_ventas['total'] = pd.to_numeric(df_ventas['total'], errors='coerce').fillna(0)
                top_cli = df_ventas.groupby('cliente')['total'].sum().nlargest(5).reset_index()
                grafica_clientes = get_plot(top_cli['total'], top_cli['cliente'], 
                                            'Mejores Clientes ($)', 'Total Gastado', '', 'bar', 'magma')

            # 3. Ventas por Sucursal
            ventas_suc = df_items.groupby('sucursal')['subtotal'].sum().reset_index()
            grafica_sucursales = get_plot(ventas_suc['subtotal'], ventas_suc['sucursal'], 
                                          'Ingresos por Sucursal', '', '', 'pie')

            # --- TABLA: PRODUCTO MÁS VENDIDO POR SUCURSAL ---
            grp_suc_prod = df_items.groupby(['sucursal', 'producto'])['cantidad'].sum().reset_index()
            grp_suc_prod = grp_suc_prod.sort_values(['sucursal', 'cantidad'], ascending=[True, False])
            top_por_sucursal = grp_suc_prod.groupby('sucursal').head(1)
            tabla_top_sucursal = top_por_sucursal.to_dict('records')

    # ---------------------------------------------------------
    # 3. OBTENER DATOS DE MYSQL (Stock en Tiempo Real)
    # ---------------------------------------------------------
    # Buscamos productos con stock 0
        productos_sin_stock = Producto.objects.filter(stock=0).select_related('id_marca')    
    # ---------------------------------------------------------
    # 4. CONTEXTO Y RENDER
    # ---------------------------------------------------------
    context = {
        'grafica_productos': grafica_productos,
        'grafica_clientes': grafica_clientes,
        'grafica_sucursales': grafica_sucursales,
        'tabla_top_sucursal': tabla_top_sucursal,
        'productos_sin_stock': productos_sin_stock,
    }

    return render(request, 'dashboard.html', context)