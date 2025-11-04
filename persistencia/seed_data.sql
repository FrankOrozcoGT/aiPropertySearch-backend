-- PropTech Seed Data
-- 20 propiedades variadas + amenidades + relaciones

-- ============================================================================
-- AMENIDADES (Catálogo de servicios - 15 amenidades)
-- ============================================================================

INSERT INTO amenidades (nombre, tipo, ubicacion, zona_administrativa) VALUES
('Colegio Hermano Miguel', 'colegio', 'Calzada Roosevelt, Zona 10', 'Zona 10'),
('Instituto Técnico Maya', 'colegio', 'Avenida la Reforma, Zona 10', 'Zona 10'),
('Colegio Técnico Mixto', 'colegio', '7a Avenida, Zona 10', 'Zona 10'),
('Colegio Americano', 'colegio', 'Vista Hermosa, Zona 15', 'Zona 15'),
('Colegio Monte María', 'colegio', 'Boulevard Los Alamos, Zona 15', 'Zona 15'),
('Parada 15 línea 3', 'parada_bus', 'Calzada Roosevelt, Zona 10', 'Zona 10'),
('Parada 22 línea 5', 'parada_bus', 'Avenida la Reforma, Zona 10', 'Zona 10'),
('Parada Central Zona 15', 'parada_bus', 'Boulevard Los Alamos, Zona 15', 'Zona 15'),
('Carrefour Zona 10', 'supermercado', 'Calzada Roosevelt, Zona 10', 'Zona 10'),
('Walmart Reforma', 'supermercado', 'Avenida la Reforma, Zona 10', 'Zona 10'),
('Despensa Familiar', 'supermercado', 'Boulevard Los Alamos, Zona 15', 'Zona 15'),
('Parque La Aurora', 'parque', 'Calzada Roosevelt, Zona 10', 'Zona 10'),
('Parque Los Alamos', 'parque', 'Boulevard Los Alamos, Zona 15', 'Zona 15'),
('Hospital CIMA', 'hospital', 'Avenida la Reforma, Zona 10', 'Zona 10');

-- ============================================================================
-- PROPIEDADES (20 propiedades variadas)
-- ============================================================================

-- ZONA 10 - CASAS
INSERT INTO propiedades (titulo, descripcion, tipo, precio, habitaciones, banos, area_m2, ubicacion, zona_administrativa, fecha_publicacion, estado) VALUES
('Casa moderna 3 habitaciones Zona 10', 'Casa con acabados modernos, patio grande, cochera para 2 autos', 'casa', 320000.00, 3, 2, 250.00, 'Calzada Roosevelt, Zona 10', 'Zona 10', DATE_SUB(NOW(), INTERVAL 5 DAY), 'activa'),
('Casa familiar 4 habitaciones', 'Casa en lote de 500m2, ideal para familia, jardín, piscina', 'casa', 450000.00, 4, 3, 380.00, 'Avenida la Reforma, Zona 10', 'Zona 10', DATE_SUB(NOW(), INTERVAL 15 DAY), 'activa'),
('Casa pequeña 2 habitaciones', 'Casa compacta en condominio privado, acceso a piscina y áreas verdes', 'casa', 180000.00, 2, 1, 120.00, '7a Avenida, Zona 10', 'Zona 10', DATE_SUB(NOW(), INTERVAL 20 DAY), 'activa'),

-- ZONA 10 - DEPARTAMENTOS
('Departamento moderno 3 hab', 'Apartamento en edificio con seguridad 24/7, vista a la ciudad', 'departamento', 145000.00, 3, 2, 110.00, 'Calzada Roosevelt, Zona 10', 'Zona 10', DATE_SUB(NOW(), INTERVAL 2 DAY), 'activa'),
('Departamento lujo 2 habitaciones', 'Penthouse con terraza privada, acabados de lujo, sistema inteligente', 'departamento', 280000.00, 2, 2, 95.00, 'Avenida la Reforma, Zona 10', 'Zona 10', DATE_SUB(NOW(), INTERVAL 7 DAY), 'activa'),
('Departamento estudiantes', 'Apartamento pequeño para estudiantes, cerca a universidad', 'departamento', 85000.00, 1, 1, 55.00, '7a Avenida, Zona 10', 'Zona 10', DATE_SUB(NOW(), INTERVAL 25 DAY), 'activa'),
('Departamento ejecutivo', 'Apartamento premium con gym, piscina, salón de eventos', 'departamento', 210000.00, 2, 2, 120.00, 'Calzada Roosevelt, Zona 10', 'Zona 10', DATE_SUB(NOW(), INTERVAL 10 DAY), 'activa'),

-- ZONA 10 - TERRENOS
('Terreno comercial 800m2', 'Terreno en esquina, ideal para comercio o proyecto residencial', 'terreno', 75000.00, NULL, NULL, 800.00, 'Avenida la Reforma, Zona 10', 'Zona 10', DATE_SUB(NOW(), INTERVAL 12 DAY), 'activa'),
('Terreno residencial 500m2', 'Lote urbano con servicios básicos, escritura al día', 'terreno', 55000.00, NULL, NULL, 500.00, '7a Avenida, Zona 10', 'Zona 10', DATE_SUB(NOW(), INTERVAL 18 DAY), 'activa'),

-- ZONA 15 - CASAS
('Casa elegante 4 habitaciones Zona 15', 'Casa en residencial privada, piscina, jardín amplio, 3 garajes', 'casa', 520000.00, 4, 3, 420.00, 'Vista Hermosa, Zona 15', 'Zona 15', DATE_SUB(NOW(), INTERVAL 8 DAY), 'activa'),
('Casa colonial 3 habitaciones', 'Casa con estilo colonial, patio interno, áreas comunes seguras', 'casa', 280000.00, 3, 2, 240.00, 'Boulevard Los Alamos, Zona 15', 'Zona 15', DATE_SUB(NOW(), INTERVAL 22 DAY), 'activa'),
('Casa nueva 2 habitaciones', 'Casa recién construida, moderna, con terraza', 'casa', 165000.00, 2, 1, 100.00, 'Calle Principal, Zona 15', 'Zona 15', DATE_SUB(NOW(), INTERVAL 3 DAY), 'activa'),

-- ZONA 15 - DEPARTAMENTOS
('Departamento 2 hab Zona 15', 'Apartamento en edificio moderno con elevador y estacionamiento', 'departamento', 135000.00, 2, 1, 85.00, 'Boulevard Los Alamos, Zona 15', 'Zona 15', DATE_SUB(NOW(), INTERVAL 6 DAY), 'activa'),
('Departamento familiar 3 hab', 'Apartamento amplio, ideal para familia, cocina integral, balcón', 'departamento', 165000.00, 3, 2, 115.00, 'Vista Hermosa, Zona 15', 'Zona 15', DATE_SUB(NOW(), INTERVAL 14 DAY), 'activa'),
('Departamento premium', 'Apartamento con acabados premium, vista panorámica, piscina', 'departamento', 195000.00, 2, 2, 105.00, 'Calle Principal, Zona 15', 'Zona 15', DATE_SUB(NOW(), INTERVAL 9 DAY), 'activa'),

-- ZONA 15 - TERRENOS
('Terreno 1000m2 Zona 15', 'Terreno grande para proyecto importante, con factibilidad de servicios', 'terreno', 120000.00, NULL, NULL, 1000.00, 'Boulevard Los Alamos, Zona 15', 'Zona 15', DATE_SUB(NOW(), INTERVAL 30 DAY), 'activa'),

-- OTROS TERRENOS
('Terreno industrial 2000m2', 'Terreno para uso industrial, acceso a carretera principal', 'terreno', 180000.00, NULL, NULL, 2000.00, 'Carretera a Petapa, Zona 3', 'Zona 3', DATE_SUB(NOW(), INTERVAL 35 DAY), 'activa'),
('Lote urbano 600m2', 'Lote en zona desarrollada, todos los servicios, listo para construir', 'terreno', 95000.00, NULL, NULL, 600.00, 'Avenida Simón Bolívar, Zona 8', 'Zona 8', DATE_SUB(NOW(), INTERVAL 28 DAY), 'activa');

-- ============================================================================
-- RELACIONES: PROPIEDADES Y AMENIDADES (Distribuir amenidades)
-- ============================================================================

-- Propiedad 1 (Casa 3 hab Zona 10) - Calzada Roosevelt
INSERT INTO propiedades_amenidades (propiedad_id, amenidad_id, distancia_km, notas) VALUES
(1, 1, 0.5, 'Muy cerca'),
(1, 6, 0.3, 'A una cuadra'),
(1, 9, 0.8, 'Accesible');

-- Propiedad 2 (Casa 4 hab Zona 10) - Avenida la Reforma
INSERT INTO propiedades_amenidades (propiedad_id, amenidad_id, distancia_km, notas) VALUES
(2, 2, 0.6, 'Cerca'),
(2, 7, 0.4, 'Muy cercano'),
(2, 10, 0.9, 'A poca distancia');

-- Propiedad 3 (Casa pequeña 2 hab) - 7a Avenida
INSERT INTO propiedades_amenidades (propiedad_id, amenidad_id, distancia_km, notas) VALUES
(3, 3, 0.7, 'Accesible'),
(3, 11, 1.2, 'Distancia moderada');

-- Propiedad 4 (Departamento 3 hab) - Calzada Roosevelt
INSERT INTO propiedades_amenidades (propiedad_id, amenidad_id, distancia_km, notas) VALUES
(4, 1, 0.4, 'Muy cerca'),
(4, 6, 0.2, 'A la esquina'),
(4, 12, 0.5, 'Cercano');

-- Propiedad 5 (Departamento lujo 2 hab) - Avenida la Reforma
INSERT INTO propiedades_amenidades (propiedad_id, amenidad_id, distancia_km, notas) VALUES
(5, 2, 0.5, 'Accesible'),
(5, 10, 0.7, 'Conveniente'),
(5, 13, 0.9, 'Moderna');

-- Propiedad 6 (Departamento estudiantes) - 7a Avenida
INSERT INTO propiedades_amenidades (propiedad_id, amenidad_id, distancia_km, notas) VALUES
(6, 3, 0.6, 'Acceso directo'),
(6, 11, 1.0, 'Camino');

-- Propiedad 7 (Departamento ejecutivo) - Calzada Roosevelt
INSERT INTO propiedades_amenidades (propiedad_id, amenidad_id, distancia_km, notas) VALUES
(7, 1, 0.3, 'Muy cerca'),
(7, 9, 0.5, 'Accesible'),
(7, 12, 0.4, 'Cercano');

-- Propiedad 8 (Terreno comercial) - Avenida la Reforma
INSERT INTO propiedades_amenidades (propiedad_id, amenidad_id, distancia_km, notas) VALUES
(8, 7, 0.6, 'Buen acceso'),
(8, 10, 0.8, 'Conveniente');

-- Propiedad 9 (Terreno residencial) - 7a Avenida
INSERT INTO propiedades_amenidades (propiedad_id, amenidad_id, distancia_km, notas) VALUES
(9, 11, 0.9, 'Accesible');

-- Propiedad 10 (Casa elegante 4 hab Zona 15) - Vista Hermosa
INSERT INTO propiedades_amenidades (propiedad_id, amenidad_id, distancia_km, notas) VALUES
(10, 4, 0.7, 'Cercano'),
(10, 8, 0.5, 'Buen acceso'),
(10, 14, 0.6, 'Conveniente');

-- Propiedad 11 (Casa colonial 3 hab) - Boulevard Los Alamos
INSERT INTO propiedades_amenidades (propiedad_id, amenidad_id, distancia_km, notas) VALUES
(11, 5, 0.4, 'Muy cerca'),
(11, 11, 0.3, 'A la esquina');

-- Propiedad 12 (Casa nueva 2 hab) - Calle Principal
INSERT INTO propiedades_amenidades (propiedad_id, amenidad_id, distancia_km, notas) VALUES
(12, 4, 0.6, 'Acceso directo'),
(12, 11, 0.5, 'Cercano');

-- Propiedad 13 (Departamento 2 hab Zona 15) - Boulevard Los Alamos
INSERT INTO propiedades_amenidades (propiedad_id, amenidad_id, distancia_km, notas) VALUES
(13, 5, 0.5, 'Muy cercano'),
(13, 8, 0.4, 'Accesible'),
(13, 11, 0.6, 'Conveniente');

-- Propiedad 14 (Departamento familiar 3 hab) - Vista Hermosa
INSERT INTO propiedades_amenidades (propiedad_id, amenidad_id, distancia_km, notas) VALUES
(14, 4, 0.5, 'Cercano'),
(14, 14, 0.7, 'Acceso directo');

-- Propiedad 15 (Departamento premium) - Calle Principal
INSERT INTO propiedades_amenidades (propiedad_id, amenidad_id, distancia_km, notas) VALUES
(15, 4, 0.4, 'Muy cerca'),
(15, 11, 0.5, 'Conveniente');

-- Propiedad 16 (Terreno 1000m2 Zona 15) - Boulevard Los Alamos
INSERT INTO propiedades_amenidades (propiedad_id, amenidad_id, distancia_km, notas) VALUES
(16, 8, 0.8, 'Buen acceso');

-- Propiedades 17-20 sin amenidades relaciones (terrenos no urbanos)

-- ============================================================================
-- VERIFICACIÓN DE DATOS
-- ============================================================================
-- SELECT COUNT(*) as total_propiedades FROM propiedades;
-- SELECT COUNT(*) as total_amenidades FROM amenidades;
-- SELECT COUNT(*) as total_relaciones FROM propiedades_amenidades;
