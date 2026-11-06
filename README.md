# BuscaTron

Buscador de precios local para comparar tiendas online españolas (pensado para juegos de mesa, válido para cualquier producto). Consulta las tiendas en vivo desde tu propio PC, sin APIs de pago, sin cuentas y sin depender de ninguna IA: solo la biblioteca estándar de Python.

> Estado: **prototipo**. Funciona con tiendas que sirven los resultados en el HTML; las que cargan con JavaScript o bloquean bots aparecen en el informe como «sin resultados».

## Uso

Requiere Python 3.9 o superior. No hay nada que instalar.

```
python -m buscatron --abrir              # interfaz web en http://127.0.0.1:8790 (o doble clic en BuscaTron.bat)
python -m buscatron "marvel champions"   # búsqueda por línea de comandos
```

Para tiendas que cargan con JavaScript, el navegador opcional está activado por defecto (se puede desactivar en Ajustes) (necesita `pip install playwright` y Chrome o Edge instalados; no se descarga ningún navegador). BuscaTron no intenta saltarse comprobaciones antibot: si una tienda pide un captcha, lo indica y, con la ventana visible, lo resuelves tú una vez.

En la web puedes:

- Buscar un producto y ver los N más baratos con enlace a la tienda.
- Filtrar por palabras que debe contener o excluir, y por precio mínimo y máximo.
- Ocultar agotados.
- Vigilar búsquedas (pestaña Seguimiento): precio objetivo o bajada respecto a su media, revisión cada X horas y avisos por Telegram, correo o dentro de la app.
- Activar, desactivar, renombrar y añadir tiendas: basta el dominio (`ejemplo.es`), con un nombre propio opcional. Si su buscador no se detecta, pega una URL de búsqueda con `{q}` donde va el producto (`https://ejemplo.es/buscar?q={q}`).
- Marcar una tienda como «solo enlace»: no se consulta, pero cada búsqueda te ofrece su enlace para abrirlo tú (pensado para webs que bloquean todo acceso automático, como Amazon).

## Cómo encuentra los productos

1. Lee la portada de cada tienda y descubre su formulario de búsqueda. Si no lo encuentra, prueba plantillas habituales (PrestaShop, Magento, Shopify, WooCommerce).
2. Descarga los resultados y se queda con los enlaces cuyo texto contiene todas las palabras de la búsqueda, junto al primer precio vigente (ignora precios tachados) y si pone «agotado».
3. Ordena por precio y guarda cada búsqueda en `buscatron.db` (SQLite) para tener historial.

Limitaciones conocidas: solo se lee la primera página de resultados de cada tienda, y el planificador solo trabaja mientras BuscaTron está abierto. Hay tiendas que bloquean cualquier acceso automático (por ejemplo Amazon) y no se pueden consultar.

## Archivos locales

`tiendas.json` (tu lista de tiendas y los buscadores descubiertos), `buscatron.db` (historial), `config.json` (tokens y ajustes) y `navegador_perfil/` (sesión del navegador opcional) se crean al usar la herramienta y no se suben al repositorio.

## Licencia

AGPL-3.0. Consulta [LICENSE](LICENSE).
