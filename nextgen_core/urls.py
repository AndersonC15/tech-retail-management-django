from django.contrib import admin
from django.urls import path

# IMPORTANTE: Solo importamos lo que existe en views.py
from ventas.views import nueva_venta, listar_ventas 

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('probar-venta/', crear_venta_prueba), <--- BORRA O COMENTA ESTA LÍNEA (esa función ya no existe)
    path('ventas/', listar_ventas),
    path('nueva-venta/', nueva_venta),
]