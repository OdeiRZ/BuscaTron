# Changelog

Todos los cambios relevantes de BuscaTron se documentan aquí.
El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y el proyecto usa [versionado semántico](https://semver.org/lang/es/).

## [0.5.0] - 2026-11-06

### Añadido
- **Acceso desde el móvil por la Wi-Fi**: BuscaTron escucha ahora en la red local por defecto (`--host 0.0.0.0`; `--host 127.0.0.1` para limitarlo a este equipo). Al arrancar muestra las direcciones de acceso, y también aparecen en Ajustes → «Acceso desde el móvil».
- `permitir_acceso_movil.bat`: abre el puerto 8790 del cortafuegos de Windows solo para la red local; se eleva a administrador por sí solo.
- **PIN de acceso opcional** para dispositivos distintos del propio equipo: sesión en cookie firmada (`HttpOnly`, 30 días) y bloqueo de 5 minutos tras 5 intentos fallidos. El secreto de firma se genera una vez y nunca se muestra.
- **Filtro de IP**: solo se aceptan direcciones privadas, de Tailscale o locales; el resto recibe un 403.
- **Editar tiendas ya guardadas**: nombre, dirección o URL de búsqueda y modo «solo enlace». Cambiar a otro dominio vuelve a descubrir su buscador; se rechazan duplicados y direcciones no válidas.
- **Opción «Solo castellano»** (activada por defecto) en la búsqueda y en cada seguimiento: descarta los productos que indican otro idioma salvo que mencionen también el castellano.
- Pruebas del filtro de idioma, de las IP permitidas, de las direcciones y de la sesión por PIN (18 pruebas en total).

### Documentación
- Nueva sección «Usar desde el móvil» en el README, con la configuración paso a paso, qué hacer si el móvil no carga (Wi-Fi frente a datos móviles, dirección correcta, comprobación de la regla del cortafuegos y aislamiento de clientes del router) y las medidas de seguridad.

### Cambiado
- El icono de la pestaña es ahora un SVG dibujado (etiqueta de precio sobre degradado) en lugar de un emoji, que se veía recortado según el sistema.
- `BuscaTron.bat` usa el modo red por defecto.

### Corregido
- **Productos no disponibles que salían como disponibles**: tiendas como Dungeon Marvels no escriben «agotado», sino «Reserva» o «EN REPOSICIÓN… cuando el artículo vuelva a estar disponible». Ahora se reconocen y se ocultan con «Ocultar agotados».

## [0.4.1] - 2026-11-06

### Añadido
- **Botón para alternar entre modo claro y oscuro** en la cabecera (🌙 / ☀️). Por defecto sigue el tema del sistema y recuerda la elección del usuario. El tema se aplica antes de pintar la página para evitar el parpadeo, y también adapta los controles del navegador (casillas, campos) y el color de la barra del móvil.

### Corregido
- **Título de la pestaña**: ahora es «BuscaTron · Comparador de precios», sin emoji.
- **Iconos duplicados**: el emoji aparecía dos veces en la pestaña (en el título y como icono) y la cabecera repetía el 🔎 del botón «Buscar». Ahora la marca es 🏷️ (icono de pestaña y cabecera) y 🔎 queda solo para buscar.

## [0.4.0] - 2026-11-06

### Añadido
- **Interfaz rediseñada para móvil** (probada a 360 px) y escritorio: barra de pestañas fija abajo con iconos y contador de avisos, tarjetas de resultados con el precio destacado y el más barato resaltado, filtros y tiendas plegables, avisos tipo «toast», pantallas vacías con mensaje y modo oscuro automático.
- Emoji 🔎 en el título de la pestaña, en el icono y en la cabecera.
- **Tiendas con nombre propio**: cada tienda guarda un nombre para mostrar y su dirección. Se pueden renombrar y quitar desde «Gestionar tiendas».
- **Alta de tiendas con URL de búsqueda**: se puede pegar una URL con `{q}` donde va el producto, para webs cuyo buscador no se detecta.
- **Tiendas «solo enlace»**: las webs que bloquean todo acceso automático no se consultan; cada búsqueda ofrece su enlace para abrirlo a mano (apartado «Para revisar a mano»). Amazon (ordenado por precio ascendente) y Ferretería Ibérica Madrid vienen así de serie.
- Prueba del extractor con títulos recortados.

### Cambiado
- El **navegador opcional** (Chrome) viene activado por defecto.
- **Ocultar agotados** viene activado por defecto, también en la línea de comandos.
- README reescrito con la guía completa, la configuración de Telegram, el estado de las tiendas y las limitaciones.

### Corregido
- Títulos recortados por la propia web («Marvel Champions:…»): se recupera el título del atributo `title` o, si no hay, se reconstruye a partir de la dirección del producto. Así los filtros de exclusión también los ven completos.

## [0.3.0] - 2026-11-06

### Añadido
- **Navegador opcional** (`navegador.py`): usa tu Chrome o Edge con Playwright, en un perfil propio y persistente, para tiendas que cargan los resultados con JavaScript. Funciona en un único hilo dedicado.
- Si una tienda pide una comprobación humana (captcha), se indica y, con la ventana visible, la resuelve el usuario. No se intenta saltar ninguna protección antibot.
- Ajustes del navegador en la interfaz.
- Soporte de **Turol Games** (con navegador) y **Masqueoca** (URL de búsqueda propia, bajo `/tienda/`).
- Pruebas del extractor.

### Corregido
- **Falsos «agotado»**: el extractor ignora el texto de elementos ocultos (`display:none`, `hidden`). En Turol Games salían 20 de 20 agotados por culpa de un bloque oculto.
- Las etiquetas sin cierre (`<br>`, `<img>`…) descuadraban la lectura de precios y tachados.
- El navegador espera a las pantallas de carga que se recargan solas (meta refresh) en vez de tratarlas como captcha, y reintenta la lectura si la página se está recargando.
- En Windows, dos instancias de BuscaTron podían engancharse al mismo puerto sin error. Ahora la segunda se niega con un mensaje claro.

## [0.2.0] - 2026-11-06

### Añadido
- **Seguimiento**: búsquedas vigiladas con revisión cada X horas, precio objetivo, aviso por bajada respecto a la media histórica del artículo, y opción de revisar ahora, pausar, editar y borrar.
- **Avisos** por Telegram, correo (SMTP) y dentro de la app, sin repetir (solo se vuelve a avisar si el precio baja más o pasados 30 días).
- **Planificador** en segundo plano que lanza las revisiones cuando toca.
- Pestañas Seguimiento, Avisos y Ajustes, con detección automática del chat de Telegram y botones de prueba.
- Historial de precios y base de datos SQLite (`buscatron.db`).
- Argumentos `--host`, `--puerto` y `--abrir`, y lanzador `BuscaTron.bat`.
- Pruebas de las reglas de aviso, sin red.

### Notas
- Telegram verificado con un bot real. El envío por correo está implementado pero sin probar con un servidor real.

## [0.1.0] - 2026-11-06

### Añadido
- Primer prototipo: motor que consulta las tiendas en paralelo y ordena por precio, solo con la biblioteca estándar.
- **Autodescubrimiento del buscador** de cada tienda a partir del formulario de su portada, con plantillas de reserva (PrestaShop, Magento, Shopify, WooCommerce).
- Extractor genérico de productos: enlaces que contienen la búsqueda, primer precio vigente (ignora tachados) y detección de agotado.
- Filtros por palabras (contiene y excluye) y por precio mínimo y máximo.
- Interfaz web local y búsqueda por línea de comandos.
- Licencia AGPL-3.0.
