#!/usr/bin/env python3
"""Corrección directa del archivo SQL con sintaxis correcta"""

def fix_sql_file():
    sql_file = "src/infrastructure/database/sql_telemetry_repository.py"
    
    print(f"📖 Leyendo archivo: {sql_file}")
    try:
        with open(sql_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"❌ No se encontró el archivo: {sql_file}")
        print("   Asegúrate de estar en el directorio ~/Proyecto-UrbIA/urbia-clean")
        return False
    
    print("🔧 Corrigiendo sintaxis SQL...")
    
    # Crear backup
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_file = f"{sql_file}.backup.{timestamp}"
    
    with open(backup_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Backup creado: {backup_file}")
    
    # Reemplazar el CREATE TABLE problemático completo
    old_table_sql = '''cursor.execute(\"\"\"
                CREATE TABLE IF NOT EXISTS telemetry_records (
                    id TEXT PRIMARY KEY,
                    sensor_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    data_type TEXT NOT NULL,
                    value REAL NOT NULL,
                    unit TEXT NOT NULL,
                    location_lat REAL NOT NULL,
                    location_lng REAL NOT NULL,
                    priority TEXT NOT NULL,
                    gateway_id TEXT,
                    metadata_json TEXT,
                    processed BOOLEAN DEFAULT FALSE,
                    created_at TEXT NOT NULL,
                )
            \"\"\")'''
    
    new_table_sql = '''cursor.execute(\"\"\"
                CREATE TABLE IF NOT EXISTS telemetry_records (
                    id TEXT PRIMARY KEY,
                    sensor_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    data_type TEXT NOT NULL,
                    value REAL NOT NULL,
                    unit TEXT NOT NULL,
                    location_lat REAL NOT NULL,
                    location_lng REAL NOT NULL,
                    priority TEXT NOT NULL,
                    gateway_id TEXT,
                    metadata_json TEXT,
                    processed BOOLEAN DEFAULT FALSE,
                    created_at TEXT NOT NULL
                )
            \"\"\")'''
    
    # Hacer el reemplazo
    if old_table_sql in content:
        content = content.replace(old_table_sql, new_table_sql)
        print("✅ CREATE TABLE corregido (eliminada coma extra)")
    else:
        print("⚠️ No se encontró el patrón exacto de CREATE TABLE")
    
    # Eliminar cualquier línea con INDEX dentro del CREATE TABLE que pueda quedar
    lines = content.split('\n')
    fixed_lines = []
    in_create_table = False
    create_table_level = 0
    
    for line in lines:
        stripped = line.strip()
        
        # Detectar inicio de CREATE TABLE
        if 'CREATE TABLE IF NOT EXISTS telemetry_records' in stripped:
            in_create_table = True
            create_table_level = stripped.count('(') - stripped.count(')')
        
        # Si estamos dentro del CREATE TABLE, verificar si es línea de INDEX
        if in_create_table:
            if stripped.startswith('INDEX_') or 'INDEX_' in stripped:
                print(f"🗑️ Eliminando línea de INDEX: {stripped}")
                continue  # Saltar esta línea
        
        # Actualizar nivel de anidación
        if in_create_table:
            parens_in_line = stripped.count('(')
            parens_out_line = stripped.count(')')
            create_table_level += parens_in_line - parens_out_line
            
            if create_table_level <= 0 and ')' in stripped:
                in_create_table = False
        
        fixed_lines.append(line)
    
    # Unir de vuelta
    content = '\n'.join(fixed_lines)
    
    # Escribir archivo corregido
    print(f"💾 Escribiendo archivo corregido: {sql_file}")
    with open(sql_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("🎉 Corrección SQLite completada exitosamente")
    return True

if __name__ == "__main__":
    print("=== CORRECCIÓN SQLITE PARA URBA ===")
    fix_sql_file()
