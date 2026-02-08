import json
import datetime
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt 

# --- CAMBIO IMPORTANTE: Importamos desde 'inventario.models' ---
from inventario.models import Producto, Sucursal, Empleado 
from .db_mongo import get_db_handle 

def nueva_venta(request):
    if request.method == 'GET':
        # Carga los datos para los SELECTS del HTML
        context = {
            'empleados': Empleado.objects.all(),
            'sucursales': Sucursal.objects.all(),
            # Usamos select_related con los nombres exactos que tienes en models.py (id_marca, id_categoria)
            'productos': Producto.objects.select_related('id_marca', 'id_categoria').filter(stock__gt=0),
        }
        return render(request, 'formulario_venta.html', context)

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            id_sucursal = data.get('id_sucursal')
            items = data.get('items', [])
            
            if not items:
                return JsonResponse({'error': 'El carrito está vacío'}, status=400)

            total_venta = 0
            productos_para_actualizar = []
            items_detalle = []

            # --- Lógica de Validación y Cálculo ---
            for item in items:
                prod_id = item['id_producto']
                cantidad_solicitada = int(item['cantidad'])
                
                # Buscamos el producto
                producto = Producto.objects.get(pk=prod_id)
                
                if producto.stock < cantidad_solicitada:
                    return JsonResponse({
                        'error': f'Stock insuficiente para {producto.nombre}. Disponibles: {producto.stock}'
                    }, status=400)
                
                # Descontar stock (en memoria)
                producto.stock -= cantidad_solicitada
                productos_para_actualizar.append(producto)
                
                # Calcular subtotal
                # Aseguramos que sea float para evitar error de tipos
                precio_float = float(producto.precio_unitario) if producto.precio_unitario else 0.0
                subtotal = precio_float * cantidad_solicitada
                total_venta += subtotal
                
                # --- Construcción del Item para Mongo ---
                # NOTA: Según tu models.py, las relaciones se llaman id_marca e id_categoria
                # y sus nombres son nombre_marca y nombre_categoria
                nombre_marca = producto.id_marca.nombre_marca if producto.id_marca else "Sin Marca"
                nombre_categoria = producto.id_categoria.nombre_categoria if producto.id_categoria else "Sin Categoria"

                items_detalle.append({
                    "id_producto_mysql": producto.id_producto,
                    "nombre": producto.nombre,
                    "marca": nombre_marca,
                    "categoria": nombre_categoria, 
                    "cantidad": cantidad_solicitada,
                    "precio_unitario": precio_float,
                    "subtotal": subtotal
                })

            # --- Guardar cambios en MySQL ---
            for p in productos_para_actualizar:
                p.save()

            # --- Insertar en MongoDB ---
            # --- Insertar en MongoDB ---
            # 4. Insertar en MongoDB con NOMBRES REALES y CÓDIGO PERSONALIZADO
            mongo_id = None
            try:
                db_mongo = get_db_handle()
                collection = db_mongo['ventas'] # Asegúrate que coincida con tu colección
                
                # A) GENERAR CÓDIGO PERSONALIZADO (Ej: REF-0001)
                # Contamos cuántos documentos hay para sumar 1
                cantidad_tickets = collection.count_documents({}) 
                secuencia = cantidad_tickets + 1
                # f"REF-{secuencia:04d}" crea un string rellenando con ceros: REF-0001, REF-0002...
                codigo_personalizado = f"REF-{secuencia:04d}"

                # B) OBTENER NOMBRES REALES DE MYSQL
                # Buscamos el objeto completo usando el ID que llegó del JSON
                sucursal_obj = Sucursal.objects.get(pk=id_sucursal)
                
                # Para el empleado, validamos que venga el ID
                id_emp = data.get('id_empleado')
                if id_emp:
                    empleado_obj = Empleado.objects.get(pk=id_emp)
                    nombre_vendedor = f"{empleado_obj.nombre} {empleado_obj.apellido}"
                else:
                    nombre_vendedor = "Venta Online / Sin Vendedor"

                # C) CREAR EL DICCIONARIO CON DATOS LEGIBLES
                ticket = {
                    "codigo": codigo_personalizado,     # <--- TU CÓDIGO REF-000X
                    "fecha": datetime.datetime.now(),
                    "cliente": data.get('cliente'),
                    "sucursal": sucursal_obj.nombre,    # <--- NOMBRE REAL (No ID)
                    "vendedor": nombre_vendedor,        # <--- NOMBRE REAL (No ID)
                    "total": total_venta,
                    "items": items_detalle              # Tus productos con nombre y marca
                }
                
                print(f"Guardando ticket: {codigo_personalizado}")
                result = collection.insert_one(ticket)
                mongo_id = str(result.inserted_id)

            except Sucursal.DoesNotExist:
                 return JsonResponse({'error': 'La sucursal enviada no existe'}, status=400)
            except Empleado.DoesNotExist:
                 return JsonResponse({'error': 'El empleado enviado no existe'}, status=400)
            except Exception as e:
                mongo_id = f"Error Mongo: {str(e)}"
                print("Error guardando en Mongo:", e)

            # 5. Responder ÉXITO
            return JsonResponse({
                'mensaje': 'Venta registrada correctamente',
                'codigo_ticket': codigo_personalizado, # <--- Devolvemos el código legible
                'id_ticket_mongo': mongo_id,
                'nuevo_total': total_venta
            })

        except Producto.DoesNotExist:
            return JsonResponse({'error': 'Producto no encontrado'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Método no permitido'}, status=405)
def listar_ventas(request):
    try:
        db = get_db_handle()
        
        # CAMBIO AQUÍ TAMBIÉN:
        collection = db['ventas'] 
        
        ventas = list(collection.find().sort("fecha", -1)) 
        
        for v in ventas:
            v['id_mongo'] = str(v['_id'])
            del v['_id']
            if 'fecha' in v:
                v['fecha'] = str(v['fecha'])
        
        return JsonResponse({'historial': ventas})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)