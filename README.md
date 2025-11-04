# PropTech Backend API

Búsqueda de propiedades con lenguaje natural usando FastAPI + Ollama LLM + MySQL.

## 🚀 Quick Start

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Crear .env desde template
cp .env.example .env

# 3. Correr el servidor
uvicorn app.main:app --reload

# 4. Ver documentación automática
# http://localhost:8000/docs
# http://localhost:8000/redoc

# 5. Probar health check
curl http://localhost:8000/health
```

## 📋 Estructura del Proyecto

```
app/
├── main.py                    # FastAPI app, lifespan, health checks
├── config.py                  # Settings desde .env
├── database.py               # MySQL connection manager
├── di.py                     # Dependency injection container
│
├── domain/                   # Lógica de negocio pura (sin deps externas)
│   ├── use_cases/
│   │   └── search_property.py      # Orquestación de búsqueda
│   ├── ports/                       # Interfaces/contratos
│   │   ├── property_repository.py
│   │   └── llm_service.py
│   └── schemas.py            # Pydantic models (request/response)
│
├── infrastructure/           # Adaptadores (detalles técnicos)
│   ├── repositories/         # Implementación de IPropertyRepository
│   │   ├── __init__.py
│   │   └── mysql_property_repo.py   # ← TODO
│   └── llm/                  # Implementación de ILLMService
│       ├── __init__.py
│       └── ollama_adapter.py        # ← TODO
│
└── presentation/             # HTTP layer
    └── routes/
        └── search_routes.py  # FastAPI routes

persistencia/
├── schema.sql               # Creación de BD + tablas
└── seed_data.sql           # Datos de ejemplo
```

## 🏗️ Arquitectura Hexagonal

### Las 3 Capas

**1. Presentation (HTTP)**
- `POST /api/search` - Búsqueda de propiedades
- Error handling con `HTTPException`
- Logging de requests

**2. Domain (Core - Pure Business Logic)**
- `SearchPropertyUseCase` - Orquestación
- Validación de entrada
- Sin FastAPI, sin MySQL aquí
- Depende de puertos (interfaces)

**3. Infrastructure (Adapters)**
- `MySQLPropertyRepository` - Adapter de BD
- `OllamaLLMAdapter` - Adapter de LLM
- Detalles técnicos aquí

### Ventajas
✅ Testeable (mockear adapters fácil)
✅ Desacoplado (cambiar Ollama por OpenAI = cambiar 1 archivo)
✅ Claro (cada capa tiene responsabilidad)

## 🔌 Endpoints

### POST /api/search
Buscar propiedades usando lenguaje natural.

**Request:**
```json
{
  "query": "Busco casas de 3 habitaciones en zona 10"
}
```

**Response:**
```json
{
  "sql": "SELECT * FROM propiedades WHERE habitaciones = 3 AND ubicacion LIKE '%zona 10%'",
  "results": [
    {
      "id": 1,
      "titulo": "Casa moderna",
      "precio": 250000,
      "habitaciones": 3,
      "ubicacion": "zona 10"
    }
  ]
}
```

**Errors:**
- `400 Bad Request` - Query vacía o inválida
- `500 Internal Server Error` - Error en LLM o BD

### GET /health
Health check - Verifica conectividad a BD.

**Response:**
```json
{
  "status": "healthy",
  "database": "connected"
}
```

### GET /ready
Readiness check - Indica si la app está lista para recibir traffic.

**Response:**
```json
{
  "ready": true,
  "version": "1.0.0"
}
```

## ⚙️ Configuración

Variables de entorno en `.env` (ver `.env.example`):

```bash
# App
APP_NAME=PropTech API
APP_VERSION=1.0.0
DEBUG=False

# Database
DB_HOST=mysql
DB_PORT=3306
DB_USER=appuser
DB_PASSWORD=apppass
DB_NAME=propiedades_db

# LLM (Ollama)
OLLAMA_URL=http://host.docker.internal:11434
OLLAMA_MODEL=llama3.2:3b
OLLAMA_TIMEOUT=30

# API
CORS_ORIGINS=*
API_PREFIX=/api

# Logging
LOG_LEVEL=INFO
```

## 🧪 Testing

```bash
# Correr tests
pytest tests/

# Con coverage
pytest --cov=app tests/

# Solo tests unitarios
pytest tests/unit/

# Solo tests de integración
pytest tests/integration/
```

## 📦 Dependencias

- **FastAPI** 0.104.1 - Framework web
- **Uvicorn** 0.24.0 - ASGI server
- **Pydantic** 2.5.0 - Validación de datos
- **mysql-connector-python** 8.2.0 - Driver MySQL
- **requests** 2.31.0 - HTTP client (para Ollama)
- **python-dotenv** 1.0.0 - Variables de entorno
- **python-multipart** 0.0.6 - Form handling

## 🐳 Docker

```bash
# Build
docker build -t proptech-backend .

# Run
docker run -p 8000:8000 \
  -e DB_HOST=mysql \
  -e OLLAMA_URL=http://host.docker.internal:11434 \
  proptech-backend
```

## 📊 Flujo de Datos

```
Frontend (Vue)
    ↓
POST /api/search { "query": "..." }
    ↓
search_routes.py (HTTP adapter)
    ↓
SearchPropertyUseCase.execute()
    ├─ Valida query
    ├─ Genera SQL (Ollama via ILLMService)
    ├─ Valida SQL (seguridad)
    ├─ Ejecuta búsqueda (MySQL via IPropertyRepository)
    └─ Retorna { sql, results }
    ↓
Frontend: Muestra resultados
```

## 🔒 Seguridad

### SQL Injection Prevention
- ✅ SQL generado por LLM es validado
- ✅ Solo permitido `SELECT` statements
- ✅ Forbidden keywords: DROP, DELETE, UPDATE, INSERT, ALTER, CREATE, TRUNCATE
- ✅ No se permite punto y coma (`;`)

### Best Practices
- ✅ Tipos estrictos (Pydantic)
- ✅ Validación de entrada
- ✅ Error handling sin información sensible
- ✅ Logging de seguridad
- ✅ CORS configurado

## 📝 Logging

Logs automáticos para:
- Startup/shutdown
- Requests HTTP (info)
- Errores (error)
- Queries SQL (debug)
- Health checks

Nivel configurable en `.env` (LOG_LEVEL=INFO|DEBUG|WARNING|ERROR|CRITICAL)

## 🚨 Troubleshooting

### Error: "Database not connected"
```bash
# Verificar conexión MySQL
curl -i http://localhost:8000/health

# Verificar .env
cat .env

# Verificar MySQL está corriendo
docker ps | grep mysql
```

### Error: "LLM connection failed"
```bash
# Verificar Ollama está corriendo
curl http://host.docker.internal:11434/api/tags

# Verificar modelo está disponible
ollama list

# Si no está, descargar:
ollama pull llama3.2:3b
```

### Error: "Invalid SQL"
- Query en lenguaje natural no es clara
- LLM generó SQL inválido
- Ver logs: `LOG_LEVEL=DEBUG`

## 📚 Documentación Adicional

- `ARCHITECTURE.md` - Explicación de arquitectura hexagonal
- `/docs` - Swagger UI (http://localhost:8000/docs)
- `/redoc` - ReDoc (http://localhost:8000/redoc)

## 👤 Autor

Proyecto educational - PropTech API

## 📄 License

MIT
