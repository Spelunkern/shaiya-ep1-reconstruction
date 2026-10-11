# Identidad, entrega y aceptación

## Identidad del trabajo

La baseline enlaza el inventario completo, el exportador, el planificador, la
versión de Ghidra y los hashes de todos los exports. Su `baseline_id` aparece en
cada bloque, reserva y entrega. El catálogo también tiene checksum propio.

Un bloque de función se identifica como `<binary_id>-fn-<entry_rva>`. Sus rangos
son RVA semiabiertos `[inicio, fin)`, ordenados; no se presupone un único intervalo.
El digest del cuerpo es SHA-256 de los bytes concatenados en ese orden. No cortar
funciones para equilibrar carga. Las referencias del análisis inicial son evidencia
parcial; no sustituyen la investigación de llamadas indirectas y callbacks.

| Tipo | Trabajo esperado |
|---|---|
| `function` | Fuente y contrato de una función completa |
| `data` | Globals, tablas, estructuras, recursos o relleno; descripción y generación reproducible |
| `unclassified` | Determinar si son instrucciones, datos, relleno o contenido opaco; aportar evidencia |
| `integration` | Cabeceras y bytes de archivo no incluidos en secciones, imports, exports, recursos, relocaciones, ABI y build completo |

Las regiones de datos y las no clasificadas se acotan a 64 KiB como tareas de
inspección. Ese límite **no afirma** que tengan independencia semántica ni que
sean funciones. Una tabla que cruza límites necesita coordinar sus bloques.
Los ceros virtuales forman parte de la imagen PE; no se confunden con bytes
presentes en el archivo. Los bloques de integración registran los intervalos
de archivo externos a las secciones, incluidos cabeceras y posibles overlays.

Los saltos o llamadas directas cuyo destino no es una entrada de función conocida
requieren revisar límites y propiedad del código antes de reservar el bloque.
Un salto al interior de otra función puede esconder un cuerpo compartido aunque
los rangos de Ghidra no se superpongan. `--available`, `claim` y `start` excluyen
estos casos; descubrir nuevas entradas exige la migración descrita más abajo.

Los cuerpos compartidos se registran en `blocks/baseline.json` y se bloquean para
reservas normales. Padding y recursos siguen como tareas pendientes hasta su
clasificación; contarlos en el catálogo no significa que estén reconstruidos.

## Contratos e integración

Dentro de un binario usar nombres estables: `ep1_<binary_id>_<rva>` para funciones
y `data_<rva>` para datos. Documentar cualquier nombre semántico como alias.
La implementación puede usar C o C++ según la evidencia. No adoptar el supuesto
`__cdecl` de Ghidra sin comprobar pila, registros y callers.

Documentar tamaño y offsets de cada tipo, alineación, padding, signo, ownership
y vida útil. Los cambios de tipos compartidos deben identificar todos los bloques
que los usan. El catálogo incluye dependencias de llamadas/saltos a entradas
conocidas y de referencias estáticas a regiones de datos; los contratos adicionales
hallados por el contribuidor se documentan en el análisis, con evidencia.

El integrador traslada o referencia una implementación aceptada por símbolo en
`reconstruction/<binary_id>/`, mantiene un mapa símbolo → bloque y evita definiciones
duplicadas. Los builds de integración deben fallar ante símbolos no reconstruidos;
no se completa artificialmente el enlace con stubs. El entorno y compilador originales
aún deben determinarse. Los recursos y datos distribuidos conservan su propia
identidad en el inventario. Las bases de datos requieren una fase de extracción
y reconstrucción de esquema si se pretende sustituir también su formato original.

## Estados y prueba

`draft` y `ready` son estados del aporte. `ready` exige archivos de fuente,
evidencia, tests, un análisis, contratos de dependencias y `unknowns` vacío;
una función además requiere ABI. La CLI valida esa estructura, sin ejecutar
comandos arbitrarios de la entrega ni certificar su contenido.

La revisión tiene etapas separadas:

1. `source_reviewed`: comparación manual de fuente, ensamblador y contratos.
2. `block_validated`: build y pruebas contra el original, con comandos y logs.
3. `integrated`: el aporte participa en una reconstrucción que pasa pruebas de
   integración del binario completo, con el alcance y los límites documentados.

El revisor independiente reproduce los resultados y prepara un `proof.json`
declarado en `evidence_files`. Para validación, usar esta estructura:

```json
{
  "environment": "OS, arquitectura, compilador, opciones y harness concretos",
  "reasoning": "Qué equivalencia se comprobó y sus límites",
  "build": {"result": "pass", "command": "COMANDO_REAL", "log": "logs/build.log"},
  "comparison": {
    "result": "pass",
    "command": "COMANDO_REAL",
    "log": "logs/comparison.log",
    "original_sha256": "SHA256_COMPLETO_DEL_BINARIO",
    "method": "Método reproducible: ejecución, emulación o prueba sobre instrucciones",
    "cases": ["Casos reales y condiciones límite verificadas"]
  },
  "limitations": ["Límites específicos de esta comparación"]
}
```

Para `integrated`, añadir `integration` con `result`, `command` y `log` del binario
completo. Todos los logs deben estar declarados. El registro se crea con:

```bash
python3 tools/reverse.py review ID_DEL_BLOQUE --reviewer REVISOR \
  --stage block_validated --proof proof.json
python3 tools/reverse.py validate
```

El registro guarda un digest de la entrega, fuente, pruebas y evidencia. Modificar
cualquiera invalida la evaluación. Un nombre de revisor en JSON no es autenticación;
solo la revisión y aceptación del mantenedor en la rama protegida hace oficial
ese estado. Configurar protección de `main` y revisión obligatoria antes de
abrir contribuciones públicas. Los PR no deben cambiar reservas ajenas ni
introducir evaluaciones propias. CI no contiene secretos ni ejecuta los binarios.

No hay un porcentaje único que pruebe el objetivo. Medir función/datos clasificados,
fuente revisada, bloques validados, integración y pruebas de sistema por separado.
Una comparación byte a byte exige además reproducir layout, herramientas y opciones;
las pruebas finitas de comportamiento no constituyen por sí solas una prueba universal.

## Cambios de baseline

Corregir funciones mal delimitadas, descubrir código oculto o dividir una región
exige una nueva baseline. No renumerar tareas dentro de la existente. El mantenedor
conserva la versión anterior, publica un mapa `old_id → new_id`, revisa reservas y
aportes afectados y vuelve a verificar cobertura y cuerpos. La CLI inicial rechaza
recrear inventario o plan sobre archivos congelados; una migración debe realizarse
en una nueva versión de trabajo y preservar explícitamente la anterior.
