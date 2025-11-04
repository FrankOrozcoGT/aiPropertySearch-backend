# Sequence Diagram: Property Search Flow

## Arquitectura Hexagonal - Flujo Actual

```mermaid
sequenceDiagram
    participant Client as Client<br/>(HTTP)
    participant Route as Routes<br/>(Presentation)
    participant UseCase as SearchPropertyUseCase<br/>(Domain)
    participant LLMAdapter as OllamaLLMAdapter<br/>(Infrastructure)
    participant Ollama as Ollama<br/>(External LLM)
    participant MySQLAdapter as MySQLPropertyRepository<br/>(Infrastructure)
    participant MySQL as MySQL<br/>(Database)

    Client->>+Route: POST /api/search<br/>{"query": "..."}
    Note over Route: ✓ Pydantic validates<br/>SearchRequest
    
    Route->>+UseCase: execute(search_request)
    Note over UseCase: 1. Entrada validada<br/>por Pydantic
    
    UseCase->>+LLMAdapter: generate_sql(query)
    Note over LLMAdapter: Input: "casas baratas<br/>en zona 10"
    
    LLMAdapter->>+Ollama: POST /api/generate<br/>prompt=<SQL query>
    Ollama-->>-LLMAdapter: {"response": "SELECT..."}
    Note over LLMAdapter: SQL sin validar
    
    LLMAdapter->>LLMAdapter: sql = parse_response(response)
    Note over LLMAdapter: sql = "SELECT * FROM...<br/>WHERE precio < 500000"
    
    LLMAdapter->>+LLMAdapter: validate_sql(sql)
    Note over LLMAdapter,LLMAdapter: 🔒 VALIDACIÓN (5 CHECKS)<br/>app/infrastructure/llm/<br/>ollama_adapter.py<br/>lines 106-170
    
    rect rgb(200, 100, 100)
        Note over LLMAdapter: ✓ Check 1: SELECT only<br/>✓ Check 2: No forbidden keywords<br/>✓ Check 3: No ending semicolon<br/>✓ Check 4: No multiple statements<br/>✓ Check 5: No SQL injection patterns
    end
    
    LLMAdapter->>-LLMAdapter: returns: True/False
    
    alt SQL Válido
        LLMAdapter-->>-UseCase: sql (validated)
        
        UseCase->>+MySQLAdapter: search(sql)
        Note over MySQLAdapter: Recibe SQL ya<br/>validado
        
        MySQLAdapter->>+MySQL: execute_query(sql)
        MySQL-->>-MySQLAdapter: results[]
        
        MySQLAdapter->>-UseCase: PropertyList
        
        UseCase->>-Route: SearchResponse{<br/>  properties: [],<br/>  total: n,<br/>  query_id: uuid<br/>}
        Note over Route: Pydantic serializa<br/>respuesta
        
        Route-->>-Client: 200 OK + JSON
        
    else SQL Inválido
        LLMAdapter-->>-UseCase: ValueError
        Note over UseCase: SQL no pasó<br/>validación
        
        UseCase->>-Route: SearchException
        
        Route-->>-Client: 400 Bad Request<br/>+ error details
    end
```

---

## Ubicación de la Validación SQL

### 📍 Archivo: `app/infrastructure/llm/ollama_adapter.py`

**Líneas 106-170**: Método `validate_sql(sql: str) -> bool`

```python
def validate_sql(self, sql: str) -> bool:
    """
    Valida que el SQL generado sea seguro.
    5 niveles de validación:
    """
    
    # CHECK 1: Debe ser SELECT únicamente
    if not sql.strip().upper().startswith("SELECT"):
        raise ValueError("SQL must start with SELECT")
    
    # CHECK 2: Sin palabras clave peligrosas
    forbidden = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", 
                 "CREATE", "TRUNCATE", "EXEC", "EXECUTE", "SCRIPT", "PRAGMA"]
    if any(word in sql.upper() for word in forbidden):
        raise ValueError("Forbidden SQL keywords detected")
    
    # CHECK 3: Sin punto y coma al final
    if sql.rstrip().endswith(";"):
        raise ValueError("SQL statement cannot end with semicolon")
    
    # CHECK 4: Sin múltiples statements
    if ";" in sql:
        raise ValueError("Multiple SQL statements not allowed")
    
    # CHECK 5: Sin patrones de SQL injection
    if "--" in sql or "/*" in sql or "*/" in sql:
        raise ValueError("Comment-based SQL injection detected")
    
    return True
```

---

## Cadena de Responsabilidad - Hexagonal

```
┌─────────────────────────────────────────────────────────────┐
│                   PRESENTATION LAYER                         │
│               Routes → Pydantic Validation                   │
│                                                              │
│  ✓ Valida estructura del request (SearchRequest)            │
│  ✓ Valida tipos de datos                                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    DOMAIN LAYER                              │
│          SearchPropertyUseCase → Pure Business Logic         │
│                                                              │
│  ✓ Orquesta el flujo (use case)                            │
│  ✓ No conoce detalles de implementación                     │
│  ✓ Usa interfaces (ports): ILLMService, IRepository         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              INFRASTRUCTURE LAYER                            │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  OllamaLLMAdapter (ILLMService implementation)       │  │
│  │                                                      │  │
│  │  1. generate_sql(query) → Calls Ollama              │  │
│  │  2. validate_sql(sql) → 🔒 5-LEVEL VALIDATION 🔒   │  │
│  │                                                      │  │
│  │  📍 Líneas 106-170 de ollama_adapter.py            │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  MySQLPropertyRepository (IRepository impl)          │  │
│  │                                                      │  │
│  │  execute_query(validated_sql)                       │  │
│  │  → Recibe SQL YA VALIDADO                           │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

---

## Resumen de Validación

| Nivel | Ubicación | Validación |
|-------|-----------|-----------|
| 1️⃣ **HTTP** | `routes/__init__.py` | Pydantic `SearchRequest` |
| 2️⃣ **Business Logic** | `SearchPropertyUseCase.execute()` | Lógica de negocio |
| 3️⃣ **LLM Adapter** | `ollama_adapter.py:106-170` | 🔒 **SQL Validation** 🔒 |
| 4️⃣ **SQL Execution** | `mysql_property_repo.py` | `execute_query()` |
| 5️⃣ **Database** | MySQL | Constraints + Indexes |

---

## Flujo Normal (Happy Path)

```
Client Request
    ↓
✓ Pydantic validates SearchRequest
    ↓
✓ Routes forwards to UseCase
    ↓
✓ UseCase calls LLMAdapter.generate_sql()
    ↓
✓ Ollama returns SQL
    ↓
✓ LLMAdapter.validate_sql() CHECKS 5 LEVELS
    ↓
✓ If valid: UseCase calls Repository.search()
    ↓
✓ MySQLRepository executes validated SQL
    ↓
✓ Results returned back through chain
    ↓
✓ SearchResponse serialized + sent to client
```

---

## Flujo de Error (Validation Fails)

```
Client Request
    ↓
✓ Pydantic validates SearchRequest
    ↓
✓ Routes forwards to UseCase
    ↓
✓ UseCase calls LLMAdapter.generate_sql()
    ↓
✓ Ollama returns SQL
    ↓
✗ LLMAdapter.validate_sql() FAILS CHECK
    ↓
✗ ValueError raised with specific error
    ↓
✗ UseCase catches and converts to SearchException
    ↓
✗ Routes returns 400 Bad Request with error details
    ↓
✗ Client receives error message
```

---

## Seguridad: ¿Por qué aquí?

La validación está en el **OllamaLLMAdapter** porque:

1. **Separación de responsabilidades**: El adapter es el único que sabe qué es SQL válido en este contexto
2. **Defense in Depth**: Se valida ANTES de que el SQL llegue a MySQL
3. **Hexagonal**: Es la frontera entre la lógica de negocio y la ejecución real
4. **Fail-Fast**: Si falla, nunca llega a la base de datos
5. **Auditable**: Se loguea qué SQL se rechazó y por qué

```python
# En ollama_adapter.py líneas 100-105
try:
    self.validate_sql(sql)
except ValueError as e:
    logger.error(f"SQL validation failed: {e}")
    logger.error(f"Rejected SQL: {sql}")
    raise SearchException(f"Invalid query generated: {str(e)}")
```
