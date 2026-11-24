# Hidden Wonders — banco de ideas inicial

Investigación: 23-11-2026. Canal en inglés, sin cara: misterios históricos reales, ingeniería, descubrimientos, inventos e historias documentadas.

## Cómo se verificó

**Temas descartados.** No se repite ningún tema de «Ciencia con Pruebas». Se revisaron los 26 slugs de `content/scripts/` y `content/experimento-01/scripts/`: plaga del baile, Krakatoa, punto azul pálido, Semmelweis, Tunguska, Phineas Gage, año sin verano, tardígrados, Anticitera, Wow!, Mona Lisa, Eratóstenes, disco de oro, Voynich, guerra de los emús, Venus, piedras que se mueven, Bloop, la Luna se aleja, Olympus Mons, Fleming, Galvani, Newton, Arquímedes, Halley y Carrington.

**Fuentes.** Todas las URL citadas se abrieron con WebFetch y la página confirmaba el dato. Las que no cargaron (403 o timeout) no se citan; se marcan como bloqueadas en el apartado de cautelas. Varias webs de referencia rechazan las descargas automáticas: smithsonianmag.com, britannica.com, las fichas de colección de britishmuseum.org y olympics.com. Cuando una fuente es el Museo Británico vía Google Arts & Culture, el texto es del propio museo.

**Imágenes.** Se comprobaron con `engine/find_images.py`, que solo lista dominio público, CC0, CC BY y «No restrictions»; excluye CC BY-SA. Se cita un archivo real por idea. CC BY exige atribución en la descripción del vídeo. Las imágenes NASA son de dominio público, salvo crédito de terceros.

**Lo que no entra.** Personas vivas como protagonistas, tragedias recientes, política actual, salud práctica y conspiraciones sin base.

---

## 1. Las 20 ideas

Formato: S = Short (30-45 s), D = documental (8-12 min), S+D = ambos.

| # | Working title | Categoría | Gancho (1 frase) | Por qué interesa internacionalmente | Fuente 1 | Fuente 2 | Imagen libre comprobada | Formato |
|---|---|---|---|---|---|---|---|---|
| 1 | **The Warship That Sank in 20 Minutes (Vasa)** | ingeniería / historia real | El buque más poderoso de Suecia se hundió en su viaje inaugural tras navegar 1.300 m, y hoy se conserva más del 98 % de su estructura original. | Barco del s. XVII casi intacto; fallo de ingeniería universal; 400.º aniversario en 2028. | [Vasa Museum – Timeline](https://www.vasamuseet.se/en/explore/vasa-history/timeline) | [SLAC/Stanford – resumen de Sandström et al., *Nature* 415 (2002)](https://www-ssrl.slac.stanford.edu/research/highlights_archive/vasa.html) | `File:Vasa, Swedish warship 1628 (30352310637).jpg` (CC BY 2.0) y decenas más; `File:Vasa rig diagram.jpg` (CC BY 3.0) | S+D |
| 2 | **The Day Chicago Lifted Itself Out of the Mud** | ingeniería | Hacia 1860, unos 600 hombres giraron 6.000 gatos de tornillo a la vez para levantar una manzana entera de Lake Street, con los negocios abiertos. | Historia urbana insólita; Chicago es conocida en todo el mundo. | [WBEZ – «Raising Chicago» (2013)](https://www.wbez.org/shows/wbez-news/raising-chicago/aae67013-459b-424d-850e-8d9cb6dcadbf) | [ASCE – Ellis S. Chesbrough](https://www.asce.org/about-civil-engineering/history-and-heritage/notable-civil-engineers/ellis-sylvester-chesbrough) | `File:Street Raising on Lake Street.jpg` (PD); `File:Tremont House (NBY 1730).jpg` (PD) | S |
| 3 | **The Great Stink: How a Smell Built London's Sewers** | ingeniería | En el verano de 1858 el Támesis olía tan mal que el Parlamento aprobó la ley de alcantarillado en 18 días. | Origen de la ingeniería sanitaria moderna; Londres tiene tirón global. | [London Museum – Great Stink of 1858](https://londonmuseum.org.uk/collections/london-stories/great-stink-of-1858) | [Hansard, Commons, 15-07-1858](https://api.parliament.uk/historic-hansard/commons/1858/jul/15/first-reading) (+ [London Museum – Bazalgette](https://londonmuseum.org.uk/collections/london-stories/how-bazalgette-built-londons-first-super-sewer/)) | `File:FaradayFatherThames.jpg` (PD, *Punch* 1855); `File:Joseph Bazalgette by Lock & Whitfield.jpg` (PD) | S+D |
| 4 | **Hubble's $1.5-Billion Blur** | ingeniería | El espejo de Hubble salió con un error de 2,2 micras, 1/50 de un cabello, por una lente de prueba descolocada 1,3 mm. | NASA y Hubble son marcas globales; historia de error y redención. | [NASA Science – Hubble's Mirror Flaw](https://science.nasa.gov/mission/hubble/overview/hubbles-mirror-flaw) | [NASA Science – Servicing Mission 1](https://science.nasa.gov/mission/hubble/observatory/missions-to-hubble/servicing-mission-1) | NASA `s93-48826` (arte STS-61), `9400368` (History of HST) (PD NASA). **No verificado:** la comparativa antes/después (M100) por API. | S+D |
| 5 | **The Mars Probe Lost to Inches and Pounds** | ingeniería | Un software de tierra dio el impulso en libras-fuerza·s en lugar de newtons·s, un error de ×4,45, y la sonda entró en Marte a ~57 km en vez de a 226 km. | Error de unidades que entiende cualquiera; caso de estudio mundial. | [NASA – MCO Mishap Investigation Board Phase I Report (1999, PDF)](https://llis.nasa.gov/llis_lib/pdf/1009464main1_0641-mr.pdf) | [NASA NSSDCA – Mars Climate Orbiter 1998-073A](https://nssdc.gsfc.nasa.gov/nmc/spacecraft/display.action?id=1998-073A) | NASA `PIA02330` (MARCI Approach Image), `KSC-98pc1085` (PD NASA) | **S** |
| 6 | **The Clock That Solved the Sea (Harrison's H4)** | invento | En el viaje de prueba a Jamaica (1761-62), el reloj H4 solo atrasó unos 5 s, unas 2 millas de error, y aun así el premio de 20.000 £ nunca se concedió oficialmente. | Problema de la longitud: historia marítima global; David contra la Royal Society. | [Royal Museums Greenwich – Harrison's clocks](https://www.rmg.co.uk/stories/time/harrisons-clocks-longitude-problem) | [Linda Hall Library – John Harrison](https://www.lindahall.org/about/news/scientist-of-the-day/john-harrison) | `File:John Harrison (Gemälde) 01.jpg` (PD); réplica H1 CC0 (Clockmakers' Museum). **No encontrada** foto libre del propio H4. | S+D |
| 7 | **The Chess Machine That Fooled Europe (The Mechanical Turk)** | invento / misterio | Un «autómata» jugó al ajedrez ante la corte de María Teresa (1769-70) y engañó al público más de 80 años: dentro había un jugador escondido. | Precursor mítico de la IA; Poe, Napoleón (leyenda), París, EE. UU. | [Linda Hall Library – Wolfgang von Kempelen](https://www.lindahall.org/about/news/scientist-of-the-day/wolfgang-von-kempelen) | [JSTOR Daily – Before Deep Blue](https://daily.jstor.org/before-deep-blue-the-automaton-chess-player) | `File:Racknitz - The Turk 3.jpg` (PD); serie `Chess Automaton Willis 1821` (PD) | S+D |
| 8 | **The Loom That Taught Computers to Read** | invento | Tejer un retrato de Jacquard en seda exigió más de 24.000 tarjetas perforadas, y Wellington lo confundió con un grabado. | Puente entre el textil y la informática (Babbage, Lovelace). | [Science History Institute – The French Connection](https://www.sciencehistory.org/stories/magazine/the-french-connection/) | [Computer History Museum – Preserving the Legend of J. M. Jacquard](http://www.computerhistory.org/blog/artifact-adopted-preserving-the-legend-of-j-m-jacquard/) | `File:À la mémoire de J.M. Jacquard … LCCN2002737214.tif` (PD, 10470×14334, Library of Congress); `File:Jacquard loom cards.jpg` (CC0) | S |
| 9 | **The Roman Cup That Changes Color** | descubrimiento | Esta copa romana del s. IV es verde con luz de frente y roja a contraluz por partículas de oro y plata de unos 50 nm; no se entendió hasta 1990. | «Nanotecnología» accidental de hace ~1.700 años; efecto visual inmediato. | [British Museum vía Google Arts & Culture – Discover the Lycurgus Cup](https://artsandculture.google.com/story/discover-the-lycurgus-cup/mwWBqnUNwgBpLQ?hl=en) | [Kool et al., *Beilstein J. Nanotechnol.* 11 (2020), PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC6964654) | 9 fotos CC0: `File:British Museum The Lycurgus Cup 01 15022019 4376.jpg`; roja y verde: `File:Top view of the famed Lycurgus Cup…jpg` (CC BY 4.0) | **S** |
| 10 | **The Man Who Read the Flood Before Noah** | descubrimiento | En 1872 un empleado autodidacta del Museo Británico leyó en una tablilla de Nínive un relato del diluvio más antiguo que el bíblico, y según el museo empezó a desvestirse de la emoción. | Gilgamesh y el Diluvio interesan en todo el mundo, con o sin religión. | [British Museum vía Google Arts & Culture – The Flood Tablet](https://artsandculture.google.com/asset/the-flood-tablet-relating-part-of-the-epic-of-gilgamesh/wQGL1dmyVmXRYA?hl=en) | [National Geographic – How the Epic of Gilgamesh was discovered](https://www.nationalgeographic.com/history/history-magazine/article/history-gilgamesh-epic-discovery) | `File:British Museum Flood Tablet.jpg` (CC0); `File:George Smith-Assyriologist 001.jpg` (PD) | S |
| 11 | **The Planet Found With a Pen** | descubrimiento | Le Verrier calculó dónde debía estar un planeta invisible, y Galle lo encontró en menos de 30 minutos a ~1° del punto previsto (23-09-1846). | Triunfo de la física newtoniana; rivalidad Francia-Inglaterra. | [NASA History – 175 Years Ago: Neptune](https://www.nasa.gov/history/175-years-ago-astronomers-discover-neptune-the-eighth-planet) | [Royal Museums Greenwich – Astronomy in the 19th century](https://www.rmg.co.uk/stories/space-astronomy/astronomy-19th-century) (+ [MacTutor, St Andrews](https://mathshistory.st-andrews.ac.uk/HistTopics/Neptune_and_Pluto/)) | NASA `PIA02210` (Neptune, Voyager) (PD); `File:T4- d721 - Fig. 445 — M. Le Verrier reçu par le roi Louis-Philippe.png` (PD) | S |
| 12 | **The Girl Who Dug Up Sea Dragons (Mary Anning)** | descubrimiento | Con 12 años, Mary Anning y su hermano sacaron de un acantilado de Lyme Regis el primer ictiosaurio casi completo descrito por la ciencia. | Paleontología, mujeres en la ciencia, dinosaurios marinos. | [Natural History Museum – Mary Anning: the unsung hero](https://www.nhm.ac.uk/discover/mary-anning-unsung-hero.html) | [Linda Hall Library – Mary Anning](https://www.lindahall.org/about/news/scientist-of-the-day/mary-anning) | `File:Mary Anning painting.jpg` (PD, 5633×7283) | S |
| 13 | **Endurance: The Ship the Ice Ate** | historia real | El hielo del mar de Weddell aplastó el Endurance en 1915 y sobrevivieron los 28 hombres; en 2022 apareció el pecio a 3.008 m. | Supervivencia legendaria; fotos de Hurley de dominio público. | [Scott Polar Research Institute (Cambridge) – Endurance 1914-16](https://www.spri.cam.ac.uk/picturelibrary/expeditions/endurance/5.html) | [Scientific American – Endurance discovered (2022)](https://www.scientificamerican.com/article/legendary-shipwreck-of-shackletons-endurance-is-discovered-in-antarctic-waters/) | `File:Endurance trapped in pack ice.jpg` (PD); `File:Endurance Final Sinking.jpg` (PD); serie RMG (PD) | S+D |
| 14 | **The Franklin Expedition: 129 Men Who Vanished in the Ice** | misterio | 129 hombres entraron en el Ártico en 1845 y ninguno volvió; el testimonio inuit, despreciado durante un siglo, llevó a los pecios en 2014 y 2016. | Misterio polar clásico; la ciencia moderna (ADN, plomo) y el saber indígena. | [Parks Canada – Franklin's 1845 expedition](https://parks.canada.ca/lhn-nhs/nu/epaveswrecks/culture/histoire-history/expedition) | [Swanston et al., *PLOS ONE* 13(8) e0202983 (2018)](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0202983) (+ [RMG – Inuit oral history](https://www.rmg.co.uk/stories/maritime-history/how-inuit-oral-history-helped-locate-erebus-terror)) | `File:HMS Erebus and Terror - ILN 1845.jpg` (PD); mapa 1860 (PD); `File:Discovery of John Franklin's cairn.jpg` (No restrictions). Fotos de los pecios: © Parks Canada, **no libres**. | S+D |
| 15 | **The Mary Celeste: What Really Happened** | misterio | En 1872 hallaron el Mary Celeste a la deriva con 1.701 barriles de alcohol y víveres para seis meses, sin rastro de sus 10 ocupantes, y el té caliente es un invento. | Fantasma del mar más famoso; desmontar mitos (Conan Doyle). | [Royal Museums Greenwich – The mystery of the Mary Celeste](https://www.rmg.co.uk/stories/maritime-history/mystery-mary-celeste) | [American Heritage, vol. 32 n.º 2 (1981)](https://www.americanheritage.com/mystery-mary-celeste) | `File:Mary Celeste as Amazon in 1861.jpg` (PD); `File:Mary Celeste NYTimes 1873February26.png` (PD); escritorio de Briggs (CC0, Peabody Essex) | S+D |
| 16 | **CROATOAN: The Colony That Vanished** | misterio | En 1590 John White volvió a Roanoke y encontró la colonia vacía y solo una palabra tallada, sin la cruz que habían pactado como señal de peligro. | Misterio fundacional de Norteamérica; muy buscado en EE. UU. | [NPS Fort Raleigh – 1590 Rescue Voyage](https://www.nps.gov/fora/learn/historyculture/1590-rescue-voyage.htm) | [NPS – 1587: The Lost Colony](https://www.nps.gov/fora/learn/historyculture/1587-the-lost-colony.htm) (+ relato primario de White en Hakluyt, [transcripción](https://www.constitution.org/primarysources/ronoake.html), web no institucional) | `File:William Ludwell Sheppard & William James Linton - CROATOAN, The Lost Colony (John White).jpg` (No restrictions); `File:Ruins of the English Settlement at Roanoke.jpg` (PD) | S |
| 17 | **The Lighthouse Keepers Who Disappeared** | misterio | En diciembre de 1900 tres fareros de las islas Flannan desaparecieron sin dejar rastro, y el famoso diario «de tormenta» es una invención posterior. | Misterio escocés muy viral; desmentir mitos con documentos. | [National Records of Scotland – blog (2023)](https://blog.nrscotland.gov.uk/2023/12/12/flannan-isles-lighthouse-keepers-the-disappearance/) | [NRS – research guide](https://nrscotland.gov.uk/learning-and-events/research-guides/lighthouses/the-mystery-of-the-flannan-islands-lighthouse) (misma institución; no hay segunda independiente fiable) | Solo `File:Admiralty Chart No 3331 Flannan Isles, Published 1903.jpg` (PD). **Sin fotos libres** del faro en la búsqueda (las de Commons suelen ser CC BY-SA). | S |
| 18 | **The Great Moon Hoax: Bat-People on the Moon** | historia real | En 1835 un diario de Nueva York contó que el telescopio de Herschel había visto unicornios, castores bípedos y hombres-murciélago en la Luna. | Primera *fake news* viral; conecta con la desinformación actual sin entrar en política. | [Library of Congress – Folklife blog, The Great Moon Hoax](https://blogs.loc.gov/folklife/2014/08/the-great-moon-hoax/) | [Linda Hall Library – Richard Adams Locke](https://www.lindahall.org/about/news/scientist-of-the-day/richard-adams-locke) | `File:Lunar animals and other objects … LCCN2003665049.jpg` (PD, 8793×6030, Library of Congress); litografías italianas de 1836 (PD) | **S** |
| 19 | **The Strangest Olympic Marathon Ever (1904)** | historia real | En el maratón de San Luis 1904, el ganador corrió a base de estricnina y brandy, otro hizo parte del recorrido en coche y solo acabaron 14 de 32. | Juegos Olímpicos = audiencia mundial; absurdo y documentado. | [Olympedia – Marathon, Men 1904](https://www.olympedia.org/results/56131) | [The Olympic Museum (Lausanne) vía Google Arts & Culture – Thomas Hicks](https://artsandculture.google.com/story/thomas-hicks-the-olympic-museum/cAURyxnqwnD81w?hl=en) | `File:Start of the 1904 Olympic Marathon Race. David R. Francis firing the starting gun.jpg` (PD); Hicks atendido (PD) | S |
| 20 | **The Telegram That Pulled America Into WWI** | historia real | En 1917 Alemania ofreció en secreto Texas, Nuevo México y Arizona a México, y los descifradores británicos de la Room 40 lo leyeron. | Criptografía y espionaje; documento original en el Archivo Nacional de EE. UU. | [US National Archives – Zimmermann Telegram (Milestone Documents)](https://www.archives.gov/milestone-documents/zimmermann-telegram) | [GCHQ – Room 40 and the Zimmermann Telegram](https://www.gchq.gov.uk/features/century-how-work-gchqs-predecessors-contributed-us-entering-world-war-i) | `File:Zimmermann-telegramm-offen.jpg` (PD, solo 508×600). El escaneo de NARA (ID 302025) es de dominio público por ser del Gobierno de EE. UU., pero **no se comprobó** con el script. | S |

**Reserva:** *The Boston Molasses Flood (1919)*, una ola de unos 8,7 millones de litros de melaza que mató a 21 personas. Fuentes: [City of Boston](https://www.boston.gov/news/100-years-ago-today-molasses-crashes-through-bostons-north-end) y [APS News, ene. 2017](https://www.aps.org/apsnews/2017/01/this-month-in-physics-history). Imágenes: `File:BostonMolassesDisaster.jpg` (PD). Queda en reserva porque es una tragedia con víctimas civiles y conviene tratarla con tono sobrio.

### Cautelas de rigor por idea (no decir en el guion)

1. **Vasa**
   - Muertos: «unos 30» según la cifra actual del museo; las cartas de la época dan 30-50, así que no decir 50.
   - No afirmar que el rey ordenó un segundo puente a última hora, ni que el casco era asimétrico, ni que lo hundió una salva: nada de eso está verificado.
   - El PEG se pulverizó 17 años. Los «26 años» que se leen a veces suman también el secado.
2. **Chicago**
   - Altura elevada: unos 10 pies según la ASCE, hasta 14 según WBEZ.
   - Las cifras de hombres y tornillos del Tremont House varían entre fuentes.
   - Que los huéspedes «no notaron nada» es folclore.
   - Pullman fue uno de varios contratistas.
   - La Encyclopedia of Chicago no cargó.
3. **Great Stink**
   - Se actuó por la teoría del miasma, no de los gérmenes, y el cólera de 1866 llegó igualmente.
   - Que el Parlamento colgara cortinas empapadas en cal no está verificado.
4. **Hubble**
   - Fue aberración esférica, no «desenfoque».
   - El espejo nunca se cambió: se corrigió con óptica delante de los instrumentos.
   - No centrar el vídeo en astronautas vivos.
5. **Mars Climate Orbiter**
   - No fue «la NASA usó unidades imperiales»: el archivo de tierra del contratista incumplía la especificación de interfaz.
   - El informe da igual peso a los fallos de proceso.
   - El coste de la misión no está verificado.
6. **Harrison**
   - No ganó «el premio»: cobró 23.065 £ en pagos sucesivos.
   - Decir «unos 5 s», no 5,1.
7. **Turco**
   - Las partidas con Napoleón y Franklin son relatos posteriores. Con Franklin solo consta una carta de invitación.
   - Fuego de 1854: decir «un museo de Filadelfia».
8. **Jacquard**
   - No inventó las tarjetas perforadas: antes las usaron Bouchon y Falcon.
   - Retrato de hacia 1839.
9. **Licurgo**
   - No decir que los romanos «entendían» las nanopartículas.
   - Sin cifras en ppm: no se pudo abrir Freestone 2007.
   - Smithsonian bloqueó la descarga.
10. **Flood Tablet**
    - La anécdota de desvestirse es tardía y de segunda mano: presentarla como «según el Museo Británico».
    - Smith no excavó la tablilla, la leyó.
11. **Neptuno**
    - Acreditar a d'Arrest.
    - Adams: no darle la autoría.
12. **Anning**
    - No fue «el primer ictiosaurio».
    - El cráneo lo encontró su hermano Joseph.
    - El trabalenguas *She sells sea shells* y el rayo que la alcanzó de bebé no están verificados.
13. **Endurance**
    - 28 hombres contando a Shackleton.
    - Tres hombres del grupo del mar de Ross sí murieron.
    - El anuncio «Men wanted…» es apócrifo.
14. **Franklin**
    - 134 zarparon y 129 siguieron tras Groenlandia.
    - El plomo como causa está **en debate**: Swanston 2018 lo relativiza.
    - El canibalismo está corroborado: cortes en huesos en 1997 y la mandíbula de Fitzjames en 2024.
    - Las profundidades de los pecios no están verificadas.
15. **Mary Celeste**
    - El té tibio, el desayuno a medio comer y los botes en su sitio son ficción.
    - La teoría de los vapores de alcohol es una hipótesis.
16. **Roanoke**
    - Las páginas del NPS dicen 117 o 118 colonos.
    - El destino de la colonia es desconocido.
    - El Museo Británico (acuarelas de White) bloqueó la descarga.
17. **Flannan**
    - Las entradas dramáticas del diario y la silla volcada salen del poema de 1912.
    - Las edades no cuadran entre fuentes: no darlas.
18. **Moon Hoax**
    - El Sun nunca se retractó.
    - No dar cifras de tirada, que no están verificadas.
    - Autor: «la mayoría de historiadores atribuyen a Locke».
19. **Maratón 1904**
    - Smithsonian y olympics.com no cargaron.
    - Los perros que persiguieron a Taunyane y la siesta de Carvajal no están verificados.
20. **Zimmermann**
    - El 17 de enero solo se descifró una parte.
    - La guerra submarina total pesó tanto como el telegrama.

---

## 2. Puntuación (1-5)

Criterios: Interés internacional (Int.), Calidad de fuentes (Fuentes) y Posibilidades visuales con imágenes libres (Visual).

| # | Idea | Int. | Fuentes | Visual | **Total /15** |
|---|---|---|---|---|---|
| 1 | Vasa | 5 | 5 | 5 | **15** |
| 18 | Great Moon Hoax | 5 | 5 | 5 | **15** |
| 13 | Endurance | 5 | 5 | 5 | **15** |
| 4 | Hubble's blur | 5 | 5 | 4 | **14** |
| 7 | Mechanical Turk | 5 | 4 | 5 | **14** |
| 9 | Lycurgus Cup | 5 | 4 | 5 | **14** |
| 14 | Franklin Expedition | 5 | 5 | 4 | **14** |
| 19 | 1904 Marathon | 5 | 4 | 5 | **14** |
| 3 | Great Stink | 4 | 5 | 4 | **13** |
| 5 | Mars Climate Orbiter | 5 | 5 | 3 | **13** |
| 8 | Jacquard loom | 4 | 5 | 4 | **13** |
| 10 | Flood Tablet | 4 | 5 | 4 | **13** |
| 11 | Neptune | 4 | 5 | 4 | **13** |
| 12 | Mary Anning | 4 | 5 | 4 | **13** |
| 15 | Mary Celeste | 5 | 4 | 4 | **13** |
| 6 | Harrison H4 | 4 | 5 | 3 | **12** |
| 16 | Roanoke | 4 | 4 | 4 | **12** |
| 20 | Zimmermann | 4 | 5 | 3 | **12** |
| 2 | Raising Chicago | 4 | 3 | 4 | **11** |
| 17 | Flannan Isles | 4 | 4 | 2 | **10** |

Notas a la puntuación:
- **Mars Climate Orbiter** baja en lo visual porque casi no hay fotos de la sonda y necesitará animación y diagramas. Pero el diagrama (226 km frente a 57 km) es fácil y muy claro.
- **Flannan** baja porque no hay fotos libres del faro.
- **Chicago** baja en fuentes por las cifras contradictorias y porque la Encyclopedia of Chicago no cargó.

---

## 3. Selección

### Las 3 mejores para Shorts

1. **The Great Moon Hoax: Bat-People on the Moon (#18)**, 15/15.
   - El gancho funciona en 2 segundos: «In 1835, a newspaper reported bat-people on the Moon.»
   - Las litografías de 1835-36 de la Library of Congress están en dominio público y en alta resolución (8793×6030). Se ven muy bien en vertical con zooms.
   - Fuentes institucionales: el blog de la LOC y la Linda Hall Library.
   - Cierre con giro: el Sun nunca se retractó.
2. **The Roman Cup That Changes Color (#9)**, 14/15.
   - Es el Short más visual posible: la misma copa en verde y luego en rojo, con 9 fotos CC0 del Museo Británico y otras CC BY 4.0.
   - Funciona sin texto, lo que ayuda en un canal internacional.
   - Fuentes: el propio Museo Británico y un artículo revisado por pares de 2020.
3. **The Mars Probe Lost to Inches and Pounds (#5)**, 13/15.
   - Tiene la fuente primaria más sólida de la lista: el informe oficial de la junta de investigación de la NASA, con citas exactas.
   - Es un error que entiende cualquier espectador del mundo, y la cifra ×4,45 cabe en un Short.
   - Elegido frente al maratón de 1904 (14) porque su fuente es más fuerte. El maratón queda como 4.º Short.
   - Lo visual se resuelve con un diagrama animado de la trayectoria y la foto MARCI de Marte.

Siguientes en cola para Shorts: 1904 Marathon, Mechanical Turk, Mary Celeste (desmontando mitos) y Flood Tablet.

### Documental piloto (8-12 min): **The Warship That Sank in 20 Minutes — Vasa**

Por qué Vasa y no Endurance o Franklin, que tienen la misma nota:
- **Arco completo y cerrado:** construcción, aviso ignorado, desastre, juicio sin culpable, olvido, redescubrimiento, rescate y una carrera actual por salvarlo. Encaja en 10-11 minutos sin relleno.
- **Fuentes:** un archivo institucional coherente (Vasa Museum: cronología, investigación, rescate y conservación) más ciencia independiente revisada por pares (*Nature* 2002 vía SLAC y Scientific American).
- **Imagen:** el barco existe y está casi entero. Commons tiene decenas de fotos CC BY 2.0 en alta resolución y un diagrama del aparejo CC BY 3.0. Queda solo exigir atribución en la descripción.
- **Momento:** 2028 es el 400.º aniversario y el refuerzo de acero del casco está en obras de 2024 a 2028. El tema seguirá vigente.
- **Riesgo bajo:** encaja con la línea de ingeniería del canal, no hay personas vivas protagonistas y la tragedia es de 1628. Franklin tiene canibalismo y 129 muertos, lo que es más delicado para anunciantes, y las fotos de sus pecios no son libres. Endurance es ya un tema muy explotado por otros canales.
- **Segundo documental recomendado:** Franklin (#14), con mapas y grabados de época en dominio público.

---

## 4. Esquema del documental piloto: Vasa (≈ 10:45)

| # | Capítulo | Duración aprox. | Contenido verificado | Visuales (libres) |
|---|---|---|---|---|
| 1 | **Cold open: 1,300 metres** | 0:00-1:00 (1:00) | 10-08-1628: el Vasa zarpa en Estocolmo, recorre 1.300 m y se hunde en minutos a 32 m. Hoy se conserva más del 98 % de su estructura original. ¿Cómo falla así el barco más caro del reino? | Fotos CC BY 2.0 de la popa, zoom lento; mapa animado del puerto con la línea de 1.300 m |
| 2 | **A King's Order** | 1:00-2:30 (1:30) | Ene. 1625: Gustavo II Adolfo encarga cuatro barcos al maestro holandés Henrik Hybertsson y a Arendt de Groote. Quilla en 1626. Hybertsson enferma, cede la obra a Hein Jakobsson y muere en 1627. Botadura en 1627: 69 m, más de 1.200 t, 10 velas, 64 cañones, 120 t de lastre. | Retrato de Gustavo II Adolfo (PD); `Vasa rig diagram.jpg` (CC BY 3.0); detalle de las esculturas |
| 3 | **The Test Nobody Reported** | 2:30-3:45 (1:15) | Verano de 1628: el capitán Söfring Hansson hace correr a 30 hombres de banda a banda ante el vicealmirante Klas Fleming. El barco escora tanto que se detiene la prueba, y nadie informa al rey. | Animación 2D del barco escorando; diagrama del centro de gravedad |
| 4 | **Twenty Minutes** | 3:45-5:15 (1:30) | 10-08-1628, por la tarde, con 4 de 10 velas: una racha lo escora y se recupera. La segunda le mete agua por las portas bajas abiertas. Iban 150-200 personas a bordo; murieron unas 30 (las cartas de la época dicen 30-50). Los supervivientes nadan unos 120 m hasta Beckholmen. | Mapa animado, diagrama de las portas abiertas, fotos de las portas en el museo (CC BY 2.0) |
| 5 | **A Trial With No Culprit** | 5:15-6:15 (1:00) | 5-09-1628: comisión de 17 miembros presidida por el almirante Karl Karlsson Gyllenhielm. El barco no tenía suficiente «vientre» para su obra alta y pesada. Nadie fue castigado: la culpa recayó en Hybertsson, ya muerto. | Documento o grabado de época si existe en PD; si no, tipografía y diagrama de proporciones |
| 6 | **The Diving Bell** | 6:15-7:00 (0:45) | 1663-65: Treileben y Peckell bajan a unos 30 m con campana de buceo y recuperan casi todos los cañones, que se venden. En 1920 se rechaza volarlo para aprovechar el roble. | Grabado de campana de buceo del s. XVII (PD, por buscar); animación |
| 7 | **333 Years Underwater** | 7:00-9:00 (2:00) | 25-08-1956: el sacatestigos de Anders Franzén saca roble negro; el 4-09-1956 los buzos confirman que es un barco. 1957-59: buzos de la Armada excavan 6 túneles bajo el casco para pasar cables hasta los pontones Oden y Frigg. Primer izado el 20-08-1959; traslado en 18 etapas a 17 m de profundidad y unos 18 meses de sellado. El 24-04-1961 a las 9:03 el casco sale a la superficie. Se recuperan más de 700 esculturas. | Diagrama animado de túneles y pontones; fotos actuales CC BY 2.0. Las fotos de 1961 suelen tener copyright del museo, así que hay que comprobarlas una a una. |
| 8 | **The Second Race: Saving Vasa** | 9:00-10:45 (1:45) | 1962-1979: 17 años de pulverización con PEG y unos 9 de secado; museo abierto en 1990. En 2000, tras un verano húmedo, afloran sales ácidas: el azufre de la madera, catalizado por el hierro de los pernos, podría generar más de 5.000 kg de ácido sulfúrico (*Nature* 2002). Se cambian los pernos y el barco se inclina un poco a babor. Desde 2024 se instala una nueva cuna de acero, con 2028 como objetivo, el 400.º aniversario. Cierre: el barco que se hundió por exceso de ambición ahora necesita ingeniería para no hundirse en sí mismo. | Fotos interiores CC BY 2.0; gráfico de la reacción azufre + hierro → ácido; línea de tiempo 1628-2028 |

**Fuentes principales del documental:**
1. Vasa Museum. Las cuatro páginas cubren la cronología completa, el hundimiento, la investigación de 1628, el rescate y la conservación actual:
   - Timeline: https://www.vasamuseet.se/en/explore/vasa-history/timeline
   - The Disaster: https://www.vasamuseet.se/en/explore/vasa-history/disaster
   - The Inquest: https://www.vasamuseet.se/en/explore/vasa-history/inquest
   - The Salvage: https://www.vasamuseet.se/en/explore/vasa-history/salvage
2. Vasa Museum – Preservation timeline: https://www.vasamuseet.se/en/explore/research/how-we-preserve-vasa/preservation-timeline. Cubre el PEG, la crisis del azufre en 2000, el cambio de pernos y la nueva cuna de 2024-2028.
3. Sandström et al., «Deterioration of the seventeenth-century warship Vasa by internal formation of sulphuric acid», *Nature* 415, 893-897 (2002). El resumen de SLAC/Stanford se pudo abrir: https://www-ssrl.slac.stanford.edu/research/highlights_archive/vasa.html. La página de nature.com pide inicio de sesión.
4. Scientific American (21-02-2002), «Sulfur within recovered ship…»: https://www.scientificamerican.com/article/sulfur-within-recovered-s/. Es una fuente independiente para la cifra de más de 5.000 kg.
5. Complementaria: la FAQ del museo (https://faq.vasamuseet.se/category/45?lang=en), que da las 150-200 personas a bordo y explica la horquilla de 30-50 muertos.

**Pendiente antes del guion:**
- Comprobar las cifras discrepantes: 55, 61 o «casi todos» los cañones rescatados en el s. XVII; 4.000, 5.000 u 8.000 pernos; el peso actual.
- Buscar con `find_images.py` un retrato libre de Gustavo II Adolfo y un grabado de campana de buceo.
- Confirmar la licencia de cada foto concreta de Commons que se use, porque la atribución CC BY es obligatoria.
- Pasar el skill `fact-checker` al guion final.
