-- PropTech Database Schema
-- Normalizada para soportar queries complejas de propiedades y amenidades

-- ============================================================================
-- TABLA 1: PROPIEDADES (Main table)
-- ============================================================================
CREATE TABLE IF NOT EXISTS propiedades (
    id INT PRIMARY KEY AUTO_INCREMENT,
    titulo VARCHAR(255) NOT NULL,
    descripcion TEXT,
    tipo ENUM('casa', 'departamento', 'terreno', 'local', 'oficina') NOT NULL,
    precio DECIMAL(12, 2) NOT NULL,
    habitaciones INT,
    banos INT,
    area_m2 DECIMAL(10, 2),
    ubicacion VARCHAR(255) NOT NULL,
    zona_administrativa VARCHAR(50),
    fecha_publicacion DATE NOT NULL,
    estado ENUM('activa', 'vendida', 'alquilada') DEFAULT 'activa',
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_tipo (tipo),
    INDEX idx_precio (precio),
    INDEX idx_habitaciones (habitaciones),
    INDEX idx_zona (zona_administrativa),
    INDEX idx_fecha_publicacion (fecha_publicacion)
);

-- ============================================================================
-- TABLA 2: AMENIDADES (Catálogo de servicios/lugares cercanos)
-- ============================================================================
CREATE TABLE IF NOT EXISTS amenidades (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(255) NOT NULL,
    tipo ENUM(
        'colegio',
        'parada_bus',
        'supermercado',
        'parque',
        'hospital',
        'gym',
        'restaurante',
        'cine',
        'banco',
        'farmacia',
        'centroComercial'
    ) NOT NULL,
    ubicacion VARCHAR(255),
    zona_administrativa VARCHAR(50),
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_amenidad (nombre, tipo, ubicacion),
    INDEX idx_tipo (tipo),
    INDEX idx_zona (zona_administrativa)
);

-- ============================================================================
-- TABLA 3: PROPIEDADES_AMENIDADES (Relación muchos-a-muchos)
-- ============================================================================
CREATE TABLE IF NOT EXISTS propiedades_amenidades (
    id INT PRIMARY KEY AUTO_INCREMENT,
    propiedad_id INT NOT NULL,
    amenidad_id INT NOT NULL,
    distancia_km DECIMAL(5, 2),
    notas VARCHAR(255),
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (propiedad_id) REFERENCES propiedades(id) ON DELETE CASCADE,
    FOREIGN KEY (amenidad_id) REFERENCES amenidades(id) ON DELETE CASCADE,
    UNIQUE KEY unique_propiedad_amenidad (propiedad_id, amenidad_id),
    INDEX idx_propiedad (propiedad_id),
    INDEX idx_amenidad (amenidad_id),
    INDEX idx_distancia (distancia_km)
);

-- ============================================================================
-- TABLA 4: ESTADISTICAS (Para análisis, opcional)
-- ============================================================================
CREATE TABLE IF NOT EXISTS estadisticas_queries (
    id INT PRIMARY KEY AUTO_INCREMENT,
    query_usuario VARCHAR(500) NOT NULL,
    sql_generado TEXT NOT NULL,
    resultados INT,
    tiempo_ms INT,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_fecha (fecha_creacion)
);
