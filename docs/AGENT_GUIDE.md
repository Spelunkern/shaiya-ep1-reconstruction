# Procedimiento exacto para el agente

Trabajar desde la raíz del fork y sobre un bloque reservado en upstream. Leer
`AGENTS.md`, `CONTRIBUTING.md` y `docs/PROTOCOL.md`. No aplicar este procedimiento
al bloque de ejemplo, que ya tiene una entrega, salvo para reproducir sus pruebas.

## Entrada y alcance

El contribuidor proporciona un prompt generado por `reverse.py prompt` con su ID
y usuario. Ese comando resuelve binario, ruta, hash y baseline. Leer la reserva
aceptada, comprobar identidad y vencimiento. Una reserva creada en una rama local
no acredita aceptación central; contrastar `upstream/main` después de `git fetch`.

```bash
python3 tools/reverse.py show ID_DEL_BLOQUE
python3 tools/reverse.py verify
python3 tools/reverse.py audit --originals
```

Los binarios están en el clone. No descargar la data del cliente para estos pasos.
La baseline y los originales no se modifican. Si la tarea aún no tiene directorio:

```bash
python3 tools/reverse.py start ID_DEL_BLOQUE --owner USUARIO_GITHUB
```

## Preparar y consultar Ghidra

En Linux x86_64 con Python 3.12+:

```bash
python3 tools/install_toolchain.py
export GHIDRA_HOME="$PWD/work/toolchain/ghidra_12.1.4_PUBLIC"
export JAVA_HOME="$PWD/work/toolchain/jdk-21.0.12.1+1"
python3 tools/reverse.py analyze --binary ID_DEL_BINARIO
python3 tools/reverse.py export ID_DEL_BLOQUE
```

El instalador requiere acceso de red y espacio para Ghidra/JDK. Una instalación
existente de las mismas versiones puede usarse con las variables anteriores.
`analyze` reproduce el export; `export` comprueba hash de proyecto y cuerpo.
Si falla, registrar el error antes de continuar; no utilizar archivos viejos como
si fueran evidencia nueva. Los bloques no funcionales se inspeccionan por rangos.

## Análisis obligatorio

Examinar todas las instrucciones del cuerpo, callers, callees, saltos, datos usados,
imports y callbacks. Comprobar RVA + image base para cada dirección citada. Para
cada decisión de tipo, convención, offset o algoritmo, registrar instrucciones u
observaciones que la sustentan. Diferenciar firma de Ghidra y contrato demostrado.

Resolver parámetros, retorno, limpieza de pila, registros, tamaño y signo de
valores, alineación, efectos y errores. No asumir nombres originales. No ampliar
silenciosamente el alcance si el pseudocódigo salta fuera del cuerpo. Proponer una
revisión de límites con evidencia cuando sea necesaria.

## Implementación y prueba

Escribir fuente en el directorio del bloque. Usar símbolos por binario/RVA y
contratos aceptados. Reconstruir los efectos observables, incluso aritmética de
32 bits y orden de accesos cuando importen. Los helpers internos del fuente
pueden ser necesarios, pero no deben presentarse como nuevas funciones recuperadas.

Usar el [ejemplo](FIRST_BLOCK.md) para comprender el formato de entrega. Elegir
un harness adecuado al bloque; no copiar sus 4.068 resultados ni su contrato.
Comparar contra bytes/instrucciones originales o una observación reproducible.
Los dobles de prueba requieren contratos y pertenecen a los tests, no a producción.

Registrar comandos, entorno, compiler target, versiones, casos y logs. No convertir
una emulación parcial en una afirmación de integración del ejecutable completo.

## Cierre del aporte

Completar `submission.json`: identidad, owner, listas de archivos, ABI, contratos
y preguntas abiertas. Usar `draft` si sigue faltando evidencia o entorno; `ready`
solo cuando cumple el protocolo. No generar una autoevaluación en `reviews/`.

```bash
python3 tools/reverse.py validate --block ID_DEL_BLOQUE
```

Ejecutar los tests propios y entregar un resumen del comportamiento, archivos,
comandos, resultados reales y límites. Crear un PR cuando el usuario haya autorizado
esa entrega; no publicar por el mero hecho de haber leído el prompt. Si aparece
un impedimento, completar la evidencia independiente y describir qué falta y dónde.
