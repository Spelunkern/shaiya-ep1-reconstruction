# Análisis inicial del corpus

Baseline local del **11 de octubre de 2026**, generada con Ghidra 12.1.4 y JDK 21.
No se ejecutaron los binarios originales durante el inventario y autoanálisis.

```text
baseline_id: 7c4fe1157c5b3af787cf27c11ff47ab2903b30f627ede2e9b4a81fea1b7e057a
```

El corpus tiene 394 archivos, 27 rutas PE y 23 binarios únicos. Las cuatro rutas
PE redundantes corresponden a copias de `dbgeng.dll` y `dbghelp.dll`.

| Tipo de bloque | Cantidad |
|---|---:|
| Funciones detectadas | 45,259 |
| Datos y recursos | 1,495 |
| Regiones ejecutables sin clasificar | 33,443 |
| Integración por binario único | 23 |
| Total | 80,220 |

Hay **94 funciones que requieren revisión de límites o flujo directo** y
se excluyen de reservas normales. No se detectaron superposiciones de cuerpos en
los rangos exportados; esto no descarta colas compartidas que Ghidra haya atribuido
a una sola función.

## Cobertura de análisis

Los cuerpos de función ocupan 8,045,885 de 10,352,640 bytes de secciones
marcadas ejecutables, aproximadamente 77.72%. Esto **no** es un porcentaje de
fuente reconstruida. Todos los bytes restantes de esas secciones tienen bloques
de clasificación; los datos y los intervalos de archivo externos a las secciones
también están asignados. Las pruebas de cobertura verifican que no haya huecos
sin una tarea en esas áreas del PE.

| Ruta principal del binario | Funciones | Bytes ejecutables en cuerpos | Bytes ejecutables pendientes |
|---|---:|---:|---:|
| `Client/CONFIG.exe` | 88 | 90.58% | 1,881 |
| `Client/GameGuard.des` | 1 | 0.11% | 433,689 |
| `Client/Updater.exe` | 2,445 | 88.91% | 31,801 |
| `Client/game.exe` | 7,116 | 81.65% | 361,469 |
| `Client/ijl15.dll` | 406 | 70.35% | 94,733 |
| `Client/zlib.dll` | 154 | 90.52% | 3,739 |
| `Server/PSM_Client/Bin/dbgeng.dll` | 6,179 | 79.91% | 439,151 |
| `Server/PSM_Client/Bin/dbghelp.dll` | 5,390 | 82.73% | 149,554 |
| `Server/PSM_Client/Bin/ggauth.dll` | 627 | 81.11% | 9,286 |
| `Server/PSM_Client/Bin/ggauth53.dll` | 706 | 95.75% | 6,961 |
| `Server/PSM_Client/Bin/ggauth54.dll` | 560 | 95.50% | 5,900 |
| `Server/PSM_Client/Bin/ggauth55.dll` | 512 | 93.97% | 7,160 |
| `Server/PSM_Client/Bin/ggauth60.dll` | 629 | 85.94% | 11,520 |
| `Server/PSM_Client/Bin/ggsrvdll.dll` | 174 | 93.64% | 1,824 |
| `Server/PSM_Client/Bin/ps_dbAgent.exe` | 1,571 | 79.57% | 70,281 |
| `Server/PSM_Client/Bin/ps_game.exe` | 3,438 | 82.57% | 156,349 |
| `Server/PSM_Client/Bin/ps_gameLog.exe` | 1,247 | 77.71% | 53,859 |
| `Server/PSM_Client/Bin/ps_login.exe` | 1,327 | 76.68% | 60,167 |
| `Server/PSM_Client/Bin/ps_session.exe` | 1,314 | 77.31% | 58,559 |
| `Server/PSM_Client/Bin/ps_userLog.exe` | 1,226 | 77.31% | 52,036 |
| `Server/PSM_Client/PSM_Agent.exe` | 2,806 | 78.49% | 88,096 |
| `Server/PSM_Server/PSMServer_Agent.exe` | 2,804 | 79.15% | 84,536 |
| `Server/PSM_Server/PSMServer_Mgr.exe` | 4,539 | 79.78% | 124,204 |

La columna de cobertura incluye relleno y regiones virtuales de la imagen PE;
no estima cuántas instrucciones reales faltan. Hay 25.669 bloques sin clasificar
de hasta 16 bytes. Muchos pueden corresponder a alineación, pero su clasificación
no se da por supuesta. Se pueden coordinar lotes de bloques con entregas separadas.

## Hallazgos y prioridades

- `Client/game.exe`: 7.116 funciones detectadas. Antes de reconstruir subsistemas,
  fijar contratos de objetos, datos globales, callbacks y ABI.
- `ps_game.exe`: 3.438 funciones detectadas. Priorizar contratos de sesión,
  mensajes y acceso a datos, respaldados por evidencia de instrucciones.
- `GameGuard.des`: una sola función y 0,11% de cobertura ejecutable. Su sección
  `.text` no contiene bytes raw en el archivo; su disposición sugiere contenido
  preparado en ejecución. Es un candidato a análisis de carga/empaquetado,
  **no** un binario cuyo código completo ya haya sido descubierto.
- Las DLL de terceros tienen catálogo propio. Identificar versión y procedencia
  de código disponible puede ahorrar trabajo, pero su sustitución requiere
  demostrar correspondencia con el binario del corpus y sus contratos.

Un caso comprobado es `86424e839ec26fb4-fn-000032d0`: el cuerpo de Ghidra contiene
solo tres instrucciones, incluida una transferencia a `0x00403345`. El decompilador
muestra un algoritmo de copia de cadenas que excede ese cuerpo. El destino directo
queda sin resolver en el catálogo, y la reserva de ese bloque se bloquea hasta
revisar los límites. Este caso muestra por qué pocas instrucciones y pseudocódigo
legible no garantizan una unidad independiente de reconstrucción.

## Verificación del arranque

- Los 23 exports completaron autoanálisis sin timeout.
- Los hashes de los cuerpos de las 45.259 funciones coinciden con los bytes
  originales, incluyendo la representación de ceros virtuales cuando corresponde.
- Se reprodujo desde un proyecto nuevo el export de `CONFIG.exe`: las funciones
  y el resumen coincidieron byte a byte con la baseline publicada.
- Se ejercitó la exportación de listado y pseudocódigo de una función individual,
  verificando identidad del proyecto y digest del cuerpo antes de exportar.
- Las pruebas cubren cobertura de secciones y archivo, identidad del aporte,
  archivos fuera de alcance, contratos, revisión invalidada por cambios y reservas.
- El paquete de originales está en `dist/`, con tamaño y checksum registrados.

Las advertencias del autoanálisis se conservan resumidas en
[diagnostics.json](../analysis/diagnostics.json), y los logs completos siguen
localmente en `work/logs/`. Un autoanálisis terminado puede tener errores de tipos,
recursos o límites que deben revisarse. Los resultados son un mapa inicial de
trabajo; no una certificación de recuperación completa.

**Estado al generar esta baseline: 0 bloques validados, 0 binarios reconstruidos.**
La publicación posterior incluye únicamente los PE y un primer aporte real en
`ready`, descrito en [FIRST_BLOCK.md](FIRST_BLOCK.md). Sus pruebas diferenciales
pasaron; aún requiere revisión independiente. El reporte vivo es
`python3 tools/reverse.py report`. El inventario de 394 archivos es histórico;
los contribuidores reciben 27 PE y no necesitan la data del cliente.
