# Changelog

Todos los cambios relevantes de BuscaTron se documentan aquí.
El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y el proyecto usa [versionado semántico](https://semver.org/lang/es/).

## [0.9.6] - 2026-11-07

### Añadido
- **Filtro «al menos una de estas»** (palabras o frases separadas por comas) en la búsqueda y en las búsquedas vigiladas. Permite vigilar todas las campañas de un juego con **una sola búsqueda** (el nombre del juego, que trae todo el catálogo) en lugar de una por campaña, que dependía del buscador de cada tienda y casi no encontraba nada. Ignora espacios y puntos: «shield» encuentra «S.H.I.E.L.D.».
- 4 pruebas nuevas (130 en total), entre ellas una que comprueba que las opciones de una búsqueda vigilada existen de verdad en el motor.

### Corregido
- **Las búsquedas vigiladas con «resumen por Telegram» fallaban** (v0.9.5): la opción se pasaba al motor de búsqueda, que no la admite, y la revisión se habría interrumpido sin avisar. Las pruebas simulaban el motor y no lo detectaron.
- Turol Games pone «Producto agotado» delante del título: ahora se quita del título y el producto cuenta como agotado.

## [0.9.5] - 2026-11-07

### Añadido
- **Ordenar los avisos**: selector «Ordenar por» en la pestaña Avisos, con más recientes, precio de menor a mayor, precio de mayor a menor, nombre (A-Z) y tienda (A-Z). Se recuerda la elección; con precios iguales desempata por nombre, y con nombres iguales por precio.
- **Resumen por Telegram** (opción de cada búsqueda vigilada): si una revisión no trae avisos nuevos, manda igualmente un mensaje con los 5 más baratos que cumplen la búsqueda (sin agotados ni preventas, según la configuración) y cuántas tiendas no respondieron. Si hay avisos nuevos se manda el aviso, no el resumen.
- 3 pruebas nuevas (126 en total).

### Notas
- Una revisión sin avisos nuevos no enviaba nada a Telegram, y una búsqueda vigilada con «Precio máximo» pero sin «Avisarme si cuesta como mucho» casi nunca avisa: el precio máximo solo filtra. Documentado en el README.

## [0.9.4] - 2026-11-07

### Cambiado
- **Nombres y mensajes más claros en toda la aplicación**, con un mismo nombre para cada cosa:
  - La pestaña «Seguimiento» pasa a **«Vigiladas»**, a juego con el botón «Vigilar esta búsqueda»; sus tarjetas dicen en frases completas cuándo avisan («Te avisa si cuesta 39,00 € o menos»), dónde («pestaña Avisos y Telegram») y cuándo se revisan («se revisa sola cada 12 h; la próxima, dentro de 5,8 h»).
  - Filtros: «Solo títulos que contengan» y «Descartar títulos que contengan» en vez de «Debe contener» y «Excluir palabras»; «Resultados que se muestran».
  - Idioma: modos «En castellano», «Solo castellano seguro» y «Cualquier idioma», explicados debajo; etiquetas «En castellano», «Probablemente en castellano», «En inglés»…
  - Tiendas bloqueadas: «Tiendas que tienes que mirar tú», con «Pegar resultados» y «Añadir a los resultados»; la etiqueta pasa a «Pegado a mano hace X h».
  - Búsqueda guardada: «Búsqueda guardada hace X: los precios pueden haber cambiado», con el botón «Repetir».
- **Mensajes de error de las tiendas que explican qué pasó**: «rechaza las consultas automáticas (error 403)», «no encuentra la página de búsqueda (error 404)», «no tiene nada que coincida con la búsqueda», «no responde; se volverá a probar dentro de N min», «pide demostrar que eres humano…».
- **Motivo de los avisos** con el precio y en formato español: «cuesta 36,50 €, por debajo de tu objetivo de 39,00 €» o «un 18 % más barato que su precio habitual (44,95 €)».
- Confirmaciones que dicen qué se conserva («Se borran también sus avisos; el historial de precios se conserva») y mensajes de conexión que dicen qué comprobar.

### Corregido
- En el móvil, la opción de idioma se cortaba, el botón de la búsqueda guardada se partía en tres líneas y los contadores de los desplegables se partían en dos. Las horas decimales se muestran con coma.

## [0.9.3] - 2026-11-07

### Corregido
- **Precio erróneo en El Taller del Modelista**: se mostraba el descuento («-2,59 €») en lugar del precio (22,40 €). Ahora se ignoran los importes con signo menos y los de clases de descuento («discount», «descuento», «ahorro»…), y se usa el precio de los microdatos (`itemprop="price"`) cuando la tienda lo da. Se borraron del historial los 9 precios falsos de 2,59 €, que además marcaban un «Mínimo histórico» falso.
- **Stock de los microdatos**: `itemprop="availability"` con *OutOfStock* o *PreOrder* marca el producto como agotado o preventa (el Shadowlands de El Taller del Modelista es una preventa).
- **Avisos de productos sin stock**: antes de avisar se lee la ficha de cada candidato (datos de schema.org) y no se avisa si dice agotado, ni si dice preventa salvo que el seguimiento incluya preventas. Se recuerda 6 horas por producto (tabla `fichas`).
- **Bixoto** pasa a «solo enlace» con «Pegar resultados»: cada búsqueda automática acababa en un bloqueo temporal de la IP. Comprobado después: una única petición con un Chrome real también provoca el bloqueo, así que no hay forma de consultarla automáticamente sin esquivar su protección.
- 5 pruebas nuevas (123 en total).

### Notas
- Tablerum anuncia «Motivos Siniestros» como disponible tanto en el listado como en la ficha (*InStock*, con botón de compra), así que BuscaTron no puede saber que no hay stock; el aviso se ocultó a mano.

## [0.9.2] - 2026-11-07

### Cambiado
- **Python 3.13** (antes 3.10.0, cuya rama ya no recibe correcciones de seguridad): BuscaTron usa ahora un entorno propio (`.venv`, fuera del repositorio) con Python 3.13.17 y Playwright. `BuscaTron.bat` usa ese entorno si existe y, si no, el `python` del sistema; el arranque con Windows se recrea con `.venv\Scripts\python -m buscatron --arranque on`. Las 118 pruebas pasan con 3.13.
- Instalación en paralelo, sin tocar los otros Python del equipo ni el `PATH`: `python` sigue siendo el de antes para el resto de proyectos.

## [0.9.1] - 2026-11-07

### Corregido
- **«Error: TypeError: Failed to fetch» en el móvil**: una búsqueda tarda entre 30 y 90 s y la página la esperaba con una sola conexión abierta; si se bloqueaba la pantalla, se cambiaba de app o se recargaba, el navegador cortaba esa conexión (11 de los 12 fallos del registro venían del móvil) y se perdía el resultado. Ahora la búsqueda corre en segundo plano en el servidor: la página recibe un número al instante (`/api/buscar` con `asincrono`) y pregunta cada 2 s cómo va (`/api/trabajo`). Si se corta la conexión, la búsqueda sigue; al volver a la página o a la app se retoma sola, y si BuscaTron se reinició mientras tanto se muestra la última búsqueda guardada. Los resultados se conservan una hora para recogerlos.
- Las peticiones cortas reintentan una vez si la red falla un momento (por ejemplo, al desbloquear el móvil).
- 4 pruebas nuevas (118 en total).

## [0.9.0] - 2026-11-07

### Añadido
- **Selector «Idioma de los juegos»** en la búsqueda y en cada seguimiento, con tres modos: *Solo castellano* (oculta lo que dice expresamente otro idioma; es el de siempre), *Castellano estricto* (solo lo que está o parece en castellano) y *Cualquier idioma*. Sustituye a la casilla «Solo castellano», que era fácil de pasar por alto y casi no tenía efecto visible: de 649 títulos reales, 575 no decían su idioma.
- **Etiqueta de idioma en cada producto**: «Castellano», «Parece castellano», «Inglés», «Parece inglés», «Otro idioma». Se deduce por el título: expresiones explícitas, términos españoles frente a ingleses y, para los que no dicen nada, el idioma mayoritario de esa tienda (no se aplica a tiendas mixtas como Amazon).
- **Comprobación del idioma en la ficha del producto antes de avisar** (seguimientos): se lee el campo «Idioma» de la ficha, también en las filas de detalles de Amazon con sus marcas Unicode invisibles, y no se avisa si no es castellano. Se guarda 30 días en una tabla propia (`idiomas`). Si la ficha no lo dice o no se puede leer, se avisa con «idioma no verificado» en el motivo.
- 19 pruebas nuevas (114 en total), y una prueba de la página sin navegador, con un DOM simulado.

### Corregido
- **Avisos de Amazon en otro idioma**: Amazon traduce los títulos de sus anuncios, y «Extensión Marvel Champions: Deadpool» era la edición francesa. El título no puede delatarlo, así que ahora se mira la ficha. El aviso erróneo se ocultó de la lista.
- La preposición «de» y «héroes» cuentan como palabras españolas, para que «…the card game deadpool pack de héroes» (castellano con marca en inglés) no se tome por inglés.

## [0.8.5] - 2026-11-06

### Corregido
- **Avisos de productos importados a mano**: un aviso (en la app y por Telegram) de un producto que el usuario pegó a mano, por ejemplo de Ferretería Ibérica, no decía que su precio no se consulta en directo, así que parecía que BuscaTron había comprobado esa tienda. Ahora el motivo añade «precio importado a mano hace X h, no en directo».
- 1 prueba nueva (95 en total).

## [0.8.4] - 2026-11-07

### Añadido
- Cada seguimiento muestra su **próxima revisión automática** («en 11,6 h (07/11 11:23)» o «toca ya»), o «sin revisión automática» si está en pausa, para ver de un vistazo que los barridos están en marcha.

### Notas
- Comprobado en la instalación real que el planificador lanza solo un seguimiento vencido: a los 111 s de dejarlo a «cada 0,25 h» se ejecutó, actualizó 77 resultados y generó 4 avisos nuevos con envío por Telegram. Después se restauró el intervalo de 12 h.

## [0.8.3] - 2026-11-06

### Añadido
- **Cortesía con las tiendas**: pausa de 0,6 s entre peticiones seguidas a la misma web (candidatas y páginas), tope de 4 direcciones de prueba cuando no se conoce el buscador, parada inmediata ante un «429 demasiadas peticiones» y 10 minutos sin volver a llamar a una web que no responde a la conexión (se muestra «no responde, se vuelve a intentar en N min»; así tampoco se espera 20 s en cada búsqueda). Motivo: una tienda recién añadida sin buscador conocido recibía muchas peticiones en pocos segundos, ritmo que dispara los bloqueos automáticos de IP.
- **Bixoto** con su dirección de búsqueda ya configurada (`https://bixoto.com/es?search={q}`), sin necesidad de descubrirla.
- 5 pruebas nuevas (94 en total).

### Notas
- En la conexión del usuario, `bixoto.com` no acepta conexiones (puertos 80 y 443 sin respuesta) mientras que con datos móviles sí, lo que apunta a un bloqueo temporal de la IP doméstica en su servidor. BuscaTron lo muestra como «no responde» y el resto de tiendas funciona con normalidad.

## [0.8.2] - 2026-11-06

### Añadido
- **Quitar un aviso individual**: cada tarjeta de la pestaña Avisos tiene una **✕**. El aviso se *oculta* en vez de borrarse, porque BuscaTron usa esa lista para no repetir avisos: si se borrara, el producto volvería a avisar por Telegram en la siguiente revisión. Así solo vuelve a avisar si baja más de precio (o pasan 30 días). «Vaciar avisos» sigue borrándolos todos (y entonces sí pueden repetirse).
- 3 pruebas nuevas (89 en total).

### Mejorado
- **«Solo castellano»** reconoce también títulos claramente ingleses que no dicen «inglés», muy comunes en Amazon: «Players», «Playing Time», «Minutes» y «Ages 14». Si el título menciona el castellano, sigue ganando este.

## [0.8.1] - 2026-11-06

### Corregido
- **Direcciones de producto inestables**: las de Amazon llevaban códigos de seguimiento (`ref=sr_1_40?dib=…&qid=…`) que cambian en cada búsqueda, así que BuscaTron veía el mismo producto como uno distinto cada vez: no acumulaba su historial ni su «Mínimo histórico» y los avisos por Telegram se **repetían en cada revisión**. Ahora cada producto tiene una dirección canónica: en Amazon, `https://www.amazon.es/dp/ASIN`; en el resto se quitan solo los parámetros de seguimiento (`utm_*`, `srsltid`, `gclid`, `fbclid`, `ref`, `referrer`, `qid`…) y el segmento `/ref=…`, sin tocar los que identifican el producto. En una prueba real, dos búsquedas seguidas en Amazon dieron las mismas 28 direcciones, de 49 caracteres como máximo, y los mensajes de Telegram dejan de llevar direcciones de varios cientos de caracteres.
- 3 pruebas nuevas (86 en total).

### Notas
- **Avisos por Telegram verificados** de punta a punta: mensaje de prueba y aviso real (seguimiento temporal con precio objetivo, 18 avisos nuevos, mensaje con los 10 primeros), ambos enviados sin error. El seguimiento temporal se borró después.
- La importación a mano se ha probado con texto real de Ferretería Ibérica: 47 productos leídos correctamente.

## [0.8.0] - 2026-11-06

### Añadido
- **Búsquedas recientes**: cada búsqueda hecha desde la web se guarda con sus resultados, filtros e informe de tiendas (hasta 12; repetir la misma sustituye a la anterior). Al abrir BuscaTron se restaura la última al instante, con el aviso «resultados guardados hace X, no se han vuelto a consultar» y un botón **Actualizar**. Una lista plegable permite abrir cualquiera (restaura también sus filtros) y **borrarlas** una a una con la ✕ o todas a la vez. API `/api/busquedas`.
- **Importar a mano** (📋 Pegar resultados) para las tiendas «solo enlace»: se pega el texto o el HTML de la página copiado desde tu propio navegador y BuscaTron lee los productos y precios, sin contactar con la tienda. Se mezclan al instante con la lista que ya está en pantalla (solo se consulta esa tienda, que no hace peticiones), se guardan 72 horas, entran en el historial de precios y quedan guardados dentro de la búsqueda reciente. Pensado para Ferretería Ibérica, cuya web está detrás de Cloudflare.
- 16 pruebas nuevas (83 en total).

### Corregido
- La lectura del texto importado se llevaba el precio del producto siguiente («Camiseta Marvel 12,00 €») si venía justo detrás; ahora solo cuenta el grupo de precios pegado a cada título.

### Notas
- Ferretería Ibérica sigue sin poder consultarse automáticamente: su buscador (Doofinder) funciona con sesiones firmadas de Phoenix LiveView y su web exige una comprobación de Cloudflare que rechaza el navegador controlado por BuscaTron, también cuando la resuelve una persona. Aceptar esa comprobación exigiría ocultar la automatización, algo que BuscaTron no hace.

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
