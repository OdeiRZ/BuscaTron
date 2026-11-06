# 🔎 BuscaTron

Buscador y vigilante de precios **local** para tiendas online españolas. Pensado para juegos de mesa, válido para cualquier producto: consulta las tiendas en vivo desde tu propio PC, ordena los resultados por precio y te avisa cuando algo baja.

- **Sin APIs de pago, sin cuentas y sin depender de ninguna IA.** Funciona con la biblioteca estándar de Python.
- **Datos en vivo**: no usa cachés ni comparadores intermedios, así que el precio es el que ves en la tienda.
- **Tus datos se quedan en tu equipo**: lista de tiendas, historial y tokens se guardan en archivos locales que no se suben al repositorio.

> Estado: **versión funcional** (v0.6.0). Consulta el [CHANGELOG](CHANGELOG.md).

## Inicio rápido

Requiere Python 3.9 o superior (probado con 3.10). No hay nada que instalar para lo básico.

```
python -m buscatron --abrir              # interfaz web en http://127.0.0.1:8790
python -m buscatron --bandeja            # igual, con icono junto al reloj y sin ventana de mensajes (Windows)
python -m buscatron "marvel champions"   # búsqueda por línea de comandos
python -m buscatron --arranque on        # arrancar con Windows (off para quitarlo, estado para consultarlo)
```

En Windows también puedes hacer doble clic en `BuscaTron.bat`: abre el navegador, deja el icono en la bandeja y, si algo falla, vuelve a mostrar la ventana con el error.

Opciones: `--puerto N` (por defecto 8790) y `--host 127.0.0.1` para que solo sea accesible desde este equipo. Por defecto escucha en la red local, para poder usarlo desde el móvil (ver [Usar desde el móvil](#usar-desde-el-móvil)).

## Qué puedes hacer

La web está pensada para móvil (probada a 360 px) y escritorio. Arranca con el tema claro u oscuro de tu sistema y tiene un botón (🌙 / ☀️) en la cabecera para alternarlo; recuerda tu elección.

### 🔎 Buscar
- Busca un producto en todas las tiendas activas y ve los **N más baratos**, con precio, tienda, enlace y etiquetas (preventa, segunda mano y su estado, mínimo histórico…).
- Filtros: palabras que debe contener o excluir, precio mínimo y máximo, y **páginas leídas por tienda** (1 a 6).
- **Ocultar agotados** (activado por defecto). Reconoce «agotado», «sin stock», «en reposición» y «reserva», y descarta los productos que la tienda no puede enviar ya.
- **Solo castellano** (activado por defecto): descarta los productos que indican otro idioma (inglés, francés, alemán…) salvo que mencionen también el castellano. Desmárcalo para ver todos los idiomas.
- En **«Más fuentes y opciones»** (se recuerdan entre búsquedas):
  - **Incluir preventas**: por defecto se ocultan, porque no se pueden recibir todavía. Se distinguen de los agotados («Lanzamiento aproximado: 26/3/2027», «Preventa»).
  - **Sumar el envío al precio**: ordena por el precio total (ver [Gastos de envío](#gastos-de-envío)).
  - **Incluir segunda mano** (ver [Segunda mano](#segunda-mano)).
  - **Buscar también en otras webs** (ver [Búsqueda abierta](#búsqueda-abierta)), con región España, Unión Europea o cualquier país.
- **Historial** (📈 en cada resultado): gráfica del precio de ese artículo con mínimo, media, máximo y precio actual. La etiqueta «Mínimo histórico» salta cuando está al precio más bajo que se le ha visto, con al menos tres datos previos.
- Tiendas: actívalas o desactívalas con un toque, añade otras con el dominio (`ejemplo.es`) y, en «Gestionar tiendas», **edita su nombre, su dirección o URL de búsqueda, el envío y el modo «solo enlace»** cuando quieras. Si el buscador de una web no se detecta, pega una URL de búsqueda con `{q}` donde va el producto: `https://ejemplo.es/buscar?q={q}`. Cambiar la dirección a otro dominio hace que se vuelva a descubrir su buscador.
- **Solo enlace**: marca así las tiendas que bloquean el acceso automático (por ejemplo Amazon). No se consultan, pero cada búsqueda te ofrece su enlace ya preparado para abrirlo tú.

### 👁️ Seguimiento
Guarda una búsqueda y deja que BuscaTron la revise sola cada X horas mientras esté abierto (con el [arranque con Windows](#arranque-con-windows-y-bandeja), siempre).
- **Aviso por precio objetivo** («menos de 39 €»), por **bajada respecto a la media histórica** del artículo («un 15 % menos de lo habitual»), o por ambos.
- Cada seguimiento lleva las mismas opciones que la búsqueda: preventas, envío, segunda mano, otras webs y páginas por tienda.
- No repite avisos: solo vuelve a avisar si el precio baja más, o pasados 30 días.
- Revisar ahora, pausar, editar y borrar (al borrar un seguimiento se borran también sus avisos; el historial de precios se conserva).

### 🔔 Avisos
Lista de todo lo que ha saltado, con el motivo, la tienda, el enlace y el historial (📈). Un contador rojo en la pestaña indica los nuevos.

Cada revisión **retira los avisos que ya no cumplen tu búsqueda** (porque se agotó, es una preventa, está en otro idioma o salió de tu rango de precio), siempre que la tienda haya respondido: si una web falla, no se borra nada. Si un producto vuelve a estar disponible a un precio que cumple, avisa de nuevo. Con «Vaciar avisos» puedes limpiar la lista a mano.

### ⚙️ Ajustes
- **Búsqueda**: páginas que se leen por tienda por defecto.
- **Arranque con Windows**: interruptor para iniciar BuscaTron al encender el equipo.
- **Telegram** y **correo (SMTP)** para recibir los avisos, con botón de prueba.
- **Acceso desde el móvil** y PIN opcional.
- **Navegador**: usar tu Chrome para tiendas que cargan con JavaScript.

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
4. Las webs nuevas aparecen en «Webs nuevas encontradas» con un botón para **añadirlas a tu lista** y consultarlas siempre.

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

## Usar desde el móvil

BuscaTron escucha en tu red local, así que puedes abrirlo desde el móvil conectado a la **misma Wi-Fi**:

1. **Una sola vez**, haz doble clic en `permitir_acceso_movil.bat`. Pide permisos de administrador y abre el puerto 8790 del cortafuegos de Windows **solo para tu red local** (regla «BuscaTron (red local)»).
2. Arranca BuscaTron con `BuscaTron.bat` o con el arranque con Windows. Las direcciones, por ejemplo `http://192.168.0.28:8790`, aparecen en la ventana y en Ajustes → «Acceso desde el móvil».
3. Escribe la dirección de tu red local (suele empezar por 192.168) en el navegador del móvil. Puedes guardarla en favoritos o añadirla a la pantalla de inicio.
4. **Recomendado:** pon un **PIN** en Ajustes → «Acceso desde el móvil». El móvil lo pedirá una vez y lo recordará 30 días. Este equipo no lo necesita.

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
2. **Descarga los resultados** y se queda con los enlaces cuyo texto contiene todas las palabras de la búsqueda, junto al primer precio vigente (dentro de la tarjeta del producto o justo después). Ignora los precios tachados y el texto oculto de la página, y detecta «agotado» y «preventa». Si la tienda recorta el título, lo reconstruye a partir del atributo `title` o de la dirección del producto.
3. **Sigue las páginas siguientes** (enlace `rel="next"` o «Siguiente») hasta el número de páginas elegido, mientras aporten productos nuevos.
4. **Si el método rápido no encuentra nada** y el navegador está activado, vuelve a intentarlo renderizando la página con tu Chrome (con Playwright). Si funciona, recuerda que esa tienda lo necesita.
5. **Ordena por precio** (o por precio total) y guarda cada resultado en `buscatron.db` (SQLite). Ese historial alimenta la regla de «bajada respecto a la media», la etiqueta «Mínimo histórico» y las gráficas.

### Navegador opcional
Para las tiendas que cargan sus resultados con JavaScript. Está activado por defecto, pero solo funciona si tienes instalado Playwright y Chrome o Edge:

```
pip install playwright
```

No se descarga ningún navegador: usa el que ya tienes, con un perfil propio (`navegador_perfil/`).

**BuscaTron no intenta saltarse protecciones antibot.** Si una tienda pide una comprobación humana, te lo dice. Con «Mostrar la ventana» activado en Ajustes, puedes resolverla tú una vez y la sesión queda guardada. Las tiendas que bloquean todo acceso automático se ofrecen como «solo enlace».

## Tiendas probadas

Resultado de la prueba el 6/11/2026 (las webs cambian, así que puede variar):

| Estado | Tiendas |
|---|---|
| ✅ Funcionan (15) | Juegos de la Mesa Redonda, Zacatrus, Dungeon Marvels, Jugamos Una, Jugamos Otra, El Taller del Modelista, Mathom, Tablerum, Outlet Games, Ludus Belli, Bandua, Goblin Trader, Gameria, Masqueoca, Turol Games (esta con navegador) |
| ➖ Responden, sin el producto probado (2) | Tiendas MGI, Outlet-PC |
| 🔗 Solo enlace (2) | Amazon, Ferretería Ibérica Madrid |
| 🛒 Segunda mano | Vinted y Milanuncios funcionan; Wallapop y eBay, solo enlace |

## Archivos locales

Se crean al usar la herramienta y no se suben al repositorio:

| Archivo | Contenido |
|---|---|
| `tiendas.json` | tu lista de tiendas, nombres, envío y buscadores descubiertos |
| `buscatron.db` | historial de precios, seguimientos y avisos (SQLite) |
| `config.json` | tokens de Telegram, PIN, ajustes de correo, de búsqueda y del navegador |
| `navegador_perfil/` | sesión del navegador opcional |
| `buscatron.log` | mensajes y errores cuando BuscaTron se inicia sin ventana |

## Estructura

```
buscatron/
  __main__.py      arranque (web, bandeja, arranque con Windows o línea de comandos)
  web.py           servidor web y API (filtro de IP, PIN)
  pagina.html      interfaz (una sola página, sin dependencias)
  motor.py         búsqueda en paralelo, páginas, filtros, envío, historial y orden
  extract.py       extractor genérico de productos, precios, estados y páginas siguientes
  abierta.py       búsqueda abierta (Bing / DuckDuckGo) y lectura de precios de las webs halladas
  descubre.py      descubrimiento del buscador de cada tienda
  fetch.py         descargas con la biblioteca estándar
  navegador.py     navegador opcional (Playwright + Chrome)
  tiendas.py       lista de tiendas, plantillas, segunda mano y tiendas «solo enlace»
  seguimiento.py   vigilancia, reglas de aviso y no repetición
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

57 pruebas, sin red. Cubren las reglas de aviso (objetivo, media histórica, no repetir, reaviso, limpieza de obsoletos), el extractor (precios tachados, texto oculto, títulos recortados, preventas, estados de segunda mano, páginas siguientes, datos de producto, envío), el motor (paginación, filtros, total con envío, mínimo histórico, historial), la búsqueda abierta, el filtro de IP y el PIN.

## Limitaciones conocidas

- Las revisiones programadas solo se ejecutan **mientras BuscaTron esté abierto**: activa el arranque con Windows para que lo esté siempre.
- No reconoce «el mismo producto» entre tiendas: filtra por palabras. Usa «Excluir» para descartar accesorios, packs o ediciones que no te interesan.
- Las tiendas cambian su web de vez en cuando y su lector puede dejar de funcionar. La web indica qué tiendas no han respondido.
- Amazon, Ferretería Ibérica, Wallapop y eBay bloquean cualquier acceso automático: solo se ofrece su enlace.
- La búsqueda abierta usa buscadores web gratuitos: es menos precisa, solo lee precios en euros y puede dejar de funcionar si el buscador la bloquea.
- Los gastos de envío los pones tú (o los sugiere «Detectar», que es solo una pista); no se leen del carrito de cada tienda.
- Las preventas se reconocen por el texto de la tienda («Preventa», «Lanzamiento aproximado»…); una tienda que no lo diga puede colarse como disponible.
- El envío por correo (SMTP) está implementado pero todavía sin probar con un servidor real.

## Licencia

AGPL-3.0. Consulta [LICENSE](LICENSE).
