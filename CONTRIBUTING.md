# Contribuir un bloque con un agente de IA

El proyecto oficial es [Spelunkern/shaiya-ep1-reconstruction](https://github.com/Spelunkern/shaiya-ep1-reconstruction).
Los binarios ya están incluidos. El [primer bloque](docs/FIRST_BLOCK.md) muestra
una entrega real y cómo repetir sus pruebas.

## 1. Preparar el fork

Crear un fork desde GitHub, clonarlo y agregar el upstream. Con GitHub CLI:

```bash
gh repo fork Spelunkern/shaiya-ep1-reconstruction --clone
cd shaiya-ep1-reconstruction
git remote -v
# Si gh no creó upstream:
git remote add upstream https://github.com/Spelunkern/shaiya-ep1-reconstruction.git
```

No agregar un upstream duplicado: comprobar primero `git remote -v`.
Desde la raíz del fork:

```bash
python3 tools/reverse.py verify
python3 tools/reverse.py audit --originals
python3 tools/reverse.py list --kind function --available --max-instructions 30 --limit 20
```

Revisar `show ID_DEL_BLOQUE`. Empezar con pocas instrucciones y dependencias.
`--available` excluye reservas, entregas existentes y flujos directos pendientes;
una función corta todavía puede ser un thunk o requerir contratos complejos.
No elegir el bloque de ejemplo: ya tiene una entrega.

## 2. Reservar centralmente

Sustituir los valores en mayúsculas por el ID del catálogo y el usuario de GitHub:

```bash
git fetch upstream
git switch -c claim/ID_DEL_BLOQUE upstream/main
python3 tools/reverse.py claim ID_DEL_BLOQUE --owner USUARIO_GITHUB
git add claims/ID_DEL_BLOQUE.json
git commit -m "Reserve ID_DEL_BLOQUE"
git push -u origin HEAD
gh pr create --repo Spelunkern/shaiya-ep1-reconstruction --base main \
  --title "Reserve ID_DEL_BLOQUE" --body "Reservation for USUARIO_GITHUB"
```

Esperar el merge del PR de reserva en upstream. La creación del archivo local es
exclusiva, pero no es un bloqueo entre clones; la rama principal es la autoridad.
Una issue puede coordinar la tarea, pero no sustituye la reserva aceptada.
Las reservas vencen en siete días; renovación o reasignación requiere revisión.
Los aportes entregados no vuelven a ser tareas libres al vencer la reserva.

## 3. Iniciar el trabajo reservado

Después de que la reserva esté aceptada:

```bash
git fetch upstream
git switch -c reverse/ID_DEL_BLOQUE upstream/main
python3 tools/reverse.py start ID_DEL_BLOQUE --owner USUARIO_GITHUB
mkdir -p work
python3 tools/reverse.py prompt ID_DEL_BLOQUE --owner USUARIO_GITHUB > work/task.md
```

Abrir el agente en la raíz del fork y darle el contenido de `work/task.md`.
La [guía para agentes](docs/AGENT_GUIDE.md) fija el procedimiento completo.
El prompt incluye el ID del binario, su ruta, SHA-256 y baseline.

Instalar el Ghidra/JDK fijados según `docs/TOOLCHAIN.md`; luego:

```bash
python3 tools/reverse.py analyze --binary ID_DEL_BINARIO
python3 tools/reverse.py export ID_DEL_BLOQUE
```

En un clon nuevo, `analyze` genera el proyecto y exige que el export reproduzca
la baseline. Si difiere, conservar logs y presentar el diagnóstico; no cambiar
el catálogo. Para datos o clasificación, inspeccionar los rangos directamente.

## 4. Completar la entrega

Toda la implementación del bloque vive en `contributions/<block_id>/`:

```text
submission.json
analysis.md
src/...
include/...
original/listing.txt
original/decompiled.c
proof.json
logs/build.log
logs/comparison.log
tests/...
```

Registrar análisis por dirección, ABI, tipos y offsets, efectos y contratos de
todas las dependencias del catálogo. Investigar llamadas indirectas, callbacks y
referencias pendientes. `decompiled.c` es evidencia, no fuente de producción.

Los tests deben contrastar el comportamiento con evidencia del original, detectar
desviaciones e incluir condiciones límite. Conservar comandos reales, versiones,
logs y límites de cada comparación. La compilación de lógica en Linux de 64 bits
no valida el ABI Windows x86. No añadir stubs de producción para lograr enlace.

Declarar en `source_files`, `test_files` y `evidence_files` todos los archivos
necesarios para reconstruir y repetir la evaluación. Las modificaciones de tipos
compartidos van en propuestas coordinadas con sus consumidores.

## 5. Proponer el bloque

Mantener `draft` si faltan contratos o verificaciones. Usar `ready` cuando se
cumpla `docs/PROTOCOL.md` y `unknowns` esté vacío. `ready` no equivale a aprobación.

```bash
python3 tools/reverse.py validate --block ID_DEL_BLOQUE
# Ejecutar también el comando de pruebas real de tu bloque.
git add contributions/ID_DEL_BLOQUE
git commit -m "Reconstruct ID_DEL_BLOQUE"
git push -u origin HEAD
gh pr create --repo Spelunkern/shaiya-ep1-reconstruction --base main
```

Completar la plantilla del PR con comportamiento, baseline, ABI, pruebas y límites.
Cada bloque necesita su propia reserva y entrega, incluso si un PR coordina varios.
No incluir archivos generados en `work/`, cambios a los originales ni evaluaciones
propias. El revisor independiente reproduce los resultados; el mantenedor acepta
la evaluación en la rama principal. Editar el aporte invalida una revisión previa.
