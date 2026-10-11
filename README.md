# Shaiya EP1 — reconstrucción comunitaria

Repositorio de trabajo para reconstruir desde los binarios del corpus preparado
el cliente, los servicios, las herramientas y las DLL de Shaiya EP1. Cada aporte
se vincula a un binario concreto, un bloque y una baseline reproducible de Ghidra.

El objetivo es obtener fuente mantenible y reconstrucciones verificadas de todos
los binarios. El inventario inicial contiene **394 archivos, 27 rutas PE y 23
binarios únicos**, con **1.846.545.691 bytes** de originales. El estado inicial y
el número real de bloques se describen en [el análisis inicial](docs/INITIAL_ANALYSIS.md).

La recuperación literal del fuente original —comentarios, nombres eliminados,
macros o estructura de proyectos— no se puede garantizar desde un ejecutable.
Se mide por separado cobertura del binario, fuente reconstruida, pruebas de
comportamiento e integración; la identidad byte a byte es una meta adicional que
requiere reproducir compilador, enlazador y opciones originales.

Para contribuir, seguir [CONTRIBUTING.md](CONTRIBUTING.md) y entregar al agente el
[prompt de trabajo](docs/AGENT_PROMPT.md). Las instrucciones obligatorias para
agentes están en [AGENTS.md](AGENTS.md).

```bash
python3 tools/reverse.py list --kind function --available --limit 20
python3 tools/reverse.py show ID_DEL_BLOQUE
python3 tools/reverse.py report
```

El catálogo fija los rangos de funciones detectadas por Ghidra; conserva rangos
discontinuos y detecta
cuerpos compartidos. También incluye datos, regiones ejecutables sin clasificar
y tareas de integración. Los límites semánticos requieren revisión: los flujos directos no resueltos
bloquean reservas normales. El número de bloques resulta del análisis, sin fijar
artificialmente 10.000. Las DLL idénticas en varias carpetas comparten un único
catálogo, con todas sus rutas registradas.

| Ruta | Contenido |
|---|---|
| `Client/`, `Server/` | Originales intactos, presentes en la copia local |
| `manifests/` | Identidad SHA-256 de todo el corpus y herramientas fijadas |
| `analysis/baseline/` | Funciones, rangos y referencias exportados por Ghidra |
| `blocks/` | Catálogo congelado y su identidad |
| `claims/` | Reservas aceptadas en la rama principal |
| `contributions/` | Fuente, contratos, análisis, pruebas y evidencia por bloque |
| `reviews/` | Evaluaciones vinculadas al contenido exacto del aporte |
| `reconstruction/` | Integración de aportes aceptados en proyectos compilables |
| `work/` | Proyectos locales de Ghidra, herramientas y logs; fuera de Git |

Los originales se distribuyen como un paquete separado, verificable y asociado
al repositorio. Esto incluye la carpeta completa, sin introducir 1,8 GB de bases
de datos y recursos en cada revisión de Git. `python3 tools/reverse.py bundle`
crea `dist/shaiya-ep1-originals.tar` y su checksum; consultar
[distribución](docs/DISTRIBUTION.md). El repositorio local todavía no tiene remoto.

```bash
python3 -m unittest discover -s tests -v
python3 tools/reverse.py audit
python3 tools/reverse.py validate
# Con los originales instalados:
python3 tools/reverse.py verify
python3 tools/reverse.py audit --originals
```

La validación automática comprueba identidad, cobertura y coherencia de las
entregas. La aceptación técnica exige revisar ensamblador, ABI, compilación y
comparaciones contra el original, como establece [el protocolo](docs/PROTOCOL.md).
