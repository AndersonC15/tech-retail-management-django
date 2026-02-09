from django.contrib import admin
from django.urls import path,include
from ventas.views import nueva_venta, listar_ventas 

urlpatterns = [
    path('admin/', admin.site.urls),
    path('ventas/', listar_ventas),
    path('nueva-venta/', nueva_venta),
    path('', include('analisis.urls')),
]