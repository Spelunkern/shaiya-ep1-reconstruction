# Prompt para copiar al agente de IA

Generar el prompt con `python3 tools/reverse.py prompt ID_DEL_BLOQUE --owner USUARIO_GITHUB`.
Ese comando resuelve también `ID_DEL_BINARIO`. Si se copia manualmente, sustituir
los tres valores por la reserva aceptada y el binario de `show`. Ejecutar este
prompt dentro de la raíz del repositorio, con originales y herramientas instalados.

```text
Trabaja en la reconstrucción del bloque ID_DEL_BLOQUE para USUARIO_GITHUB.

1. Lee AGENTS.md, README.md, CONTRIBUTING.md y docs/PROTOCOL.md.
   Lee también docs/AGENT_GUIDE.md y docs/FIRST_BLOCK.md como referencia.
   Confirma que la reserva de claims/ pertenece a USUARIO_GITHUB, no está vencida
   y ya fue aceptada en la rama principal del repositorio comunitario.
2. Ejecuta show para el bloque, verify y audit --originals. Identifica el binario
   por su SHA-256 completo, la baseline, el RVA de entrada y todos los rangos.
   Usa image_base + RVA para ubicar direcciones en Ghidra.
3. Si no existe el directorio del aporte, usa start. Si falta el proyecto local,
   usa analyze --binary ID_DEL_BINARIO. Para funciones, usa export y examina el
   listado completo de instrucciones, los callers, los callees, los datos usados
   y el pseudocódigo. Para otros tipos inspecciona los rangos y obligaciones.
4. Reconstruye el comportamiento y documenta evidencia por dirección en analysis.md.
   Determina convención de llamada, parámetros, retorno, offsets de estructuras,
   globals, efectos, errores y comportamiento límite. Distingue hechos de hipótesis.
   Registra llamadas indirectas, referencias no resueltas y contratos externos.
5. Escribe fuente mantenible del alcance asignado. No copies pseudocódigo sin
   resolver sus tipos y semántica. Usa símbolos por RVA, respeta ABI Windows x86
   y reutiliza contratos aceptados. No implementes otros bloques ni inventes
   dependencias; solicita coordinación si falta un contrato.
6. Crea pruebas que puedan detectar desviaciones respecto de las instrucciones
   originales. Incluye condiciones límite y efectos observables. Ejecuta las
   comparaciones posibles y conserva comandos, entorno y logs. No marques como
   pasada una prueba que no ejecutaste ni confundas tests portables con validación ABI.
7. Completa submission.json con archivos, ABI, contratos y unknowns. Copia evidencia
   al directorio del aporte. Usa draft si quedan incógnitas o faltan verificaciones;
   usa ready solo si cumple el protocolo. Ejecuta validate --block ID_DEL_BLOQUE.
8. Entrega un resumen del comportamiento, archivos, pruebas reales y límites.
   No apruebes tu propio trabajo ni publiques un PR sin autorización del usuario.

Persiste con el análisis autorizado. Si aparece una dependencia sin resolver,
completa la evidencia independiente y registra el impedimento con precisión.
La cantidad de código escrito no sustituye evidencia de equivalencia.
```
