# Instrucciones para agentes en este repositorio

Leer `README.md`, `CONTRIBUTING.md`, `docs/PROTOCOL.md` y
`docs/AGENT_PROMPT.md` antes de trabajar. El idioma de documentación es español;
los identificadores y formatos de herramientas son estables y usan inglés.

## Alcance y evidencia

- Trabajar únicamente en los bloques asignados y reservados al contribuidor.
  Verificar el ID, la baseline y el SHA-256 del binario antes de interpretar código.
- No modificar, ejecutar ni parchear los originales para el análisis estático.
  Una comparación dinámica autorizada se hace en una copia de trabajo aislada,
  con datos de prueba y comandos registrados. No usar los servicios con datos reales.
- `analysis/baseline/`, `blocks/` y `manifests/originals.json` están congelados.
  No reescribirlos para hacer pasar un aporte; solicitar una migración con evidencia.
- No considerar el pseudocódigo de Ghidra una implementación ni una prueba.
  Inferir firmas, tipos, offsets, flujo, excepciones y efectos desde instrucciones,
  referencias y observaciones. Registrar lo desconocido en `submission.json`.
- No inventar nombres originales, estructuras, algoritmos, paquetes ni resultados.
  Usar identificadores ligados a RVA hasta que exista evidencia de mejores nombres.
- No crear implementaciones ficticias para dependencias. Se permiten dobles de
  prueba explícitos, separados del fuente de producción, con el contrato descrito.
- Las funciones con cuerpo compartido requieren coordinación antes de una entrega.
  Los saltos directos no resueltos también bloquean reservas normales. Los saltos
  a otras funciones, callbacks y llamadas indirectas deben investigarse.

## Entregas

- Mantener el aporte en `contributions/<block_id>/`. Cambios en tipos compartidos
  van en una propuesta de contrato separada, con todos los consumidores afectados.
- Conservar las convenciones de llamada x86 Windows, tamaños, signo, alineación,
  orden de efectos y comportamiento en condiciones límite. Una compilación de
  pruebas en Linux de 64 bits no valida el ABI de Windows de 32 bits.
- Registrar comandos, entorno y resultados reales de las pruebas. No afirmar
  pruebas no ejecutadas. Si faltan dependencias o entorno, dejar el aporte en draft.
- `ready` significa listo para revisión. El agente del contribuidor no puede
  aceptar su propio bloque ni marcarlo integrado. Las evaluaciones corresponden
  a un revisor independiente y a la aceptación del mantenedor en la rama principal.
- Ejecutar `python3 tools/reverse.py validate --block <block_id>` y las pruebas
  pertinentes al aporte. Cambios de infraestructura requieren los tests del repo.
- No publicar, enviar mensajes ni crear PR externos salvo instrucción del usuario.
  No delegar a otros agentes salvo autorización explícita para ese trabajo.

## Infraestructura

Python 3.12+ sin dependencias para la CLI. Ghidra 12.1.4 y JDK 21 para el análisis.
Los proyectos Ghidra se guardan en `work/ghidra/` y no se sobreescriben.
Cambiar el planificador altera la identidad de la baseline: requiere una migración
explícita; una corrección de documentos no altera el catálogo.
