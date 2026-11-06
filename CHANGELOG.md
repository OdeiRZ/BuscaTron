# Changelog

Todos los cambios relevantes de BuscaTron se documentan aquí.
El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y el proyecto usa [versionado semántico](https://semver.org/lang/es/).

## [0.7.1] - 2026-11-06

### Corregido
- **Comprobaciones de Cloudflare en español**: la pantalla «Un momento… Verificación de seguridad en curso» no se reconocía como una comprobación humana y se trataba como una página de tienda sin productos. Ahora se detecta y se indica como cualquier otra.
- **Espera a una persona**: con la ventana visible, BuscaTron volvía a cargar la página cada 5 segundos mientras esperaba, lo que reiniciaría la comprobación antes de poder resolverla. Ahora espera sin recargar y continúa en cuanto la página deja de ser una comprobación.

### Notas
- Ferretería Ibérica Madrid sigue como «solo enlace». Su buscador es el de Doofinder, que funciona con sesiones firmadas de Phoenix LiveView y no con una API consultable, y su web está detrás de una comprobación de Cloudflare que hay que resolver a mano en una ventana.
- 3 pruebas nuevas (67 en total).

## [0.7.0] - 2026-11-06

### Añadido
- **Amazon.es se consulta automáticamente** (antes solo enlace). Con un Chrome real, y sin ninguna comprobación humana ni ventana, devuelve los resultados: 56 productos en una prueba con 3 páginas, con precios, agotados y paginación. Se migra tu entrada una sola vez; si Amazon volviera a pedir una comprobación, se indica como en cualquier otra tienda.

### Corregido
- **Precios tachados detectados por error**: se buscaba `old` dentro del nombre de las clases CSS y `a-text-bold` (que Amazon pone en todos sus precios) contiene «b**old**». Ahora se comparan palabras completas, y se reconocen también `style="text-decoration: line-through"` y el atributo `data-a-strike` de Amazon.
- **Página siguiente**: los enlaces sin texto (una imagen) coincidían con «Siguiente», porque al quitar los símbolos del texto quedaba una cadena vacía, y los botones de un carrusel se confundían con la paginación. Ahora se prefieren las direcciones con pinta de paginación (`page=2`, `/pagina-2`, `start=20`…) y, como último recurso, los enlaces con la palabra «Siguiente».
- **Ventanas del navegador**: con «Mostrar la ventana» activado, cada búsqueda que usaba el navegador abría una ventana visible, y cerrarla a mano rompía las demás consultas. Ahora todo se hace en segundo plano y solo las tiendas que piden comprobación humana se reintentan, de una en una, con ventana.

### Cambiado
- La opción de Ajustes pasa a llamarse «Abrir una ventana solo si una tienda pide comprobar que eres humano».
- 7 pruebas nuevas (64 en total).

## [0.6.1] - 2026-11-06

### Corregido
- Con el arranque con Windows activado, abrir `BuscaTron.bat` (o `--abrir`) mostraba un error de «puerto ocupado» porque BuscaTron ya estaba en marcha. Ahora detecta que ese puerto lo usa otro BuscaTron y se limita a abrir su web en el navegador. Sin `--abrir`, o si el puerto lo usa otra aplicación, sigue fallando con un mensaje claro.

## [0.6.0] - 2026-11-06

### Añadido
- **Arranque con Windows** (Ajustes o `--arranque on|off|estado`): acceso directo en la carpeta Inicio del usuario, sin permisos de administrador. Inicia BuscaTron sin ventana (`pythonw`) y con **icono en la bandeja** (ctypes, sin dependencias) con menú para abrirlo, ver u ocultar los mensajes y cerrarlo. Sin ventana, los mensajes van a `buscatron.log`. Solo se puede cambiar desde el propio equipo. Icono `.ico` propio.
- **Segunda mano** (opción «Incluir segunda mano»): Vinted y Milanuncios se consultan y muestran el **estado** del artículo; Wallapop y eBay, que devuelven un 403 a cualquier acceso automático, van como «solo enlace». Se pueden añadir otras webs marcándolas como segunda mano.
- **Búsqueda abierta** (opción «Buscar también en otras webs»): encuentra tiendas fuera de tu lista con Bing (y DuckDuckGo de respaldo), lee el precio de fichas de producto (schema.org / Open Graph) y de listados, filtra por región (España, UE, cualquier país), descarta las tiendas ya conocidas, las que bloquean bots y las que no son tiendas, y ofrece añadir las webs nuevas a la lista con un toque.
- **Varias páginas por tienda** (1 a 6, por defecto 3, configurable en Ajustes y en cada búsqueda): sigue los enlaces `rel="next"` o «Siguiente» mientras aporten productos nuevos. En las pruebas, 3 páginas aportaron 16 productos más.
- **Preventas** como categoría propia (distinta de «agotado»), con la opción «Incluir preventas». Se reconocen por «Preventa», «Lanzamiento aproximado», «Próximamente»…
- **Gastos de envío por tienda** (envío y «gratis desde»), con un botón «Detectar» que lo busca en la portada, y la opción «Sumar el envío al precio» para ordenar por el total.
- **Historial de precios en gráfica** (📈 en resultados y avisos): mínimo, media, máximo y precio actual, con gráfica SVG que respeta el modo claro y oscuro. Etiqueta «Mínimo histórico» cuando un artículo está a su precio más bajo.
- Los **seguimientos** admiten las mismas opciones (preventas, envío, segunda mano, otras webs, región y páginas).
- El extractor lee el **precio dentro del enlace** de la tarjeta (necesario para tiendas cuyo enlace envuelve todo el producto), el estado de segunda mano, las páginas siguientes, los datos estructurados de producto y las frases de envío gratis.
- 19 pruebas nuevas (57 en total).

### Cambiado
- La web se reorganiza: opciones nuevas en «Más fuentes y opciones» (se recuerdan entre búsquedas), tarjetas de resultado con el botón de historial, filas de tienda con envío y ajuste de «Búsqueda» y «Arranque con Windows».
- `BuscaTron.bat` arranca con icono en la bandeja y vuelve a mostrar la ventana si hay un error.

### Corregido
- Borrar un seguimiento dejaba sus avisos huérfanos en la lista; ahora se borran con él (el historial de precios se conserva).
- Vinted: se lee el precio del artículo del título de la tarjeta («…, 1.00 €, 1.75 €») y se limpian la marca y el estado del título.
- Un producto sin precio ya no se queda con el precio del producto siguiente.

## [0.5.1] - 2026-11-06

### Añadido
- Botón **«Vaciar avisos»** en la pestaña Avisos.
- Pruebas de la limpieza de avisos (22 pruebas en total).

### Corregido
- **Avisos obsoletos**: los avisos guardados nunca se volvían a comprobar, así que un producto que se había colado antes de los arreglos de idioma y stock (por ejemplo, un pack en inglés no disponible) seguía apareciendo en la pestaña Avisos. Ahora cada revisión retira los avisos de productos que ya no cumplen la búsqueda (agotados, preventas, otro idioma o fuera de precio), solo para las tiendas que han respondido, de modo que un fallo de red no borra nada. Si el producto vuelve a estar disponible, avisa de nuevo.

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
