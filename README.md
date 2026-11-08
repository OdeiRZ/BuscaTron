# 🔎 BuscaTron

Buscador y vigilante de precios **local** para tiendas online españolas. Pensado para juegos de mesa, válido para cualquier producto: consulta las tiendas en vivo desde tu propio PC, ordena los resultados por precio y te avisa cuando algo baja.

- **Sin APIs de pago, sin cuentas y sin depender de ninguna IA.** Funciona con la biblioteca estándar de Python.
- **Datos en vivo**: no usa cachés ni comparadores intermedios, así que el precio es el que ves en la tienda.
- **Tus datos se quedan en tu equipo**: lista de tiendas, historial y tokens se guardan en archivos locales que no se suben al repositorio.

> Estado: **versión funcional** (v0.12.0). Consulta el [CHANGELOG](CHANGELOG.md).

## Inicio rápido

Requiere Python 3.9 o superior (probado con 3.10 y 3.13). No hay nada que instalar para lo básico.

En Windows se recomienda un entorno propio, que es lo que usan `BuscaTron.bat` y el arranque con Windows si existe:

```
py -3.13 -m venv .venv            # o la ruta completa de tu python.exe 3.13
.venv\Scripts\python -m pip install playwright
.venv\Scripts\python -m buscatron --arranque on
```

```
python -m buscatron --abrir              # interfaz web en http://127.0.0.1:8790
python -m buscatron --bandeja            # igual, con icono junto al reloj y sin ventana de mensajes (Windows)
python -m buscatron "marvel champions"   # búsqueda por línea de comandos
python -m buscatron --arranque on        # arrancar con Windows (off para quitarlo, estado para consultarlo)
```

En Windows también puedes hacer doble clic en `BuscaTron.bat`: abre el navegador, deja el icono en la bandeja y, si algo falla, vuelve a mostrar la ventana con el error. Si BuscaTron ya está en marcha (por ejemplo, porque arranca con Windows), solo abre su web.

Opciones: `--puerto N` (por defecto 8790) y `--host 127.0.0.1` para que solo sea accesible desde este equipo. Por defecto escucha en la red local, para poder usarlo desde el móvil (ver [Usar desde el móvil](#usar-desde-el-móvil)).

## Qué puedes hacer

La web está pensada para móvil (probada a 360 px) y escritorio. Arranca con el tema claro u oscuro de tu sistema y tiene un botón (🌙 / ☀️) en la cabecera para alternarlo; recuerda tu elección.

### 🔎 Buscar
- **Agrupa el mismo producto de varias tiendas** (opción «Agrupar», activada por defecto): una tarjeta por producto con su mejor precio y, desplegables, las demás tiendas. El producto se reconoce por sus palabras significativas (sin editorial, «expansión», «castellano», referencias de la tienda…) o, si usas «al menos una de estas», por la frase que encaja (salvo que la frase sea la propia búsqueda: con «Vantage» buscando «Vantage» juntaría en una tarjeta el juego, un reloj Polar Vantage y un coche Aston Martin Vantage). El desplegable dice cuántas tiendas hay de verdad: «6 tiendas más» o, si una tienda tiene varias ofertas, «40 ofertas más en 3 tiendas».
- **Ordenar por** precio (de menor a mayor o al revés), nombre o tienda, encima de los resultados; se recuerda tu elección. «Más barato» marca siempre el más barato, esté donde esté.
- **Descuento sobre el precio de mercado**: «−19 % sobre su precio de mercado (44,99 €)», donde el precio de mercado es el que más se repite entre al menos 3 tiendas (sin contar la segunda mano, y contando también las tiendas que tu filtro de precio deja fuera).
- Debajo de cada producto, dos acciones:
  - **🎯 Avisarme a…**: un precio objetivo solo para ese producto («avísame de Civil War a 30 €»). Tus búsquedas vigiladas usan ese objetivo en vez del suyo cuando lo encuentran, en cualquier tienda; el producto lleva la etiqueta «🎯 Tu objetivo». Se ven y se quitan en Ajustes → «Objetivos por producto».
  - **🚫 No me interesa** (ya lo tengo): oculta un producto para siempre, en todas las tiendas, en tus búsquedas y en los avisos. Se recupera en Ajustes → «Productos ocultos».
- La búsqueda **sigue en BuscaTron aunque cierres o bloquees el móvil, cambies de app o recargues**: al volver se recoge sola el resultado.
- Busca un producto en todas las tiendas activas y ve los **N más baratos**, con precio, tienda, enlace y etiquetas (preventa, segunda mano y su estado, mínimo histórico…).
- Las palabras se buscan **desde el principio de una palabra del título**: «carta» encuentra «cartas», pero «vantage» ya no encuentra «Tactical Advantage».
- **Nombres que comparten otros productos** («Vantage» es también un reloj Polar, un coche Aston Martin y unos guantes Ansell): ningún filtro por nombre los distingue, porque la palabra es la misma. Lo que funciona es combinar un **precio mínimo** cercano al del juego con **Descartar** las palabras de lo que se cuela. Con «Vantage», precio mínimo 50 € y descartar `aston amr buggy rc guante siku carson ftx coche` deja exactamente las 9 ofertas del juego.
- Filtros: palabras que debe contener, **al menos una de varias** (separadas por comas; ideal para vigilar varias ediciones o expansiones con una sola búsqueda, p. ej. `tirania, galaxia, titan loco`; ignora espacios y puntos, así que `shield` encuentra «S.H.I.E.L.D.»), palabras a descartar, precio mínimo y máximo, y **páginas leídas por tienda** (1 a 6).
- **Ocultar agotados** (activado por defecto). Reconoce «agotado», «sin stock», «en reposición» y «reserva», y descarta los productos que la tienda no puede enviar ya.
- **Idioma de los juegos** (selector con tres modos y una etiqueta de idioma en cada producto; ver [Idioma de los juegos](#idioma-de-los-juegos)): por defecto *Solo castellano*.
- En **«Más fuentes y opciones»** (se recuerdan entre búsquedas):
  - **Incluir preventas**: por defecto se ocultan, porque no se pueden recibir todavía. Se distinguen de los agotados («Lanzamiento aproximado: 26/3/2027», «Preventa»).
  - **Sumar el envío al precio**: ordena por el precio total (ver [Gastos de envío](#gastos-de-envío)).
  - **Incluir segunda mano** (ver [Segunda mano](#segunda-mano)).
  - **Buscar también en otras webs** (ver [Búsqueda abierta](#búsqueda-abierta)), con región España, Unión Europea o cualquier país.
- **Historial** (📈 en cada resultado): con «Agrupar», la gráfica del **producto**: su mejor precio en cualquiera de tus tiendas (nuevo, con stock, sin preventas), hora a hora, y en qué tienda está ahora; el botón «Ver solo …» enseña la de esa tienda. Sin agrupar (y en Avisos), la del artículo de esa tienda. Con mínimo, media, máximo y precio actual. La etiqueta «Mínimo histórico» salta cuando está al precio más bajo que se le ha visto, con al menos tres datos previos.
- **Búsquedas recientes** (🕘): cada búsqueda se guarda con sus resultados (hasta 12; repetir la misma sustituye a la anterior). Al abrir BuscaTron reaparece la última al instante, con el aviso «resultados guardados hace X» y un botón **Actualizar** para volver a consultarla. Tocando una de la lista se restauran también sus filtros. Cada una se borra con la ✕, o todas con «Borrar todas».
- Tiendas: actívalas o desactívalas con un toque, añade otras con el dominio (`ejemplo.es`) y, en «Gestionar tiendas», **edita su nombre, su dirección o URL de búsqueda, el envío y el modo «solo enlace»** cuando quieras. Si el buscador de una web no se detecta, pega una URL de búsqueda con `{q}` donde va el producto: `https://ejemplo.es/buscar?q={q}`. Cambiar la dirección a otro dominio hace que se vuelva a descubrir su buscador.
- **Solo enlace**: marca así las tiendas que bloquean el acceso automático (por ejemplo Wallapop). No se consultan, pero cada búsqueda te ofrece su enlace ya preparado para abrirlo tú y un botón **📋 Pegar resultados** para [importar a mano](#importar-a-mano) lo que veas en ellas.

### 👁️ Vigiladas
Pulsa «Vigilar esta búsqueda» (o crea una en la pestaña Vigiladas) y deja que BuscaTron la revise sola cada X horas mientras esté abierto (con el [arranque con Windows](#arranque-con-windows-y-bandeja), siempre).
- **Aviso por precio objetivo** («menos de 39 €»), por **bajada respecto a la media histórica** del artículo («un 15 % menos de lo habitual»), o por ambos. Si un producto tiene **su propio objetivo (🎯)**, se usa ese en lugar del de la búsqueda («por debajo de tu objetivo para este producto de 30 €»); tiene que estar dentro del precio mínimo y máximo de la búsqueda. Un objetivo 🎯 **solo avisa si alguna búsqueda vigilada activa encuentra ese producto**: al ponerlo, BuscaTron te dice cuál lo cubre o, si ninguna, te ofrece vigilar la búsqueda en ese momento.
- Cada seguimiento lleva las mismas opciones que la búsqueda: preventas, envío, segunda mano, otras webs y páginas por tienda.
- **Comprueba la ficha del producto** antes de avisar: si su ficha dice que está agotado o en preventa (y no las incluyes), no avisa, aunque el listado de la tienda no lo diga. También el idioma (ver [Idioma de los juegos](#idioma-de-los-juegos)): un juego en francés no te avisa aunque su título esté en español.
- No repite avisos: solo vuelve a avisar si el precio baja más, o pasados 30 días.
- **Resumen por Telegram** (opcional, en cada búsqueda vigilada): si una revisión no trae avisos nuevos, te manda igualmente los 5 más baratos del momento, para saber que la vigilancia funciona. Ojo: «Precio máximo» solo filtra resultados; para que te avise hay que rellenar «Avisarme si cuesta como mucho» o el % de bajada.
- **Revisión automática**: cada seguimiento se revisa solo cada X horas (por defecto 12) mientras BuscaTron esté en marcha, y la tarjeta muestra cuándo toca la próxima. Si el equipo estaba apagado, la revisión pendiente se lanza al encender, en menos de un minuto. Cada revisión actualiza los precios y el historial.
- **Estado de cada revisión** en su tarjeta: «3 productos (10 ofertas), 0 avisos nuevos, 1 tiendas sin respuesta». «Sin respuesta» son solo las tiendas que fallaron (sin conexión, captcha, error de su web); una tienda que respondió pero no tiene ese producto no cuenta. Si la revisión entera falla, se anota «la revisión falló: …» y espera a su hora, en lugar de repetirse cada minuto contra todas tus tiendas.
- **🔄 Buscar ahora** (una revisión inmediata, con sus avisos; no quita la pausa), **⏸️ Pausar / ▶️ Reanudar** (al reanudar, si ya le tocaba, se revisa en menos de un minuto), editar y borrar (al borrar un seguimiento se borran también sus avisos; el historial de precios se conserva).

### 🔔 Avisos
Lista de todo lo que ha saltado, con el motivo, la tienda, el enlace y el historial (📈). Se puede **ordenar** por fecha, por precio (de menor a mayor o al revés), por nombre o por tienda, y recuerda tu elección. Un contador rojo en la pestaña indica los nuevos.

Cada revisión **retira los avisos que ya no cumplen tu búsqueda** (porque se agotó, es una preventa, está en otro idioma o salió de tu rango de precio), siempre que la tienda haya respondido: si una web falla (sin conexión, captcha, error), no se borra nada de esa tienda; si responde pero ya no tiene el producto, su aviso se retira. Los avisos largos de Telegram se parten en varios mensajes (el límite de Telegram es de 4096 caracteres). Si un producto vuelve a estar disponible a un precio que cumple, avisa de nuevo. Con «Vaciar avisos» puedes limpiar la lista a mano, o quitar uno solo con la **✕** de su tarjeta: se oculta de la lista pero BuscaTron recuerda que ya te avisó, así que no vuelve a avisar de ese producto salvo que baje más de precio (o pasen 30 días).

### ⚙️ Ajustes
- **Búsqueda**: páginas que se leen por tienda por defecto.
- **Arranque con Windows**: interruptor para iniciar BuscaTron al encender el equipo.
- **Estado de las tiendas**: cuántas de sus últimas 10 consultas dieron resultados, cuándo fue el último y su último problema, con un botón para desactivarla. Distingue la tienda que **no responde** (conviene desactivarla) de la que **responde bien pero no ha tenido nada de lo que buscas** (por ejemplo, Outlet-PC sin stock de ese juego): esa solo conviene desactivarla si no suele tener tus juegos.
- **Productos ocultos**, para volver a mostrarlos.
- **Objetivos por producto** (🎯), para quitarlos.
- **Telegram** y **correo (SMTP)** para recibir los avisos, con botón de prueba.
- **Acceso desde el móvil**: las direcciones para abrirlo, con la HTTPS de Tailscale (🔒) la primera si la tienes publicada, y PIN opcional.
- **Navegador**: usar tu Chrome para tiendas que cargan con JavaScript.

## Idioma de los juegos

Los títulos de las tiendas casi nunca dicen el idioma (en una muestra real, el 88 % no lo decía), así que BuscaTron lo deduce y te enseña **qué sabe de cada producto** con una etiqueta:

| Etiqueta | Significa |
|---|---|
| **En castellano** (verde) | el título lo dice: «Castellano», «Español» |
| **Probablemente en castellano** (verde) | se deduce: artículos y términos españoles («Pack de héroes», «La Tiranía del Cráneo Rojo»), o la mayoría de lo que vende esa tienda está en castellano |
| **En inglés** / **En otro idioma** (rojo) | el título lo dice: «Inglés», «Français», o frases inglesas como «Players», «Playing Time», «Ages 14+» |
| **Probablemente en inglés** (rojo) | se deduce por palabras inglesas sin ninguna española («Hero Pack … Card Game») |
| *(sin etiqueta)* | no hay pistas |

El selector **«Idioma del juego»** (en la búsqueda y en cada seguimiento) tiene tres modos:
- **En castellano (incluye los dudosos)** (por defecto): oculta solo lo que **dice expresamente** estar en otro idioma. Lo dudoso se muestra, con su etiqueta.
- **Solo castellano confirmado**: deja solo lo que **está o parece** en castellano. Es más seguro, pero también oculta los títulos sin pistas.
- **Cualquier idioma**: no filtra.

**La ficha manda en los avisos.** Algunas tiendas, sobre todo Amazon, traducen los títulos de sus anuncios: «Extensión Marvel Champions: Deadpool» puede ser la edición francesa. Por eso, antes de enviar un aviso de un seguimiento, BuscaTron abre la **ficha del producto** y lee su campo «Idioma» («Idioma: Francés»): si no es castellano, no avisa. Si la ficha no dice el idioma o no se puede leer, avisa igualmente pero el motivo lo indica («idioma sin confirmar»). El resultado se recuerda 30 días, así que cada ficha se consulta una vez. Con «Cualquier idioma» no se consulta ninguna ficha.

## Importar a mano

Para las tiendas que no se pueden consultar solas (por ejemplo **Ferretería Ibérica**, cuya web está detrás de una comprobación de Cloudflare que rechaza cualquier navegador controlado por un programa), **tú miras en tu navegador y BuscaTron lee lo que copies**:

1. En los resultados, en «Tiendas que tienes que mirar tú», abre el enlace de la tienda: ya lleva tu búsqueda puesta.
2. En esa página selecciona todo (Ctrl+A) y copia (Ctrl+C). En el móvil: mantén pulsado, «Seleccionar todo» y «Copiar».
3. Pulsa **📋 Pegar resultados**, pega el texto y pulsa **Añadir a los resultados**.

Unas 12 horas antes de que caduquen, BuscaTron te lo **recuerda por Telegram** (una vez por pegado). Los avisos de productos importados lo indican («precio pegado a mano hace 5 h, sin comprobar en directo»), porque BuscaTron no puede comprobar esa tienda por su cuenta. Los productos y precios se mezclan **al instante** con el resto de la lista (y con el historial, las gráficas y los avisos de los seguimientos), con la etiqueta «Pegado a mano hace X h». Se recuerdan **72 horas** y se guardan también en la búsqueda reciente, así que no hace falta repetirlo al volver.

- Acepta el texto de la página o su código HTML (en ese caso conserva los enlaces de cada producto). **No hace ninguna petición a la tienda.**
- Se leen los productos cuyo título contiene tu búsqueda y que llevan un precio justo después; si hay dos precios seguidos (el anterior y el actual) se toma el menor. Las cabeceras («Resultados de búsqueda…»), los productos sin relación y los precios de lo que viene detrás no se cuentan. Reconoce «agotado» y «preventa» igual que en las demás tiendas. Probado con el texto real de Ferretería Ibérica: 47 productos leídos con sus precios.
- Es una lectura de texto, no de la estructura de la página: si una tienda presenta los precios de una forma muy distinta (por ejemplo, el precio antes del título), puede fallar. En ese caso BuscaTron te dice que no encontró productos.

## Segunda mano

Con «Incluir segunda mano» se consultan además estas webs, y los resultados llevan el **estado** del artículo («nuevo con etiquetas», «muy bueno», «bueno»…):

| Web | Estado |
|---|---|
| Vinted | ✅ se consulta |
| Milanuncios | ✅ se consulta |
| Wallapop | 🔗 solo enlace: devuelve un 403 («Request blocked») a cualquier acceso automático, también con un navegador real |
| eBay | 🔗 solo enlace: igual que Wallapop |

Se añaden a tu lista de tiendas la primera vez (como «segunda mano») y puedes quitarlas, renombrarlas o añadir otras marcando «Es una web de segunda mano» al dar de alta una tienda.

## Búsqueda abierta

«Buscar también en otras webs» sirve para **descubrir tiendas que no tienes en la lista**:

1. Hace la búsqueda en **Bing** (y en DuckDuckGo si Bing da pocas direcciones), con dos formulaciones y dos páginas de resultados.
2. Descarta las tiendas que ya consultas, las que bloquean bots (Amazon, eBay, Wallapop…), las redes sociales, enciclopedias y reseñas, y las webs de países fuera de la región elegida (España: `.es` y dominios genéricos; Unión Europea: además otros países de la UE; cualquier país: todas).
3. Lee el precio de las páginas halladas: fichas de producto (datos estructurados de schema.org o Open Graph) y listados de tiendas. Solo se muestran precios en euros.
4. Las webs nuevas aparecen en «Tiendas que no tienes en tu lista» con un botón para **añadirlas a tu lista** y consultarlas siempre.

Es menos precisa y más lenta que las tiendas de tu lista: úsala para descubrir y, cuando una web te guste, añádela.

## Gastos de envío

El precio mostrado no incluye el envío salvo que lo configures:
- En «Gestionar tiendas», cada tienda tiene **Envío (€)** y **Gratis desde (€)**. El botón **Detectar** busca en la portada de la tienda frases como «Envío gratis a partir de 50 €» y rellena los campos; es solo una pista, así que revísala.
- Si el envío de una tienda es conocido, la tarjeta muestra «+ 4,95 € envío» o «envío gratis».
- Con «Sumar el envío al precio», los resultados se ordenan por el **precio total** (precio + envío, o 0 si superas el mínimo gratuito).

## Arranque con Windows y bandeja

- Activa «Arrancar con Windows» en Ajustes (o `python -m buscatron --arranque on`). Crea un acceso directo en la carpeta Inicio de tu usuario (`shell:startup`): **no necesita permisos de administrador**.
- BuscaTron se inicia **sin ventana** (`pythonw`) y deja un **icono junto al reloj**. Doble clic abre la web; el menú permite abrirla, ver u ocultar la ventana de mensajes (si la hay) y cerrar BuscaTron.
- Sin ventana, los mensajes y errores van a `buscatron.log`.
- Por seguridad, el interruptor solo se puede cambiar desde el propio equipo, no desde el móvil.

## Configurar Telegram

1. En Telegram, habla con **@BotFather**, crea un bot con `/newbot` y copia su token.
2. En BuscaTron: Ajustes → pega el token.
3. Escribe cualquier mensaje a tu bot desde tu cuenta.
4. Pulsa **Detectar chat** (rellena el Chat ID solo) y luego **Enviar prueba**.
5. En Seguimiento, marca «Avisarme por Telegram» en cada búsqueda que quieras.

> El token se guarda en texto plano en `config.json`, que está en `.gitignore`. No lo compartas ni lo subas.

### Órdenes al bot
Con BuscaTron abierto en el ordenador, el bot también te responde (el menú «/» de Telegram las muestra):

| Orden | Qué hace |
|---|---|
| `/buscar civil war` (o escribir solo `civil war`) | busca en tus tiendas (en castellano y con stock) y te manda los 5 productos más baratos, agrupados, con las otras tiendas |
| `/vigiladas` | tus búsquedas vigiladas, su última revisión y la próxima |
| `/revisar` | revisa ahora todas las vigiladas activas; los avisos llegan como siempre |
| `/ayuda` | la lista de órdenes |

Solo obedece al chat configurado en Ajustes (cualquier otro se ignora) y hace una búsqueda a la vez. Escucha con *long polling* (`getUpdates`), así que no hace falta abrir puertos ni tener dirección pública. «Detectar chat» sigue funcionando: toma el último chat que escribió al bot.

## Usar desde el móvil

BuscaTron escucha en tu red local, así que puedes abrirlo desde el móvil conectado a la **misma Wi-Fi**:

1. **Una sola vez**, haz doble clic en `permitir_acceso_movil.bat`. Pide permisos de administrador y abre el puerto 8790 del cortafuegos de Windows **solo para tu red local** (regla «BuscaTron (red local)»).
2. Arranca BuscaTron con `BuscaTron.bat` o con el arranque con Windows. Las direcciones, por ejemplo `http://192.168.0.28:8790`, aparecen en la ventana y en Ajustes → «Acceso desde el móvil».
3. Escribe la dirección de tu red local (suele empezar por 192.168) en el navegador del móvil. Para tenerla como una app, en Chrome: menú ⋮ → **«Añadir a pantalla de inicio»** (BuscaTron trae su nombre e icono). Para que se abra a pantalla completa, sin la barra del navegador, Chrome exige una conexión segura (HTTPS), que la red local no tiene; por ejemplo, `tailscale serve` da una dirección HTTPS.
4. **Recomendado:** pon un **PIN** en Ajustes → «Acceso desde el móvil». El móvil lo pedirá una vez y lo recordará 30 días. Este equipo no lo necesita.

### Desde fuera de casa y a pantalla completa (Tailscale)
Con [Tailscale](https://tailscale.com) en el PC y en el móvil, BuscaTron funciona desde cualquier sitio y con HTTPS, que es lo que Chrome pide para abrir la app a pantalla completa:

1. En la consola de Tailscale, **DNS → HTTPS Certificates → Enable** (una vez por red; MagicDNS tiene que estar activado).
2. En el PC: `tailscale serve --bg 8790`. Publica `https://<nombre-del-pc>.<tu-red>.ts.net` **solo dentro de tu red de Tailscale** (no es Funnel: nadie de fuera la ve) y lo reenvía a BuscaTron.
3. En el móvil, con Tailscale conectado, abre esa dirección y «Añadir a pantalla de inicio». BuscaTron la detecta sola y la enseña la primera, con un 🔒, en **Ajustes → Acceso desde el móvil**.

Las peticiones que llegan por `tailscale serve` no cuentan como «este equipo»: el arranque con Windows sigue sin poder cambiarse desde el móvil. Para quitarlo: `tailscale serve --https=443 off`.

Si el móvil no carga:
- Comprueba que usa la **Wi-Fi** y no los datos móviles, y que es la misma red que el PC.
- Mira que la dirección sea la de «red local» (192.168…) y no la de Tailscale ni la de Hyper-V. La IP puede cambiar si el router te asigna otra; la web la muestra siempre actualizada.
- Comprueba la regla del cortafuegos: `netsh advfirewall firewall show rule name="BuscaTron (red local)"` debe mostrarla habilitada, con `LocalPort: 8790` y `RemoteIP: LocalSubnet`. Si no existe, vuelve a ejecutar `permitir_acceso_movil.bat`.
- Algunos routers tienen activado el **aislamiento de clientes** (AP isolation), típico de las Wi-Fi de invitados: impide que los dispositivos se vean entre sí. Hay que usar la Wi-Fi principal o desactivarlo en el router.
- Si usas el puerto con `--puerto N`, la regla del cortafuegos sigue siendo para el 8790: ejecútala de nuevo cambiando el puerto en el `.bat`.

Seguridad:
- Solo se aceptan conexiones de **direcciones privadas** (red local, Tailscale y este equipo). Cualquier IP pública recibe un 403.
- Con PIN, los intentos fallidos se bloquean durante 5 minutos tras 5 errores. La sesión se guarda en una cookie firmada que no puede leer JavaScript.
- Sin PIN, cualquier dispositivo de tu red local puede usar BuscaTron, incluidos tus ajustes. Úsalo sin PIN solo en una red de confianza.
- Si no quieres acceso desde otros equipos: `python -m buscatron --host 127.0.0.1`.

## Cómo encuentra los productos

1. **Descubre el buscador** de cada tienda leyendo el formulario de su portada. Si no lo encuentra, prueba plantillas habituales (PrestaShop, Magento, Shopify, WooCommerce) y recuerda la que funciona. Algunas tiendas llevan su URL de búsqueda conocida en el código.
2. **Descarga los resultados** y se queda con los enlaces cuyo texto contiene todas las palabras de la búsqueda, junto al primer precio vigente (dentro de la tarjeta del producto o justo después). Ignora los precios tachados y el texto oculto de la página, y detecta «agotado» y «preventa». Entiende el punto de miles («1.299 €» son 1299 €) y el punto decimal («29.99 €»), y descarta los enlaces que no son direcciones web y los que llevan a otra búsqueda (sugerencias como «En lugar de lo anterior, busca…» o búsquedas relacionadas). Si la tienda recorta el título, lo reconstruye a partir del atributo `title` o de la dirección del producto. Las direcciones se guardan **sin códigos de seguimiento** (en Amazon, `amazon.es/dp/ASIN`; en el resto, sin `utm_*`, `ref`, `srsltid`…), de modo que un mismo producto es siempre la misma dirección: así acumula historial, «Mínimo histórico» y no repite avisos.
3. **Trata bien a las tiendas**: pausa de 0,6 s entre dos peticiones a la misma web, como mucho 4 direcciones de prueba cuando no conoce su buscador, parada inmediata si una tienda responde «429 demasiadas peticiones», no vuelve a llamar durante 10 minutos a una web que no ha respondido a la conexión, nunca lee más de 6 páginas por tienda (aunque pongas más en Ajustes) y una revisión vigilada que falla no se reintenta hasta su hora. Bixoto y Ferretería Ibérica no se consultan nunca de forma automática, tampoco desde la búsqueda abierta. Así evita que una tienda te bloquee la IP por parecer un ataque; si lo hiciera, te aparecería como «no responde».
4. **Sigue las páginas siguientes** (enlace `rel="next"` o «Siguiente») hasta el número de páginas elegido, mientras aporten productos nuevos.
5. **Si el método rápido no encuentra nada** y el navegador está activado, vuelve a intentarlo renderizando la página con tu Chrome (con Playwright). Si funciona, recuerda que esa tienda lo necesita.
6. **Ordena por precio** (o por precio total) y guarda cada resultado en `buscatron.db` (SQLite). Ese historial alimenta la regla de «bajada respecto a la media», la etiqueta «Mínimo histórico» y las gráficas. Una vez al día, lo de hace más de 6 meses se compacta a un precio por producto y día, para que no crezca sin control.

### Navegador opcional
Para las tiendas que cargan sus resultados con JavaScript. Está activado por defecto, pero solo funciona si tienes instalado Playwright y Chrome o Edge:

```
pip install playwright
```

No se descarga ningún navegador: usa el que ya tienes, con un perfil propio (`navegador_perfil/`).

Todas las consultas con navegador se hacen **en segundo plano**, sin ventanas. **BuscaTron no intenta saltarse protecciones antibot.** Si una tienda pide una comprobación humana, te lo dice; con «Mostrar la ventana» activado en Ajustes, solo para esa tienda se abre una ventana para que la resuelvas tú, y la sesión queda guardada. Las tiendas que bloquean todo acceso automático se ofrecen como «solo enlace».

## Tiendas probadas

Resultado de la prueba el 6/11/2026 (las webs cambian, así que puede variar):

| Estado | Tiendas |
|---|---|
| ✅ Funcionan (16) | Juegos de la Mesa Redonda, Zacatrus, Dungeon Marvels, Jugamos Una, Jugamos Otra, El Taller del Modelista, Mathom, Tablerum, Outlet Games, Ludus Belli, Bandua, Goblin Trader, Gameria, Masqueoca, Turol Games y **Amazon** (estas dos con navegador; Amazon, solo en su sección «Juguetes y juegos») |
| ➖ Responden, sin el producto probado (2) | Tiendas MGI, Outlet-PC |
| 🔗 Solo enlace (2) | Ferretería Ibérica Madrid y Bixoto (con [importación a mano](#importar-a-mano)); Bixoto bloquea la IP incluso con una sola consulta automática desde un Chrome real (probado el 7/11/2026), así que no se consulta nunca de forma automática |
| 🛒 Segunda mano | Vinted y Milanuncios funcionan; Wallapop y eBay, solo enlace |

## Archivos locales

Se crean al usar la herramienta y no se suben al repositorio:

| Archivo | Contenido |
|---|---|
| `tiendas.json` | tu lista de tiendas, nombres, envío y buscadores descubiertos |
| `buscatron.db` | historial de precios, seguimientos y avisos (SQLite) |
| `config.json` | tokens de Telegram, PIN, ajustes de correo, de búsqueda y del navegador |
| `navegador_perfil/` | sesión del navegador opcional |
| `buscatron.log` | mensajes y errores cuando BuscaTron se inicia sin ventana (al pasar de 2 MB se archiva como `buscatron.log.1`) |
| `.venv/` | entorno de Python propio de BuscaTron (opcional) |

`tiendas.json` y `config.json` se guardan de forma segura (en un temporal que sustituye al bueno de una vez), así que nunca quedan a medias aunque se lean y escriban a la vez; y lo que una búsqueda aprende de una tienda se guarda sin pisar lo que cambiaste mientras buscaba.

## Estructura

```
buscatron/
  __main__.py      arranque (web, bandeja, arranque con Windows o línea de comandos)
  web.py           servidor web y API (filtro de IP, PIN)
  pagina.html      interfaz (una sola página, sin dependencias)
  motor.py         búsqueda en paralelo, páginas, filtros, envío, historial y orden
  extract.py       extractor genérico de productos, precios, estados y páginas siguientes
  abierta.py       búsqueda abierta (Bing / DuckDuckGo) y lectura de precios de las webs halladas
  importar.py      importación a mano de lo que se copia de una tienda (texto o HTML)
  busquedas.py     últimas búsquedas guardadas con sus resultados
  descubre.py      descubrimiento del buscador de cada tienda
  fetch.py         descargas con la biblioteca estándar
  navegador.py     navegador opcional (Playwright + Chrome)
  tiendas.py       lista de tiendas, plantillas, segunda mano y tiendas «solo enlace»
  seguimiento.py   vigilancia, reglas de aviso y no repetición
  telegram_bot.py  órdenes por Telegram (/buscar, /vigiladas, /revisar)
  programador.py   revisiones automáticas cada X horas
  notifica.py      avisos por Telegram y correo
  ajustes.py       configuración local
  bd.py            base de datos SQLite
  bandeja.py       icono en la bandeja de Windows (ctypes, sin dependencias)
  arranque.py      acceso directo de arranque con Windows
  icono.ico        icono de la aplicación
tests/             pruebas sin red
BuscaTron.bat                 lanzador (Windows)
permitir_acceso_movil.bat     abre el cortafuegos para tu red local (pide administrador)
```

## Pruebas

```
python -m unittest discover -s tests
```

175 pruebas, sin red. Cubren las reglas de aviso (objetivo de la búsqueda y del producto, media histórica, no repetir, reaviso, limpieza de obsoletos, tienda caída frente a tienda sin el producto), qué vigilada cubre cada objetivo, el historial por producto, las órdenes del bot y los mensajes largos de Telegram, la escritura segura de los archivos y los cambios de tiendas durante una búsqueda, los errores del servidor, el tope de páginas y las revisiones que fallan, los precios con punto de miles, el extractor (precios tachados, texto oculto, títulos recortados, preventas, estados de segunda mano, páginas siguientes, datos de producto, envío), el motor (paginación, filtros, total con envío, mínimo histórico, historial), la búsqueda abierta, el filtro de IP y el PIN, la importación a mano y las búsquedas guardadas.

## Limitaciones conocidas

- Las revisiones programadas solo se ejecutan **mientras BuscaTron esté abierto**: activa el arranque con Windows para que lo esté siempre.
- No reconoce «el mismo producto» entre tiendas: filtra por palabras. Usa «Descartar» para quitar accesorios, packs o ediciones que no te interesan, y un precio mínimo para los productos que se llaman igual que tu juego.
- Amazon se consulta solo en su sección **«Juguetes y juegos»** (`&i=toys` en su dirección de búsqueda): sin ella, «Vantage» devolvía 166 relojes, protectores y coches y el juego ni aparecía. Si buscas otras cosas en Amazon, quítalo de su dirección en «Editar la lista de tiendas».
- Las tiendas cambian su web de vez en cuando y su lector puede dejar de funcionar. La web indica qué tiendas no han respondido.
- Ferretería Ibérica, Wallapop y eBay bloquean cualquier acceso automático: solo se ofrece su enlace y, para ellas, la [importación a mano](#importar-a-mano). Amazon solo responde a un navegador real, así que necesita el [navegador opcional](#navegador-opcional) (Playwright y Chrome o Edge) y puede volver a pedir una comprobación humana si lo considera sospechoso.
- La búsqueda abierta usa buscadores web gratuitos: es menos precisa, solo lee precios en euros y puede dejar de funcionar si el buscador la bloquea.
- Los gastos de envío los pones tú (o los sugiere «Detectar», que es solo una pista); no se leen del carrito de cada tienda.
- Las preventas se reconocen por el texto de la tienda («Preventa», «Lanzamiento aproximado»…); una tienda que no lo diga puede colarse como disponible.
- El envío por correo (SMTP) está implementado pero todavía sin probar con un servidor real.

## Licencia

AGPL-3.0. Consulta [LICENSE](LICENSE).
