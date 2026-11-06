# BuscaTron

Buscador de precios local para comparar tiendas online españolas (pensado para juegos de mesa, válido para cualquier producto). Consulta las tiendas en vivo desde tu propio PC, sin APIs de pago, sin cuentas y sin depender de ninguna IA: solo la biblioteca estándar de Python.

> Estado: **prototipo**. Funciona con tiendas que sirven los resultados en el HTML; las que cargan con JavaScript o bloquean bots aparecen en el informe como «sin resultados».

## Uso

Requiere Python 3.9 o superior. No hay nada que instalar.

```
python -m buscatron --abrir              # interfaz web en http://127.0.0.1:8790 (o doble clic en BuscaTron.bat)
python -m buscatron "marvel champions"   # búsqueda por línea de comandos
```

En la web puedes:

- Buscar un producto y ver los N más baratos con enlace a la tienda.
- Filtrar por palabras que debe contener o excluir, y por precio mínimo y máximo.
- Ocultar agotados.
- Activar, desactivar y añadir tiendas (basta el dominio, por ejemplo `ejemplo.es`).

## Cómo encuentra los productos

1. Lee la portada de cada tienda y descubre su formulario de búsqueda. Si no lo encuentra, prueba plantillas habituales (PrestaShop, Magento, Shopify, WooCommerce).
2. Descarga los resultados y se queda con los enlaces cuyo texto contiene todas las palabras de la búsqueda, junto al primer precio vigente (ignora precios tachados) y si pone «agotado».
3. Ordena por precio y guarda cada búsqueda en `buscatron.db` (SQLite) para tener historial.

Limitaciones conocidas del prototipo: solo se lee la primera página de resultados de cada tienda, y no hay todavía envío de avisos ni barridos programados.

## Archivos locales

`tiendas.json` (tu lista de tiendas y los buscadores descubiertos) y `buscatron.db` (historial) se crean al usar la herramienta y no se suben al repositorio.

## Licencia

AGPL-3.0. Consulta [LICENSE](LICENSE).
