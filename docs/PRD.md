PRD — SkyRide 2.x
0. Resumen ejecutivo

SkyRide es un marketplace paritario de vuelos charter con fee de servicio 5%, y un SaaS/OS para operadores (calendario, slots, precios, analytics). Incorpora empty legs (v1: pierna opuesta, v2: venta por asiento con fee 25%), pagos Wompi, WhatsApp (Chatrace), Supabase Postgres y Redis para holds/locking. Frontend React (shadcn/Tailwind), widget embebible en WordPress, y panel /ops para operadores.

1. Objetivos y éxito
1.1 Objetivos de negocio

Paridad de precios con operador (0% markup base).

Monetización: 5% service fee (charter), 25% fee sobre empty legs seats.

Capturar demanda turista/concierge con respuesta inmediata (WhatsApp + Hosted Quote).

Ofrecer un OS para Operadores (slots, pricing, analytics) para retención y moat.

1.2 KPIs (núcleo)
KPI	Meta inicial
Tasa de “hold” (add_to_cart/visitas)	≥ 5%
Tasa de conversión (purchase/hold)	≥ 25%
Tiempo a primer contacto (WA)	≤ 2 min
Sell-through de empty legs	≥ 40%
Tasa de respuesta WA (24h)	≥ 90%
Downtime app (mensual)	≤ 0.5%
2. Alcance y roadmap
2.1 Alcance v2.0 (demo listos)

Infra: Supabase (DB gestionada), Redis (holds, rate-limit).

API: availability/slots, holds (TTL + idempotencia), quotes (PriceBook+surcharges+ITBMS 7%+fee).

Pagos: Wompi Payment Links + webhook firmado.

Mensajería: WhatsApp/Chatrace send-template + webhook inbound.

Widget: /widget.js (selector → quote → CTA).

WP: bloque CTA/Deals.

ICS v1: import manual por aeronave.

Operación: health, rate-limit, CORS/CSP básicos, CI mínimo, docs y GO_LIVE.

2.2 v2.1 (próximo sprint)

Portal Operador /ops: bandeja solicitudes, calendario CRUD, viewer de PriceBook, analytics básicos.

Widget docs completas + ejemplos data-*.

ICS: cron 5–10 min por aeronave; UI para icsUrl.

Empty legs v1: publicar pierna opuesta (flag OFF por defecto), páginas /deals.

2.3 v2.2 (sprint posterior)

Empty legs v2 (seats): prorrateo, multi-seat, fee 25%.

Yappy como pasarela alternativa.

Dashboards GA4/KPIs: hold-rate, conversion, WA response, sell-through empties, leakage proxy.

RLS/Supabase Auth para multi-tenant en /ops.

3. Usuarios y casos de uso
3.1 Personas

Turista/Cliente final: busca tour o punto a punto; quiere disponibilidad y pago sencillo.

Concierge/Hotel/Tour operador: necesita cotización rápida y “link para cobrar”.

Operador (OPS): administra slots, precios, ICS, confirma reservas.

Admin SkyRide: monitoreo, pricing global, auditoría, soporte.

3.2 Flujos clave

Lead → Hosted Quote → Hold → Pago Wompi → Booking → WhatsApp follow-up.

WA inbound (cliente responde): registrar en MessageLog; reenganchar con plantilla.

Operador: carga ICS / CRUD de slots / revisa solicitudes / ajusta PriceBook.

Empty legs: al cerrar tramo, sugerir pierna opuesta; en v2, seats por pasajero.

4. Requisitos funcionales
4.1 Frontend Público (React + Widget)

Widget /widget.js:

Props data-*: aircraft-id, lang, brand-color, cta.

Flujo: fecha/hora/pax → POST /api/quotes → CTA Hosted Quote o WhatsApp.

Emite GA4: view_item, add_to_cart, begin_checkout.

Hosted Quote /q/:token:

Desglose de precio (base, ITBMS, fee, total), countdown hold.

CTAs: Pagar (Wompi) y WhatsApp.

Deals:

Lista y detalle de empty legs (v1) y seats (v2).

4.2 Portal Operador /ops (v2.1)

Bandeja de solicitudes (quotes/holds).

Calendario CRUD por aeronave; colores por estado (AVAILABLE/BUSY/MAINTENANCE/ICS).

PriceBook Viewer + edición básica (v2.2).

Analytics: ocupación por aeronave, lead-to-book, tiempo de respuesta.

4.3 Backend API (FastAPI)

Disponibilidad:

POST /api/ops/slots (upsert; valida solapes).

GET /api/availability?aircraftId&dateRange=YYYY-MM-DD..YYYY-MM-DD.

Holds:

POST /api/holds con Idempotency-Key; TTL; 409 en conflicto; 429 por rate-limit.

DELETE /api/holds/{id}; expiración automática.

Quotes:

POST /api/quotes → PriceBook + surcharges + ITBMS + fee (desglose).

Pagos:

POST /api/payments/wompi/link (opcional si no es directo en server).

POST /webhooks/wompi (verificación HMAC + idempotencia; transita booking→PAID).

WhatsApp:

POST /api/wa/send-template (Chatrace); guardar MessageLog OUTBOUND.

POST /webhooks/wa para INBOUND y status.

ICS:

POST /api/ops/ics/sync?aircraftId= (v1 manual); v2 cron 5–10 min por aeronave.

Operación:

GET /api/health (DB+Redis), GET /api/version.

4.4 Integraciones
Área	Proveedor	Uso
DB	Supabase (Postgres)	Datos core; pooler 6543 (app); 5432 (migraciones)
Cache/Locks	Redis (Upstash)	Holds TTL, rate-limit, idempotencia
Pagos	Wompi	Payment Link + webhook firmado
Mensajería	Chatrace/WA	Templates outbound + webhook inbound
Analytics	GA4	Eventos ecommerce y lead
5. Requisitos no funcionales
5.1 Rendimiento y disponibilidad

Latencia p95 API pública: ≤ 300 ms (sin picos).

Caducidad de hold: configurable (p.ej., 10–30 min).

Resiliencia a reintentos de webhooks (idempotencia estricta).

5.2 Seguridad y cumplimiento

CORS: https://www.skyride.city, https://booking.skyride.city, https://*.vercel.app (preview).

CSP: default-src 'self'; script-src 'self' vercel.app booking.skyride.city; connect-src api sky...;.

TLS: Supabase exige SSL; sslmode=require.

Idempotencia: header Idempotency-Key en holds; tabla/log en Redis/DB.

Rate-limit: 5 req/min en holds y quotes.

PII: mínimo necesario; hash/cifrado para tokens; logs sin datos sensibles.

5.3 Observabilidad

Logs estructurados (request_id, user_agent, ip).

Métricas: ratio 2xx/4xx/5xx, latencia, expiración holds, retry webhooks.

Alertas: webhook fallido, caídas de Redis/DB, tasa de error > 2%.

6. Arquitectura y datos
6.1 Vista lógica

Frontend SPA (Vercel) consume Backend FastAPI (Render/Railway).

DB Supabase (schemas: operators, aircraft, routes, listings, pricebook, slots, quotes, holds, bookings, customers, message_logs, webhook_events, event_logs).

Redis: keys hold:{slot}, idemp:{key}, RL rl:{route}:{ip}.

6.2 Entidades (resumen)

Operator: datos y preferencias; pricing floor; métricas de desempeño.

Aircraft: registration, modelo, seats, ics_url, ics_last_sync.

Route: origin, destination.

Listing: relación operator/aircraft/route; tipo (CHARTER/SEAT/EMPTY_LEG).

PriceBook/Surcharge: base + recargos.

Slot: start, end, status, source (PORTAL/ICS/GOOGLE).

Quote: token, pax, fechas, breakdown, expiración.

Hold: status, expiresAt, depositAmount.

Booking: status (PENDING/PAID/CANCELED), amounts, bookingNumber.

Customer: email/phone, preferencias.

MessageLog: OUTBOUND/INBOUND; WA id; payload.

WebhookEvent: idempotencia y auditoría.

EventLog: trazabilidad de acciones.

6.3 Reglas clave

Locks: Redis SET key value NX PX ttl + release con script Lua.

Conflictos: si dos holds compiten por mismo slot → 1 éxito, 1 409.

Wompi: HMAC del raw body con secret; marcar PAID una sola vez.

7. API (contratos resumidos)

Nota: ejemplos concisos; las descripciones largas viven en la doc de referencia del repo.

POST /api/quotes
Request: { origin, destination, aircraftType?, pax, date? }
Response: { quoteId, token, breakdown: { base, serviceFee, itbms, total }, expiresAt }

POST /api/holds
Headers: Idempotency-Key
Request: { quoteId | registration+start+end, pax }
Response: { holdId, expiresAt, status }
Errores: 409 (conflicto), 429 (rate-limit), 422 (validación)

GET /api/availability
Query: aircraftId, dateRange=YYYY-MM-DD..YYYY-MM-DD
Response: [ { start, end, status, source } ]

POST /api/ops/slots
Body: { aircraftId, start, end, status, source, notes? } → upsert.

POST /api/ops/ics/sync?aircraftId=
Ejecución manual (v1) → crea/actualiza slots con source="ICS".

POST /webhooks/wompi
Valida firma HMAC; idempotente; transición a PAID.

POST /api/wa/send-template
Body: { to, templateName, params[] } → registra en MessageLog OUTBOUND.

POST /webhooks/wa
Registra INBOUND/status.

GET /api/health
{ db: bool, redis: bool, status: "ok" }

8. Analítica (GA4)
8.1 Eventos y momentos
Evento	Momento	Params clave
view_item	Vista Hosted Quote	items[] (item_id, item_name, price)
add_to_cart	Creación hold	items[], value, currency
begin_checkout	CTA pagar	value, currency
add_payment_info	Redir a Wompi	payment_type
purchase	Webhook APPROVED	transaction_id, value, currency
generate_lead	Click-to-Chat WA	lead_type="whatsapp"
9. Entregables por release
9.1 v2.0 (cerrado para demo)

Criterios de aceptación: CI verde, health ok, holds TTL, Wompi firmado/idempotente, WA outbound+inbound, widget, ICS v1 manual, docs y GO_LIVE completos.

9.2 v2.1

/ops con bandeja + calendario CRUD + viewer PriceBook + analytics.

ICS cron + UI para icsUrl.

Widget docs listas; Empty legs v1 (flag OFF).

QA con escenarios multi-operador.

9.3 v2.2

Empty legs seats (prorrateo, seatsRemaining).

Yappy (toggle de pasarela).

Dashboards GA4/KPIs.

10. Requisitos de diseño (Brand/UI)

Brand: Navy #152c46, Blue #4670b5; Tipografía Open Sans.

UI: shadcn/ui; Tailwind; bordes rounded-2xl, espacios generosos; CTA primario Navy; diseño claro de desglose de precios.

Accesibilidad: contraste AA, labels/aria en inputs, focus visible.

11. Entornos y despliegue
Entorno	Lugar	Notas
Local	Docker compose (Postgres/Redis)	Dev rápido
Staging	Backend (Render/Railway), Frontend (Vercel)	CORS/preview
Producción	Backend (Render/Railway/Fly), Frontend (Vercel)	Dominios booking.skyride.city + www.skyride.city

Vercel

Root Directory: frontend

Build: npm run build

Output: build

ENV: REACT_APP_BACKEND_URL

Backend

DATABASE_URL (pooler 6543 + SSL)

DATABASE_URL_MIGRATIONS (5432 + SSL)

REDIS_URL (TLS)

CORS_ORIGINS, WOMPI_*, CHATRACE_*

12. Seguridad y compliance

Rotación de secretos cada 90 días.

Política de reintentos segura para webhooks (registro en WebhookEvent).

Sanitización de logs (sin PII sensible).

Backups: pg_dump diario + restore probado.

13. QA y pruebas
13.1 Escenarios mínimos

Carrera de holds sobre mismo slot (1 gana, 1 409).

Expiración TTL → disponibilidad vuelve.

Wompi sandbox APPROVED → purchase GA4 y booking PAID una vez.

WA: envío plantilla + recepción inbound.

ICS: sync de una aeronave con eventos solapados (upsert correcto).

Widget: crea quote, hold, dispara eventos GA4.

14. Riesgos y mitigaciones
Riesgo	Mitigación
Saltos directos al operador	Ofrecer OS /ops + SLA + deals exclusivos
Fail webhook pagos	Idempotencia + retries + alertas
Datos ICS inconsistentes	De-dupe por UID + merge conservador
Sobreventa seats	Locks Redis + checks antes de purchase
Wompi/Yappy caída	Toggle pasarela + fallback WA pay link
15. Supuestos y dependencias

Operadores proporcionan icsUrl o cargan slots manualmente.

PriceBook y surcharges están definidos por ruta/aircraft_type.

WhatsApp plantillas aprobadas en Chatrace.

Supabase/Redis disponibles con SSL.

16. Pendientes (open questions)

Política exacta de cancelaciones y reembolsos (Wompi).

RLS/Auth de Supabase para multi-tenant en /ops (mapa operator_id ↔ usuario).

Definición final de surcharges por aeropuerto y tasas locales.

17. Anexos (artefactos de entrega)

Postman/Thunder: colección de endpoints.

CSV templates: operators, aircraft, pricebook, surcharges, slots.

Seed SQL mínimo: demo “Panamá” (op, 2 aeronaves, 2 slots).

vercel.json/_redirects: rewrites SPA.