#!/usr/bin/env python3
"""Corrector SQLite ultra-robusto que detecta y corrige problemas automáticamente"""

import re
import os

def find_and_fix_sqlite_issues():
    sql_file = "src/infrastructure/database/sql_telemetry_repository.py"
    
    print(f"📖 Analizando archivo: {sql_file}")
    
    if not os.path.exists(sql_file):
        print(f"❌ Archivo no encontrado: {sql_file}")
        print("💡 Asegúrate de estar en: ~/Proyecto-UrbIA/urbia-clean")
        return False
    
    # Leer archivo
    with open(sql_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    print(f"📄 Archivo leído: {len(lines)} líneas")
    
    # Crear backup
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_file = f"{sql_file}.backup.critical.{timestamp}"
    with open(backup_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Backup creado: {backup_file}")
    
    # Buscar y corregir problemas de SQL
    fixed_content = []
    in_create_table = False
    table_level = 0
    fixes_applied = []
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        
        # Detectar inicio de CREATE TABLE de telemetry_records
        if 'CREATE TABLE IF NOT EXISTS telemetry_records' in line_stripped:
            in_create_table = True
            table_level = line_stripped.count('(') - line_stripped.count(')')
            fixed_content.append(line)
            print(f"🎯 Encontrado CREATE TABLE en línea {i+1}")
            continue
        
        # Si estamos dentro del CREATE TABLE
        if in_create_table:
            # Detectar problemas específicos de SQL
            
            # Problema 1: INDEX dentro de CREATE TABLE
            if 'INDEX_' in line_stripped and not line_stripped.startswith('CREATE INDEX'):
                fixes_applied.append(f"INDEX removido de CREATE TABLE (línea {i+1}): {line_stripped}")
                continue  # Saltar líneas de INDEX dentro del CREATE TABLE
            
            # Problema 2: Coma extra antes del cierre de paréntesis
            if line_stripped.endswith(' ,') or line_stripped.endswith(' ,'):
                # Remover coma extra
                fixed_line = line.rstrip(' ,').rstrip()
                fixed_content.append(fixed_line)
                fixes_applied.append(f"Coma extra removida (línea {i+1})")
                print(f"🔧 Corregida coma extra en línea {i+1}")
                continue
            
            # Problema 3: Cierre de paréntesis con coma antes
            if '),' in line_stripped and table_level <= 0:
                fixed_line = line.replace('),', ')')
                fixed_content.append(fixed_line)
                fixes_applied.append(f"Paréntesis con coma corregido (línea {i+1})")
                print(f"🔧 Corregido paréntesis en línea {i+1}")
                continue
            
            # Actualizar nivel de paréntesis
            table_level += line_stripped.count('(') - line_stripped.count(')')
            
            # Verificar si salimos del CREATE TABLE
            if table_level <= 0 and ')' in line_stripped and in_create_table:
                in_create_table = False
                fixed_content.append(line)
                print(f"✅ Salimos del CREATE TABLE en línea {i+1}")
                continue
        
        # Línea normal, agregar tal como está
        fixed_content.append(line)
    
    # Reconstruir contenido
    fixed_sql_content = '\n'.join(fixed_content)
    
    # Aplicar corrección adicional: buscar y reemplazar el SQL problemático completo
    print("\n🔧 Aplicando corrección avanzada...")
    
    # Patrón más específico para detectar el problema exacto
    problem_patterns = [
        r'cursor\.execute\(.*?CREATE TABLE IF NOT EXISTS telemetry_records.*?\)',  # Patrón general
        r'cursor\.execute\(\"\"\"(.*?)CREATE TABLE IF NOT EXISTS telemetry_records(.*?)\"\"\"',  # Patrón con """ 
    ]
    
    corrected = False
    for pattern in problem_patterns:
        matches = re.search(pattern, fixed_sql_content, re.DOTALL)
        if matches:
            # Si encontramos el patrón problemático, aplicar corrección completa
            fixed_sql_content = re.sub(
                pattern,
                '''cursor.execute("""
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
            """)''',
                fixed_sql_content,
                flags=re.DOTALL
            )
            corrected = True
            print("✅ Aplicada corrección completa de CREATE TABLE")
            break
    
    # Si no se corrigió con patrones, aplicar corrección línea por línea más agresiva
    if not corrected:
        print("🔧 Aplicando corrección línea por línea...")
        lines_to_fix = fixed_sql_content.split('\n')
        final_lines = []
        
        for line in lines_to_fix:
            # Limpiar comas extra antes del final del CREATE TABLE
            if 'created_at TEXT NOT NULL,' in line:
                line = line.replace(',', '')  # Remover la coma
                print("🔧 Removida coma final de created_at")
            
            # Remover líneas con INDEX que puedan quedar
            if line.strip().startswith('INDEX_'):
                print(f"🗑️ Removida línea INDEX residual: {line.strip()}")
                continue
                
            final_lines.append(line)
        
        fixed_sql_content = '\n'.join(final_lines)
    
    # Escribir archivo corregido
    print(f"\n💾 Escribiendo archivo corregido...")
    with open(sql_file, 'w', encoding='utf-8') as f:
        f.write(fixed_sql_content)
    
    # Resumen de correcciones
    print(f"\n🎉 CORRECCIÓN COMPLETADA")
    print(f"📊 Resumen de correcciones:")
    for fix in fixes_applied:
        print(f"   ✅ {fix}")
    
    if not fixes_applied:
        print(f"   ℹ️  No se detectaron problemas obvios de sintaxis")
        print(f"   💡 El archivo ya puede estar corregido o tener un problema diferente")
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("🔧 CORRECTOR SQLITE ULTRA-ROBUSTO")
    print("=" * 60)
    find_and_fix_sqlite_issues()
