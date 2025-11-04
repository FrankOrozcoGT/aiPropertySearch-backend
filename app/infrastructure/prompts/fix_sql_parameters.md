# Fix SQL Query Prompt

You are fixing a parameterized SQL query that has an error.

**ERROR:**
{error}

**Current SQL:**
```sql
{sql}
```

**Current Parameters:**
```json
{params}
```

**USER QUERY:**
{query}

**DATABASE TABLES:**
- propiedades: id, titulo, descripcion, tipo, precio, habitaciones, banos, area_m2, ubicacion, zona_administrativa, fecha_publicacion, estado
- amenidades: id, nombre, tipo (colegio, parada_bus, supermercado, parque, hospital, gym, restaurante, cine, banco, farmacia, centroComercial), ubicacion, zona_administrativa
- propiedades_amenidades: id, propiedad_id, amenidad_id, distancia_km, notas

**FIX THE SQL:**
- Ensure placeholders (%s) match parameter count
- Only use SELECT queries
- Always include: AND estado = 'activa'
- Use DISTINCT with JOINs to avoid duplicates

**RESPONSE FORMAT (two blocks only):**

## MySQL Query
```mysql
SELECT * FROM propiedades WHERE tipo = %s AND estado = 'activa'
```

## Parameters
```json
["casa"]
```

**IMPORTANT:**
- Match %s count with parameter count exactly
- No extra text or explanations
