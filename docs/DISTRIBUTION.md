# Distribución pública de binarios

Los 27 archivos PE del corpus —23 binarios únicos— están versionados directamente
en `Client/` y `Server/`, con sus rutas originales. No requieren Git LFS, extracción
de la data del juego ni descarga de un paquete de varios gigabytes. El total de
binarios es **20.910.273 bytes**.

```bash
git clone https://github.com/Spelunkern/shaiya-ep1-reconstruction.git
cd shaiya-ep1-reconstruction
python3 tools/reverse.py verify
```

`verify` comprueba por defecto todos los binarios publicados, con tamaño y SHA-256.
`manifests/public-binaries.json` lista exactamente lo que se distribuye.
`GameGuard.des` está incluido porque es un PE, aunque no use extensión `.exe`.
Las DLL idénticas comparten `binary_id`; el SHA-256 completo es la autoridad.

## Descarga de solo los binarios

La [versión v0.1.0](https://github.com/Spelunkern/shaiya-ep1-reconstruction/releases/tag/v0.1.0)
incluye `shaiya-ep1-binaries.zip`, `binaries-bundle.json` y `SHA256SUMS`.
El ZIP contiene únicamente esos PE y su manifiesto público. Puede extraerse en
la raíz de una copia del repositorio para restaurar los originales.

Para regenerar el paquete desde un clon verificado:

```bash
python3 tools/reverse.py bundle
```

El resultado queda en `dist/`. El comando usa una lista explícita de archivos PE;
no incluye otros archivos presentes localmente dentro de `Client/` o `Server/`.
Antes de extraer una descarga, verificar su checksum con `sha256sum -c SHA256SUMS`.
Después, `verify` contrasta los archivos contra el inventario del repositorio.

## Lo que permanece local

Los archivos de data del cliente (`data.saf`, `data.sah`), mapas externos, bases
de datos, configuraciones y logs del corpus preparado no se publican. Las carpetas
originales siguen intactas en la estación del mantenedor, pero Git solo contiene
las rutas PE autorizadas. CI ejecuta `tools/check_distribution.py` para impedir
que se añadan otros originales bajo esas carpetas.

`manifests/originals.json` conserva hashes y rutas del inventario histórico de
394 archivos porque participa de la baseline congelada. No contiene los archivos
ni sus contenidos. Para verificar aquel corpus completo, disponible únicamente
en la copia local del mantenedor:

```bash
python3 tools/reverse.py verify --full-corpus
```

Ese comando no forma parte de la preparación del contribuidor. La distribución
actual permite análisis estático y pruebas aisladas por bloque. Las pruebas del
juego o servidor completos requerirán datos de prueba en una fase de integración.
