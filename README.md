# 🤖 aiPropertySearch - Backend API

API FastAPI para búsqueda de propiedades usando IA con Ollama LLM y MySQL.

Traduce consultas en lenguaje natural a SQL de forma segura y los ejecuta.

## ✨ Características

- 🤖 **Ollama LLM Integration**: Traduce lenguaje natural a SQL
- 🛡️ **100% SQL Injection Safe**: Parámetros separados + validación
- ⚡ **FastAPI**: Framework web asincrónico
- 🗄️ **MySQL**: Base de datos normalizada
- 📚 **Documentación Automática**: Swagger + ReDoc
- 🏗️ **Arquitectura Hexagonal**: Separación clara de capas
- 🔐 **Seguridad**: Validación SQLAlchemy, palabras clave bloqueadas

## 📦 Stack Tecnológico

- **FastAPI** - Framework web asincrónico
- **Python 3.11+** - Lenguaje principal
- **Ollama** - LLM local para NLP
- **MySQL 8.0+** - Base de datos
- **SQLAlchemy** - ORM y validación de SQL
- **Pydantic** - Validación de datos
- **Uvicorn** - ASGI server
- **Docker** - Contenedorización

## 📋 Requisitos

### Para Desarrollo Local
- **Python** 3.11+
- **MySQL** 8.0+
- **Ollama** (para LLM)
- **pip** o **poetry**

### Para Docker
- **Docker** 20.10+
- **Docker Compose** 2.0+

## 🚀 Instalación

### Opción 1: Desarrollo Local

#### 1. Clonar repositorio

```bash
git clone https://github.com/FrankOrozcoGT/aiPropertySearch-backend.git
cd aiPropertySearch-backend
```

#### 2. Crear ambiente virtual

```bash
python -m venv venv

# Activar (Linux/Mac)
source venv/bin/activate

# Activar (Windows)
venv\Scripts\activate
```

#### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

#### 4. Configurar variables de entorno

```bash
cp .env.example .env
```

**Editar `.env`:**
```env
# Database
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=tu_password
DB_NAME=propiedades

# Ollama (LLM)
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=mistral
OLLAMA_TIMEOUT=30

# API
API_PREFIX=/api/v1
LOG_LEVEL=INFO
```

#### 5. Crear base de datos

```bash
mysql -u root -p < persistencia/schema.sql
mysql -u root -p propiedades < persistencia/seed_data.sql
```

#### 6. Descargar modelo de Ollama

```bash
# Instalar Ollama desde https://ollama.ai
# Luego descargar modelo:
ollama pull mistral
```

#### 7. Ejecutar servidor

```bash
uvicorn app.main:app --reload
```

Backend disponible en: **http://localhost:8000**

Documentación: **http://localhost:8000/docs**

### Opción 2: Docker Compose (Recomendado)

```bash
docker-compose up -d
```

Todos los servicios se levantarán:
- Backend: http://localhost:8000
- Frontend: http://localhost
- MySQL: localhost:3306
- Ollama: http://localhost:11434

## 📝 Estructura del Proyecto

```
app/
├── main.py                    # FastAPI app, lifespan, health checks
├── config.py                  # Settings desde .env
├── database.py                # MySQL connection manager
├── di.py                      # Dependency injection container
│
├── domain/                    # Lógica de negocio pura
│   ├── use_cases/
│   │   └── search_property.py      # Orquestación de búsqueda
│   ├── ports/                      # Interfaces/contratos
│   │   ├── llm_service.py
│   │   ├── property_repository.py
│   │   └── prompt_service.py
│   └── schemas.py             # Pydantic models
│
├── infrastructure/            # Adaptadores técnicos
│   ├── llm/
│   │   └── ollama_adapter.py       # Adapter para Ollama
│   ├── repositories/
│   │   └── mysql_property_repo.py  # Adapter MySQL
│   └── prompts/
│       ├── markdown_prompt_adapter.py
│       ├── sql_generation.md
│       └── fix_sql_parameters.md
│
└── presentation/              # HTTP layer
    └── routes/
        └── search_routes.py   # Endpoint /search

persistencia/
├── schema.sql                 # Estructura de BD
└── seed_data.sql              # Datos de ejemplo
```

## 🔌 API Endpoints

### Health Check

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "database": "connected"
}
```

### Ready Check

```http
GET /ready
```

**Response:**
```json
{
  "ready": true
}
```

### Search Properties

```http
POST /api/v1/search
Content-Type: application/json

{
  "query": "Casas de 3 habitaciones en zona 10"
}
```

**Response:**
```json
{
  "sql": "SELECT propiedades.id, propiedades.titulo... FROM propiedades LEFT JOIN propiedades_amenidades... WHERE habitaciones = 3 AND zona_administrativa LIKE '%zona 10%'",
  "results": [
    {
      "id": 1,
      "titulo": "Casa moderna",
      "descripcion": "Casa hermosa en zona residencial",
      "tipo": "casa",
      "precio": 250000,
      "habitaciones": 3,
      "banos": 2,
      "area_m2": 150,
      "ubicacion": "Zona 10, Guatemala",
      "zona_administrativa": "zona 10",
      "fecha_publicacion": "2025-11-01",
      "amenidades_tipos": "colegio,parque",
      "amenidades_cercanas": "Colegio Maya (2km), Parque Central (1.5km)"
    }
  ]
}
```

## 📚 Documentación Interactiva

### Swagger UI

```
http://localhost:8000/docs
```

Prueba los endpoints directamente desde el navegador.

### ReDoc

```
http://localhost:8000/redoc
```

Documentación estática en formato ReDoc.

## 🎯 Ejemplos de Búsqueda

El LLM entiende y traduce consultas como:

1. **"Casas de 3 habitaciones en zona 10"**
   - ✅ Busca casas
   - ✅ Filtra por 3 habitaciones
   - ✅ Ubicación en zona 10

2. **"Departamentos baratos menores a Q100,000"**
   - ✅ Filtra por tipo = departamento
   - ✅ Precio < 100000

3. **"Propiedades cerca de colegio y parque"**
   - ✅ Busca propiedades
   - ✅ Con amenidades: colegio, parque

4. **"Terrenos grandes en zona 18"**
   - ✅ Filtra por tipo = terreno
   - ✅ Área grande
   - ✅ Zona 18

## 🏗️ Arquitectura Hexagonal

```
HTTP (Presentation)
       ↓
Routes/Handlers
       ↓
Use Cases (Domain)
       ↓
Ports (Interfaces)
       ↓
Adapters (Infrastructure)
       ↓
External Services (Ollama, MySQL)
```

### Capas:

1. **Presentation**: Rutas HTTP FastAPI
2. **Domain**: Lógica de negocio pura (SearchPropertyUseCase)
3. **Ports**: Interfaces (ILLMService, IPropertyRepository)
4. **Infrastructure**: Implementaciones (OllamaLLMAdapter, MySQLPropertyRepository)
5. **External**: Servicios externos (Ollama, MySQL)

## 🛡️ Seguridad - SQL Injection

### ✅ Protegido

El sistema es **100% a prueba de SQL injection**:

1. **Parámetros Separados**
   ```python
   sql = "SELECT * FROM propiedades WHERE precio < %s"
   params = [100000]  # Separado del SQL
   execute_query_with_params(sql, params)
   ```

2. **Validación SQLAlchemy**
   - Verifica sintaxis antes de ejecutar
   - Rechaza sentencias peligrosas

3. **Placeholders MySQL**
   - `%s` con escape automático
   - `mysql.connector` maneja escaping

4. **Palabras Clave Bloqueadas**
   - DROP, DELETE, UPDATE, INSERT, CREATE, ALTER, EXEC, EXECUTE, TRUNCATE

## 🔧 Configuración

### Variables de Entorno (.env)

```env
# Database Configuration
DB_HOST=localhost                    # Host de MySQL
DB_PORT=3306                        # Puerto MySQL
DB_USER=root                        # Usuario MySQL
DB_PASSWORD=password                # Password MySQL
DB_NAME=propiedades                 # Nombre BD

# Ollama LLM Configuration
OLLAMA_URL=http://localhost:11434   # URL Ollama
OLLAMA_MODEL=mistral                # Modelo LLM
OLLAMA_TIMEOUT=30                   # Timeout en segundos

# API Configuration
API_PREFIX=/api/v1                  # Prefijo API
APP_NAME=aiPropertySearch           # Nombre app
APP_VERSION=1.0.0                   # Versión
DEBUG=False                         # Debug mode
LOG_LEVEL=INFO                      # Nivel logging
CORS_ORIGINS=*                      # CORS origins
```

## 🐳 Docker

### Build

```bash
docker build -t aipropertyseach-backend:latest .
```

### Run

```bash
docker run -d \
  --name aipropertyseach-backend \
  -p 8000:8000 \
  -e DB_HOST=db \
  -e OLLAMA_URL=http://ollama:11434 \
  aipropertyseach-backend:latest
```

## 🧪 Desarrollo

### Ejecutar con hot reload

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Ver logs

```bash
# Todos los logs
docker-compose logs -f backend

# Solo stderr
docker-compose logs -f backend 2>&1 | grep ERROR
```

### Acceder a MySQL

```bash
# Con Docker
docker exec -it proyecto_guate_db mysql -u root -ppassword propiedades

# Sin Docker
mysql -u root -p propiedades
```

## 🔍 Solución de Problemas

### Ollama no conecta

```bash
# Verificar Ollama está corriendo
curl http://localhost:11434

# Ver logs del backend
docker-compose logs backend | grep -i ollama
```

### Error de conexión a BD

```bash
# Verificar BD está corriendo
docker-compose ps db

# Revisar logs
docker-compose logs db

# Reintentar conexión
docker-compose restart backend
```

### Puerto 8000 en uso

```bash
# Ver qué proceso usa el puerto
lsof -i :8000

# Cambiar puerto en docker-compose.yml
ports:
  - "8001:8000"
```

## 📊 Performance

- ✅ Async/await para operaciones no bloqueantes
- ✅ Connection pooling en MySQL
- ✅ Índices en tablas principales
- ✅ Caché de prompts
- ✅ Health checks cada 30s

## 📄 Licencia

MIT

## 🤝 Contacto

**Autor:** Frank Orozco  
**Email:** frank.orozco.11.87@gmail.com

---

**Estado:** ✅ Funcional | Actualmente en desarrollo  
**Última actualización:** Noviembre 2025
