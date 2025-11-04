# Backend - FastAPI con Arquitectura Hexagonal

## 🎯 Estado Actual

La base de **FastAPI con Arquitectura Hexagonal** está lista. Solo falta:
1. ✅ Estructura base
2. ✅ Puertos (interfaces)
3. ✅ UseCase (lógica de negocio)
4. ✅ Configuración y base de datos
5. ✅ Routes (presentación)
6. ✅ Inyección de dependencias
7. ❌ **ADAPTADORES** (falta crear)

## 📁 Estructura del Proyecto

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                          # 🚀 FastAPI init
│   ├── config.py                        # ⚙️ Settings/variables de entorno
│   ├── database.py                      # 🗄️ MySQL connection manager
│   ├── di.py                            # 💉 Dependency Injection container
│   │
│   ├── domain/                          # 🧠 CORE BUSINESS LOGIC (sin deps externas)
│   │   ├── __init__.py
│   │   ├── schemas.py                   # Pydantic models (request/response)
│   │   ├── ports/                       # 🚪 Interfaces/Contratos
│   │   │   ├── __init__.py
│   │   │   ├── property_repository.py   # IPropertyRepository (contrato para BD)
│   │   │   └── llm_service.py           # ILLMService (contrato para LLM)
│   │   └── use_cases/
│   │       ├── __init__.py
│   │       └── search_property.py       # SearchPropertyUseCase (lógica pura)
│   │
│   ├── infrastructure/                  # 🔧 ADAPTADORES (detalles técnicos)
│   │   ├── __init__.py
│   │   ├── repositories/                # Implementación de IPropertyRepository
│   │   │   ├── __init__.py
│   │   │   └── mysql_property_repo.py   # ← PRÓXIMO: Crear esto
│   │   └── llm/                         # Implementación de ILLMService
│   │       ├── __init__.py
│   │       └── ollama_adapter.py        # ← PRÓXIMO: Crear esto
│   │
│   └── presentation/                    # 🎨 HTTP LAYER
│       ├── __init__.py
│       └── routes/
│           ├── __init__.py
│           └── search_routes.py         # FastAPI routes
│
├── persistencia/
│   ├── schema.sql                       # SQL para crear tablas
│   └── seed_data.sql                    # Datos de ejemplo
│
├── tests/
│   ├── unit/                            # Test unitarios (use cases, etc)
│   └── integration/                     # Test de integración (API, BD)
│
├── requirements.txt
├── .env.example
├── Dockerfile
└── README.md
```

## 🏗️ Arquitectura Hexagonal Implementada

### Las 3 Capas

```
┌─────────────────────────────────────────────────────┐
│         PRESENTACIÓN (HTTP)                         │
│  routes/search_routes.py                            │
│  ↓ Recibe requests, llama use case, retorna response│
└────────────────┬────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────┐
│         DOMINIO (NÚCLEO)                            │
│  domain/use_cases/search_property.py                │
│  ↑ Lógica pura, SIN FastAPI, SIN MySQL             │
│  ├ Valida input                                    │
│  ├ Genera SQL con LLM (a través de puerto)         │
│  ├ Valida SQL (seguridad)                          │
│  └ Ejecuta búsqueda (a través de puerto)           │
└────────────────┬────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────┐
│      INFRAESTRUCTURA (ADAPTADORES)                 │
│  infrastructure/repositories/  +  infrastructure/llm/
│  ↓ Implementan los puertos                         │
│  ├ MySQLPropertyRepository (IPropertyRepository)    │
│  └ OllamaLLMAdapter (ILLMService)                  │
└─────────────────────────────────────────────────────┘
```

## 🔌 Puertos (Interfaces) - YA CREADOS

### 1. IPropertyRepository
```python
# Contrato: acceder a propiedades
interface IPropertyRepository:
    async search(sql: str) -> list[dict]  # Ejecutar query, retornar resultados
```

### 2. ILLMService
```python
# Contrato: generar SQL desde lenguaje natural
interface ILLMService:
    async generate_sql(query: str) -> str  # Generar SQL
    async validate_sql(sql: str) -> bool   # Validar SQL (seguridad)
```

## 💡 UseCase - YA CREADO

`domain/use_cases/search_property.py`: **SearchPropertyUseCase**

```
Flujo:
1. Recibe: SearchRequest { query: "casas 3 habitaciones" }
2. Valida que query no esté vacío
3. Llama a llm_service.generate_sql(query)
4. Llama a llm_service.validate_sql(sql)
5. Llama a property_repository.search(sql)
6. Retorna: SearchResponse { sql, results }
```

## ⚙️ Configuración - YA CREADA

- **config.py**: Settings desde `.env`
- **database.py**: Connection manager para MySQL
- **di.py**: ServiceContainer para inyección de dependencias
- **.env.example**: Variables de entorno de ejemplo

## 🚀 FastAPI Inicializado - YA CREADO

`app/main.py`:
- ✅ Lifespan hooks (startup/shutdown)
- ✅ CORS configurado
- ✅ Health check (`/health`)
- ✅ Ready check (`/ready`)
- ✅ Logging configurado
- ❌ Routes registradas (se añaden cuando adaptadores estén listos)

## ❌ PRÓXIMO PASO: Crear Adaptadores

Necesitamos implementar:

### 1. MySQLPropertyRepository
**Archivo**: `app/infrastructure/repositories/mysql_property_repo.py`

Debe implementar `IPropertyRepository`:
```python
class MySQLPropertyRepository(IPropertyRepository):
    async def search(self, sql: str) -> list[dict]:
        # Validar SQL
        # Ejecutar en BD
        # Retornar resultados
```

### 2. OllamaLLMAdapter
**Archivo**: `app/infrastructure/llm/ollama_adapter.py`

Debe implementar `ILLMService`:
```python
class OllamaLLMAdapter(ILLMService):
    async def generate_sql(self, query: str) -> str:
        # Llamar Ollama
        # Retornar SQL
    
    async def validate_sql(self, sql: str) -> bool:
        # Validar SELECT only
        # No SQL injection
        # Retornar True/False
```

## 📝 Para Correr Ahora (con placeholders)

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Crear .env desde .env.example
cp .env.example .env

# 3. Correr FastAPI (sin modelos, solo health check)
uvicorn app.main:app --reload

# 4. Ver documentación automática
# http://localhost:8000/docs
# http://localhost:8000/redoc

# 5. Health check
# curl http://localhost:8000/health
```

## 🎯 Principios Hexagonal Implementados

✅ **Dominio Puro**: UseCase NO conoce FastAPI, NO conoce MySQL
✅ **Puertos**: Contratos claros para adaptadores
✅ **Inyección**: Dependencias inyectadas, no acopladas
✅ **Testeable**: Fácil mockear adapters
✅ **Flexible**: Cambiar Ollama por OpenAI = cambiar 1 adaptador

## 🔄 Próxima Conversación

Te detenemos aquí para que definas el MODELO de datos.
Necesitamos hablar sobre:
- ¿Qué campos tiene la tabla `propiedades`?
- ¿Cómo se relacionan con el búsqueda?
- ¿Hay validaciones especiales?

Una vez definido el modelo, crearemos:
1. Schema SQL (persistencia/schema.sql)
2. Entity en dominio (si aplica)
3. Adaptadores (MySQL + Ollama)
4. Tests
