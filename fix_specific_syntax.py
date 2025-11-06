#!/usr/bin/env python3
"""Corrector específico para el SyntaxError en línea 217"""

import re

def fix_specific_syntax_error():
    sql_file = "src/infrastructure/database/sql_telemetry_repository.py"
    
    print(f"📖 Leyendo archivo: {sql_file}")
    with open(sql_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    print(f"📄 Archivo leído: {len(lines)} líneas")
    
    # Crear backup
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_file = f"{sql_file}.backup.syntax.{timestamp}"
    with open(backup_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Backup creado: {backup_file}")
    
    # Mostrar líneas alrededor de 217 para entender el contexto
    print(f"\n📋 Contexto alrededor de línea 217:")
    start_line = max(0, 217 - 5)
    end_line = min(len(lines), 217 + 5)
    for i in range(start_line, end_line):
        line_marker = ">>>" if i == 217 - 1 else "   "
        print(f"{line_marker} Línea {i+1}: {repr(lines[i])}")
    
    # Corregir problemas específicos
    fixed_lines = []
    fixes_applied = []
    
    for i, line in enumerate(lines, 1):
        line_stripped = line.strip()
        
        # Problema específico: línea de comentario SQL mal placed
        if i == 217 and line_stripped == "-- Crear índices reales":
            # Si es la línea problemática, verificar el contexto
            prev_line = lines[i-2] if i > 2 else ""
            next_line = lines[i] if i < len(lines) else ""
            
            print(f"🔍 Analizando línea 217: {repr(line)}")
            print(f"   Línea anterior: {repr(prev_line)}")
            print(f"   Línea actual: {repr(next_line)}")
            
            # Si el comentario está después de un cursor.execute() sin cerrar, corregir
            if prev_line.strip().endswith('cursor.execute("""') or prev_line.strip().endswith('cursor.execute(\'\'\''):
                # Mover el comentario fuera del cursor.execute()
                fixed_lines.append('            """')  # Cerrar el cursor.execute()
                fixed_lines.append('')
                fixed_lines.append('            -- Crear índices reales')
                fixes_applied.append(f"Comentario movido fuera de cursor.execute() (línea {i})")
                continue
            elif 'cursor.execute(' in prev_line and not prev_line.strip().endswith('"""'):
                # Cursor.execute sin cerrar
                fixed_lines.append(prev_line + '"""')
                fixed_lines.append('')
                fixed_lines.append('            -- Crear índices reales')
                fixes_applied.append(f"cursor.execute() cerrado y comentario movido (línea {i})")
                continue
            else:
                # Solo agregar el comentario con indentación correcta
                fixed_lines.append('            -- Crear índices reales')
                fixes_applied.append(f"Comentario con indentación corregida (línea {i})")
                continue
        
        # Verificar si hay problemas con comentarios mal placed en general
        if '-- Crear índices reales' in line and 'cursor.execute(' in lines[i-3] if i > 3 else False:
            # Problema detectado: comentario dentro de cursor.execute()
            if i > 3:
                lines[i-3] = lines[i-3] + '"""'
                fixes_applied.append(f"cursor.execute() cerrado en línea {i-2}")
            
            # Reemplazar la línea problemática
            fixed_lines.append('            -- Crear índices reales')
            fixes_applied.append(f"Comentario reubicado (línea {i})")
            continue
        
        # Verificar problemas con CREATE INDEX mal formed
        if 'cursor.execute(' in line and 'CREATE INDEX' in line and line_stripped.count('"') % 2 == 1:
            # Cursor.execute mal cerrado
            if not line.strip().endswith('"""'):
                fixed_lines.append(line + '"')
                fixes_applied.append(f"cursor.execute() cerrado (línea {i})")
                continue
        
        # Línea normal
        fixed_lines.append(line)
    
    # Reconstruir contenido
    fixed_content = '\n'.join(fixed_lines)
    
    # Aplicar corrección específica para el patrón problemático
    print(f"\n🔧 Aplicando corrección específica para el patrón problemático...")
    
    # Buscar y corregir el patrón específico: cursor.execute con comentario mal placed
    problem_pattern = r'(cursor\.execute\(\"\"\".*?)-- Crear índices reales(.*?\)\)') 
    if re.search(problem_pattern, fixed_content, re.DOTALL):
        # Reemplazar por cursor.execute cerrado + comentario fuera
        fixed_content = re.sub(
            problem_pattern,
            r'\1"""\n            \n            -- Crear índices reales\2',
            fixed_content,
            flags=re.DOTALL
        )
        fixes_applied.append("Patrón cursor.execute con comentario corregido")
    
    # También corregir cualquier cursor.execute incompleto
    incomplete_cursor_pattern = r'(cursor\.execute\(\"\"\"[^"]*?)"(?!"""|")'
    if re.search(incomplete_cursor_pattern, fixed_content):
        fixed_content = re.sub(incomplete_cursor_pattern, r'\1"""', fixed_content)
        fixes_applied.append("cursor.execute() incompleto corregido")
    
    # Escribir archivo corregido
    print(f"\n💾 Escribiendo archivo corregido...")
    with open(sql_file, 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    # Resumen
    print(f"\n🎉 CORRECCIÓN ESPECÍFICA COMPLETADA")
    print(f"📊 Resumen de correcciones:")
    for fix in fixes_applied:
        print(f"   ✅ {fix}")
    
    if not fixes_applied:
        print(f"   ℹ️  No se detectaron problemas específicos")
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("🔧 CORRECTOR ESPECÍFICO DE SYNTAX ERROR")
    print("=" * 60)
    fix_specific_syntax_error()
