from django.db import models
class Categoria(models.Model):
    id_categoria = models.IntegerField(primary_key=True)
    nombre_categoria = models.CharField(max_length=100)
    class Meta:
        managed = False
        db_table = 'categoria'

class Empleado(models.Model):
    id_empleado = models.IntegerField(primary_key=True)
    nombre = models.CharField(max_length=100, blank=True, null=True)
    apellido = models.CharField(max_length=100, blank=True, null=True)
    puesto = models.CharField(max_length=100, blank=True, null=True)
    class Meta:
        managed = False
        db_table = 'empleado'

class Marca(models.Model):
    id_marca = models.IntegerField(primary_key=True)
    nombre_marca = models.CharField(max_length=100)
    class Meta:
        managed = False
        db_table = 'marca'

class Producto(models.Model):
    id_producto = models.IntegerField(primary_key=True)
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)
    stock = models.IntegerField(blank=True, null=True)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    id_marca = models.ForeignKey(Marca, models.DO_NOTHING, db_column='id_marca', blank=True, null=True)
    id_categoria = models.ForeignKey(Categoria, models.DO_NOTHING, db_column='id_categoria', blank=True, null=True)
    class Meta:
        managed = False
        db_table = 'producto'

class Sucursal(models.Model):
    id_sucursal = models.IntegerField(primary_key=True)
    nombre = models.CharField(max_length=255, blank=True, null=True)
    ciudad = models.CharField(max_length=100, blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    telefono = models.CharField(max_length=50, blank=True, null=True)
    class Meta:
        managed = False
        db_table = 'sucursal'
