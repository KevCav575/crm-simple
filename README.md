# CRM Simple

Un sistema CRM (Customer Relationship Management) simple desarrollado con Flask y JavaScript.

## Características

- Gestión de clientes
- Gestión de contactos
- Gestión de oportunidades de venta
- Gestión de tareas
- Dashboard con estadísticas
- Sistema de autenticación

## Estructura del proyecto

```
crm-simple/
├── app.py                  # Aplicación principal Flask
├── templates/              # Plantillas HTML
│   ├── index.html          # Página principal del dashboard
│   └── login.html          # Página de login y registro
├── static/                 # Archivos estáticos
│   ├── css/
│   │   └── style.css       # Estilos CSS
│   └── js/
│       └── client.js       # JavaScript del cliente
├── requirements.txt        # Dependencias Python
├── Procfile                # Configuración para despliegue 
└── README.md               # Documentación
```

## Requisitos

- Python 3.8+
- Flask
- SQLAlchemy
- JWT para autenticación
- Navegador web moderno

## Instalación local

1. Clonar el repositorio:
   ```
   git clone https://github.com/tu-usuario/crm-simple.git
   cd crm-simple
   ```

2. Crear un entorno virtual:
   ```
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. Instalar las dependencias:
   ```
   pip install -r requirements.txt
   ```

4. Ejecutar la aplicación:
   ```
   python app.py
   ```

5. Abrir el navegador en `http://localhost:5000`

## Configuración

Las siguientes variables de entorno pueden ser configuradas:

- `SECRET_KEY`: Clave secreta para JWT y Flask
- `DATABASE_URL`: URL de conexión a la base de datos (por defecto: SQLite)

## Despliegue

Este proyecto está configurado para desplegarse fácilmente en plataformas como Render, Railway o PythonAnywhere. Consulta la sección "Despliegue" en la documentación para más detalles.

## Licencia

Este proyecto está disponible bajo la licencia MIT.
