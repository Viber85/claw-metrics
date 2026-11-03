# Claw Metrics v0.2.4-test.60 — Layout slider safe margins

Finishes the sizing improvement from test.59 for Decky's narrow Quick Access
Menu. Every Layout slider now has **10px internal left padding and 14px
internal right padding**, measured inside a responsive border-box wrapper.
The slider width automatically shrinks to the remaining inner space. No
fixed track width, negative margins or clipping are added.

The label and value align on their first text baseline; long labels still
wrap and numeric values remain fully visible. The native SteamOS SliderField
keeps its normal thumb range, controller focus and stepping behavior.

Changes are confined to Layout's UI CSS. No changes to MangoHud, Horizontal
or Vertical rendering, metric settings, graphs or stored styles.

Verify Layout → Size & appearance and Layout → Spacing on MSI Claw,
especially the leftmost and rightmost thumb position at the extremes.
The label, entire track, slider thumb and value should stay inside the
rounded card and have a comfortable visual gap from each side.

---

# Claw Metrics v0.2.4-test.59 — QAM slider width fix

Fixes the truncated numeric values and labels in Layout's Size & appearance,
Spacing, Position and Frametime graph cards. All 15 sliders have a shared
reusable, responsive wrapper with a dedicated label/value heading.

- Current numeric values always render in a 48px-minimum column instead of
  SteamOS's ellipsized inline label/value layout.
- Long titles wrap inside their own flexible column.
- The slider track uses the actual width of the inset card. The previous
  arbitrary 330px cap and overlapping margin are removed.
- Native SteamOS SliderField remains for D-pad focus, value adjustment,
  min/max and disabled states. Thumbs are not hidden or clipped.
- No changes to MangoHud, overlay rendering, graph styles or stored settings.

On-device test: open Layout > Size & appearance / Spacing, confirm full
numbers at minimum and maximum on Text size, Background opacity,
Vertical HUD width, Metric value gap and Vertical category gap. Verify
D-pad adjustment and maximum thumb position without clipping.

---

# Claw Metrics v0.2.4-test.58 — Smooth Curve & Dual Layer (native Vertical)

Adds two true native frametime renderer styles with their own icons and
controller-friendly tiles under **Layout → Frametime graph**:

- **Smooth Curve** (ID 4): bounded Catmull-Rom interpolation of 48 real
  frametime samples (four subsegments each). It does not fabricate or erase
  actual measurements and avoids overshooting sampled endpoint values.
- **Dual Layer** (ID 5): the same smoothed foreground plus a second,
  five-sample rolling trend line and a translucent local-variation ribbon.
  Distinct from the existing **Line + fill** which fills to the baseline.

**Both Horizontal and Vertical** offer all six graph modes and icon buttons.
Their selections are independent: Horizontal defaults to Line, and Vertical
defaults to Smooth Curve on new installs. The horizontal native renderer also
uses real samples for Smooth Curve and Dual Layer. Existing saved vertical profiles
that had an earlier graph style are migrated without changing their choice.

The native Vertical Graph Height default is **44 px** (previously 28 px),
and the slider extends to **120 px** (previously 72). Custom old heights,
including 28 px, are preserved; use the slider or Reset Layout to adopt
the larger default.

The original four graph modes and existing saved styles remain available.
Other rendering, vertical wrapping, metric spacing, and TDP/DRAW are unchanged.
Only the horizontal graph renderer gains these two additional draw modes.

**Device testing:** fully exit/relaunch the game, select Smooth Curve then
Dual Layer, check both icons/graphs, then verify the independent horizontal
selection and a custom saved style. CI success checks compilation only;
the actual on-screen visuals require MSI Claw validation.

---

# Claw Metrics v0.2.4-test.57 — Vertical Category Spacing

Adds **Vertical category gap (px)** under Layout → Spacing, range 0–20 px
(default 6 px). This adjusts additional ImGui table cell Y padding for
individual metric rows (FPS, GPU, CPU, RAM, VRAM, Battery, TDP, DRAW, Time
and the frametime graph).

It controls the spacing BETWEEN categories, not CPU/GPU values or the
automatic second-line value wrapping within one category. Existing Metric
value gap, graph width/height, styles, positions and DRAW behavior remain
unchanged. Settings are saved in both Saved Styles and Reset Layout restores
the default. Older styles load with their original settings preserved.

The control only appears in the Vertical HUD orientation and uses our native
Claw MangoHud renderer. Stock fallback and horizontal display are unchanged.
Fully close/restart the game after saving new settings. Native build success
does not guarantee visual results on the MSI Claw.

---

# Claw Metrics v0.2.4-test.56 — Automatic Vertical Metric Wrapping

Vertical Stacked now checks the **available HUD width before each metric value**,
using the selected token font. When multiple CPU/GPU/VRAM submetrics no longer
fit on one line, the next complete value moves to a continuation line inside
the same group, aligned with the numeric values column. Units are measured
with their number (e.g., 2532MHz, 3.1W or 4.0GiB) so they are not separated.

- The HUD width stays fixed; continuation lines grow only that group's height.
- Row separators remain between metric groups, not between wrapped values.
- The setting is automatic in native Vertical Stacked, with no extra toggle.
- Horizontal behavior, group ordering, saved styles, graph options and
  charging DRAW `--` behavior are unchanged.
- Stock MangoHud's fallback vertical display is untouched.

**Test in game after a complete restart:** enable GPU Junction, Core Clock,
Power and Voltage plus CPU Temp, Clock and Power. Check that overflow readings
appear on a second line inside their group and do not escape the right edge.
Also check text at 12 and 28 px and manual widths 160 and 260 px. CI checks
compilation but only on-device testing confirms final geometry.

---

# Claw Metrics v0.2.4-test.55 — Vertical Graph Dimensions & FPS Polish

The native two-column Vertical Stacked HUD gains three independent settings:
- **Metric value gap** 0–16 px (default 8 px) to space CPU/GPU values without
  altering horizontal Inner gap.
- **Vertical graph width**: Automatic (full available HUD width, default),
  or 80–420 px capped safely at the actual available width.
- **Vertical graph height**: 16–72 px (default 28 px), for all four native
  real-sample frametime graph styles.

The vertical FPS label and frametime text are now centered against the
selected oversized FPS number via its real font height. Horizontal FPS
centering code and its drawing behavior are preserved. Row separators are
slightly muted again. All settings are saved in both styles, and old styles
are backwards compatible. DRAW remains read-only and shows -- on AC power.

Close and restart the game to reload the native Vulkan library and HUD
configuration. Compile/test success does not establish the appearance on
MSI Claw; confirm it with on-device screenshots, including FPS scale 100,
150 and 200, and graph widths smaller than the HUD.

---

# Claw Metrics v0.2.4-test.54 — Vertical Exec Rows and FPS Scaling

Fixes the visibly overlapping TDP and DRAW strings in the native two-column
Vertical Stacked layout. Each host-supplied exec metric now uses its own row,
with the original label in the left column and its current value in the right
column. Custom token colors remain available. Native row divider opacity is
reduced while the four adaptive frametime graph styles are preserved.

Layout > Size & appearance > FPS value scale (100–200%) is now enabled in
vertical mode. It uses the existing dedicated FPS font from the Claw native
renderer; other metric font sizes stay unchanged. Close/restart a game after
switching HUD settings; visually confirm fit for large FPS sizes.

This release is experimental. It cannot force CPU/GPU temperatures or clocks
to display if their individual Metrics switches are disabled, and in-game
visual verification is still required.

---

# Claw Metrics v0.2.4-test.53 — Vertical Layout Polish

The native Vertical Stacked renderer now uses normal-sized sensor units
(MHz, W and GiB) and read-only TDP/DRAW values rather than small fonts.
Its frametime graph uses real samples, an adaptive amplitude range, a
muted fill and four styles (Line, Filled area, Bars, Dual), now selectable
in Layout. The existing Within-group gap slider is enabled in Vertical
mode, and row borders have been made less prominent.

The custom graph width and FPS-only scaling remain disabled in Vertical.
Horizontal mode keeps its existing native renderer behavior, and the
stock MangoHud vertical fallback is unchanged.

This ZIP is a native-build-tested preview, not yet validated in a running
game on an MSI Claw. Close and restart the game after upgrading.

---

# Claw Metrics v0.2.4-test.52 — Vertical Stacked native preview

This version develops the separate Vertical Stacked renderer. With the
bundled Claw MangoHud 0.8.1 library it uses two-column metric rows,
a prominent FPS header and a real-sample frametime graph footer.

The native auto-width is based on font size and starts at 260 pixels.
Manual width remains 160–420 pixels. Horizontal rendering and saved
orientation preferences are not changed. If the custom renderer is
unavailable, stock MangoHud retains its three-column vertical layout.

This is a native-build-tested preview; the real MSI Claw A8 game
appearance still requires validation. The FPS-only scale, inline
spacing toggle and graph-style controls intentionally remain disabled
in vertical mode until tested vertical implementations exist.

---

# Claw Metrics v0.2.4-test.51 — vertical HUD width

This isolated development version extends the native vertical preview from test.50.
Under **Layout → Size & appearance** choose **Automatic vertical width** (default)
or set a fixed width from 160 to 420 pixels. MangoHud v0.8.1 supports its
vertical `width` setting without modifying the Vulkan renderer. Horizontal
configuration ignores this preference and remains unchanged. Both saved style
slots store it; old styles retain their existing behavior. Restart the running
game to apply layout changes.

The native vertical renderer still needs device validation. FPS-only scaling,
custom inline gaps, and all horizontal graph-style behaviors are not yet
implemented for vertical mode; disabled controls remain available in horizontal.

---

# Claw Metrics v0.2.4-test.42 — popravak GitHub provjere ažuriranja

U test.41 pritisak na **Advanced → Provjeri novu verziju** mogao je završiti
generičkom porukom **Python Exception**. Provjera se oslanjala samo na
Python `urllib`, a Decky je sakrivao stvarnu poruku pogreške.

**Novo u test.42:** provjera najprije šalje HTTPS zahtjev preko vlastitog
Decky Loader mrežnog API-ja (`utilities/http_request`). Python backend
zatim provjerava službeni GitHub release, točan naziv ZIP-a, HTTPS adresu
iz našeg repozitorija, SHA-256 i numeričku verziju. Ako je Deckyjev HTTPS
zahtjev nedostupan, Python pokušava rezervnu provjeru. U oba slučaja
mrežne pogreške vraćaju se kao čitljiv status, a ne neobrađena iznimka.

Instalacija i dalje zahtijeva potvrdu korisnika i koristi Deckyjev sustav
za provjeru checksum-a i ponovno učitavanje plugina. Nikakve automatske
instalacije ni promjene Vulkan renderera nisu uvedene.

**Instalacija:** ručno instaliraj test.42 kao ZIP. Nakon toga u Advanced
pritisni **Provjeri novu verziju**. Ako je test.42 trenutno najnoviji,
trebala bi se pojaviti poruka da nema novijeg izdanja. Kad kasnije
objavimo noviju verziju, trebali bi se pojaviti opis i instalacijski
prozor. Provjeru na samom MSI Clawu još treba potvrditi.

---

# Claw Metrics v0.2.4-test.41 — popravak zasivljenih kontrola

U test.40 nova datoteka `updates.py` bila je zapakirana u korijensku mapu
plugina. Decky Loader izvršava `main.py` preko `spec_from_file_location`
i za dodatne module koristi isključivo mapu `py_modules/`. Zato uvoz
`from updates import check_github_update` nije uspijevao, Python backend
se nije učitao, a cijelo Decky sučelje ostalo je zasivljeno. Overlay je
ostao prikazan iz posljednje spremljene konfiguracije preko zasebnog
Vulkan procesa.

**Popravak:** test.41 sadrži `py_modules/updates.py`. Automatski test
pokreće `main.py` na isti izolirani način kao Decky Loader te potvrđuje
da se backend može učitati. Test također reproducira neuspješan slučaj
kad se `updates.py` nalazi samo u korijenu.

**Kako popraviti:** instaliraj ZIP test.41 ručno iz Decky instalacije jer
test.40 backend ne može izvršavati tipku za ažuriranje. Decky obično sam
ponovno učita plugin, a ako je potrebno restartaj samo Decky Loader.
Nemoj brisati `~/.config/ClawMetrics/settings.json`: postojeći stilovi
i postavke ostaju. Launcher i nativni renderer ne mijenjaju se.

---

# Claw Metrics v0.2.4-test.40 — ažuriranja iz GitHub Releasesa

U **Advanced → Ažuriranja s GitHuba** odaberi **Provjeri novu verziju**. Plugin
provjerava numeričke testne verzije u repozitoriju
[ikorljan-droid/claw-metrics](https://github.com/ikorljan-droid/claw-metrics/releases).
Ako je dostupna nova verzija, otvara se SteamOS prozor s brojem verzije,
opisom promjena i tipkom **Instaliraj**. Instalaciju moraš izričito potvrditi.

Instalacija koristi vlastiti instalacijski mehanizam Decky Loadera
(`utilities/install_plugin` s tipom UPDATE). ZIP adresa mora točno
odgovarati izdanju s GitHuba; SHA-256 se preuzima iz službenog release
metapodatka i Decky ga provjerava. Plugin sam ne zamjenjuje svoje datoteke.
Decky obično sam ponovno učita plugin nakon ažuriranja; ako to izostane,
učitaj ga ponovno u Decky Settings → Plugins, odnosno ponovno pokreni
Decky Loader. Ponovno pokreni **igru** ako je u njoj još učitan stari Vulkan
renderer. Cijeli SteamOS ili MSI Claw nije potrebno restartati samo radi
ažuriranja.

Ako Decky instalacijski API nije dostupan, prikazuje se ručna ZIP poveznica
za Decky Settings → Developer → Install Plugin from URL. Offline provjera
jasno prijavljuje pogrešku. Nijedno ažuriranje ne pokreće se automatski.
Instalirana verzija čita se iz ugrađenog `package.json` (od ovog izdanja
ispravno postavljen na 0.2.4-test.40).

**Activation** je skraćen na provjereni kratki Steam launcher. Standardna
i duga rezervna komanda premještene su u Advanced. Prethodni stilovi,
metrike i native layout/fps/frametime popravci ostaju.

---

# Claw Metrics v0.2.4-test.30 — vratiti visinu i veličinu fonta iz test.28

Ispravak regresije nastale u test.29: prilikom stabilizacije širine brojeva dodatni ImGui BeginGroup/EndGroup/Dummy elementi promijenili su izračun visine i optički smanjili tekst u odnosu na povećanu traku, čak kada je dodatni gornji/donji padding 0.

U test.30 stabilna brojčana polja više ne stvaraju dodatne ImGui elemente. Originalni RenderOutlinedText crta slova potpuno jednako kao prije, a kod ImGui::ItemSize povećava se samo **horizontalna širina** rezerviranog brojčanog polja. Druga koordinata ItemSize, tekst i pozicija ostaju netaknuti. Time visina trake, font i margine trebaju izgledati kao u provjerenom test.28.

Brojevi CPU/GPU (8%→10%→100%), FPS, temperature, frekvencije, W, memorija i sat i dalje imaju rezerviranu širinu i ne bi trebali izazivati vodoravno podrhtavanje. Centriranje uzima u obzir i njihove nevidljive horizontalne krajeve, ali ne dodaje prazan gornji i donji padding.

Provjera na MSI Claw A8: postaviti padding gore/dolje na 0, usporediti visinu trake i veličinu teksta s test.28 te promatrati stabilnost trake pri promjenama brojki. Automatski build nije zamjena za vizualni test na uređaju.

---
# Claw Metrics v0.2.4-test.29 — stabilna širina brojčanih podataka

Popravak mikro-pomicanja horizontalno centriranog HUD-a tijekom igre kada se CPU, GPU ili druge metrike mijenjaju između jedne, dvije ili tri znamenke.

Modificirani MangoHud 0.8.1 sada u našem jednorednom prikazu dodjeljuje **fiksne unutarnje slotove brojčanim vrijednostima**: FPS i frametime, CPU/GPU opterećenje i temperaturu, frekvencije i potrošnju, VRAM/RAM, bateriju, sat i TDP/DRAW. Font i boja svakog elementa ostaju nepromijenjeni. Rezervirana širina odgovara uobičajenom najdužem prikazu te uključuje male kompenzacije za širinu glifova.

Slot se rezervira pomoću ImGui group + invisible Dummy nakon ispisane vrijednosti; time sljedeći element počinje na istoj poziciji. Mehanizam automatskog centriranja iz test.28 uz stvarno nacrtane piksele u obzir uzima i **rezervirani desni rub** nevidljivog polja, čime crna traka zadržava stabilnu širinu bez rastezanja prazne tablice.

Nema dodatnog razmaka između kategorija, niti promjena grafova A/B/C/F, zadržanih stilova, promjenjivog FPS fonta, plavog fokusa kartica ili CPU/GPU/TDP/DRAW očitavanja. Jedinstveni fontovi i korisnička podešavanja margina ostaju kao prije.

Uvjet: tipičan raspon vrijednosti (FPS do tri znamenke, opterećenje do 100%, do četiri znamenke za frekvencije). Neočekivano velike vrijednosti i eventualna promjena aktivnih metrika mogu i dalje promijeniti širinu overlaya. Testirati uređaj na 8% → 10%, 9% → 100% CPU/GPU, te 99 → 100 FPS.

---
# Claw Metrics v0.2.4-test.28 — ispravak horizontalnog centriranja

Na Clawu je prijavljeno da uključivanje opcije Centriraj horizontalno produljuje crnu traku do desnog ruba, umjesto da smjesti cijeli overlay na sredinu.

Uzrok u native rendereru: mjerenje širine na temelju ImGui::GetItemRectMax može obuhvatiti praznu širinu tablice. Sada se tijekom crtanja pojedine metrike mjeri desni rub stvarno iscrtane geometrije teksta i grafa (ImDrawList::VtxBuffer). Izračunat desni rub uz korisnikov bočni padding postaje širina samog prozora. Ta širina se ograničava širinom zaslona, a kompaktni HUD pozicionira se na sredinu.

Kad je automatsko centriranje isključeno, ručni X pomak ostaje kako je bio postavljen. Ostaju isti FPS skaliranje i vertikalno poravnanje, grafovi A/B/C/F, fokus kartica i CPU/GPU/TDP/DRAW očitavanja.

Provjera: uključiti centriranje, mijenjati uključene metrike, veličinu FPS-a i širinu grafa. Cijeli sadržaj s crnom pozadinom treba ostati jednako udaljen od lijevog i desnog ruba, bez praznog repa.

---
# Claw Metrics v0.2.4-test.27 — plavo isticanje fokusa kartica

- Sve glavne kartice (Overlay, Layout, Metrics, Colors & Font, Activation i Advanced) osvijetljene su istom plavom pozadinom kad su otvorene ili u fokusu kontrolera.
- Uklonjeni su bijeli obrubi, dodatni unutarnji selection ring i bijeli sjaj. Fokus ostaje vidljiv kroz svjetliju pozadinu, svjetliju ikonu, tirkizni lijevi rub i vrlo blag plavi sjaj.
- Otvorena kartica ostaje vizualno aktivna kada fokus ode na drugu karticu. Nema promjena u ponašanju navigacije i otvaranja sekcija.
- Podržani su standardni DOM fokus i Steam/Decky gpfocus. Postojeći FPS scale od 100% do 200%, vertikalno poravnanje, A/B/C/F frametime grafovi, stilovi te CPU/GPU, TDP i DRAW ostaju nepromijenjeni.
- Potreban je test Game Mode fokusa na MSI Claw A8.

---
# Claw Metrics v0.2.4-test.26 — FPS skala i fokus kontrolera

- FPS broj koristi font rasteriziran na 200% prilikom pokretanja igre. Native ImGui Scale potom prilagođava veličinu za 100, 110, 120 ... 190 i 200%, umjesto da veličina ovisi o početnoj vrijednosti pri gradnji font atlasa. Samo FPS broj je povećan; drugi fontovi ostaju isti. Skup FPS znamenki smanjuje trošak atlasa.
- Vertikalno poravnanje koristi stvarnu visinu nakon primjene ImFont::Scale, pa ostali elementi ostaju centrirani prema prikazanom FPS broju.
- Svih šest glavnih kartica u Decky izborniku sada pokazuje tanak bijeli outline dok ih kontroler fokusira, čak i kad su zatvorene. Fokus je odvojen od stila trenutno otvorene sekcije. Podržani su standardni DOM fokus i Steamova klasa gpfocus.
- Spremljeni stilovi, grafovi A/B/C/F, CPU/GPU, TDP i DRAW su sačuvani. Za pouzdano učitavanje nove konfiguracije ili fontova ponovno pokreni igru.
- Dodani su regresijski testovi za svih 11 vrijednosti FPS skale i fokus zatvorenih kartica.

---

# Claw Metrics v0.2.4-test.25 — vertikalno centriranje uz povećani FPS

- Pri FPS veličini iznad 100%, sve ostale metrike, FPS oznaka, frametime (ms) i frametime graf centriraju se vertikalno uz povećani FPS broj. Računa se stvarna visina fonta iz MangoHud/ImGui font atlasa, a ne pretpostavljena visina; primjenjuje se nakon raspoređivanja elemenata u stupce tako da podržava promjenu redoslijeda.
- Sam povećani FPS broj ostaje u originalnoj poziciji. Na 100% ili kada povećani font nije učitan svi elementi ostaju na postojećem položaju. Ne mijenjaju se ostali fontovi, horizontalni položaj ili razmaci.
- Nema promjena na Z2 Extreme CPU/GPU potrošnji, aktivnom TDP profilu, DRAW-u, četiri A/B/C/F stila grafa, ikonama odabira, spremanju Stil 1/Stil 2 ili ostalim korisničkim opcijama.
- Izmjena vrijedi za modificirani Vulkan renderer. Potrebna je provjera prikaza na stvarnom MSI Claw A8 pri 100%, 150% i 200% FPS veličine.

---

# Claw Metrics v0.2.4-test.24 — četverostruki frametime graf

Layout → **Tip frametime grafa**: A Ispuna, B Linijski graf, C Histogram, F Linija + blaga ispuna. Zadano je B, dosadašnji prikaz. Koriste se stvarni frametime podaci i postojeća boja grafa. Odabir se sprema u Stil 1 i Stil 2. Izmjena djeluje u našem modificiranom Vulkan rendereru nakon ponovnog pokretanja igre, bez promjena na CPU/GPU, TDP, DRAW, FPS veličini ili centriranju.

---

# Claw Metrics v0.2.4-test.23 — FPS broj & automatsko horizontalno centriranje

- FPS broj ima zasebni slider od 100% do 200% s korakom od 10% i prikaz veličine u Layout panelu. Ostali tekst i metrike ostaju nepromijenjeni. Modificirani MangoHud učitava dodatne FPS fontove i koristi samo jedan povećani font pri iscrtavanju FPS broja.
- Pill opcija **Centriraj horizontalno** centrira cijeli HUD red prema širini ekrana i izračunatoj širini reda iz prethodnog framea (umjesto MangoHudovog problematičnog top-center načina). Uključena opcija zasivljuje X slider; isključena ga vraća na prethodno spremljenu vrijednost s korakom od 1 px. Y pomak ostaje neovisan.
- FPS scale i centriranje spremaju se u Stil 1 i Stil 2, uz ostale parametre. Početne postavke su FPS 100% i centriranje isključeno, tako da nema promjena na postojećem izgledu dok korisnik ne uključi opcije.
- Očitavanje CPU/GPU potrošnje iz AMD `gpu_metrics` 3.0 na Claw A8, TDP aktivne igre, DRAW i postojeće boje/fontovi ostaju kao u test.22.
- Nova veličina fonta i poravnanje zahtijevaju pokretanje igre s modificiranim Vulkan rendererom te ponovno pokretanje igre nakon promjene.

---

# Claw Metrics v0.2.4-test.22 — Z2 Extreme CPU/GPU power telemetry

MSI Claw A8 user confirmed `gpu_metrics` starts with `8 1 3 0`: structure size 264 bytes (0x108), format revision **3**, content revision **0**. The pinned MangoHud 0.8.1 rejected this format and fell back to GPU sysfs, making CPU 0.0 W and GPU power potentially reflect whole APU power.

- Backport the AMDGPU `gpu_metrics_v3_0` layout (from MangoHud 0.8.2) to **our existing modified MangoHud 0.8.1**, checking exact 264-byte structure size, format and read length.
- GPU W comes from v3 `average_gfx_power` (mW); the CPU/APU remainder comes from `max(0, average_apu_power - average_gfx_power)` (mW), matching upstream's verified Z2 Extreme fix (flightlessmango/MangoHud#1851, November 2025).
- CPU power calculation is an upstream-defined APU remainder, not independently measured silicon CPU rail. No direct device wattage accuracy claim until Game Mode validation.
- Retains per-game Panel de Control TDP readback (test.19), DRAW behavior, QAM styles, editable labels, condensed fonts and selected group border (test.21). No changes to power limits.

Source: https://github.com/flightlessmango/MangoHud/issues/1851

---

# Claw Metrics v0.2.4-test.21 — selected group border / style action icons

- Draw the selected main group's white outline directly **over** the section header, with a positioned, pointer-transparent ring; keep a CSS `!important` outline on Decky's button, rather than relying on the outer card border that did not appear reliably in SteamOS Game Mode. The ring persists when focus moves into the group's controls, and has no effect on click or gamepad input.
- The two compact style slots now have explicit **Play** icons for Učitaj and **Download-to-tray** icons for Spremi, matching the approved visual proposal. Action labels stay centered and their buttons use responsive `minmax(0,1fr)` widths.
- Retain all working test.20 UI behavior and the verified per-game Panel de Control TDP + DRAW monitoring from test.19, with no sensor or renderer changes.

---

# Claw Metrics v0.2.4-test.20 — compact styles & selected section

- Two saved appearance presets in Colors & Font → MOJI STILOVI; each fits within Decky's narrow Quick Access Menu. Each card offers only **Učitaj** and **Spremi**. Style 3 is no longer offered or read into current settings.
- Under the style description, the currently loaded style is clearly displayed; modified current settings are marked *izmijenjen*. Save/load behavior still persists all typography, colors, layout, and spacing options.
- A persistent white outline marks the currently expanded main category (Overlay, Layout, Metrics, Colors & Font, Activation, Advanced).
- No changes to per-game Panel de Control TDP readback, DRAW, native MangoHud 0.8.1 renderer or the SteamOS rename keyboard.
- Unit tests, TypeScript, native renderer build, and full ZIP packaging are checked by Actions. Hardware Game Mode validation is still required.

---

# Claw Metrics v0.2.4-test.19 — per-game Panel de Control TDP

- Read-only TDP fallback now follows the foreground Steam game (including PDC's stable non-Steam `ns:` identifiers) even while the Decky menu is closed. It uses the game's PL1 or the global PL1 when the game follows global. Auto TDP and explicit Steam-owned profiles do not claim a fixed PDC setpoint. All fallback readings are explicitly unverified as hardware readings.
- Context is refreshed every 3 seconds and expires after 25 seconds; on game change the old TDP is cleared until the new one is read. No TDP writes. Advanced has per-source diagnostics.
- Build includes the same patched MangoHud v0.8.1 Vulkan renderer and the offline Barlow fonts as test.17. Overlay and keyboard remain unchanged.

---

# Claw Metrics v0.2.4-test.18 — dijagnostika TDP-a

Advanced → Provjeri TDP očitanje sada prikazuje stanje zasebnih izvora: MSI firmware, RyzenAdj i konfigurirani Panel de Control (globalni limit, Auto TDP, različiti profili igara). Rezultati ne otkrivaju ID-eve igara. Nijedna TDP vrijednost se ne mijenja. Ovaj build služi utvrđivanju zašto se TDP ne očitava; ne tvrdi da je očitanje na SteamOS-u riješeno. Ostale izmjene test.17 ostaju iste.

---

# Claw Metrics v0.2.4-test.17 — TDP configured setpoint and normal text size

- TDP probes RyzenAdj from the real Decky plugin directory **Panel de Control/bin/ryzenadj** (with spaces), checks additional installed locations, and reads a valid STAPM row even when an unrelated RyzenAdj probe exits nonzero.
- If hardware readback is blocked by official SteamOS, it can read Panel de Control's persisted **configured global TDP** from `tdp_profiles.json` (read-only). The Advanced screen reports that a configured setpoint is **not hardware verified**. It refuses that fallback for Auto TDP and conflicting per-game overrides.
- The native 1-line HUD now renders TDP and DRAW at the same normal font size as other metric groups; each retains its own token color and font-weight overrides.
- No power limits are written. DRAW continues to show measured system battery discharge, not an APU-only estimate. Test.16 SteamOS TextField keyboard fix and compact layout are included.
- This version requires device validation on official SteamOS. A running game reporting no TDP can mean no usable hardware readback and no unambiguous configured PDC profile.

---

# Claw Metrics v0.2.4-test.16 — SteamOS virtual keyboard fix (experimental)

The Rename Metric modal now uses Decky's Steam-native `TextField` rather than a raw browser `<input>`. In Game Mode, highlight "Naziv stavke" and press A to invoke the SteamOS text keyboard. The built-in focus behavior is used rather than DOM `autoFocus` or unsupported keyboard APIs. Renaming stays limited to 24 characters; Confirm, Cancel, and Restore Default keep their prior behavior.

The test.15 compact three-column layout and the existing custom MangoHud/TDP/DRAW renderer are unchanged.

This was compiled/tested in CI. Game Mode virtual keyboard behavior on MSI Claw A8 must be confirmed on the handheld.

---

# Claw Metrics v0.2.4-test.15 — Decky Game Mode compact UI

UI-only prerelease based on v0.2.4-test.14 (official SteamOS, MSI Claw A8 Z2 Extreme).

- **Colors & Font:** style categories and global colors now display in 3 columns with reduced 13–15px icons and smaller padding, so 11 categories and all colors fit a narrow Decky Quick Access Menu.
- **Metrics:** enabled metrics appear as compact 3-column cards. Selecting a card reveals its original edit, reorder, hide and per-submetric toggle actions in a full-width details panel below. Disabled metrics return via compact "ADD ELEMENT" tiles. Renaming, state persistence and gamepad focus are retained.
- Font-weight options use a compact 2x2 grid to prevent overflow. Saved style slots and advanced style controls remain present.
- No changes to the modified MangoHud Vulkan renderer, Decky Python backend, TDP read-only sampling or battery DRAW telemetry. Existing launch option stays the same.

The layout must be checked on the actual SteamOS Decky panel. If any focus or functionality regression occurs, reinstall test.14 from its release.

---

# Claw Metrics v0.2.4-test.14 — read-only TDP and DRAW

- Optional **TDP** metric: sustained APU limit from `ryzenadj -i` STAPM readback on official SteamOS or MSI firmware PL1 if exposed. Never invokes writes and never guesses an unavailable limit. Displays `TDP --` if neither source is readable.
- **DRAW** remains whole-device battery-discharge telemetry from battery sensors, not APU power. DRAW becomes `--` while charging or on AC because total wall draw cannot be reliably derived from the battery sensor.
- Both are separate groups in Metrics, independently ordered and colored in Colors & Font. TDP starts off for existing installs: enable with **Metrics → ADD ELEMENT → TDP**; position it as desired near DRAW.
- Advanced → Provjeri TDP očitanje reports the current source. If kernel blocks RyzenAdj information, the display cannot promise a number.
- Read-only sensor sampling runs on the Decky backend, not inside games. The native modified Vulkan MangoHud renderer and test.13 layout are preserved.

Linux/CI checks do not prove hardware TDP readback or Proton behavior. SteamOS MSI Claw A8 verification needed. Roll back to test.13 if anything regresses.

---

# Claw Metrics v0.2.4-test.13 — Claw DevLab sync (experimental)

Source: `ikorljan-droid/claw-devlab` main commit `9acb36c6ab1b3e3d3a866f6dc09ff0eaf548431e` (2026-10-31).

Imports the current DevLab Decky QAM UI: named metrics, global font weight clearing manual overrides, palette changes clearing related manual colors, separate Clock/DRAW/Values categories, active style marker, and full visual style presets including font size, position, padding and spacing.

The backend now normalizes/persists the new settings and migrates older color/preset configurations. Native modified MangoHud keeps its Vulkan renderer, implements custom RAM/VRAM/Battery labels and maps the Clock and DRAW appearance independently; FPS/CPU/GPU labels use existing MangoHud config parameters. DRAW is still host-sampled battery discharge, not APU TDP.

**Compatibility:** This is a separate prerelease, not a change to SteamOS MangoHud. The overlay is an opt-in experiment with the same short Steam launch option as test.12. Native Game Mode/Proton results must be checked on the MSI Claw A8; browser preview and CI alone do not establish compatibility. Use test.12 to roll back.

---

# v0.2.4-test.12 — stability only

The short launcher now publishes executable content atomically and avoids rewriting itself when already valid. If the renderer library, Vulkan manifest or custom HUD configuration is missing during an update, it launches the game normally without the custom HUD. It does not try to inject or fix an incompatible present layer. No TDP additions, SteamOS native integrations or native renderer changes in this build.

---
# Claw Metrics v0.2.4-test.11 — short launcher for experimental Vulkan

This is a minimal follow-up to test.10. The custom Vulkan renderer, font atlas, metric styles and QAM visuals have not changed. A small POSIX shell launcher is now written automatically to the persistent user config directory at startup (and regenerated after settings updates), with executable permissions. The launcher exports **exactly the same** `VK_ADD_LAYER_PATH`, `VK_INSTANCE_LAYERS`, `DISABLE_MANGOHUD` and `MANGOHUD_CONFIGFILE` variables as the long experimental command, then uses `exec "$@"` to start the Steam game without changing its arguments or exit status.

**Use:** Open **Activation**, copy **Kratka testna komanda**, and paste it into the Steam Launch Options for a selected game. The command is an absolute path such as `/home/deck/.config/ClawMetrics/claw-metrics %command%`; this avoids relying on an uncertain Game Mode `PATH` and remains valid when Decky updates the plugin files. The old full-length experimental command remains available behind **Prikaži dugu rezervnu komandu**, and the standard stock MangoHud command is unchanged.

This does not automatically inject the overlay into every game. It is still **opt-in 64-bit Vulkan experimental support**; check **Provjeri koristi li igra eksperimentalni renderer** while playing. If a game fails to launch, revert its Steam Launch Options to the previous working command. Tests in GitHub Actions verify POSIX-shell delegation, environment variables, paths with whitespace/quotes, executable permissions and fallback. Actual SteamOS Game Mode/Proton compatibility still requires an on-device test.

---

# Claw Metrics v0.2.4-test.10 — individual typography and persistent QAM navigation

This experimental build preserves the exact QAM design from v0.2.4-test.9: dark blue cards, cyan active border, purple inactive accents, and six collapsible sections. The existing one-row Claw Metrics overlay, Vulkan launch method, Barlow Semi Condensed fonts, metrics and slider settings remain unchanged by default.

## Navigation correction

Decky can remount the React plugin panel when a setting is saved. The expanded QAM section, current metric submenu, and selected Colors & Font category now survive a remount while the plugin remains loaded. The Colors & Font tab does not jump back to Metrics after every edit.

## Colors & Font

Within the existing **Colors & Font** accordion there are compact tabs:
- **Global**: current default font, separator/label/value colors, FPS Bold toggle, three independent style-preset slots
- **FPS**: FPS label, FPS number and frametime in ms
- **CPU**: label, load, temperature, clock, power
- **GPU**: label, load, temperature, clock, power, junction, fan and voltage (where supported)
- **RAM**: label and GiB usage
- **VRAM**: label, usage, temperature and clock
- **Battery**: label, percent/icon, remaining time and watts
- **Clock**: time value

Each supported text token has a font-weight action that cycles **Global → Light → Regular → SemiBold → Bold → Global**. The same token may optionally override its inherited text color via the opaque-only HSL picker; **Vrati** removes that override. Text defaults to **Global**, preserving the user-tested look until deliberately changed. The three style slots each save/reload the complete palette and weight overrides.

### Native renderer

New experimental MangoHud configuration keys `claw_weight_map` (one character per token) and `claw_color_map` (opaque hex RGB or inherit for each token) drive actual ImGui font push/pop and token colors in the custom **64-bit Vulkan** renderer. The four bundled Barlow font weights are loaded into the font atlas. No changes are made to system MangoHud, Panel de Control, or the stable v0.2.3 release. DRAW (battery discharge read from an external command) and native frametime graph plotting use the existing **global** text/graph controls, not individual text-font overrides.

On-game font weight changes might need a game restart if the font atlas has not refreshed. Color changes should follow the existing live settings path. This release requires on-device verification before declaring these new renderer paths stable.

## Suggested Claw smoke test

Install as a test over the Decky plugin. Open **Colors & Font → CPU**, change `Temperatura` to SemiBold and its color, and verify the CPU temperature changes without affecting load, clock or GPU. Then open **GPU**, change the temperature to Light and check it stays open during save. Finally save Style 1, make a change and restore Style 1. Confirm that all metrics remain on one row and unchanged when overrides return to Global. If the game fails to start or text disappears, return to the previous working v0.2.4-test.9 package.

---

# Claw Metrics v0.2.4-test.9 — grouped QAM redesign

**UI-only changes based on the user-tested v0.2.4-test.8 native renderer.** All existing overlay functionality, the one-line HUD, fonts, metric preferences, colors, copyable launch commands and diagnostic functions are retained.

The Decky QAM now displays six controller-accessible, collapsible icon cards. Only one top-level card opens at once; **Metrics** opens by default:

1. **Overlay** — enable/disable and backend status
2. **Layout** — x/y position, text size, graph width, padding, separation and compact presets
3. **Metrics** — metric visibility, in-group switches, reorder buttons, hide/restore groups
4. **Colors & Font** — fully opaque HSL color picker, reset palette, Barlow Semi Condensed Light / Regular / SemiBold / Bold and FPS Bold
5. **Activation** — Steam launch options and one-click copying for normal/experimental Vulkan commands
6. **Advanced** — renderer diagnostics, unavailable TDP readback notice, battery DRAW notes and reconnect

The cards are styled with a restrained dark blue background, cyan accents for the open card and purple accents when collapsed; icons use packaged react-icons (no network dependency). Each heading is a Decky `DialogButton` for gamepad focus and selection.

No new backend calls, new sensors, live overlay renderer changes, TDP integrations, OS modifications or launch command changes were introduced by this UI update. Users can return to v0.2.4-test.8 directly if the QAM layout does not work well on their MSI Claw A8.

## Suggested smoke test on MSI Claw

Open the Decky plugin, switch between each card and verify only the chosen card is expanded. In **Metrics**, reorder CPU/GPU and change a sensor toggle, then restore it. Under **Colors & Font**, change a separator color and switch Regular/SemiBold. Under **Activation**, check that the experimental launch option can still be copied. Finally, make sure the in-game HUD remains on one line, with no changes to the saved profile.

---

# Claw Metrics v0.2.4-test.8 — four offline font weights and alpha-safe colors

This test build retains the working v0.2.4-test.7 Vulkan renderer, single-row overlay, all sensors, all spacing controls and separate separator-color configuration.

**Font weights**: Barlow Semi Condensed Light 300, Regular 400, SemiBold 600, Bold 700. The user-provided four files were inspected to verify the intended font family and weight variants. The release build fetches corresponding licensed official Google Fonts binaries at an immutable revision, validates Git blob hashes, and includes their OFL license in the plugin assets. They are the same family and weights but not guaranteed byte-identical to the four supplied files. The actual installed MSI Claw requires **no internet for font loading**. The plugin installs them from its assets on startup and verifies them. Existing settings are preserved and normal font preference defaults to Regular; FPS may use real Bold separately. Previous Claw Sans remains as a fallback if packaged assets are missing or damaged.

**Color picker fix:** The built-in Decky picker exposed an Alpha slider although the plugin only stores 24-bit RGB. A custom QAM picker now offers only Hue, Saturation and Lightness and always uses fully opaque color. This avoids the unused alpha control implicated in the game's crash report; its safety in live games still needs confirmation on the user's MSI Claw.

**Testing:** Install the new ZIP through Decky and restart Decky. Confirm the Font status shows Barlow Semi Condensed available, then switch between all four weights. Keep the experimental Vulkan launch command used in test.7, or copy the new one from Activation if it changed. While a game runs, test red separator, blue VRAM, and verify other metrics remain stable with the alpha-free picker. If a game crashes or font is missing, restore the last working v0.2.4-test.7.

The existing system MangoHud, stable v0.2.3, and Panel de Control are unchanged.

---

# Claw Metrics v0.2.4-test.7 — separator color and Barlow Semi Condensed

Based on the user-tested v0.2.4-test.6 renderer. The existing single row, metrics, color controls, and spacing options are preserved.

**Fixed**: Separators used a 24-bit RGB configuration color directly as an ImGui draw-list color. Draw-list colors require packed RGBA with an opaque alpha channel. The native fix converts the configured RGB to `IM_COL32(r,g,b,255)`, so separator and VRAM colors remain independent.

**Font**: Replaces the primary Claw Sans look with the slightly narrower, legible **Barlow Semi Condensed** family. QAM Appearance offers Light (300), Regular (400), Bold (700). The FPS Bold option uses the actual Bold font at the same point size, rather than faux-bold, when available. If fonts are unavailable, the existing Claw Sans and faux-bold remain safe fallbacks.

To avoid shipping font files directly, the Decky backend downloads the three weights on initial startup from an immutable Google Fonts revision and verifies the canonical Git blob hash of each file. **Internet access is required on first install.** Once downloaded, the fonts are cached locally and work offline. If Google Fonts is unreachable, the original font remains in use; restarting Decky online retries. Source and license:
- https://github.com/google/fonts/tree/89f5431ff0db41bd2fe3f7ba21a723a01622428b/ofl/barlowsemicondensed
- https://github.com/google/fonts/blob/89f5431ff0db41bd2fe3f7ba21a723a01622428b/ofl/barlowsemicondensed/OFL.txt (SIL Open Font License 1.1)

**Test**: Install the v0.2.4-test.7 ZIP. Restart Decky once online. The QAM Appearance font status should say Barlow Semi Condensed available. Start a 64-bit Vulkan game with the experimental launch command, check renderer ACTIVE, then compare Light/Regular/Bold; restart the game if the font doesn't reload. Next, change separators to red and VRAM label to green. Confirm only separators change. Toggle FPS bold; font size must stay unchanged. Stable v0.2.3 and user-confirmed v0.2.4-test.6 remain published and unchanged.

---

# Claw Metrics v0.2.4-test.6 — gamepad color editor

Based on the verified working `v0.2.4-test.5` layout. Keeps the one-line overlay, inner spacing controls, bold FPS, the explicit Vulkan launch path, and all sensor options.

## What's new

The **BOJE / COLORS** section in Decky QAM includes a controller-operated color picker (hue, saturation, lightness) for:
- Numeric values / clock / DRAW (shared `text_color`)
- Vertical separators between categories (**independent** from VRAM)
- FPS label and FPS number (separate controls)
- CPU, GPU, RAM, VRAM and BATT category labels
- Frametime graph

The existing defaults are kept as the initial palette. Values are saved as six-digit RGB colors, validated in Python, and applied to both MangoHud configs. `Vrati zadane boje` resets **only** the colors.

**Technical compatibility:** stock MangoHud 0.8.1 draws separators with `params.vram_color`. The experimental native patch changes that to a new `horizontal_separator_color` parameter, making independent separator customization work; stock MangoHud will still tie separator color to VRAM. This test is for our **experimental Vulkan** launch command.

## Test

Install the Decky ZIP, restart Decky if needed, launch a 64-bit Vulkan game with the experimental command, and confirm renderer status **AKTIVNO**. In QAM, open **BOJE / COLORS**, choose a color, move the HSL sliders and confirm. The game overlay should update without restarting, as in the preceding test. Try separator bright red and VRAM label green to verify the colors are independent; then restore default colors. Changes outside a running game are persisted for next launch.

If color changes do not refresh automatically in your game, re-open the overlay or restart that game. Do not change system MangoHud, OS files or Panel de Control settings.

**Status:** compiled in CI, not yet device-tested for the color editor. The confirmed functional prior `v0.2.4-test.5` release remains available.

---

# Claw Metrics v0.2.4-test.5 — uniform spacing across ALL metric groups

Built from the working `v0.2.3` baseline; retains the working experimental Vulkan layer integration confirmed on the MSI Claw in v0.2.4-test.3.

Changes compared with test.4:
- The **FPS** label, number and frametime in ms now use one group with equal interior spacing.
- **RAM**, **VRAM** and **BATT** use the same single-cell layout as the now-working CPU and GPU blocks.
- **DRAW** and **time** are already single-text cells; their inter-group spacing is controlled by existing horizontal gap settings.
- The numeric FPS value is drawn with additional left/right strokes (+/-1.1 px and +1.8 px) without increasing font size. This is faux-bold, not a distinct bold font. The prior +0.8 px stroke was too subtle.
- All functionality remains in **one horizontal line**. Existing QAM sliders and normal MangoHud fallback are preserved.

## How to compare
Install the ZIP in Decky, use the newly copied experimental Vulkan launch command, keep the SteamOS overlay disabled. Confirm renderer diagnostic `AKTIVNO`. Turn on `Jednaki razmaci: FPS, CPU, GPU, RAM, VRAM, BATT`; adjust `Razmak unutar grupa` to 3–5 px; toggle `Podebljani FPS broj` and compare just the numerical FPS. Changes should appear live as in the last hardware test. If text clips or any metric disappears, turn off the compact setting or restore v0.2.3 command.

This version has **not** been device-tested. GitHub compilation passing is not sufficient proof of on-device behavior.

---

# Claw Metrics v0.2.4-test.4 — uniform inline CPU/GPU + bold FPS

This experimental version changes **only the custom renderer**. It retains one single horizontal row, all existing metrics, and the known-working Vulkan launch integration from test.3.

- The CPU/GPU sections use the same adjustable **inner gap** between label, load, temperature, clock and power. They are no longer separate right-aligned four-character-wide table cells.
- `Razmak unutar CPU/GPU (px)` (0–16 px, default 4 px) controls that gap.
- `CPU/GPU vrijednosti u jednom redu` toggles the custom layout on/off for comparison.
- `Podebljani FPS broj` makes the **numeric FPS** slightly bolder by drawing an additional subpixel stroke. **Font size does not change.** This is faux-bold, not a separate bold font.
- The current FPS* label is the temporary experimental-config diagnostic.
- The four previous spacing controls remain. Stock MangoHud and Panel de Control are left unchanged.

## Test steps

Install this version and use the **experimental Vulkan 64-bit launch command** in a single game. Keep the built-in SteamOS performance overlay off. While the game runs, verify `AKTIVNO` under renderer diagnostics. Compare CPU/GPU with `CPU/GPU vrijednosti u jednom redu` off/on; adjust `Razmak unutar CPU/GPU` between 2 and 10 px. Toggle `Podebljani FPS broj` to compare. Other metrics should stay in the same single top row.

This native change is CI compiled but has **not** been tested yet on your MSI Claw hardware. Keep the working v0.2.3 for rollback.

---

# Claw Metrics v0.2.4-test.3 — Vulkan layer diagnostic

The previous test reported NIJE AKTIVNO on MSI Claw A8 / official SteamOS despite using the experimental launch command. This release is a **diagnostic experiment, not a confirmed fix**.

Changes:
- Custom Vulkan explicit layer uses a **unique layer name** `VK_LAYER_CLAW_METRICS_overlay_x86_64`, rather than colliding with system MangoHud.
- Install a discoverable but inactive-by-default JSON manifest at `~/.local/share/vulkan/explicit_layer.d/ClawMetrics.test3.x86_64.json`. The manifest does not automatically load the layer for other games; it needs the launch option. This is a user-level file, not a modification of Valve's OS files.
- Launch command requests the custom layer and sets `DISABLE_MANGOHUD=1` to prevent interference from system MangoHud.
- Diagnostics scan process library mappings and selected environment variables. No process command lines, passwords, or raw environment strings are shown.
- Existing stock v0.2.3 configuration stays unchanged; use its original launch command to revert.

**Testing:** Install v0.2.4-test.3 ZIP, restart Decky, copy the newly generated EXPERIMENTAL launch command (do not reuse the command from test.2), replace all launch options for one 64-bit Vulkan game, and relaunch the game. While running, select **Provjeri koristi li igra eksperimentalni renderer**. Read the counts:
- `native` > 0: our library was loaded.
- `zahtjev za slojem` > 0 and `native` = 0: environment reached a process but the library did not load.
- `testni config` > 0 but `zahtjev za slojem` = 0: game got config but not Vulkan request.
- Both zero: command may not have reached game, or process inspection is restricted. Do not claim a specific cause without more data.
- `manifest` = NE: on-disk manifest was not created/accessible.

The Vulkan layer has been compiled in CI, but its behavior with Proton/Steam Runtime on MSI Claw still requires hardware confirmation.

---

# Claw Metrics v0.2.4-test.2 (experimental SteamOS Vulkan injection)

**This is NOT a stable replacement for v0.2.3.**

The v0.2.4-test.1 layer was generated with implicit-layer enable/disable fields but was searched through `VK_LAYER_PATH` (an explicit layer path), so QAM controls could save values without the customized library actually loading. v0.2.4-test.2 removes those implicit fields and uses an explicitly requested Vulkan layer with `VK_ADD_LAYER_PATH` to avoid overriding other system layer search paths.

**How to test**: install the test.2 ZIP through Decky, restart Decky, enable the game-specific experimental launch option from the QAM *Activation* section, and fully restart a **64-bit Vulkan game**. Do not append the old `mangohud %command%` command. Keep SteamOS performance overlay off. Set graph width to 80, then 180 (or change gap) and restart the game between tests. If a value changes visually, the experimental renderer is working.

Two diagnostics:
- `FPS*` in the overlay proves the game read **our experimental config**. It does NOT by itself prove the modified library was loaded.
- With the game running, open QAM and press **Provjeri koristi li igra eksperimentalni renderer**. Only `AKTIVNO` means the modified `native64/libMangoHud.so` was found in the process map.

If it shows `NIJE AKTIVNO`, this might be due to the game using a 32-bit Vulkan runtime, a sandboxed path, or another layer taking precedence. If the game refuses to start, replace the launch option with the original v0.2.3 command. The stable MangoHud and Panel de Control are not changed.

## Original v0.2.3 documentation

# Claw Metrics v0.2.3

Decky QAM controls for MSI Claw A8 Z2 Extreme on official SteamOS. Generates a per-game MangoHud profile; the launch option remains necessary.

## Appearance

Content-width horizontal row with a rounded translucent dark background and manual X/Y placement. Configuration uses horizontal_stretch=0, position=top-left and explicit offset_x/offset_y. Native top-center's horizontal branch ignores offset_x, so manual placement deliberately uses top-left. X/Y are measured from the left/top edges, not as offsets from the center. Existing top-margin settings migrate to Y; default X is 8 px.

Extra vertical padding is expressed in pixels and mapped to cellpadding_y using the font size, so its effect is independent of the chosen text size. MangoHud still adds its fixed 5 px window padding. Horizontal window padding is hard-coded in this renderer and is not exposed as a working control. Keep hud_compact=0 to prevent the battery-time overwrite bug.

A licensed DejaVu Sans subset, renamed Claw Sans, ships in assets/ClawSans.ttf.gz.b64. The backend decodes it into ~/.config/ClawMetrics/ClawSans.ttf, makes it readable (0644), and verifies its SHA-256. Both font_file settings point to that profile location. There is no fontconfig or host /usr font dependency. QAM shows whether the actual installed bytes passed validation. Attribution/license ships in assets/FONT-LICENSE.txt.

The appearance preset uses 18 px text, 80% background, 10 px corner radius, X=8/Y=8 and 8 px extra vertical padding. Old size/opacity preferences are preserved until the preset button is pressed. Colors follow the supplied reference: green FPS/graph, cyan CPU, green GPU, purple RAM and pink VRAM. The font is similar to the concept, not an exact identification of its font. Separate oversized FPS, exact icon-plus-percentage combination and exact mockup proportions are not supported by this renderer.

## Elements menu

Expand groups, switch individual metrics, move visible groups using arrows, hide with × and restore with Add Element. Order and options survive restarts. CPU/GPU load are the Always metrics within each enabled group. Nine supported GPU fields are exposed rather than inventing unseen entries from the photograph's 13-option list. Available sensors depend on the hardware. VRAM clock/temperature render in the VRAM block and require both GPU and VRAM enabled. Frametime milliseconds belong to the FPS block; the graph can be moved separately. Battery icon and percentage are alternative render modes.

## DRAW and TDP

The Decky host samples battery discharge power every two seconds and writes readable draw.txt. MangoHud reads that text with cat; games do not need Python. Values use power_now, or current_now × voltage_now with sysfs unit conversion. While charging or without a valid sensor, DRAW -- is shown rather than charging watts mislabeled as total device consumption. The task is cancelled on unload. CPU/GPU watts remain separate sensors. Applied TDP readback from Panel de Control is still unavailable; no fake value or power-limit write is made.

## Installation

Install ClawMetrics-v0.2.3.zip from Releases, restart Decky Loader to install the font and regenerate the profile, then restart the game. Launch options do not change. Select Primijeni izgled prijedloga for the reference-style preset. Keep the system performance overlay disabled to avoid duplication.

## Verification and limits

CI runs Python regressions (migration, order sanitization/persistence, submetrics, compact-mode safeguard, font checksum/readability, background task lifecycle and discharge-power units), TypeScript checking, frontend build and ZIP content/version checks.

CI also compiles a headless ImGui 1.89.9 probe, the ImGui version pinned by MangoHud v0.8.1. It uses the same window positioning, table-sizing, text-drawing, rounding and battery-column traversal with fixture metrics. Manual coordinates must match the configured X/Y, increasing padding must increase the background height, labels must fit, and the installed font must have proportional glyph advances. Downloaded source files are hash-verified. Locally run: python tools/check_native_layout.py, or supply --imgui-dir with the pinned sources.

The fixture covers default and reduced rows, explicit X/Y movement, zero/default/maximum vertical padding and a compact preset at 1280 px. A manual-position reset restores X=8/Y=8 without changing other options. The compact-preset button is explicitly labeled Uži red: manji font i bez MHz. It uses a 12 px font, X=8/Y=8, 4 px extra vertical padding, and disables CPU/GPU clock submetrics to retain headroom at 1280 px. Other submetric preferences are preserved. This is a local renderer check, not a Vulkan injection or device screenshot. Native controller focus, actual game sandbox access, exact SteamOS MangoHud version and device visual appearance still require the Claw. Different metric values, lower game resolutions, larger fonts or excessive sensors can exceed screen width; reduce text size/options in that case. No automatic font shrinking is claimed. Moving a row cannot make a row that is wider than the game fit; use the compact preset or disable optional sensors in that case. Independent FPS size would require changes to the native renderer, not another config slider.

### Crash Session Recorder (test.61)

Recording starts automatically when the backend detects the exact Claw Metrics
native library mapped in a process. Detection runs every five seconds, even
with QAM closed. Three consecutive checks without the library finish the
session as `overlay_unloaded`; restricted process inspection does not end it.
A launch command or installed library alone does not trigger recording.
After reboot, the old interrupted session is retained; a new session starts
when the overlay loads again. This detects library loading, not proof that a
frame was drawn, and cannot record freezes occurring before that detection.

**Advanced → Diagnostics** still offers manual start/stop and ZIP export.
Manual stop pauses auto recording until the overlay has closed. A normal
plugin unload (including Decky restart/update) is labelled `plugin_unloaded`.

The ZIP is saved under `~/.config/ClawMetrics/diagnostics/`; its full path appears
in Diagnostics. Open Desktop Mode, copy that ZIP and attach it for analysis.
No report is uploaded automatically. Reports include the recorded OS/kernel,
overlay settings at start and last sample, game IDs, available AMD GPU/battery
readings, memory, system load and bounded journal extracts. FPS is not sampled.
Missing sensors are empty values; CPU/GPU power are not interchangeable with
battery draw. Logs are filtered to the session's boot and time window. Previous
boot logs may be missing if the OS does not persist its journal; this feature
does not change journald configuration. Common credentials, IPv4 addresses and
home usernames are redacted, but review the report before sharing it.

Telemetry is flushed and fsynced every five seconds. A hard freeze can lose the
last samples. Up to five sessions are retained with an 8 MiB telemetry limit per
session; starting a sixth deletes the oldest session and its exported ZIP.
`interrupted` means an unclean end (power loss, killed backend or reboot), not
proof of an overlay crash. Compare otherwise similar sessions with the overlay
enabled and disabled. SteamOS, Bazzite and other systemd Linux variants use the
same recorder; sensor and journal availability still need device testing.

### Pending test.62: live style reload and journal export

The file watcher now signals a pending reload; configuration parsing runs at a
render-thread frame boundary. Upstream parsing changes global HUD element lists,
so locking only the final parameter assignment allowed those lists to change
while they were being drawn. Vulkan font refresh now runs before ImGui NewFrame,
rather than first rebuilding the atlas after that frame's draw data was created.
The original notifier fails the thread-boundary regression; the corrected watcher
passes 24 atomic file replacements with AddressSanitizer/UBSan (leak detection is
disabled in the restricted test process). This test uses real inotify and native
notifier code with a stub parser. It does not execute the game's Vulkan rendering
or prove the cause of the reported game crash. Device confirmation remains needed.

Journal export normalizes stored UUID boot IDs to 32 hexadecimal characters.
Reports now include journal success/exit status and mark filtered logs unavailable
when collection fails, rather than incorrectly suggesting there were no errors.

### test.64: additional FPS and memory readings

In **Metrics → FPS**, enable **Average FPS** and **1% low FPS**. Statistics use
presented frame times in a rolling 60-second window, capped at 30,000 frames per
swapchain. Average FPS is frame count divided by total frame time; 1% low is the
reciprocal of the mean duration of the slowest ceil(1% × frame count) frames.
The low value shows `--` until 100 samples exist and recalculates at most twice
per second. Long stalls remain included. Counters restart with a new swapchain
or after both FPS statistics are disabled. These are presented-frame statistics,
not a measurement of input latency or a separate count of generated frames.

In **Metrics → RAM**, enable **Game RAM** and **SWAP**. GAME is the resident
memory of the process hosting the injected overlay (GiB), not the total memory
of every Wine/Proton process. SWAP is the system-wide used swap amount; zero is
valid. A failed process-memory read shows `--`.

All four are off by default, saved per style, and available in horizontal and
vertical Claw layouts. Individual colors and font weights are under Colors &
Font → FPS/RAM. The options require the bundled native renderer; the stock
fallback stays unchanged. The primary FPS number alone retains FPS scaling.

### test.67: overlay backgrounds and charcoal plugin theme

**Colors & Font → Background** provides a solid RGB color or a linear/radial
multistop gradient, with 2–8 editable colors and stop positions. Linear mode has
an angle control; radial mode has center X/Y and spread controls. Background
opacity uses the same existing opacity setting. New styles store background
settings; legacy styles without a background leave the current choice intact.
Solid mode remains available in stock MangoHud; gradients require the bundled
Claw renderer. Rounded corners follow Layout and gradient sampling uses pixel
space, keeping radial gradients circular on wide HUDs.

The plugin UI uses charcoal surfaces, subtle borders, light icons and blue
active controls. Existing HUD metric colors are preserved. Software Vulkan
validation covers gradient vertex colors, opacity and live layout changes;
physical-device visuals and controller navigation remain separate checks.

### test.69: background outline and slider sizing

Background now includes **Outline**, with an RGB color, 1–6 px width and
independent opacity. It follows rounded corners, stays inside the HUD rectangle
and remains visible with a 0% background fill. Outline settings are stored with
the background in each saved style; existing styles default to outline off.

Background controls reuse the Layout slider's PanelSectionRow and safe inset
wrapper. The shared native SliderField explicitly requests `layout="below"`
and `childrenContainerWidth="max"`, so the empty native label cannot leave a
fixed inline control column wider than a nested card. Control-group widths and
box sizing are constrained consistently. The frontend test checks that API
contract and endpoint callbacks; actual SteamOS control geometry/navigation
still requires device verification.

### test.70: one report export action

Diagnostics shows a single **Export Crash Report** button plus the date, state
and sample count of the latest ended session. A currently recording session is
excluded; the prior ended session can still be exported while a new game runs.
The status list is refreshed immediately before export to pick the latest
available session. Older sessions remain retained on disk without repeating
export buttons. If only the first active recording exists, stop it before
exporting. Recording, retention and report contents are unchanged.


### test.71: compatibility evidence and independent logs

Crash reports now query GPU, Decky/Steam helper and warning logs independently within the recorded boot and session window. Each query has its own 2500-line / 512 KiB output bound and collection status. General RGB floods no longer displace the dedicated query results. Logs remain bounded and may be incomplete.

`compatibility.json` records read-only device model, OS, architecture, DRM driver, named hwmon channels and battery-node availability at session start. It excludes serial numbers and does not modify hardware, TDP, OS or renderer settings. Missing nodes are unavailable, not zero. Discovery does not certify sensor accuracy or support. Old sessions explicitly report missing inventory. Legion Go 1 / Bazzite 44 is a test target, not yet device-verified.


### test.72: shorter Steam launch option

Activation now copies `~/claw-metrics %command%`. A create-only symlink in the detected user's home points to the existing persistent launcher, preserving its environment, argument forwarding and missing-assets fallback. No PATH or fixed username is required. Steam must expand `~` to the same user's home; verify this on each OS. Existing launch options remain valid. Existing files and foreign symlinks at that name are never replaced; Activation falls back to the old absolute path when the alias is unavailable.


### test.73: first installable modular overlay preview

After installing, fully restart each running game once to load the new native library. Keep your current launch command. Open **Layout → Modular layout · preview** and choose **Two rows** or **Graph focus**. The **Use modular layout** switch returns to the classic renderer. New installs/old profiles stay classic until you choose a modular layout.

Import **Export layout** JSON from the existing DevLab editor using **Import DevLab JSON**. Decky also edits the screen anchor/offset and each group's row/column direction, visibility, scale, gap and padding. Detailed element selection, nesting and reordering are authored in DevLab; this first Decky editor is not a drag-and-drop canvas. Export returns the latest document shown in the UI. Settings retain the complete document; an automatic `modular-layout-backup.json` copy is kept in the plugin's user config folder. JSON imports are bounded and validated before replacing settings.

Saved styles include modular mode and its document. Older styles restore classic mode without destroying the currently retained modular document. Fonts, token colors, global solid/linear/radial background, opacity, rounding and outline use the existing appearance controls. Node color/background overrides remain supported. Filled area is opaque, line + fill remains translucent, and all six graph shapes are supported. Numeric slots reserve width so changing readings do not continuously resize panels. Graph histories are resampled to at most 64 points per graph. Only the first selected GPU is used; battery icons are not a separate modular token in v1.

In modular mode the tree owns visibility and geometry; classic metric/position/padding controls do not rearrange it. The generated profile enables sources required by visible tree elements. Missing sources show `--`; TDP/DRAW shell error text cannot expand the HUD. The loader publishes complete immutable documents between frames. Invalid or partially written files keep the last valid native document. Vulkan draw commands honor ImGui vertex offsets for large layouts.

Validation: backend/style migration and strict JSON tests, mocked Decky callbacks, browser width checks at 350 px, hash-verified ImGui fixtures with the packaged Barlow font at 1280x800 and 1920x1080, legacy software-Vulkan regression tests and modular software-Vulkan transitions, font reload, gradients/outlines, all graph modes and a >64K-vertex document. These checks do not certify handheld rendering, gamepad navigation or hardware readings. The native release pipeline and ZIP-content checks must pass before this prerelease is offered for download.
