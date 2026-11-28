# Changelog

Todos los cambios relevantes de BuscaTron se documentan aquí.
El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y el proyecto usa [versionado semántico](https://semver.org/lang/es/).

## [0.25.15] - 2026-11-28

### Cambiado (revisión max)
- Fuera la marca «no da resultados» de la v0.25.14 y la parada automática de la v0.25.10-0.25.13: duplicaban lo que Ajustes → Estado de las tiendas ya hace (una tienda con 6 consultas sin nada sale arriba con «conviene desactivarla» y su botón) y daban datos desfasados. BuscaTron no desactiva ninguna tienda por su cuenta.
- Una tienda que pide captcha ya no se consulta en cada revisión: espera cada vez más, como una tienda caída (10 min, 1 h, 6 h).

### Corregido
- Tarjetas fundidas: el historial 📈 incluye todas las variantes aunque se juntaran en cadena, y el 🎯 puesto en una variante vale igual para los avisos que para Mi lista.
- Al volver a una pestaña que estaba en Avisos, lo que ves cuenta como visto.
- «👁️ Vigilar» con doble pulsación ya no pide el precio para luego no hacer nada.

## [0.25.14] - 2026-11-28

### Cambiado
- BuscaTron ya no desactiva tiendas solo. Una tienda que no se puede leer (sin buscador o con captcha) 3 veces seguidas durante más de un día sale en Ajustes → Estado de las tiendas como «no da resultados», con el motivo y un botón «Desactivar»: lo decides tú. La marca se quita sola en cuanto vuelve a responder bien.

## [0.25.13] - 2026-11-28

### Corregido (revisión xhigh)
- La parada automática de tiendas sin buscador nunca saltaba (ese error no llega a darse). Ahora se para la tienda sin buscador aprendido que nunca ha dado ningún resultado, con 404 o nada en todas las direcciones probadas. Hace falta que pase 3 veces seguidas y a lo largo de más de un día: un 429, una web en mantenimiento o una tienda caída no la paran, y una respuesta normal reinicia la cuenta.
- Una tienda parada ya no se consulta en las búsquedas de una página abierta desde antes.
- En una tarjeta fundida: el historial 📈 incluye todas sus variantes, «Ocultar» las oculta todas y Mi lista encuentra el 🎯 de cualquiera de ellas. Las fusiones no se aprenden sin búsqueda, se vuelven a aprender si cambian las claves y ya no pueden fallar con dos hilos a la vez.
- Lo visto en Avisos solo cuenta si tienes la pestaña delante: una pestaña olvidada en el PC ya no marca como vistos los avisos del móvil.
- Las vigiladas dicen a qué precio avisan de verdad (su precio máximo si no tienen otro) y las que se ajustaron el 27/11 vuelven a seguir a su máximo.
- El aviso de rebajas ya no queda escondido dentro de Mi lista plegada.
- Un fallo al leer la lista de tiendas ya no se apunta como tienda caída. «👁️ Vigilar» dice si la sesión ha caducado y no crea dos vigiladas con una doble pulsación. Añadir de nuevo una tienda parada con su buscador la vuelve a activar.

## [0.25.12] - 2026-11-28

### Corregido (quinta revisión de código)
- La parada automática apagaba una tienda que funciona y solo no tenía el juego; ahora solo cuenta «no encuentro su buscador» de verdad y el captcha también con ventana. Una página abierta de antes ya no reactiva una tienda parada.
- Tiendas bloqueadas: si el archivo de tiendas no se puede leer en ese instante, ya no se da por hecho que no hay ninguna bloqueada, y un bloqueo justo después de otro guardado ya no se pasa por alto.
- Las fusiones de nombres se recuerdan: el mismo juego va siempre al mismo grupo, venga solo o con su variante, así que su objetivo 🎯 y su historial siguen aplicándose. «Ant-Man» ya no cuenta como relleno.
- El precio máximo como aviso se calcula al avisar, no se guarda: si subes el máximo, el aviso sube con él.
- Lo visto en Avisos se lee sin reescribir los ajustes, solo se guarda si cambia, y nunca pasa del último aviso (con una base restaurada vuelven a salir los nuevos).
- «👁️ Vigilar» avisa si la sesión ha caducado en vez de no hacer nada.

## [0.25.11] - 2026-11-27

### Corregido
- El mismo juego salía en dos tarjetas cuando una tienda le añade una coletilla al nombre («La Tiranía de Cráneo Rojo | Cinco escenarios»). Ahora se junta con el otro grupo de la misma búsqueda si su nombre lo contiene y lo que sobra es solo relleno conocido («cinco escenarios», «color», el nombre de una tienda). Nunca se junta un accesorio con su juego, ni otro producto («Black Panther Shuri», «Héroes Reunidos 2»), ni el nombre a secas de la búsqueda («Marvel Champions» no se traga sus expansiones). Vale para búsquedas, avisos y Mi lista.

## [0.25.10] - 2026-11-27

### Corregido (auditoría con datos reales)
- Una tienda sin buscador o que pide captcha se consultaba en cada revisión, también con Chrome, sin dar nunca nada, y saturaba la cola de Chrome de las demás («demasiadas páginas pendientes»). Ahora, tras 3 búsquedas seguidas así, se para sola y sale en Ajustes con el motivo; se reactiva con su chip.
- Gameria se busca por su búsqueda normal (la suya se carga aparte y se leía vacía). Desactivadas 7 tiendas que nunca dieron resultados: Tradeinn, AliExpress, Hemolúdica, Hangar Rebelde, Khan Barrilete, Joker Comics y Arcadia Comics (captcha).

## [0.25.9] - 2026-11-27

### Corregido
- Una vigilada con precio máximo y sin «Avisarme si cuesta como mucho» nunca avisaba aunque encontrara precios por debajo. Ahora, si dejas el aviso vacío, avisa al precio máximo. Las vigiladas que ya estaban así se han ajustado.

## [0.25.8] - 2026-11-25

### Corregido
- Avisos: lo que ya has visto se guarda en BuscaTron, no en cada navegador. Lo visto en el PC ya no sale como «nuevo» en el móvil, ni al revés.

## [0.25.7] - 2026-11-25

### Cambiado
- «📋 Mi lista» aparece plegada al entrar en Vigiladas.

## [0.25.6] - 2026-11-24

### Cambiado
- Por Telegram vuelven a llegar solo los cambios de límites y objetivos: el aviso de rebajas a la vista se ve solo en la página y las tiendas que dejan de funcionar, en Ajustes → Estado de las tiendas.

## [0.25.5] - 2026-11-24

### Corregido
- La v0.25.4 dejaba la página sin funcionar (un error en «👁️ Vigilar»).

## [0.25.4] - 2026-11-24

### Corregido (cuarta revisión de código)
- Reactivar una tienda bloqueada con el formato antiguo la dejaba en consulta automática: ahora, si no se sabe cómo estaba, sigue «solo enlace». Cambiar «solo enlace» mientras está bloqueada se recuerda; no se puede cambiar su dirección estando bloqueada.
- La limpieza del historial conservaba un precio agotado y borraba el de ese día con stock.
- «👁️ Vigilar» ya no crea una vigilada repetida y la lista se actualiza.
- «Precio raro» no cuenta precios que su ficha dice agotados.
- El envío visto por dos búsquedas a la vez ya no se pierde; la comprobación de bloqueadas no relee el archivo en cada petición.

## [0.25.3] - 2026-11-24

### Corregido (tercera revisión de código de v0.21-v0.25)
- Tiendas bloqueadas: la regla de «ninguna petición» está ahora en el único punto por el que pasan todas (`ritmo.py`), también para «Detectar envío», las búsquedas ya en marcha y las tiendas añadidas de nuevo. Se elimina el sondeo. Al reactivarla vuelve a como la tenías.
- «Gastos de envío gratis desde 39 €» se leía como un coste de 39 €; cada dato del envío se conserva y se aplica por separado.
- Mi lista y Avisos: el objetivo 🎯 es el mismo que usa el motor; respeta la ficha (agotado, idioma), no se vacía si falla una revisión y se actualiza al acabar una. La compra conjunta dice qué juegos no cuenta.
- Fundas y lotes no se agrupan con su juego en las búsquedas por campañas; «Scenario Pack 2» o «10 juegos reunidos» no son lotes.
- «Precio raro» no mezcla segunda mano; «vuelve a estar disponible» cuenta el envío; «precio más bajo» exige que el precio haya variado.
- Saltar tiendas sin el juego funciona con Chrome desactivado y la comprobación semanal se mantiene; el aviso de salud ignora a las que responden bien.
- Compartir: pide elegir tienda si no se reconoce y exige el mismo acceso que la página. Las copias solo se guardan si están enteras.
- Las pruebas no tocan los archivos reales.

## [0.25.2] - 2026-11-24

### Corregido (segunda revisión de código de v0.21-v0.25)
- Una página abierta desde antes de un bloqueo ya no reactiva la tienda bloqueada al tocar otra: solo se reactiva con su propio chip.
- «Vuelve a estar disponible» no saltaba: los agotados del listado no se apuntaban. El stock se sigue por vigilada.
- Juegos distintos que compartían identificador («Arkham Horror» de rol y de cartas, «Time's Up! Family» y «Party»); ningún título queda sin identificador. Al recalcular, si dos objetivos coinciden queda el más reciente.
- «Mostrar: Juegos» avisa si ha escondido todos los resultados; «Pack 2 jugadores» o «Set de 100 juegos» no son lotes.
- Mi lista: lo pegado pasa los filtros de idioma, segunda mano y «ocultar»; la mejor oferta es con stock y según «con envío». La compra conjunta no propone agotados y respeta el «gratis desde» conocido.
- Lo pegado de una tienda bloqueada cuenta también en las vigiladas con tiendas excluidas.
- Si falla la copia de seguridad, la limpieza diaria sigue.

## [0.25.1] - 2026-11-24

### Corregido (revisión de código de v0.21-v0.25)
- Compra conjunta: un juego que está en dos vigiladas ya no la deja sin planes.
- «Salud semanal» no podía avisar de las tiendas más consultadas: la limpieza borraba su historial; ahora se conservan 40 días.
- Lo que pegas de una tienda bloqueada cuenta en búsquedas y avisos (sigue sin recibir ninguna petición).
- Al bajar el objetivo, los avisos «con envío» se comparan por el precio final. «Precio raro» funciona también con lo pegado.
- 🎯 en Avisos muestra el objetivo que ya tenía (antes salía vacío y aceptar lo borraba).
- Los vínculos de Amazon puestos a mano se recalculan con las claves nuevas, y los tapetes no sirven de referencia de un juego. El recálculo va por tandas y con índice.
- El nombre de una tarjeta no se queda en el de la serie si lo de tras «:» es el nombre de la expansión. Compartir desde el móvil ya no se pierde si la última tienda usada dejó de ser «solo enlace».

## [0.25.0] - 2026-11-24

### Cambiado (interfaz en el móvil)
- **Resultados:** nuevo desplegable «Mostrar» (Juegos / Todo / Accesorios y lotes), por defecto solo juegos, expansiones y complementos: las fundas de 2,50 € tapaban los juegos al buscar «marvel champions». Se recuerda en el navegador.
- **Tarjetas de resultado:** botones cortos que caben en el móvil («🎯 Objetivo · 👁️ Vigilar · 🚫 Ocultar»).
- **Buscar:** las dos cajas de texto de debajo del formulario son ahora dos botones en una fila («🏪 93 de 98 tiendas» y «📋 Pegar resultados»).
- **Mi lista:** casilla, nombre y precio en la primera línea; tiendas, mínimo, momento y objetivo debajo a todo el ancho; 📈 y 🎯 junto al precio. Se lee sin tantos saltos de línea.

### Corregido
- Los tapetes («Game Mat», «Tapetes») y los separadores («dividers») cuentan como accesorios.

## [0.24.0] - 2026-11-23

### Añadido
- **Mejor compra conjunta** (Mi lista): marca varios juegos y «🧺 Mejor compra de los marcados» te dice dónde comprarlos para pagar menos en total, contando el envío de cada tienda y su «gratis desde» sobre lo que compras en ella (cada juego donde sale más barato, todo en una tienda o repartido entre dos). Si de una tienda no se sabe el envío, se estima (4,95 €, gratis desde 50 €) y lo dice.
- **Rebajas a la vista:** unos días antes de Black Friday, las rebajas de enero, el Prime Day… un aviso por Telegram (una vez por campaña) y una nota en Mi lista.
- **Revisión de salud semanal:** si una tienda que solía darte resultados lleva una semana sin dar ninguno, te avisa por Telegram. Solo mira lo ya guardado: ninguna petición.

## [0.23.0] - 2026-11-23

### Añadido
- **Precio raro:** un aviso que está un 40 % o más por debajo de tus demás tiendas lo dice («⚠️ … puede ser un chollo o un error, compruébalo»).
- **¿Buen momento?** En Mi lista, cada juego dice si está en el precio más bajo que se le ha visto, por debajo de lo habitual, en lo habitual o más caro.
- **Copia de seguridad diaria** de la base de datos en la carpeta «copias» (las 7 últimas).
- **Panel de tiendas** (Ajustes): las bloqueadas («🔒 sin peticiones»), en qué vigiladas se las saltan las revisiones y su envío (tuyo o según su web).
- **👁️ Vigilar** en cada resultado: crea la vigilada de ese juego con un objetivo sugerido (un 10 % por debajo del más barato), en castellano y con envío.
- **Lotes y packs de varios productos** («Pack 3 expansiones», «Lote …», «Bundle») como tipo propio: nunca se agrupan con el juego suelto.

## [0.22.0] - 2026-11-23

### Añadido
- **Precio final con envío:** BuscaTron apunta el envío que anuncia cada tienda en su página de resultados («envío gratis a partir de 49 €»), sin peticiones extra; lo que pongas tú en Ajustes manda. Las vigiladas con «con envío incluido» (activado en las tuyas) avisan por precio + envío, y Avisos muestra el envío de cada oferta.
- **Mi lista** (arriba de Vigiladas): una línea por juego con su mejor oferta, en cuántas tiendas está, el mínimo visto y cuánto falta para tu objetivo; 📈 historial del juego en todas tus tiendas y 🎯 objetivo propio. En Avisos, 📈 y 🎯 también por juego.
- **Tiendas que no quieres en una vigilada:** no se consultan en sus revisiones ni avisan (siguen en lo demás).
- **Aviso cuando vuelve el stock** de algo que estaba agotado (cerca de tu objetivo). Los agotados se apuntan en el historial para saberlo.
- **Compartir desde el móvil:** con la app instalada, selecciona el texto de la tienda y «Compartir» → BuscaTron abre «Pegar resultados» con el texto y la tienda ya puestos.

### Cambiado
- Las revisiones se saltan las tiendas que no han tenido ese juego en sus 4 últimas consultas (y vuelven a mirar una vez por semana): menos tiempo y menos peticiones. Tus búsquedas las consultan todas.
- Kipmion y Tablerum (no responden nunca), y las tiendas bloqueadas, pasan a «solo enlace»: ninguna petición.

## [0.21.2] - 2026-11-22

### Corregido
- Más productos iguales que salían separados, encontrados revisando todo el historial de la última semana: nombres de tienda o editorial dentro del título («Eternal Decks - Gigamesh», «… Salt and Pepper Games», «ugi games toys …», «Oferta Online …», «SPA») y el mismo nombre en inglés o castellano («Wasp»/«Avispa», «Storm»/«Tormenta», «Quicksilver»/«Mercurio», «Mat»/«Tapete»). Lo que sigue separado son productos distintos (fundas frente al juego, otro héroe). Se recalcula lo guardado al arrancar.

## [0.21.1] - 2026-11-21

### Corregido
- El mismo juego salía como dos productos si una tienda añadía una descripción al título («Eternal Decks: juego de cartas cooperativo y estratégico» frente a «Eternal Decks»): las palabras que describen un juego en general (cooperativo, estratégico, familiar, de tablero, para adultos, jugadores…) ya no cuentan para saber qué producto es. Vale para todos los juegos, en avisos, búsquedas e historial.
- El nombre de la tarjeta prefiere el nombre del juego a la descripción de una tienda («Eternal Decks» y no «Eternal Decks: juego de cartas cooperativo y estratégico.»); faltar tildes solo resta si otra tienda escribe ese mismo nombre con ellas.
- Al cambiar la forma de identificar productos, BuscaTron recalcula solo al arrancar las claves guardadas (historial, «No me interesa» y objetivos 🎯), para que nada pierda su historial ni deje de aplicarse.

## [0.21.0] - 2026-11-21

### Cambiado
- Una sola regla para decidir los avisos: las revisiones y lo pegado a mano usan la misma función (`_registra_avisos`), y si una oferta cuenta (agotados, preventas, idioma) lo decide `_vale`, también para los avisos de límites de Amazon. Antes eran cuatro copias que había que mantener iguales a mano. Sin cambios de comportamiento; una prueba comprueba que revisión y pegado deciden igual.

## [0.20.9] - 2026-11-21

### Corregido (revisión exhaustiva v0.18.1..v0.20.8)
- Un aviso que no se pudo enviar ya no reaparece como «Nuevo» en cada revisión: si lo ocultaste se respeta, y con Telegram sin configurar no queda pendiente.
- Lo pegado durante una revisión se procesa luego solo en esa vigilada y solo si la tienda sigue siendo «solo enlace» (nunca una consulta en directo); un fallo ahí no tapa el resultado de la revisión. Pegar ya no marca las vigiladas como «Revisándose…».
- Órdenes desde otras webs: solo se aceptan los nombres de este equipo, su tailnet, la red local y las IP de Tailscale (no cualquier *.ts.net ni el truco de DNS rebinding).
- La «ficha de un solo resultado» solo se usa si la página es de verdad una ficha (no una categoría con un precio en los metadatos).
- Al pegar, la marca suelta solo se une a la línea siguiente si detrás viene su precio (no el buscador ni los filtros).
- Los avisos de tiendas «solo enlace» no se borran cuando caduca lo pegado (repegar no vuelve a avisar).
- Una cola larga de Chrome ya no marca la tienda como caída; un rechazo en una ficha tampoco.
- «solo_pegados» se aplica también en segundo plano; «Quitar todos» va en una sola petición; el botón de pegar de una tienda que ya se consulta sola avisa en vez de cambiarla por otra; el enlace de las tiendas con plantilla «{q-}».

## [0.20.8] - 2026-11-21

### Corregido (revisión de código de la página)
- Al quitar un aviso ya no reaparece el anterior, más caro, del mismo producto: cada aviso nuevo oculta los previos de esa tienda (siguen contando para no repetir).
- Un aviso por enlace dentro de cada vigilada (dos vigiladas con el mismo enlace ya no se pisan).
- «Nombre de la A a la Z» ordena por el nombre que se ve en la tarjeta.
- «y N ofertas más en M tiendas» cuenta solo las demás tiendas.
- Títulos: fuera «PEGI 14+», «10+ años», «a partir de 8 años», «2-4 jugadores»; un subtítulo con «:» ya no se mueve.
- Una carga vieja de Avisos ya no pinta encima de una nueva; «Quitar» quita todas a la vez, no admite doble toque y avisa si falla.

## [0.20.7] - 2026-11-21

### Corregido (revisiones de código)
- Ficha de un solo resultado: título sin entidades HTML, solo el producto de la ficha si hay varios, dirección canónica bien leída y solo http(s), preventa/agotado también por el nombre.
- Avisos: un aviso por enlace en toda la lista; fecha y «Nuevo» de su propia oferta; «N ofertas más (M tiendas)»; cada oferta con su motivo, 📈 y ✕; desplegables abiertos al repintar; títulos sin cortar y con la serie seguida de «:»; revisión fallida marcada.
- El mismo producto de la misma tienda con otra dirección no vuelve a avisar; al bajar el objetivo los avisos caros se ocultan y no se repiten.
- Figuras de colección detectadas aunque el título lleve puntuación.

## [0.20.6] - 2026-11-20

### Corregido
- La barra de carga podía acumular sondeos repetidos al servidor si se pedía dos veces a la vez (al volver a la pestaña durante una búsqueda): ahora solo sigue la última.
- La marca de «la tienda rechazó una página siguiente» es de cada consulta (antes global): ni se queda puesta tras un rechazo ni se mezcla entre búsquedas simultáneas (móvil y revisión automática).

## [0.20.5] - 2026-11-20

### Corregido
- Las figuras de colección (Marvel Legends, Funko, «figura 15 cm») ya no cuentan como juegos: una figura «Civil Warrior» salía como si fuera Civil War a 24,65 €.
- Al bajar el objetivo de una vigilada se quitan los avisos «por debajo de tu objetivo» que ya no lo están (con el objetivo en 38 €, los de 38,21 € y 38,65 € seguían).

## [0.20.4] - 2026-11-20

### Cambiado
- Cada tarjeta de Avisos lleva el nombre propio del juego («Marvel Champions: La Próxima Evolución») en vez del título de la tienda más barata con su ruido («ASMODEE JUEGO DE MESA … PEGI 14»): se limpian los títulos de todas sus tiendas (marca, «juego de mesa», PEGI, «Expansión en español», LCG, mayúsculas sueltas) y se elige el mejor (sin mayúsculas sostenidas, con tildes, el más corto). El título de cada tienda sigue en «N tiendas más» y al pasar el ratón.

## [0.20.3] - 2026-11-20

### Cambiado
- Avisos agrupados por producto: las variantes de nombre del mismo juego en distintas tiendas (Civil War, La Próxima Evolución, Los Más Buscados de la Galaxia…) van en una sola tarjeta, con la oferta más barata delante y las demás en «N tiendas más, hasta X €». Se agrupa igual que en la búsqueda (por los títulos de «alguna» de la vigilada o, si no, por el nombre del producto). De cada enlace solo cuenta su aviso más reciente. «Quitar avisos» quita los de ese producto. El banner y el número de la pestaña cuentan productos con novedades.

## [0.20.2] - 2026-11-20

### Añadido
- Avisos nuevos bien a la vista: un banner «🆕 N avisos nuevos» y las tarjetas nuevas arriba del todo y resaltadas, hasta que recargues la página (se mantienen al cambiar de pestaña).
- La pestaña Avisos se actualiza sola al acabar una búsqueda o revisión, con lo nuevo ya resaltado.
- Fecha de la última búsqueda: arriba de Avisos, la de cada vigilada activa, y en cada aviso, «Aviso del … · última búsqueda …».

### Corregido
- Títulos con el nombre repetido y la marca entre medias (Aquí Mejor: «ASMODEE … EVOLUCIÓN ASMODEE ASMODEE … EVOLUCIÓN»): ahora sale una vez; arreglados también los ya guardados.
- El aviso de «Borrar todos» decía que volverían a avisar; desde la 0.20.0 no lo hacen salvo que bajen más.

## [0.20.1] - 2026-11-19

### Corregido
- En tiendas WooCommerce el enlace del producto podía ser el de su foto (.jpg) y no el de su ficha: los enlaces a archivos ya no cuentan como producto.
- Cuando la búsqueda da un solo resultado, muchas tiendas saltan directamente a su ficha: BuscaTron no la reconocía y tomaba el enlace de la foto y un precio de otra parte de la página (MarketPvp marcaba Eternal Decks a 19,75 € cuando cuesta 35,95 €, y llegó a avisar). Ahora lee esa ficha: su nombre, su precio, su stock y su dirección de verdad.
- Se han borrado el aviso falso y los 45 precios guardados con enlaces a fotos.

## [0.20.0] - 2026-11-19

Revisión completa de la aplicación (búsqueda y tiendas, vigiladas y avisos, página y servidor) en tres pasadas.

### Corregido
- **Tiendas que te rechazan:** un 401/403 ya no hace probar otras direcciones de búsqueda ni repetir enseguida con Chrome; los rechazos en páginas siguientes y en fichas cuentan para que la tienda espere (antes parecía sana y se le volvía a preguntar igual).
- **Bixoto y Ferretería Ibermadrid** son siempre «solo enlace», aunque se desmarque la casilla. Las fichas y el idioma tampoco se consultan en tiendas caídas o bloqueadas.
- **Chrome:** una página que caducó esperando su turno ya no se abre después, fuera del ritmo de la tienda.
- **Abrir la app** ya no puede consultar una tienda: al refrescar lo pegado solo se piden tiendas que ahora son «solo enlace» (también lo comprueba el servidor).
- **«Vaciar avisos»** los oculta en vez de borrarlos: la siguiente revisión ya no vuelve a mandar todo por Telegram.
- **Si un aviso no llega** por ningún canal (Telegram caído), queda pendiente y se reintenta en la siguiente revisión, en vez de darse por avisado 30 días.
- **Una tienda bloqueada o desactivada** ya no pierde sus avisos (y no se repiten cuando vuelve).
- **Las revisiones van de una en una** (programador, «Buscar ahora» y /revisar de Telegram): nunca varias a la vez contra todas las tiendas. La barra dice «Esperando a que acabe otra revisión».
- Lo pegado mientras se revisaba esa vigilada pasa por sus avisos al terminar la revisión.
- Los avisos de límites de Amazon no cuentan agotados, preventas (si no las quieres) ni otros idiomas.
- Lo pegado lleva su tipo de producto, como lo leído en directo.
- Se guardan hasta 1000 resultados por búsqueda (antes 300, y los productos con muchas tiendas perdían ofertas) y la pestaña Avisos carga hasta 500.
- **Accesos:** otra web abierta en el navegador ya no puede mandar órdenes a BuscaTron; quien entra por tailscale serve no cuenta como «este equipo» (si pones PIN, se le pide).
- La barra muestra la fase «Comprobando el stock en las fichas».

## [0.19.10] - 2026-11-19

### Corregido
- El porcentaje de la barra de carga solo contaba tiendas: llegaba al 100 % con «quedan 0 s» a mitad, porque las tiendas lentas acaban las últimas y después aún queda trabajo (otras webs, idioma de las fichas, comprobación antes de avisar). Ahora manda el tiempo que suele tardar (la revisión anterior de esa vigilada, o la última búsqueda a escala de sus tiendas); las tiendas hechas son el 80 % de la barra como mucho, nunca marca 100 % antes de acabar y, si tarda más de lo normal, dice «terminando…» en vez de inventarse lo que queda. Se ven también las fases nuevas.

## [0.19.9] - 2026-11-19

### Añadido
- Barra de carga para las búsquedas y las revisiones de vigiladas (también las automáticas): tiendas consultadas de cuántas, porcentaje, fase («Consultando tiendas», «Comprobando las fichas antes de avisar»…), cuánto lleva y cuánto le queda. La lleva el servidor, así que sigue ahí en todas las pestañas, al recargar y en el móvil. Sin nada en marcha mira cada 4 s, para que las revisiones automáticas y las búsquedas lanzadas desde otro dispositivo salgan enseguida.

## [0.19.8] - 2026-11-19

### Corregido
- La comprobación del idioma en la ficha del producto fallaba en silencio desde la 0.19.6 (se borró por error una línea al proteger las tiendas «solo enlace»): en «solo castellano confirmado», Amazon y otras tiendas que traducen títulos no se podían confirmar. Además, nunca consulta una tienda «solo enlace».
- Al abrir una búsqueda guardada solo se traen los pegados de las tiendas de esa búsqueda, no de todas.
- Lo pegado y una revisión de la misma vigilada ya no pueden ir a la vez (avisos repetidos): se reservan como hace una revisión.
- Al pegar la dirección de una búsqueda para una tienda se elige el parámetro más claro (search, q…) y con letras, no un orden o una página.
- Las direcciones de lo pegado antes de la 0.19.7 se han pasado al formato nuevo, para que repegar no vuelva a avisar de lo mismo.

### Cambiado
- Dynos: su enlace usa el buscador Doofinder de la tienda.

## [0.19.7] - 2026-11-19

### Añadido
- Tienda Aquí Mejor (aquimejor.com).
- Al añadir o editar una tienda puedes pegar la dirección de una búsqueda hecha en su web («…/?q=Marvel+Champions»): el texto buscado pasa a ser el hueco de la búsqueda. Antes había que escribir {q} a mano o la tienda se quedaba sin buscador.

### Corregido
- El mismo producto pegado desde dos búsquedas distintas tenía dos direcciones: salía dos veces, podía avisar dos veces y partía su historial. Ahora su dirección es la búsqueda del producto en la tienda, sea cual sea la búsqueda en la que lo pegaste, y repegarlo sustituye lo anterior.
- Lo pegado pasa los mismos filtros que lo leído en directo (los que descartan lo que no es un juego).
- Pegar mientras se revisa una vigilada ya no puede dar avisos repetidos: esa vigilada lo recoge en su revisión.
- «Más barato que su precio habitual» ya no cuenta el propio precio pegado como precio anterior.
- Solo se pueden pegar resultados de tiendas «No consultar automáticamente» (pegar en una tienda normal la habría consultado en directo una vez por vigilada).
- Las claves de producto guardadas se recalculan con las reglas de la 0.19.3: las gráficas de esos productos no pierden historial.
- La lista en pantalla no se puede reagrupar mal si pegas mientras se reagrupa otra cosa.
- Fuera la mención «resumen por Telegram en cada revisión»: ese resumen se quitó en la 0.17.36 y la opción ya no hacía nada.

## [0.19.6] - 2026-11-19

### Corregido
- Lo pegado se apuntaba otra vez en el historial de precios cada vez que salía en una búsqueda (y, desde la 0.19.4, cada vez que se abría la app): ahora se apunta una sola vez, al pegarlo. Se han limpiado las filas repetidas de Dynos, Bixoto y Ferretería Ibermadrid (634 → 140).
- La ficha de un producto de una tienda «solo enlace» nunca se consulta, tampoco si pegaste su código HTML con enlaces reales.

## [0.19.5] - 2026-11-19

### Añadido
- Lo que pegas pasa al momento por tus vigiladas activas y crea sus avisos (y su mensaje de Telegram), sin esperar a la próxima revisión. No consulta ninguna tienda ni lee fichas; el aviso dice que es un precio pegado a mano.

## [0.19.4] - 2026-11-19

### Cambiado
- Lo que pegas entra al momento en la lista que tienes en pantalla, aunque la búsqueda sea otra o una guardada, y se reagrupa con las demás tiendas sin repetir la búsqueda; al abrir una búsqueda guardada también se traen los pegados de ahora y se reagrupa todo.
- Avisos se ordena por defecto por precio, de menor a mayor.

## [0.19.3] - 2026-11-19

### Corregido
- La misma expansión no se agrupaba si una tienda añadía coletillas de ficha al título («Juego De Mesa … 60 Cartas Pegi 14», «Edad Recomendada 14 Años»): ahora no cuentan para saber qué producto es.
- Se mostraban solo los 10 más baratos de toda la búsqueda y las expansiones grandes quedaban fuera aunque fueran las más baratas de su producto: ahora se muestran 30 por defecto, el número se recuerda en el navegador y una búsqueda guardada ya no lo devuelve a 10.

## [0.19.2] - 2026-11-19

### Corregido
- Una tienda «solo enlace» sin dirección de búsqueda (Dynos) se seguía consultando (y daba 403) y no salía lo que pegabas de ella: ahora no se consulta, su enlace es la portada y lo pegado aparece en las búsquedas y las vigiladas.

## [0.19.1] - 2026-11-19

### Corregido
- «Pegar resultados» no encontraba nada en tiendas que ponen la marca en su propia línea (Ferretería Ibermadrid: «15%», «VANTAGE», nombre, precio) si buscabas la marca: ahora la marca se une al nombre que la sigue.

## [0.19.0] - 2026-11-19

### Cambiado
- «📋 Pegar resultados» ya no necesita una búsqueda antes: hay un botón fijo bajo el formulario de búsqueda y otro en cada tienda «No consultar automáticamente» de Ajustes. La hoja deja elegir la tienda (recuerda la última) y qué buscas, y el enlace a la tienda se actualiza con esa búsqueda.

## [0.18.3] - 2026-11-19

### Añadido
- Arriba de los resultados, un atajo «Ir ↓» a las tiendas que tienes que mirar tú (con «📋 Pegar resultados»): la tarjeta va al final y con muchos resultados no se veía.

## [0.18.2] - 2026-11-19

### Añadido
- Las vigiladas que se están revisando dicen desde hace cuánto y cuánto tardó la revisión anterior (o, si no se sabe, que suele tardar de 10 a 15 min), y recuerdan que los avisos se crean al terminar. En «Más detalles», cuánto tardó la última revisión.

## [0.18.1] - 2026-11-18

### Cambiado
- **Telegram solo para tus juegos:** ya no avisa de que una tienda te bloqueó o vuelve a responder, ni de que caducan los precios pegados a mano. Solo llegan los cambios de límites de Amazon y los objetivos. Esos estados se siguen viendo en Ajustes → Estado de las tiendas y en «Tiendas que tienes que mirar tú».
- **Generalistas añadidas:** El Corte Inglés, Fnac, PcComponentes, Toys "R" Us, Juguettos, GAME y Casa del Libro (96 tiendas). Junto con Carrefour, Aliexpress y Kaufland cuentan como generalistas: en una búsqueda de una sola palabra solo admiten títulos de juego.
## [0.18.0] - 2026-11-18

### Cambiado: lavado de cara completo
- **Identidad propia de juegos de mesa:** papel cálido con trama de puntos, cabecera en tinta, ficha naranja como color de acción y títulos en Bricolage Grotesque. Logo nuevo (un meeple con lupa) en la web, el icono del móvil y el de la bandeja de Windows. Modo oscuro a juego.
- **Buscar más directo:** buscador grande con lupa, opciones rápidas en una fila y, en vez de las 70 fichas de tiendas, una línea «Buscando en X de Y tiendas · Gestionar tiendas». En el móvil, al buscar, la pantalla baja sola a los resultados.
- **Tiendas en Ajustes:** «🏪 Tus tiendas» reúne las fichas (con su propio desplazamiento), añadir una tienda y editar o quitar tiendas.
- **Resultados más legibles:** precio grande a la derecha, tienda destacada en verde azulado, el más barato con franja verde, y tarjetas más compactas en el móvil.
- **Navegación:** abajo en el móvil, con la pestaña activa resaltada; en el PC, pestañas arriba fijas bajo la cabecera, con el buscador fijo a la izquierda al bajar por los resultados.
- Hojas (historial, referencia, pegar resultados) que suben desde abajo en el móvil, desplegables con flecha propia, campos con foco visible, selectores con flecha a juego, y animaciones que respetan «reducir movimiento».
## [0.17.45] - 2026-11-18

### Cambiado
- Kaufland con su dirección de búsqueda (la pasaste tú): ya no pasa por la portada, que era donde pedía captcha. Probado: 4 productos de Marvel Champions.
- Fuera de los títulos los textos de botones e imágenes que algunas tiendas meten delante del nombre («Añadir el producto a la lista de favoritos», «Imagen del producto de…») y el nombre repetido.

## [0.17.44] - 2026-11-18

### Corregido
- Si una tienda pide captcha y la ventana de Chrome ya se abrió sin que se resolviera a tiempo, el aviso lo dice así, en vez de pedir que actives una opción que ya estaba activada (Kaufland).

## [0.17.43] - 2026-11-18

### Corregido
- Si una página pesada cuelga la pestaña de Chrome («Page crashed», como Kaufland), se abre otra: antes, todas las tiendas siguientes fallaban con la pestaña muerta. Probado con la búsqueda real: Comic Stores ya da 25 resultados.

## [0.17.42] - 2026-11-18

### Corregido
- **Chrome se cortaba con muchas tiendas** (Kaufland, Comic Stores, Buy Meeples…: «el navegador no respondió a tiempo», «no se pudo abrir el navegador», «Target page… closed»). BuscaTron tiene un solo Chrome que atiende las páginas de una en una:
  - el tiempo límite cuenta desde que Chrome empieza con cada página, no desde que entra en la cola;
  - al pasar a Chrome visible (una tienda que pide comprobar que eres humano) se espera a que el invisible acabe lo que tiene en cola, en vez de cortarlo a los 10 s, y el nuevo reintenta abrir el perfil si aún está ocupado;
  - una tienda cuya página se lee bien pero no tiene el producto no se repite con Chrome en cada búsqueda (3 días), lo que acorta mucho la cola.
- Direcciones de búsqueda que pasaste a mano: Comic Stores, Generación X, Akira Comics, Arcadia Comics, Dados y cubitos, Buy Meeples, En Portada Comics, Shuriken64 y Juegos de mesa y rol (estas tres ya probadas: encuentran el juego con su precio). Kinuma, Padis, Elkar y Ludoteca Maldita buscan con JavaScript sin cambiar la dirección: solo enlace.
- Kaufland cuenta como tienda generalista (vende de todo).
## [0.17.41] - 2026-11-17

### Cambiado
- El tiempo de espera de una búsqueda depende de cuántas tiendas tienes activas (medido con 70: de 2 a 4 minutos), y «Buscar ahora» de una vigilada dice «unos minutos» en vez de «hasta 1 min».
- Revisión de las 42 tiendas nuevas con una búsqueda real: 21 funcionan, 6 buscan bien pero no tenían el juego, y Cuarto de Juegos, Doctor Panush, Mi Juego Bonito y Arigatô Sevilla rechazan a los programas (429 o 500): pasan a «solo enlace».

## [0.17.40] - 2026-11-17

### Cambiado
- Tiendas: «＋ Añadir una tienda» y «✎ Editar o quitar tiendas» son dos apartados separados. Para añadir ya no hay que pasar por la lista de las 70; para editar, un buscador filtra la lista por nombre o web.

## [0.17.39] - 2026-11-17

### Cambiado
- Las tiendas salen ordenadas por nombre (sin distinguir mayúsculas ni tildes) en las fichas de Buscar, en «Tus tiendas» y en el estado de las tiendas.

## [0.17.38] - 2026-11-17

### Añadido
- **Tipo de producto** de cada resultado, deducido del título: juego base, expansión (también los packs de héroe, villano, escenario o campaña), complemento (add-on, personaje, promo) o accesorio (fundas, tapetes, organizadores). Lo que no dice qué es cuenta como juego base: nunca se descarta un juego por no llamarse «juego».
- En cada vigilada, **«Qué tipo de producto vigilar»**: por defecto todos; desmarcando, por ejemplo, complementos y accesorios, deja de avisar de add-ons y fundas. Se aplica también a lo ya guardado.
- 21 tiendas más de Ludonauta (70 en total).

### Cambiado
- Lo que seguro que no es un juego de mesa (zapatillas, ropa, correas y protectores de pantalla de reloj, rociadores, herramientas…) se descarta en todas las tiendas, no solo en las generalistas. Con tus datos: 109 resultados de basura fuera y ningún juego.
## [0.17.37] - 2026-11-17

### Añadido
- **21 tiendas de juegos de mesa** del directorio de Ludonauta (EGD Games, Play Planet, Quinto Elemento, Espacio de Juegos, Rampi Games, Empire Games, Kinuma, Kame Kame, Tira y Mueve, Ludoteca Maldita, Ludosaurus, Santuario Games, Alcalá Comics, Arcadia Comics, Ocio Central, La Cueva Roja, Shuriken64, Dados y cubitos, Comic Stores, Generación X y EcoMimos), con una sola petición a cada una para sacar su buscador. SomosJuegos corta la conexión a los programas y no se añade. Las vigiladas buscan en todas las tiendas activas, así que ya las usan.

### Cambiado
- Una web cuyo certificado no valida Python (le falta el certificado intermedio, que Chrome sí resuelve) se lee con el Chrome de BuscaTron en vez de darse por caída. Cualquier otro fallo de conexión sigue siendo «no responde»: un rechazo no se esquiva con el navegador.
## [0.17.36] - 2026-11-16

### Cambiado
- **Telegram solo avisa si hay cambios, nunca como resumen**: se quita el resumen que se mandaba tras cada revisión (la opción «mandarme un resumen» desaparece del formulario y se ignora en las vigiladas que la tenían). Si no cambia nada, no se manda nada.
- **Aviso de cambio de límites** (Telegram o correo, según los canales de la vigilada): cuando Amazon baja de su **mínimo histórico** o sube de su **máximo histórico** (camelcamelcamel) en una ficha con histórico leído. Se compara Amazon con Amazon, la misma ficha: las demás tiendas casi siempre son más baratas que Amazon y eso no es un cambio. No se repite un límite ya avisado, salvo que el precio vaya más lejos; si el aviso no llega, se reintenta en la siguiente revisión. Tabla limites_avisados.
- Se mantienen los avisos de objetivo («cuesta X o menos», «% por debajo de su precio habitual») y los avisos operativos poco frecuentes (una tienda te bloquea o vuelve, y los precios pegados que caducan).
## [0.17.35] - 2026-11-15

### Corregido
- **Un máximo imposible se guardó como bueno**: el de Motivos Siniestros (68,72 €) con una escala que llega a €60. El lector leyó «€58,72» como «68,72» (el «€5» se lee «6»), y el margen de un escalón por arriba de la comprobación de escala lo dejó pasar. Ahora, si hay dos lecturas posibles de una cifra, gana la que cabe **dentro** de la escala sin margen (la escala de camelcamelcamel abarca siempre todos los datos); el margen solo vale cuando no hay otra lectura (la etiqueta de más arriba del eje a veces no se lee). Auditadas las nueve lecturas guardadas con texto: solo cambia esa, a 58,72 €, y está corregida en tus datos.
## [0.17.34] - 2026-11-15

### Corregido
- **Falta la gráfica de «Agentes de S.H.I.E.L.D.»**: sí se había capturado bien, pero el lector desordenó las líneas de la leyenda (el mínimo salía detrás de «Current») y BuscaTron le asignaba ese valor al precio actual. Ahora el precio actual es la entrada de la leyenda con la **fecha más reciente** (solo si el valor que dice la etiqueta es de una entrada más antigua), y el mínimo es la que sobra. También se entiende la fecha partida por el lector («Nov 1 5, 2026»).
- Comprobado con la captura real: mínimo 42,22 € (04/03/2025), máximo 44,99 € (28/04/2026), actual 44,99 €.
- Las imágenes de Eternal Decks y del Too Many Bones base dicen «We can't find the requested product»: no están en camelcamelcamel y no hay histórico que leer.
## [0.17.33] - 2026-11-15

### Corregido
- **Los mínimos y máximos de Cráneo Rojo y de «No temeré ningún mal» no salían aunque la gráfica se capturaba bien**: el lector de texto confunde el «€» con la cifra que le sigue (`€48,64` sale `«8,64`, `€33,73` sale `03,73`, `€52,06` sale `62,06`) y a veces pierde la coma (`€4222` por `€42,22`), y además tomaba la fecha `Nov 15.2026` por el número 15.202 («precio actual de 15.202 €»). BuscaTron rechazaba esas lecturas por absurdas, con razón. Ahora repara cada cifra con las lecturas que corresponden a esos tres errores conocidos y se queda con la que cabe en la escala de la gráfica y cuadra con las otras dos (el máximo no baja del mínimo ni del actual…); si ninguna cuadra, **no inventa nada** y la rechaza. Las fechas con punto se leen bien y las etiquetas laterales cortadas («(4») ya no estropean la escala.
- Comprobado con las dos capturas reales de tu navegador (imágenes que BuscaTron conservó en capturas_fallidas/): Cráneo Rojo, mínimo 33,73 € (27/03/2023), máximo 48,64 € (04/11/2024), actual 44,99 €; No temeré ningún mal, mínimo 42,22 € (09/09/2026), máximo 44,99 € (03/09/2026), actual 42,22 €.
## [0.17.32] - 2026-11-15

### Corregido
- **«Leer las gráficas que faltan» daba 0 de 8 en un navegador real** («la captura no llegó a mostrar la pantalla de lectura»): ninguna imagen llegaba al servidor, el fallo ocurría entero en el navegador al buscar la marca magenta en la captura. Ahora la captura es más robusta: el vídeo de la captura va dentro de la página (uno suelto puede dejar de recibir fotogramas), el fotograma se pide a la propia pista de vídeo (ImageCapture) y, si la marca no se ve, **no se rinde**: manda el último fotograma entero y BuscaTron comprueba si trae de verdad una gráfica (si no, no se guarda nada). Probado con un navegador y tres casos: marca visible con retraso y escala 1,25 (7 de 7), marca invisible pero gráfica visible (7 de 7) y pestaña que no muestra nada (0 de 7, sin guardar nada).
- Lo que no se puede guardar deja su imagen en capturas_fallidas/ (solo en tu equipo, ignorada por git, las últimas 12; se borra al guardarse bien) para poder ver qué recibió BuscaTron. El informe dice el motivo concreto («la imagen no parece una gráfica de camelcamelcamel…») en vez de uno genérico.
- Las pruebas escribían la carpeta capturas_fallidas en la carpeta real: ahora usan una temporal.
## [0.17.31] - 2026-11-15

### Corregido
- **Se guardaron históricos falsos**: con una captura vieja, BuscaTron leyó el texto de su propia página (que ya enseñaba los históricos de otros productos) y lo guardó como si fuera la gráfica de tres productos (los tres «Too Many Bones: … Add-on Character» quedaron con los mismos mínimo, máximo y actual inventados). Borradas esas tres lecturas, y ahora **solo se guarda si la imagen es de verdad una gráfica de camelcamelcamel** (su escala vertical y su leyenda); si no, se dice y no se guarda nada. Si camel responde «We can't find the requested product», se dice que ese producto no está en camel.
- **Captura de las gráficas con marca**: la pantalla de lectura lleva una marca magenta junto a la gráfica. BuscaTron espera a verla en la captura (el navegador a veces entrega fotogramas viejos o vacíos), la usa para saber dónde está la gráfica aunque la captura traiga las barras del navegador y recorta solo la gráfica. Si la marca no aparece nunca (cambiaste de pestaña…), lo dice en el informe. Probado con un fotograma con retraso, escala 1,25 y barras: 7 de 7.
- **Los filtros se aplican siempre a lo guardado**: la Referencia (de avisos y de vigiladas), el resumen de histórico por vigilada y los avisos pasan por los filtros que tiene la vigilada AHORA (búsqueda, «Solo títulos con», «Descarta», «al menos una de estas», precio mínimo y máximo), no por los de la última revisión. Antes, al editar y guardar, lo viejo seguía saliendo hasta la siguiente revisión. Al guardar una vigilada se borran sus avisos que ya no cumplen. El 🎯 usa la misma regla.
- **La Referencia respeta la pestaña de Vigiladas** desde la que se abre (todas, activas o en pausa); antes solo miraba las activas.
- **Emparejamiento con Amazon**: una ficha con palabras de otro tipo de artículo (add-on, character, fundas, tapete, organizador…) que el producto no tiene ya no se da por su equivalente («Too Many Bones: Gasket Add-on Character» no es «Too Many Bones Edición Definitiva»).
- **Menos basura de tiendas generalistas**: en una búsqueda de una sola palabra («Vantage»), los resultados de Amazon, Outlet-PC, eBay, Vinted, Milanuncios y Wallapop solo valen si su título parece el de un juego. Fuera zapatillas, rociadores, guantes… sin tener que ir añadiendo palabras a «Descarta».
- Mejor lectura de la leyenda: sin la etiqueta «Lowest» o con el precio actual ilegible, se completa con las etiquetas de colores de la gráfica.
## [0.17.30] - 2026-11-15

### Añadido
- **Resumen del histórico de Amazon en Vigiladas**: cada búsqueda vigilada, activa o en pausa (vistas «Todas», «Activas» y «En pausa»), enseña una línea con el mínimo más bajo y el máximo más alto históricos de Amazon de los productos que encontró en su última revisión, con el producto y la fecha; y en «Más detalles», el mínimo, el máximo y el precio de hoy de cada producto. Solo sale si algún producto tiene ya su histórico leído de camelcamelcamel. Se refresca al terminar «Leer las gráficas que faltan». Nuevo /api/historico_vigiladas.
- **Al añadir un enlace de Amazon en la Referencia, se elige de qué producto es**: un desplegable con los productos de tus listas. Si eliges uno, el enlace se une a ese producto (vínculo) en vez de crear un bloque aparte; «Producto aparte» sigue siendo para los que no están en ninguna lista.

### Corregido
- Los enlaces de La Tiranía del Cráneo Rojo y Agentes de S.H.I.E.L.D. se habían añadido como bloques aparte aunque ya existían como productos de la vigilada «Campañas y Héroes Reunidos 2»: ahora están vinculados a ellos (igual que Motivos Siniestros) y los duplicados se han quitado.
## [0.17.29] - 2026-11-15

### Corregido
- **«No se pudo mostrar el resumen (can't access property "replace", h is null)»** al abrir la Referencia de Amazon: pasaba en una pestaña abierta con la página de la versión anterior mientras el servidor ya mandaba productos «añadidos por enlace», que no tienen tienda; la página antigua intenta ponerle nombre a la tienda y se rompe. Ahora esos productos llevan la tienda vacía, no nula, y una página antigua los pinta bien. Reproducido con la página de la 0.17.27 contra el servidor.
- El mensaje de error de la Referencia ya no manda solo a reiniciar BuscaTron: dice que recargues la página con Ctrl+F5 (puede que la pestaña sea de una versión anterior) y, si sigue igual, que reinicies.
## [0.17.28] - 2026-11-15

### Añadido
- **Añadir a la Referencia de Amazon un producto por su enlace, tenga o no stock**: campo «Pega aquí el enlace de un juego de Amazon» arriba de la Referencia. El producto sale con su bloque (marcado «Añadido por ti») aunque ninguna de tus tiendas lo venda ahora, con la gráfica de camelcamelcamel y su histórico, y «Leer las gráficas que faltan» lo lee como los demás. El nombre sale del propio enlace; se puede quitar. Tabla 
ef_extra.
- La pantalla de «Leer las gráficas» es más tranquila: fondo gris con barra de avance.

### Corregido
- El recuadro del histórico de camel no salía en los productos sin precios de BuscaTron (los vinculados a mano y los añadidos por enlace). Los vinculados a mano que BuscaTron aún no había visto tampoco traían su histórico.
## [0.17.27] - 2026-11-15

### Corregido
- **«Leer las gráficas que faltan» rechazaba las cinco (0 de 5)**: la leyenda de la captura sale con la letra deformada («€44,99» se leía «4,99», «€52,06» se leía «62,06», «€31,48» se leía «01,48») y el control de escala hacía bien en rechazarlo. Ahora, si una cifra de la leyenda queda fuera de la escala de la gráfica, se sustituye por la de las etiquetas de colores de la derecha que se le parezca y sí quepa en ella (se leen mucho mejor), y el informe dice qué cifra se corrigió. También entiende la coma perdida («€5Z95» = 52,95) y la fecha «Nov 15.2026».
- Cuando falta una etiqueta (a veces el lector no ve «Lowest»), las entradas de la leyenda («€32,89 (Mar 20, 2024)») se reparten solo entre lo que no se reconoció ya por su etiqueta, en el orden de la leyenda; antes el mínimo se llevaba la cifra del máximo.
- Comprobado con las lecturas reales de cinco capturas (guardadas en camel_lecturas): las cinco dan mínimo, máximo, actual y fechas coherentes con las etiquetas de la gráfica.
## [0.17.26] - 2026-11-15

### Corregido
- **«Leer las gráficas que faltan» no guardaba ninguna (0 de 5)**: lo que anotó BuscaTron de lo leído lo mostró. La captura que da el navegador trae sus barras (dirección, pestañas, marcadores) y la gráfica queda desplazada hacia abajo; el recorte por coordenadas le cortaba el pie, que es donde están el mínimo y el máximo. Ahora se manda el fotograma entero, sin recortar, y el lector busca las etiquetas (Lowest, Highest, Current) donde estén; el texto de las barras sobra pero no molesta. Reproducido con una captura del mismo formato (barras arriba y gráfica debajo): 14 de 14 guardadas.
- El lector amplía la imagen según su tamaño total (hasta 3 veces, sin pasar de 9.000 px) y las etiquetas del eje que se leen «(45» o «C45» también cuentan para comprobar la escala.
## [0.17.25] - 2026-11-15

### Añadido
- **Informe de «Leer las gráficas que faltan»**: al terminar queda en pantalla cuántas se han guardado y, de las que no, cuál es el producto y el motivo («el mínimo leído (3,09 €) queda fuera de la escala de la gráfica…», «no he encontrado el mínimo y el máximo…»). Antes se recargaba la lista y se perdía el resumen.
- **Reintento**: si la primera lectura de una gráfica no cuadra se repite con más espera (la captura llega comprimida y al principio el texto sale borroso).
- BuscaTron anota lo último que leyó de cada gráfica (el texto, no la imagen; tabla `camel_lecturas`) para poder ver por qué una no se guardó.
- Mientras captura, el aviso a pantalla completa pide no cambiar de pestaña ni tocar nada: si la pestaña deja de verse, la captura sale vieja.

## [0.17.24] - 2026-11-15

### Corregido
- **«Leer las gráficas» fallaba con «TypeError: 'getSettings' called on an object that does not implement interface MediaStreamTrack»**: al comprobar que se compartía la pestaña, `getSettings` se llamaba separado de su pista de vídeo y el navegador lo rechazaba. Es el fallo de verdad de la 0.17.21 a la 0.17.23. Ahora se llama sobre su pista. Reproducido en Chrome («Illegal invocation») y comprobado con una pestaña simulada que usa el `getSettings` real del navegador, no uno escrito a mano; también se ha comprobado el aviso al compartir la pantalla entera o una ventana.

## [0.17.23] - 2026-11-15

### Corregido
- **«Leer las gráficas que faltan» no hacía nada en Chrome**: volvían a pedirse las condiciones de captura de pestaña con las que sí se puede dar el permiso (las añadidas en la 0.17.21 podían hacer que el navegador las rechazara sin que se viera). Lo de compartir solo la pestaña se comprueba después, como antes.
- Cualquier fallo de la captura se enseña con su nombre técnico, el botón no se puede pulsar dos veces seguidas y mientras espera tu permiso sale un aviso con indicador, no una línea gris.
- Comprobado de punta a punta (navegador en segundo plano, copia de la base de datos, pestaña simulada y la gráfica real de ejemplo): las 14 gráficas se leen y se guardan en unos 40 s y salen en sus bloques. Lo que no se puede simular es el permiso real de tu navegador.

## [0.17.22] - 2026-11-15

### Añadido
- **🖼️ Leer las gráficas que faltan**, arriba en la Referencia de Amazon: con **un solo permiso** (compartir esta pestaña) recorre sola todas las fichas de Amazon que aún no tienen su histórico, pone cada gráfica un momento a tamaño grande, la lee y sigue con la siguiente (con 1,5 s entre una y otra). Muestra el avance («Leyendo 3 de 12») y al terminar recarga la lista.
- **El histórico leído se guarda por producto** (tabla `camel_extremos`, por ASIN) y sale en su bloque de la referencia: mínimo histórico con su fecha, máximo, media, precio de hoy frente al mínimo y si el mínimo coincidió con una campaña que vuelve. Solo hace falta leer cada gráfica una vez, y repetirlo con los productos nuevos. Solo se guarda una lectura que cuadra con la escala de la gráfica; las dudosas no.
- «Leer la gráfica» y «Pegar gráfica» de un producto también lo guardan.

## [0.17.21] - 2026-11-15

### Corregido
- **«Leer la gráfica» capturaba la ventana o la pantalla entera** (el texto leído traía la barra de marcadores, la dirección y otras páginas) y la gráfica quedaba desplazada y cortada, sin su leyenda. Ahora pide compartir la pestaña, y si lo compartido no es una pestaña no lo usa: lo dice y explica qué elegir («Pestaña de Chrome», no «Ventana» ni «Pantalla completa»). Así tampoco se lee nada de tu pantalla que no sea la gráfica.
- El lector de texto amplía menos las imágenes que ya son grandes (más rápido y sin pasarse del límite de Windows).

## [0.17.20] - 2026-11-15

### Corregido
- **«Leer la gráfica» no leía nada**: la imagen cargada en la página es una miniatura (600 px o menos) y con esa letra el lector de Windows no lee la leyenda, o lee «03,09» donde pone «€33,09». Con una gráfica real de camelcamelcamel (Fantasy Flight MC16ES) se ha comprobado que a 1.000 px o más lee bien el mínimo, el máximo, el precio actual y sus fechas. Ahora la página pide la gráfica a 1.200×600, la pone un momento a tamaño grande y captura esa copia, no la miniatura.
- **Una lectura dudosa ya no se enseña como cierta**: BuscaTron compara el mínimo, el máximo y el precio actual leídos con la escala de la propia gráfica (sus etiquetas €30, €35…, con un escalón de margen) y con el orden entre ellos; si no cuadran, lo dice y no da cifras. Avisa también cuando la imagen es pequeña.
- Variable sin declarar en la captura de pestaña.

## [0.17.19] - 2026-11-15

### Corregido
- «Leer la gráfica»: el resultado se pintaba debajo de los botones y, al capturar la gráfica, la página se desplazaba y lo dejaba fuera de pantalla, así que parecía que no había pasado nada. Ahora el resultado sale encima de la gráfica, enmarcado, la página se lleva la vista hasta él y sale un aviso con la primera línea (o con el error).

## [0.17.18] - 2026-11-15

### Añadido
- **🖼️ Leer la gráfica** en cada referencia de Amazon: trata la gráfica de camelcamelcamel que ya tienes cargada en la página, sin copiar ni pegar. Primero intenta leerla tal cual (si camel permite que una página lea sus imágenes); si no, captura esa zona de tu propia pestaña (el navegador te pide permiso una vez) y la manda a leer. Si el navegador no puede, lo dice y queda «Pegar gráfica». El servidor no pide nada a camelcamelcamel. Solo se puede probar en un navegador real: la captura de pestaña no existe en el móvil ni en direcciones sin HTTPS.

## [0.17.17] - 2026-11-15

### Eliminado
- El análisis del precio con los datos propios de BuscaTron (v0.17.15: gráfica diaria, bajadas, estimación y fiabilidad): no se había pedido y con 10 días de historial no servía. La Referencia de Amazon queda como antes; el histórico largo se lee con «Pegar gráfica de camel» (v0.17.16).

## [0.17.16] - 2026-11-15

### Añadido
- **📋 Pegar gráfica de camel** en cada referencia de Amazon: copias la gráfica de camelcamelcamel que ves en tu navegador (clic derecho → «Copiar imagen») y la pegas con Ctrl+V; BuscaTron lee el texto de su leyenda con el lector de Windows (es-ES), saca el **mínimo histórico y cuándo fue**, el máximo, la media y el precio actual, y dice cuánto se aleja el precio de hoy del mínimo y si el mínimo coincidió con una campaña (Black Friday, rebajas, Prime Day) que este año vuelve, con su fecha. La imagen se guarda un instante en una carpeta temporal y se borra. No se pide nada a camelcamelcamel (rechaza a los programas). Siempre enseña el texto leído. Módulos nuevos `ocr.py` y `historico.py`.
- Lo que no puede decir con solo los extremos: cada cuánto se repite una bajada; lo dice expresamente.

## [0.17.15] - 2026-11-15

### Añadido
- **Análisis del precio en la referencia de Amazon** (📊): para cada ficha de Amazon, con lo que BuscaTron ha visto de ella, enseña mínimo y máximo con sus fechas, media y mediana, en qué punto del recorrido está hoy, las bajadas de al menos un 4 % que ha tenido, una gráfica diaria, y una **estimación de cuándo puede repetirse una bajada o el mínimo** (por los días que suelen pasar entre ellas). Dice su **fiabilidad** (insuficiente, baja, media o alta): hacen falta al menos 3 bajadas y 14 días de datos para estimar, y no da fecha si no los hay. Añade como pista general la próxima fecha de ofertas (Black Friday, Cyber Monday, rebajas, Prime Day). Módulo nuevo `analisis.py`.

### Cambiado
- La vigilada «Vantage» descarta «stonemaier»: la ficha de Amazon es la edición inglesa y Amazon no dice su idioma, solo la editorial la delata.

## [0.17.14] - 2026-11-15

### Corregido
- El texto de Ajustes decía que la clave de Brave Search era gratuita: es de pago (unos 5 $ por 1.000 consultas; cada búsqueda por internet gasta 2).

## [0.17.13] - 2026-11-15

### Añadido
- **Búsqueda por internet con tu clave de Brave Search** (Ajustes → «🔎 Búsqueda por internet»). Con clave, la búsqueda abierta pregunta a la API oficial de Brave (2 consultas por búsqueda, con el filtro de relevancia) en vez de a Bing, que a un programa le devuelve resultados sin relación. Sin clave, o si la clave falla o se queda sin límite, usa Bing como antes y lo dice en el informe de la búsqueda. La clave se guarda enmascarada, como el token de Telegram.

## [0.17.12] - 2026-11-15

### Corregido
- **Búsqueda abierta**: se queda solo con los resultados del buscador cuyo título habla de lo que buscas. Bing devolvía para «Mage Knight Edición Definitiva» páginas sin relación (webs de IA, Idealista, coches) y BuscaTron perdía el tiempo leyéndolas. Con Chrome de verdad el resultado es el mismo, así que el problema es el buscador, no cómo se le pide.

## [0.17.11] - 2026-11-15

### Corregido
- **Títulos de tarjeta entera**: cuando el enlace de una tienda envuelve toda la tarjeta (Outlet-PC), el título era todo su texto: las direcciones de las imágenes, «Producto nuevo», los precios y al final el nombre. Ahora es solo el nombre del producto (el trozo entre precios que contiene la búsqueda), y se han corregido los títulos ya guardados así.

## [0.17.10] - 2026-11-14

### Corregido
- **Lector de precios**: ya no toma por precio un número seguido de una palabra que empieza por «eur» («Expansión 2 Europa» se leía 2 €; «5 Eurogames», 5 €), lo que ahorras («Ahorra 5 €», «10 € de descuento»), el mínimo del envío gratis («Envío gratis desde 50 €») ni un «€» ya leído con el número de detrás («29,95 € 2 jugadores» daba también 2 €, y al pegar resultados se quedaba ese 2 por ser el menor). Lo pegado a mano usa el mismo lector.
- La página decía que una búsqueda tarda «entre 10 y 40 segundos»: con el ritmo por tienda suele tardar 1 o 2 minutos. El bot de Telegram, igual.
- La página dejaba de esperar el final de una revisión a los 5 minutos (ahora 20), así que con el ritmo por tienda a veces no salía el aviso «Revisión terminada».
- «Próxima revisión: ahora mismo (en menos de un minuto)» ya no era cierto: las automáticas van de una en una, cada 10 min.

## [0.17.9] - 2026-11-14

### Corregido
- Una ficha que no se podía leer borraba el idioma ya verificado de ese producto (fallo de la 0.17.8): ahora se conserva y solo se descarta su stock antiguo.
- Una tienda bloqueada se consultaba igualmente si la página llevaba abierta desde antes del bloqueo (seguía en su lista de tiendas activas).
- «Detectar envío» solo consulta tiendas de tu lista.

### Cambiado
- Reactivar a mano una tienda bloqueada le da también la vuelta suave (3 días con una página por búsqueda).
- `/revisar` en Telegram dice qué vigiladas no repitió porque ya se estaban revisando, y no empieza si BuscaTron se está reiniciando.
- La limpieza diaria borra los avisos quitados hace más de 60 días (ya no sirven para evitar repetirlos).
- Las peticiones a la web de BuscaTron tienen un tope de 20 MB.

## [0.17.8] - 2026-11-14

### Añadido
- **Una tienda que te rechaza deja de recibir consultas**: un 429 («demasiadas consultas»), o dos 403 seguidos, la ponen en espera como si no respondiera (10 min, 1 h, 6 h…). Si sigue rechazándote tras tres esperas, se desactiva sola, te avisa por Telegram y desde ahí solo se prueba su portada cada 6 h hasta que vuelva.
- El formulario de una vigilada rechaza un precio mínimo mayor que el máximo.

### Cambiado
- Una ficha que no se pudo leer no se vuelve a pedir en 2 h (antes, en cada búsqueda).
- Antes de avisar se leen como mucho 4 fichas por tienda, las más baratas.
- Las revisiones automáticas van en su propio hilo: los recordatorios y la prueba de tiendas bloqueadas no esperan a que acaben. Una vigilada que ya estás revisando con «Buscar ahora» se salta sin gastar el turno de 10 min.
- Si editas una vigilada mientras se revisa, se repite como mucho una vez (antes, hasta dos).

### Corregido
- El reintento con ventana para resolver un captcha respetaba mal la vuelta suave (pedía todas las páginas).
- El resumen y el estado de una vigilada contaban la búsqueda abierta como una tienda sin respuesta.

## [0.17.7] - 2026-11-14

### Añadido
- **Ritmo máximo por tienda**: entre dos peticiones a la misma web pasan al menos 15 s, sean de una búsqueda, de sus páginas siguientes, de fichas o de la prueba de una tienda bloqueada. Las tiendas se siguen consultando a la vez (cada una a su ritmo), así que una búsqueda tarda más solo en las que piden varias páginas o fichas. Es para no parecer un programa: Dungeon Marvels bloqueó la IP de casa por una ráfaga y Ferretería Ibermadrid (detrás de Cloudflare) la rechaza desde el 14/11.
- **Vigiladas escalonadas**: las revisiones automáticas van de una en una, con al menos 10 min entre ellas, empezando por la que más espera. «Buscar ahora» no espera.
- **Vuelta suave**: una tienda que te bloqueó y vuelve a responder pasa 3 días con una sola página por búsqueda.

### Cambiado
- Zacatrus: se leen las fichas de sus 3 resultados más baratos (antes 4), cada una a su turno.

## [0.17.6] - 2026-11-14

### Corregido
- **Precios rebajados como «15,75 € - 20% = 12,6 €»** (Más que Oca): se tomaba el precio de antes de la rebaja. Ahora vale el final, y también se lee un precio con el número y el «€» en trozos distintos («<b>12,6</b> €»).
- **Agotados que salían como disponibles en Zacatrus**: su listado no dice si queda stock. Al buscar se lee la ficha de sus 4 resultados más baratos (de una en una, con pausa, y se recuerda 6 h) y lo agotado se oculta. En todas las tiendas, lo que ya se leyó en una ficha manda sobre lo que dice el listado.

## [0.17.5] - 2026-11-14

### Cambiado
- **Resumen de Telegram**: en vez de los 5 productos más baratos de la vigilada (siempre los mismos), trae cada producto que cumple la búsqueda, del más barato al más caro, con sus 3 ofertas más baratas (hasta 30 productos; si no cabe en un mensaje, se parte). Activado en todas las vigiladas activas que avisan por Telegram.

## [0.17.4] - 2026-11-09

### Corregido
- Editar una vigilada en pausa y guardarla desde el formulario la reactivaba sola. Ahora conserva su estado: solo ⏸️ Pausar / ▶️ Reanudar lo cambian.

## [0.17.3] - 2026-11-09

### Añadido
- **Tiendas que te han bloqueado**: se desactivan y BuscaTron solo prueba su portada (una petición) cada 6 h; en cuanto vuelve a responder, la reactiva y te avisa por Telegram. En Ajustes → Estado de las tiendas sale arriba con «te ha bloqueado», desde cuándo y la última prueba. Si la reactivas tú, deja de vigilarse. Dungeon Marvels queda así desde el 9/11 (bloqueo de la IP de casa tras una ráfaga de pruebas).

### Cambiado
- Vigiladas de Marvel Champions juntas: «Campañas y Héroes Reunidos 2» (una búsqueda con «al menos una de estas») cubre los 11 juegos; las 10 vigiladas sueltas que lo duplicaban quedan en pausa (sin borrar nada) y su tope sube a 50 € para cubrir Motivos Siniestros. De 15 búsquedas por ciclo a 5.

## [0.17.2] - 2026-11-09

### Cambiado
- **Una tienda que no conecta se deja en paz cada vez más tiempo**: 10 min, luego 1 h, 6 h y como mucho 24 h si sigue sin conectar, y se recuerda aunque BuscaTron se reinicie (antes, 10 min siempre y se olvidaba al reiniciar: unos 6 intentos por hora contra una web que te ha cortado, lo que puede alargar el bloqueo). Se olvida en cuanto vuelve a responder. Motivo: Dungeon Marvels bloqueó la conexión de casa el 9/11 tras una ráfaga de pruebas.

### Corregido
- Una prueba de tiendas caídas escribía en la base de datos de verdad; ahora usa una temporal y ninguna prueba sale a internet.

## [0.17.1] - 2026-11-09

### Corregido
- **«Referencia de Amazon» se quedaba en «Preparando el resumen…»** con un BuscaTron aún sin reiniciar: la página nueva esperaba datos que el servidor viejo no manda (sugerencias, vínculo) y fallaba al dibujar. Ahora funciona con los dos (lo nuevo pide reiniciar con 🆕) y, si algo falla, lo dice en vez de quedarse cargando.
- Al cambiar rápido entre «De tus avisos» y «De lo que encuentran tus vigiladas», una respuesta que llegaba tarde podía pintar la otra lista; ahora solo cuenta la última que pediste.

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
