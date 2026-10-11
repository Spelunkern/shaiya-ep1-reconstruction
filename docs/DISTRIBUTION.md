# Originales y publicación

La copia local conserva `Client/` y `Server/` en sus ubicaciones originales.
Git versiona la infraestructura, los hashes, la baseline y los aportes. Esas
carpetas están ignoradas para distribuirlas una vez por corpus como un artefacto
asociado a la versión del repositorio, sin reinsertarlas en cada clone o commit.

El inventario lista **cada archivo**, su tamaño y SHA-256, incluso datos del juego,
configuraciones, logs y bases de datos. Los PE se reconocen por su cabecera,
incluyendo `GameGuard.des`, y las copias idénticas comparten `binary_id`.
El SHA-256 completo es la autoridad; el ID corto se comprueba contra colisiones.

## Crear el paquete de la carpeta completa

```bash
python3 tools/reverse.py verify
python3 tools/reverse.py bundle
```

Se genera `dist/shaiya-ep1-originals.tar` y `dist/originals-bundle.json` con tamaño
y SHA-256. El paquete contiene exactamente los originales inventariados y el
manifiesto. No contiene Git, proyectos Ghidra ni herramientas descargadas.
El comando no publica ni sube archivos. Conservar los datos originales intactos.

Al publicar el repositorio, el mantenedor debe adjuntar ese artefacto y su checksum
a la versión correspondiente y añadir el enlace de descarga aquí. **Todavía no
hay URL de descarga ni remoto configurado.** El corpus incluye configuraciones,
logs y bases de datos: revisar su contenido antes de elegir una distribución pública.

## Instalar como contribuidor

Obtener el paquete y el checksum del mismo mantenedor y versión del repositorio.
Comprobar el SHA-256 del tar antes de extraerlo; extraer únicamente un paquete de
procedencia conocida dentro de una copia del repo. Luego ejecutar `verify` y
`audit --originals`. El manifiesto del repositorio sigue siendo la referencia,
no una sustitución enviada junto a un paquete distinto.

La verificación completa exige que coincida el conjunto de archivos, tamaños y
hashes. `verify --binaries-only` sirve para análisis estático parcial y **no**
acredita disponer de todo el corpus. Los ejecutables del corpus son x86 Windows;
no se ejecutan durante inventario, particionado, CI ni análisis estático.
