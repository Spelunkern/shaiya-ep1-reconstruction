# Primer bloque completo de ejemplo

El ejemplo es [86424e839ec26fb4-fn-00001d80](../contributions/86424e839ec26fb4-fn-00001d80/),
una función de `Client/CONFIG.exe` en VA `0x00401d80`, de 22 bytes y diez instrucciones.
Mide unidades de 16 bits hasta cero. Es un bloque real del corpus, con fuente
reconstruida, evidencia, contrato ABI y pruebas contra las instrucciones originales.

Consultar su [análisis por dirección](../contributions/86424e839ec26fb4-fn-00001d80/analysis.md),
[fuente C](../contributions/86424e839ec26fb4-fn-00001d80/src/function.c),
[entrega](../contributions/86424e839ec26fb4-fn-00001d80/submission.json) y
[resultados](../contributions/86424e839ec26fb4-fn-00001d80/logs/comparison.json).

## Repetir las pruebas en Linux x86_64

Instalar Python 3.12+ con venv y Clang. En Ubuntu/Debian, si faltan:

```bash
sudo apt-get update
sudo apt-get install clang python3-venv
```

Desde la raíz de un clon del repositorio:

```bash
python3 tools/reverse.py verify
python3 -m venv .venv
.venv/bin/python -m pip install -r contributions/86424e839ec26fb4-fn-00001d80/tests/requirements.txt
.venv/bin/python contributions/86424e839ec26fb4-fn-00001d80/tests/differential.py
python3 tools/reverse.py validate --block 86424e839ec26fb4-fn-00001d80
```

Salida esperada:

```text
PASS 3042 scan + 4 fault + 1022 arithmetic comparisons against original x86 instructions
```

Los objetos COFF y los resultados de esa ejecución se guardan en
`work/first-block-test/`; no se sobreescriben los logs de la entrega. Se verifica el
SHA-256 del binario y del cuerpo antes de emular. No hacen falta los datos del
cliente, un servidor de juego ni ejecutar `CONFIG.exe` completo.

## Qué demuestra

La prueba usa el target `i686-pc-windows-msvc` en Clang y emulación x86-32 con
Unicorn 2.1.4. Compara fuente compilada contra bytes originales, no contra una
segunda traducción del pseudocódigo. Comprueba ABI, retorno y lecturas, a dos
niveles de optimización, e incluye casos adversos y overflow de la cola aritmética.
Ver [Clang](https://clang.llvm.org/docs/CrossCompilation.html) y
[Unicorn](https://www.unicorn-engine.org/docs/tutorial.html) para sus interfaces.

No demuestra identidad byte a byte del build ni equivalencia del ejecutable
completo. Los resultados registran límites concretos de emulación y de las pruebas.
El ejemplo está `ready`, pendiente de revisión independiente; no se autoaprueba.

## Usarlo como plantilla

Reservar **otro** bloque disponible. Copiar la estructura del ejemplo, no sus
resultados, hashes ni contrato. El nuevo bloque necesita evidencia y pruebas
propias. Si requiere WinAPI, objetos, globals o red, construir un harness que
controle esas dependencias con contratos documentados. Los dobles de prueba no
se convierten en implementaciones de producción.

Leer [CONTRIBUTING.md](../CONTRIBUTING.md) y generar el prompt para el nuevo ID:

```bash
python3 tools/reverse.py prompt ID_DEL_BLOQUE --owner USUARIO_GITHUB > work/task.md
```

Crear `work/` con `mkdir -p work` si aún no existe. No reservar ni modificar el ejemplo como si fuera
una tarea libre: su fuente ya está entregada y sirve para reproducir el proceso.
