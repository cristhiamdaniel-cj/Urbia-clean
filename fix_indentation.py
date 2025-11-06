#!/usr/bin/env python3
"""Corrector de indentación para el archivo SQL"""

import re

def fix_indentation():
    sql_file = "src/infrastructure/database/sql_telemetry_repository.py"
    
    print(f"📖 Leyendo archivo: {sql_file}")
    with open(sql_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    print(f"📄 Archivo leído: {len(lines)} líneas")
    
    # Crear backup
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_file = f"{sql_file}.backup.indent.{timestamp}"
    with open(backup_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Backup creado: {backup_file}")
    
    # Corregir indentación - buscar líneas con indentación incorrecta
    fixed_lines = []
    fixes_applied = []
    
    for i, line in enumerate(lines, 1):
        line_stripped = line.strip()
        
        # Si la línea empieza con -- (comentario) pero tiene indentación incorrecta
        if line_stripped.startswith('--') and not line.startswith('            --'):
            # Reducir indentación
            if line.startswith('                --'):
                fixed_lines.append('            --' + line_stripped[2:])
                fixes_applied.append(f"Indentación de comentario corregida (línea {i})")
                continue
            elif line.startswith('            --'):
                # Ya tiene buena indentación, agregar tal como está
                fixed_lines.append(line)
                continue
        
        # Si la línea es CREATE INDEX pero tiene indentación incorrecta
        if line_stripped.startswith('CREATE INDEX') and not line.startswith('            '):
            if line.startswith('                '):
                fixed_lines.append('            ' + line_stripped)
                fixes_applied.append(f"Indentación de CREATE INDEX corregida (línea {i})")
                continue
        
        # Línea normal o que ya está bien
        fixed_lines.append(line)
    
    # Reconstruir contenido
    fixed_content = '\n'.join(fixed_lines)
    
    # Aplicar corrección adicional para asegurar que los CREATE INDEX estén bien indentados
    print("\n🔧 Aplicando corrección adicional de indentación...")
    
    # Reemplazar patrones problemáticos de indentación
    patterns_to_fix = [
        # Comentarios con indentación excesiva
        (r'                --(.*?)\n', r'            --\1\n'),
        # CREATE INDEX con indentación excesiva
        (r'                CREATE INDEX', r'            CREATE INDEX'),
        # Líneas que pueden tener problemas
        (r'                (cursor\.execute.*INDEX.*)\n', r'            \1\n'),
    ]
    
    for pattern, replacement in patterns_to_fix:
        if re.search(pattern, fixed_content):
            fixed_content = re.sub(pattern, replacement, fixed_content)
            fixes_applied.append(f"Patrón de indentación corregido: {pattern[:20]}...")
    
    # Escribir archivo corregido
    print(f"\n💾 Escribiendo archivo con indentación corregida...")
    with open(sql_file, 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    # Resumen
    print(f"\n🎉 CORRECCIÓN DE INDENTACIÓN COMPLETADA")
    print(f"📊 Resumen de correcciones:")
    for fix in fixes_applied:
        print(f"   ✅ {fix}")
    
    if not fixes_applied:
        print(f"   ℹ️  No se detectaron problemas de indentación")
    
    return True

if __name__ == "__main__":
    print("=" * 50)
    print("🔧 CORRECTOR DE INDENTACIÓN SQL")
    print("=" * 50)
    fix_indentation()
