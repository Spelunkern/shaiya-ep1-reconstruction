# Primer bloque: longitud de unidades de 16 bits

Bloque `86424e839ec26fb4-fn-00001d80`, perteneciente a `Client/CONFIG.exe`.
SHA-256 del binario:
`86424e839ec26fb454cd343c451200e290cf528a88b53c2e77e7407573dac844`.
Entrada RVA `0x1d80`, VA `0x00401d80`; cuerpo `[0x1d80,0x1d96)`, 22 bytes.
Digest del cuerpo:
`ab4bab194aae7751eae686a11b9b3777dd65c29138d9a7d064cc8a88cb137299`.

## Evidencia e interpretación

| Dirección | Evidencia | Consecuencia |
|---|---|---|
| `00401d80` | `MOV EAX,[ESP+4]` | El primer argumento es un puntero en la pila |
| `00401d84` | `MOV CX,[EAX]` de 16 bits | Lee una unidad de dos bytes |
| `00401d87`, `00401d88` | Dos `INC EAX` | Avanza dos bytes por iteración |
| `00401d89`, `00401d8c` | `TEST CX,CX; JNZ 00401d84` | Continúa hasta la primera unidad cero |
| `00401d8e` | `SUB EAX,[ESP+4]` | Calcula distancia de bytes con aritmética de 32 bits |
| `00401d92`, `00401d94` | `SAR EAX,1; DEC EAX` | Convierte la distancia y excluye el terminador |
| `00401d95` | `RET` sin inmediato | El caller limpia el argumento |
| Caller `00401bee`, `00401bf3` | `CALL 00401d80; ADD ESP,4` | Confirma la limpieza por caller de cuatro bytes |

Para cadenas habituales devuelve la cantidad de unidades no nulas. No cuenta
puntos de código Unicode: un par de sustitutos ocupa dos unidades; tampoco valida
UTF-16. No existe control de puntero nulo ni límite de longitud. El input debe
permanecer legible durante la lectura. El caller utiliza el resultado para recorrer
un buffer de palabras y buscar un separador `0x005c`, como muestra `original/callers.txt`.

No se supone que el nombre original fuera `wcslen`. Se mantiene el símbolo por
binario y RVA. Las convenciones y nombres propuestos por Ghidra son pistas; la
firma adoptada usa `const void *` para representar también entradas no alineadas.

## Decisiones de implementación

El fuente usa una copia intrínseca de dos bytes para permitir punteros no alineados.
En el target Windows x86 probado produce lecturas de 16 bits, sin imports nuevos.
Un contador unsigned conserva el módulo de 32 bits de la distancia. El helper
`finish_byte_delta` reproduce el desplazamiento aritmético y decremento originales
sin overflow de enteros signed en C. No se usa `wchar_t`, cuyo tamaño depende de
la plataforma, ni se sustituye silenciosamente `SAR` por división unsigned.

El catálogo no registra dependencias de este bloque: no contiene llamadas ni
accesos globales. Los helpers del fuente pertenecen a esta implementación y no
representan funciones adicionales recuperadas del original.

## Pruebas ejecutadas

`tests/differential.py` compila fuente real como COFF i386 Windows en `-O0` y `-O2`.
Carga el código y resuelve exclusivamente relocaciones REL32 internas a `.text`;
un import o relocación externa hace fallar la prueba. Emula el código recompilado
y los 22 bytes originales con el mismo ABI de entrada.

Pasaron **4.068 comparaciones**: 3.042 recorridos, cuatro fallos de entrada y
1.022 pruebas de la cola aritmética. Se comprobaron retorno, ESP, argumento,
registros preservados, input intacto y direcciones/tamaños de lecturas. Los casos
incluyen cadena vacía, sustitutos, unidades altas, ceros internos, alineación impar,
terminador junto a una página no mapeada y entradas aleatorias reproducibles.

Al producirse un fallo de memoria se comparan acceso, dirección y tamaño del fallo
junto con las lecturas previas. No se exige igualdad de EAX en una ejecución que no
retorna: es un registro volátil y no hay resultado definido del caller en ese caso.
Los deltas enormes se prueban entrando en la cola original `SUB/SAR/DEC/RET`, sin
pretender haber escaneado objetos de varios gigabytes.

Los logs y el entorno están en `logs/` y `proof.json`. El estado es **ready**:
pruebas terminadas y listo para revisión independiente. No existe todavía un
registro de revisión ni una reconstrucción completa de `CONFIG.exe`.
