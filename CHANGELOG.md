# Changelog

Todos los cambios relevantes de BuscaTron se documentan aquí.
El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y el proyecto usa [versionado semántico](https://semver.org/lang/es/).

## [0.17.0] - 2026-11-09

### Añadido
- **Referencia de Amazon: vincular a mano y sugerencias.** «Los Más Buscados de la Galaxia» salía como «no visto en Amazon» aunque BuscaTron había visto su ficha 19 veces: Amazon la titula «Fantasy MC16ES Flight Games Marvel Champions», sin el nombre del juego. Ahora, si no hay un equivalente seguro, se sugieren fichas parecidas (parte del nombre y precio parecido) con un botón «Es este», y se puede pegar el enlace de su ficha (también los cortos amzn.eu/d/…, que se siguen). El vínculo se recuerda, manda sobre el emparejamiento automático y se puede quitar; con un ASIN que BuscaTron no ha visto, enseña igualmente sus enlaces a camelcamelcamel y Keepa.

### Corregido
- **Un producto de Amazon, un historial**: hasta el 6/11 las direcciones de Amazon se guardaban con el rastro de la búsqueda (`/dp/ASIN/ref=…&dib=…`) y 55 productos tenían su historial partido en varias. Se unificaron 346 precios a `amazon.es/dp/ASIN`, y la referencia agrupa por ASIN.

## [0.16.1] - 2026-11-09

### Corregido
- **Reiniciar desde la web cerraba BuscaTron sin volver a abrirlo** (sin .bat, como con el arranque de Windows): primero detenía el servidor, que corre en el hilo principal, y el programa terminaba antes de lanzar el nuevo. Ahora lanza el nuevo y sale al momento (al salir suelta el puerto; el nuevo reintenta hasta que queda libre). La prueba de reinicio real se hace ahora con el servidor en el hilo principal, como en BuscaTron; la anterior lo tenía en otro hilo y por eso no lo detectó.

## [0.16.0] - 2026-11-09

### Añadido
- **Reiniciar y cerrar BuscaTron desde la app** (Ajustes → 🔧 Servicio, también desde el móvil) y desde el menú del icono de la bandeja («Reiniciar BuscaTron»), con la lógica de PixelatIA: **nunca con un trabajo en marcha** (búsqueda, revisión de una vigilada o búsqueda del bot); lo dice y deja los botones desactivados hasta que termine. Mientras sale, no empieza trabajo nuevo.
- **🆕 en la cabecera** cuando el código cambió desde que arrancó: un toque reinicia y aplica la actualización. La página espera a que vuelva y se recarga.
- Al reiniciar sale con el código 3 y **BuscaTron.bat** lo vuelve a lanzar (sin abrir otra pestaña), como PixelatIA.bat. Con el arranque de Windows (pythonw, sin .bat) se relanza él mismo. Antes de salir cierra su Chrome y quita el icono de la bandeja; el nuevo reintenta unos segundos hasta que el puerto queda libre.

## [0.15.0] - 2026-11-09

### Añadido
- **📊 Referencia de Amazon** (botón en Avisos y en Vigiladas): todos tus productos de una vez, cada uno con tu mejor precio, su equivalente en Amazon y lo que BuscaTron ha visto allí (precio actual, más barato y más caro, desde cuándo), un veredicto («14 % por debajo de lo más barato visto en Amazon», «Amazon está más barato ahora»), aviso si esa ficha no está en castellano, su gráfica y enlaces a camelcamelcamel y Keepa. Puede verse «De tus avisos» o «De lo que encuentran tus vigiladas». Sale todo de la base de datos, sin consultas.
- El emparejamiento descarta lo que descarta la vigilada (fundas…) y lo que cuesta menos de la mitad o más del doble (packs); con nombres de una palabra («Vantage») solo toma lo que se anuncia como juego.

### Corregido
- El botón «atrás» con una hoja abierta encima de otra (el historial sobre la referencia) cierra solo la de encima.
- Se borró de la caché la ficha de Bixoto de «La Próxima Evolución», mal leída como otro idioma por el fallo de la v0.13.2 (Bixoto no se consulta sola, así que no podía volver a leerse).

## [0.14.1] - 2026-11-08

### Corregido
- **Ediciones de otro país en Amazon**: avisó de «Asmodee Marvel Champions: Civil War FFG - Extensión de Juego de Cartas» (36,94 €), que es la edición francesa: su ficha no tiene campo «Idioma» y el título dice «Versión ES». Ahora, en Amazon, si la ficha no dice el idioma y tiene al menos 2 opiniones y ninguna de España, cuenta como otro idioma. Probado con 14 fichas: las ediciones en castellano tienen opiniones de España; las sospechosas eran Civil War (4 de Francia) y dos Dune de Asmodee (todas de Italia). Se borró el aviso.
- **La ficha manda también en las búsquedas**: si ya se leyó la ficha de un producto, su idioma cuenta en lugar del que sugiere el título; así esa edición francesa no sale en castellano, y lo que la ficha confirma sale como «En castellano» en vez de «Probablemente».

## [0.14.0] - 2026-11-08

### Añadido
- **PC a pantalla ancha**: Buscar a dos columnas (formulario a la izquierda, resultados a la derecha), Vigiladas y Avisos en rejilla de dos, Ajustes a dos columnas y las pestañas fijas arriba al bajar. Antes todo iba en una columna de 760 px.
- **Botón «atrás» del móvil**: vuelve a la pestaña anterior y cierra el historial de precios o «Pegar resultados», en vez de salir de la app. Cada pestaña tiene su dirección (`#avisos`…).
- **Tecla «/»** para ir a la caja de búsqueda; contorno visible al moverse con el teclado y efecto al pasar el ratón.
- **Vigiladas, filtro rápido** Todas / Activas / En pausa (con su número).
- **Avisos**: marca «Nuevo» en los que no habías visto y de qué vigilada viene cada uno.

### Cambiado
- **Tarjetas de vigiladas** más cortas: estado claro (Activa, En pausa, Revisándose…), lo esencial a la vista y los filtros largos, canales y frecuencia en «Más detalles» (no se cierra al repintar). Las pausadas, con borde discontinuo. Botones en 2×2 en el móvil, sin cortes.
- **Avisos**: el motivo ocupa todo el ancho bajo el título y los botones («Historial de precio», «Quitar aviso») van debajo, como en los resultados; antes el motivo quedaba apretado entre dos botones laterales.
- **Idioma**: en vez de un párrafo fijo, una línea que explica solo la opción elegida (también al vigilar).
- **Estado de las tiendas**: arriba solo las que piden atención; las que van bien, plegadas («21 tiendas sin problemas»).
- **Editar una vigilada** abre el formulario, lo lleva a la vista y pone el cursor en el nombre.
- Los contadores de los desplegables («3 en uso») van junto a la flecha, no flotando en medio.

### Corregido
- **Títulos de Zacatrus** con el nombre dos veces y sus precios («Hulk Hulk 16,95 € Club -10% 15,26 € ?»): ahora «Hulk». Como los números entraban en la clave del producto, tampoco se agrupaban con el mismo juego de otras tiendas. Se corrigieron los 102 precios guardados y las búsquedas recientes.
- Plurales: «1 oferta», «1 aviso nuevo», «1 tienda sin respuesta».

## [0.13.3] - 2026-11-08

### Corregido
- **Avisos de productos agotados (Zacatrus)**: si la ficha no publica la disponibilidad en sus datos, se daba por «hay stock». Avisó de Mage Knight Edición Definitiva a 108 € en Zacatrus, que dice «No está disponible · Avisadme cuando esté disponible». Ahora falta de datos es «no se sabe» y, en ese caso, se lee el botón de «Avísame/Avisadme cuando esté disponible» de la ficha. No cuenta el texto fijo de Zacatrus sobre el envío 24 h («este producto está fuera de stock en nuestro almacén»), que sale en todas sus fichas. Comprobado con fichas reales de 9 tiendas: ningún producto con stock pasa a agotado. Se borró el aviso falso.

## [0.13.2] - 2026-11-08

### Corregido
- **Avisos bloqueados por un idioma mal leído en la ficha**: si la ficha tenía una etiqueta «Idioma» vacía, se tomaba como idioma el texto siguiente («+ Detalles del producto» en Dungeon Marvels, la propia palabra «Idioma» en Goblin Trader), salía «otro idioma» y no avisaba. Le pasó a Mage Knight: Edición Definitiva en Dungeon Marvels (114,71 €, por debajo del objetivo). Ahora lo que sigue a una etiqueta vacía solo cuenta si es un idioma, y si no se sigue buscando (la ficha técnica sí dice «Castellano»). Se borraron de la caché las 3 fichas mal leídas para que se vuelvan a leer.

## [0.13.1] - 2026-11-08

### Corregido
- **«Buscando…» desaparecía** al guardar una vigilada (o pausarla, o recargar) mientras otra se revisaba: lo sabía solo el botón pulsado y la lista se volvía a pintar. Ahora el servidor dice cuáles se están revisando y la página lo muestra siempre, también en las revisiones automáticas y desde otro dispositivo; avisa al terminar sin repintar la lista mientras la usas.
- **Editar una vigilada mientras se revisa**: la revisión seguía con la configuración de antes (resultados y avisos con los filtros viejos). Ahora, si cambias la búsqueda o sus filtros, al terminar se revisa otra vez con los cambios (como mucho tres vueltas). Cambiar el nombre, la frecuencia o pausarla no la repite.
- **Borrar una vigilada mientras se revisa** podía dejar avisos suyos sin vigilada; ahora se borran.

## [0.13.0] - 2026-11-08

### Añadido
- **Ordenar las vigiladas**: en el orden en que las creaste, las últimas creadas primero, por nombre, activas primero, la próxima en revisarse o las que llevan más sin revisarse. Se recuerda y se mantiene al pausar, reanudar o revisar. Encima de la lista, cuántas hay activas y cuántas en pausa.

## [0.12.2] - 2026-11-08

### Corregido
- **Campos numéricos a `null` en la API**: una búsqueda con `"pmax": null` fallaba («could not convert string to float: 'None'»). Ahora `null` cuenta como campo vacío, igual que lo que envía la página.

## [0.12.1] - 2026-11-08

### Añadido
- **Amazon: página de repaso** para los juegos mal clasificados. Además de «Juguetes y juegos», se lee una página en todas las secciones y por relevancia, y de ella solo se toman los productos cuyo título dice que son un juego. Eternal Decks (que Amazon no tiene en «Juguetes y juegos») vuelve a salir; «Vantage» no trae relojes ni protectores.

### Corregido
- **Un producto se quedaba con el stock del siguiente**: tras un producto que coincide con la búsqueda, el extractor seguía leyendo hasta el siguiente que coincidiera, y se llevaba el aviso de los de en medio. En Dungeon Marvels, «Mage Knight: Edición Definitiva» (en preventa) salía agotado por el «En reposición» de *Krang Character*, y no aparecía. Ahora la tarjeta acaba donde empieza la de cualquier otro producto. En 36 páginas reales de 12 tiendas corrige 8 agotados falsos y no cambia nada más.
- **Lo que va entre la imagen y el título** es del producto: en Jugamos Una el «Agotado» va ahí y se perdía (5 agotados que salían como disponibles; uno acertaba de casualidad con el aviso del siguiente).
- **«Casi agotado» no es agotado** (Dracotienda: «Últimas unidades · Casi agotado»).
- **Precios con descuento en Goblin Trader**: su precio vigente lleva la clase `price--discount`, que se tomaba por tachado, así que los productos con descuento no salían o se llevaban el precio del de al lado (Mage Knight a 27 € en vez de 121,45 €). Recupera 14 productos en tres búsquedas de prueba.

## [0.12.0] - 2026-11-08

### Añadido
- **Ordenar los resultados** de una búsqueda por precio (de menor a mayor o al revés), nombre o tienda; se recuerda. Ya no hace falta ir al final de la lista para ver los más caros. «Más barato» marca siempre el más barato, no el primero de la lista.

### Cambiado
- **Amazon, solo en «Juguetes y juegos»**: con «Vantage» pasaba de 166 relojes, protectores y coches (sin el juego) a 33 ofertas con el juego entre ellas. Cambia una sola vez, y solo si tenías la dirección de Amazon de siempre; se deshace en «Editar la lista de tiendas».
- **Palabras desde el principio de una palabra**: «vantage» ya no encuentra «Tactical Advantage» (sigue valiendo «carta» para «cartas» y «spiderman» para «Spider-Man»). En la búsqueda, los filtros, las vigiladas, lo pegado a mano y la búsqueda abierta.

### Corregido
- **«148 tiendas más» que eran 148 ofertas de 9 tiendas**: el desplegable cuenta ahora las tiendas de verdad («148 ofertas más en 9 tiendas»).
- **Todo en una sola tarjeta**: con «al menos una de estas» igual a la propia búsqueda («Vantage» buscando «Vantage»), todo lo que contuviera la palabra se agrupaba como un único producto. Ahora esa frase no agrupa; las que sí distinguen productos (campañas) siguen agrupando.

## [0.11.9] - 2026-11-08

### Corregido
- **Enlaces de búsqueda tomados por productos**: en Amazon, la sugerencia «En lugar de lo anterior, busca Eternal decks» y las búsquedas relacionadas («marvel champions fundas») contienen las palabras buscadas, así que salían como un producto con el precio de la tarjeta siguiente (p. ej. 9,99 €, «Más barato» y «−72 %»), y su enlace llevaba al buscador. Ahora se descartan los enlaces que llevan a la propia página de resultados y los textos de sugerencia del buscador. Se borraron del historial los 13 precios falsos que habían dejado (ninguno llegó a avisar).

## [0.11.8] - 2026-11-08

### Cambiado
- **Estado de las tiendas** ya no da por rota una tienda que responde bien pero no tiene lo que buscas (p. ej. Outlet-PC sin stock de ese juego): lo dice así y sugiere desactivarla solo si no suele tener tus juegos. «Conviene desactivarla» queda para las que no responden.
- **README** al día con todo lo de la auditoría: qué cuenta como «tienda sin respuesta», el 🎯 que solo avisa si una vigilada encuentra el producto, revisiones fallidas, tope de 6 páginas, Bixoto y Ferretería nunca automáticas, precios con punto de miles, mensajes largos de Telegram, dirección HTTPS en Ajustes, guardado seguro de los archivos y log archivado.

## [0.11.7] - 2026-11-08

### Corregido
- Si abrías la gráfica de un producto y enseguida la de otro, la respuesta tardía del primero podía taparla.
- «¿Vigilar ahora la búsqueda…?» (al poner un 🎯 que ninguna vigilada cubre) usa la búsqueda de los resultados en pantalla, no lo que hubiera escrito después en la caja.

## [0.11.6] - 2026-11-08

### Corregido
- **Precios con punto de miles**: «1.299 €» se leía como 299 €, «2.500€» como 500 € y «€ 1.299» como 1,29 €, así que un producto caro podía salir como el más barato (y hasta avisar). Ahora se leen bien, tanto de las tiendas como de lo pegado a mano; comprobado sin cambios en páginas reales guardadas de Amazon y Bixoto.
- Las conexiones a la base de datos se cierran al terminar cada operación (antes quedaban abiertas hasta que Python las recogía).

## [0.11.5] - 2026-11-08

### Corregido
- **Sin ráfagas de consultas por un fallo**: si una revisión vigilada fallaba, no se anotaba y el programador la repetía cada minuto contra todas tus tiendas (justo lo que hace que una tienda bloquee tu conexión). Ahora se anota con «la revisión falló: …» y espera a su hora.
- **Máximo de 6 páginas por tienda** en cualquier búsqueda: el valor de Ajustes no tenía tope y un número alto hacía decenas de peticiones seguidas a cada tienda.
- **«Mínimo histórico»** salía aunque el precio no hubiera cambiado nunca; ahora solo si es lo más barato visto y antes estuvo más caro.
- El recordatorio de que caducan los precios pegados a mano se daba por enviado aunque Telegram fallara; ahora se reintenta.
- Los enlaces de producto que no son direcciones web (`javascript:`…) se descartan.

## [0.11.4] - 2026-11-08

### Corregido
- **Cambios de tiendas que se perdían**: cada búsqueda guardaba al terminar la lista de tiendas tal como estaba al empezar, así que lo que activabas, desactivabas o editabas mientras buscaba (hasta un minuto) se deshacía. Ahora solo guarda lo que ha aprendido (el buscador de cada tienda), sobre la lista actual.
- **`config.json` y `tiendas.json` a medias**: se reescribían en el sitio, y quien los leyera a la vez (el bot, el programador, otra petición) podía encontrarlos vacíos y fallar; el bot de Telegram incluso dejaba de escuchar para siempre. Ahora se escriben en un temporal y se cambian de una vez, con cerrojo y reintentos.
- **Peticiones sin respuesta**: un fallo inesperado del servidor (p. ej. «Detectar envío» con una web que no responde) cortaba la conexión y el botón se quedaba bloqueado. Ahora se responde con el error y queda anotado en el log.
- **Pegar resultados** con «Buscar también en webs que no están en tu lista» repetía la búsqueda por internet entera (lenta) y duplicaba sus resultados; y usaba lo escrito en la caja de búsqueda aunque lo hubieras cambiado después de buscar.
- **«Buscar ahora»** decía «Revisión terminada» al instante si la vigilada se acababa de revisar sola, o a los 3 minutos aunque siguiera buscando. Ahora espera a la revisión de verdad y enseña su resultado.
- **«Guardar ajustes»** decía «Ajustes guardados» aunque el guardado fallara.
- **Búsqueda abierta**: «no encontré precios» ya no cuenta como tienda caída; y Bixoto y Ferretería Ibérica no se consultan nunca de forma automática, aunque las quites de tu lista.
- Un navegador que no responde se cuenta como tienda caída, con su mensaje (antes salía vacío).

### Añadido
- **Dirección HTTPS en Ajustes → Acceso desde el móvil**: si BuscaTron está publicado con `tailscale serve`, su dirección 🔒 sale la primera; es la única con la que Chrome instala BuscaTron como app.

### Cambiado
- La base de datos prepara sus tablas una vez por arranque, no en cada consulta.
- `buscatron.log` se archiva como `buscatron.log.1` al pasar de 2 MB.
- `.gitignore` cubre los temporales de SQLite y el log archivado, para que nunca se suban datos locales.

## [0.11.3] - 2026-11-08

### Cambiado
- **El objetivo 🎯 de un producto dice si avisará**: solo avisa si alguna búsqueda vigilada activa encuentra ese producto. Al ponerlo, BuscaTron dice qué vigilada lo cubre o, si ninguna, ofrece vigilar la búsqueda en ese momento. En Ajustes → Objetivos por producto, cada uno indica qué vigilada lo vigila o avisa con ⚠️ de que no avisará.
- **Botones de las vigiladas más claros**: «🔄 Buscar ahora», «✏️ Editar», «⏸️ Pausar» / «▶️ Reanudar» y «🗑 Borrar». Al reanudar se dice si se revisa al momento o cuándo; al pausar, que no se borra nada.
- **Mismas palabras en todas partes**: el estado de una vigilada, el resumen y el bot de Telegram dicen «X productos (Y ofertas)», como la página.
- **Nombres**: «En castellano (incluye los dudosos)» y «Solo castellano confirmado»; «Páginas a mirar en cada tienda»; «Tiendas que no tienes en tu lista».
- **Botones de icono con texto** para el móvil: «📈 Precio», «✕ Quitar» y «🗑 Quitar».

## [0.11.2] - 2026-11-08

### Corregido
- **«Tiendas sin respuesta» en las vigiladas**: contaba también las tiendas que sí respondieron pero no tenían ese producto, así que una revisión normal decía «20 tiendas sin respuesta» cuando solo había fallado una. Ahora solo cuentan las caídas de verdad (red, captcha, errores HTTP), en el estado de la vigilada y en el resumen de Telegram.
- **Avisos obsoletos**: por el mismo motivo, los avisos de una tienda que ya no tenía el producto no se retiraban nunca; ahora se retiran en cuanto la tienda responde sin él.
- **Mensajes largos de Telegram**: un aviso con muchos productos podía pasar del límite de 4096 caracteres y Telegram lo rechazaba entero. Ahora se parte en varios mensajes, entre producto y producto.
- **Bot de órdenes**: al cambiar el token por el de otro bot, seguía con la numeración de mensajes del anterior y podía ignorar los del nuevo.
- **Log**: ya no se llena de trazas cada vez que el móvil corta la conexión, y una consulta con datos mal formados responde con un error en vez de quedarse sin respuesta.

## [0.11.1] - 2026-11-07

### Eliminado
- **Cesta más barata** (🧺): sin los gastos de envío de las tiendas configurados, su cálculo siempre coincidía con comprar cada producto en su tienda más barata, así que no aportaba nada. La fila de debajo de cada producto queda con «🎯 Avisarme a…» y «🚫 No me interesa». 3 pruebas menos (149).

## [0.11.0] - 2026-11-07

### Añadido
- **🎯 Precio objetivo por producto**: «Avisarme a…» debajo de cada resultado. Las búsquedas vigiladas usan ese objetivo, en lugar del suyo, cuando encuentran el producto en cualquier tienda (por su grupo, su clave o la frase de «al menos una de estas»). Etiqueta «🎯 Tu objetivo» en los resultados y lista en Ajustes → «Objetivos por producto».
- **🧺 Cesta más barata**: añade varios productos y BuscaTron calcula en qué tiendas comprarlos para pagar menos en total, con el envío de cada tienda y su «gratis desde», y cuánto ahorras frente a ir a la más barata de cada uno. Avisa de las tiendas con envío desconocido. La cesta vive en el navegador y se actualiza sola con cada búsqueda.
- **📈 Gráfica por producto**: con «Agrupar», el historial muestra el mejor precio del producto en todas tus tiendas, hora a hora (nuevo, con stock, sin preventas ni segunda mano), y en qué tienda está ahora; «Ver solo …» vuelve a la de una tienda. El historial guarda ya la clave de producto, y los precios antiguos se completan solos al arrancar.
- **Órdenes por Telegram**: `/buscar <texto>` (o el texto sin más), `/vigiladas`, `/revisar` y `/ayuda`, con su menú en Telegram. Solo responde al chat configurado y hace una búsqueda a la vez.
- **Acceso desde fuera de casa con HTTPS** documentado con `tailscale serve` (solo dentro de tu red de Tailscale), que permite abrir la app del móvil a pantalla completa.
- 11 pruebas nuevas (152 en total).

### Cambiado
- La tarjeta de resultado lleva debajo una fila de acciones (🎯 objetivo, 🧺 cesta, 🚫 no me interesa); el 🚫 deja el lateral, donde queda solo el 📈.
- «Detectar chat» toma el chat del bot de órdenes cuando este está escuchando.
- Los cambios del arranque con Windows se rechazan también cuando llegan por un proxy local (`tailscale serve`), no solo desde otra IP.

## [0.10.0] - 2026-11-07

### Añadido
- **Agrupar el mismo producto de varias tiendas** (opción «Agrupar», activada por defecto): una tarjeta por producto con su mejor precio y las demás tiendas en un desplegable; el contador dice cuántos productos y ofertas hay. Clave de producto independiente de la tienda (sin editorial, tipo de producto, idioma, referencias…) o la frase de «al menos una de estas». En una prueba real, 65 ofertas de campañas quedaron en 11 productos.
- **Descuento sobre el precio de mercado** en cada producto: el precio (redondeado al euro) que más se repite entre al menos 3 tiendas, sin contar la segunda mano y antes de aplicar tu filtro de precio. Aparece en la web y en los avisos.
- **Avisos y resumen de Telegram agrupados por producto**: un bloque por producto con su mejor precio, el descuento, el motivo, el enlace y «También: 38,21 € en Juegos de la Mesa Redonda, …», en vez de una línea por oferta.
- **Recordatorio por Telegram** unas 12 horas antes de que caduquen los precios pegados a mano de una tienda (una vez por pegado), con el enlace a la tienda.
- **Instalable en el móvil**: manifiesto, iconos PNG y service worker (sin caché, para que los precios sean siempre en directo). «Añadir a pantalla de inicio» pone el icono de BuscaTron; la pantalla completa requiere HTTPS.
- **«Ya lo tengo / no me interesa» (🚫)**: oculta un producto para siempre, en todas las tiendas, en búsquedas y avisos; lista en Ajustes → «Productos ocultos» para recuperarlo.
- **Estado de las tiendas** en Ajustes: consultas con resultados de las últimas 10, último resultado, último problema y botón para desactivar; sugiere desactivar las que nunca dan nada (con al menos 6 consultas).
- **Limpieza diaria del historial**: los precios de hace más de 180 días se compactan a uno por producto y día (el más bajo), y se podan las fichas, idiomas, pegados viejos y el registro de tiendas (30 consultas por tienda).
- 11 pruebas nuevas (141 en total).

### Cambiado
- El servidor devuelve hasta 300 resultados por búsqueda y la página enseña los N primeros productos (u ofertas, sin agrupar).
- Una tienda con productos que no pasan tus filtros lo dice («tiene productos, pero ninguno pasa tus filtros») en vez de aparecer como si no tuviera nada.

### Notas
- La etiqueta `v0.10.0` apunta al commit del código; esta documentación va en el commit siguiente.

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
