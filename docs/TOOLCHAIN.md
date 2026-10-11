# Herramientas y reproducción

La baseline está fijada a **Ghidra 12.1.4** con **JDK 21**. La CLI requiere
Python 3.12+ y biblioteca estándar. `manifests/toolchain.json` registra versiones,
URLs oficiales y SHA-256 de los archivos usados. No usar otra versión para
regenerar límites de bloques dentro de esta baseline.

## Linux x86_64

```bash
python3 tools/install_toolchain.py
export GHIDRA_HOME="$PWD/work/toolchain/ghidra_12.1.4_PUBLIC"
export JAVA_HOME="$PWD/work/toolchain/jdk-21.0.12.1+1"
python3 tools/reverse.py analyze --binary Client/game.exe
```

Se puede usar una instalación existente con esas variables o con `--ghidra` y
`--jdk`. El instalador verifica los paquetes antes de extraerlos y no cambia el
Java del sistema. No es necesario reinstalar para usar el catálogo publicado.

El análisis de los 23 binarios únicos se ejecuta con:

```bash
python3 tools/reverse.py analyze
```

Los imports iniciales usan el cargador PE y autoanálisis de Ghidra, cuatro CPUs
y un límite de 1800 segundos por archivo. Se registra idioma, compiler spec,
image base, hash, número de funciones y timeout. Un timeout impide aceptar
ese export. Las advertencias de Ghidra requieren inspección; una ejecución
exitosa no prueba que todas las funciones fueron identificadas correctamente.

Los proyectos están en `work/ghidra/<binary_id>.gpr` y los logs en `work/logs/`.
Los exports publicados están en `analysis/baseline/<binary_id>/`. Los proyectos
incompletos no se sobreescriben: conservarlos con sus logs y moverlos a una carpeta
de diagnóstico antes de reintentar. Tampoco editar el proyecto canónico al trabajar
una hipótesis; guardar una copia para anotaciones exploratorias.

## Windows y otros sistemas

Instalar el mismo Ghidra y un JDK 21 de la arquitectura correspondiente desde sus
fuentes oficiales. La CLI del análisis inicial está probada en Linux; el lanzador
Windows puede necesitar adaptación para `analyzeHeadless.bat`. No considerar ese
flujo verificado hasta reproducir el export y los hashes. Los contribuyentes pueden
usar la GUI con los mismos binarios y anotar evidencia sin alterar la baseline.

## Referencias oficiales

El flujo utiliza importación, `-postScript`, `-process`, `-noanalysis` y `-readOnly`
según la [documentación de analyzeHeadless](https://github.com/NationalSecurityAgency/ghidra/blob/master/Ghidra/RuntimeScripts/support/analyzeHeadlessREADME.md).
Ver [Ghidra 12.1.4](https://github.com/NationalSecurityAgency/ghidra/releases/tag/Ghidra_12.1.4_build)
y [Temurin JDK 21](https://github.com/adoptium/temurin21-binaries/releases).
