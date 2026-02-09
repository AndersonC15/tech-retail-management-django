import json
import datetime
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt 

from inventario.models import Producto, Sucursal, Empleado 
from .db_mongo import get_db_handle 

def nueva_venta(request):
    if request.method == 'GET':
        context = {
            'empleados': Empleado.objects.all(),
            'sucursales': Sucursal.objects.all(),
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

            # --- 1. Validación y Cálculo (MySQL) ---
            for item in items:
                prod_id = item['id_producto']
                cantidad_solicitada = int(item['cantidad'])
                
                producto = Producto.objects.get(pk=prod_id)
                
                if producto.stock < cantidad_solicitada:
                    return JsonResponse({
                        'error': f'Stock insuficiente para {producto.nombre}. Disponibles: {producto.stock}'
                    }, status=400)
                
                # Descontar stock
                producto.stock -= cantidad_solicitada
                productos_para_actualizar.append(producto)
                
                precio_float = float(producto.precio_unitario) if producto.precio_unitario else 0.0
                subtotal = precio_float * cantidad_solicitada
                total_venta += subtotal
                
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

            # --- 2. Guardar cambios en MySQL ---
            for p in productos_para_actualizar:
                p.save()

            # --- 3. Insertar en MongoDB ---
            try:
                db_mongo = get_db_handle()
                collection = db_mongo['ventas']
                
                # Generar REF-XXXX
                cantidad_tickets = collection.count_documents({}) 
                secuencia = cantidad_tickets + 1
                codigo_personalizado = f"REF-{secuencia:04d}"

                sucursal_obj = Sucursal.objects.get(pk=id_sucursal)
                
                id_emp = data.get('id_empleado')
                if id_emp:
                    empleado_obj = Empleado.objects.get(pk=id_emp)
                    nombre_vendedor = f"{empleado_obj.nombre} {empleado_obj.apellido}"
                else:
                    nombre_vendedor = "Venta Online / Sin Vendedor"

                ticket = {
                    "codigo": codigo_personalizado,     
                    "fecha": datetime.datetime.now(),
                    "cliente": data.get('cliente'),
                    "sucursal": sucursal_obj.nombre,    
                    "vendedor": nombre_vendedor,        
                    "total": total_venta,
                    "items": items_detalle              
                }
                
                result = collection.insert_one(ticket)
                mongo_id = str(result.inserted_id)

                # --- 4. RESPONDER AL HTML (CORREGIDO) ---
                return JsonResponse({
                    'mensaje': 'Venta registrada correctamente',
                    'codigo': codigo_personalizado,  # <--- AHORA COINCIDE CON TU JS (data.codigo)
                    'id_ticket_mongo': mongo_id,
                    'nuevo_total': total_venta
                })

            except Sucursal.DoesNotExist:
                 return JsonResponse({'error': 'La sucursal enviada no existe'}, status=400)
            except Exception as e:
                print("Error Mongo:", e)
                return JsonResponse({'error': f"Error guardando en Mongo: {str(e)}"}, status=500)

        except Producto.DoesNotExist:
            return JsonResponse({'error': 'Producto no encontrado'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Método no permitido'}, status=405)

# La función listar_ventas la dejé igual porque estaba bien
def listar_ventas(request):
    try:
        db = get_db_handle()
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