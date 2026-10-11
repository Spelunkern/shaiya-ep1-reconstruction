# Contribuir un bloque

## 1. Preparar una copia reproducible

Clonar el repositorio y obtener el paquete de originales de la misma versión.
Extraerlo en la raíz para obtener `Client/` y `Server/`. Seguir
`docs/DISTRIBUTION.md` y `docs/TOOLCHAIN.md`.

```bash
python3 tools/reverse.py verify
python3 tools/reverse.py audit --originals
python3 tools/reverse.py list --kind function --available --max-instructions 30 --limit 20
```

Empezar con una función pequeña, pocas dependencias y sin cuerpo compartido ni
flujos directos pendientes de resolver. `--available` excluye esos impedimentos. El
catálogo muestra cantidad de instrucciones, sin estimar dificultad semántica.
Leer el bloque completo con `show`: una función corta puede ser un thunk o
requerir conocimiento de un objeto grande.

## 2. Reservar antes de invertir trabajo

Actualizar la rama principal y crear una rama para la reserva.

```bash
python3 tools/reverse.py claim ID_DEL_BLOQUE --owner USUARIO_GITHUB
```

Enviar un PR que incluya únicamente `claims/<block_id>.json`. Esperar su merge
por un mantenedor y actualizar la copia local antes de comenzar. La creación
local usa exclusión de archivo, pero **no ofrece exclusión entre clones**; el
merge de la reserva en la rama principal resuelve la concurrencia. Una issue
puede servir para coordinar; no sustituye la reserva aceptada. Las reservas
vencen en siete días; su renovación o reasignación requiere un cambio revisado.

## 3. Crear el aporte y reunir evidencia

```bash
python3 tools/reverse.py start ID_DEL_BLOQUE --owner USUARIO_GITHUB
python3 tools/reverse.py analyze --binary ID_DEL_BINARIO
python3 tools/reverse.py export ID_DEL_BLOQUE
```

`analyze` usa los originales verificados y la versión fijada de Ghidra. En un
clon nuevo genera el proyecto local y exige que el export coincida con la
baseline publicada. Si difiere, conservar logs y consultar al mantenedor;
no sobrescribir el catálogo. `export` produce listado de instrucciones y
pseudocódigo en `work/evidence/<block_id>/`, usando el proyecto en modo de lectura.
Para bloques de datos o clasificación, inspeccionar los rangos en Ghidra.

Entregar al agente el contenido de `docs/AGENT_PROMPT.md` con el ID y el usuario.
El agente debe reconstruir y probar ese alcance, documentando dudas y contratos.
Copiar la evidencia pertinente al aporte y declararla en `submission.json`.

## 4. Implementar y probar

El aporte vive en `contributions/<block_id>/`:

```text
submission.json
analysis.md
src/function.cpp
include/contract.h
original/listing.txt
original/decompiled.c
proof.json
logs/build.log
logs/comparison.log
tests/...
```

`decompiled.c` es evidencia, no el archivo de producción. Declarar solo los
archivos existentes en `source_files`, `evidence_files` y `test_files`. Describir
ABI, efectos de memoria y contratos de todas las dependencias del catálogo.
Registrar además las llamadas indirectas y referencias no resueltas; que Ghidra
no encuentre una arista no demuestra que no exista.

No hay un compilador C++ original identificado todavía. Una contribución debe
registrar el compilador usado y sus límites; la aceptación de ABI exige un
entorno Windows x86 o una comparación equivalente documentada. Las pruebas
portables de lógica pueden ejecutarse por separado. No agregar stubs a producción
para obtener una compilación aparentemente completa.

## 5. Enviar para revisión

Mantener `status: "draft"` mientras queden incógnitas. Cambiar a `"ready"` solo
cuando haya fuente, evidencia, pruebas, contrato ABI y preguntas resueltas.

```bash
python3 tools/reverse.py validate --block ID_DEL_BLOQUE
```

Enviar un PR con el bloque, la baseline y los resultados. Un PR puede incluir
varios bloques solo si cada uno tiene reserva y entrega separadas. No modificar
otros bloques para ajustar hipótesis. Los cambios de contratos compartidos se
coordinan antes y deben identificar consumidores.

El revisor usa `docs/PROTOCOL.md`, reproduce las pruebas y registra la evaluación.
Un aporte editado después de una evaluación invalida su digest. El mantenimiento
de la rama principal decide la aceptación; los campos JSON no autentican personas.
