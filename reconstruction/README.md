# Integración del fuente

Esta carpeta recibirá proyectos compilables por binario, alimentados por aportes
aceptados. Todavía no existe una implementación reconstruida ni un build del cliente
o del servidor. El catálogo es la estructura de trabajo, no una reconstrucción.

Cada proyecto debe registrar compilador, arquitectura Windows x86, opciones,
imports/exports, recursos, inicialización, contratos compartidos y el mapa de
símbolos a bloques. Incluir una sola implementación por símbolo y dejar fallar
el enlace ante dependencias faltantes. Las DLL idénticas se construyen una vez
y sus resultados se instalan en las rutas originales inventariadas.

Los contratos de funciones, estructuras y datos deben resolverse antes de unir
bloques que los comparten. Los bloques de integración del catálogo son responsables
de esa coordinación y de las pruebas de conjunto.
