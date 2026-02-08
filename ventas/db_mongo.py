from pymongo import MongoClient

def get_db_handle():
    # Conexión local por defecto
    client = MongoClient('mongodb://localhost:27017/')
    
    # Aquí define el nombre de tu base de datos NoSQL
    db = client['nextgen_ventas'] 
    
    return db