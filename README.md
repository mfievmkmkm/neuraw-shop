# NEURAW — магазин цифровых услуг

Mobile-first Telegram Mini App. The shop accepts briefs, stores orders in SQLite, notifies the admin in Telegram, and tracks order status. Payment is not enabled; cost and timing are agreed before work begins.

## Deploy on Railway

Create a **separate** Railway service from this repository using the Dockerfile. Add a persistent volume mounted at `/data`. Set the four environment variables shown in `.env.example`; `SHOP_BOT_TOKEN` is a **new shop bot's** BotFather token, `SHOP_ADMIN_ID` is your numeric Telegram user ID, and `SHOP_WEBAPP_URL` is the service's public HTTPS URL with a trailing slash. Do not commit real secrets. Run one replica only: the server uses Telegram long polling and a local SQLite volume.

Start the bot in Telegram. The chat catalog is the primary path, and **Открыть витрину** opens the Mini App. A customer submits a brief; the admin gets a message with **В работу / Готово / Отменить** buttons. The customer gets a status message, and can check **Мои заявки** in the app or `/my` in the bot. If the admin notification fails temporarily, the order stays in SQLite; check the server log and the database before following up.

## Shop in the bot chat

`/start` or `/shop` opens a native Telegram catalog with five sections and 17 services. Each service has a short description, a starting price and a **Оставить заявку** button. A short picker helps customers choose by result. The bot collects a brief and optional deadline, then uses the same order database and admin notifications as the Mini App. `/cancel` leaves an unfinished brief. Drafts in the chat live in process memory and are lost on restart; completed orders remain in SQLite.

All listed prices are **proposed starting prices in RUB**, editable in `CATALOG` in `server.py`. They are not a firm quote or an invoice. Approve them before advertising the shop widely. Telegram may render the supported button styles differently across clients; custom emoji icons need the actual emoji IDs and an eligible bot owner.

## How to fulfil an order

1. In the admin chat, read the brief and press **В работу** once you accept it. Send `/orders` to see the 15 most recent orders.
2. Ask for any missing details with `/reply 12 Пришлите логотип и референсы` (replace `12` with the order number). The customer sends text beginning `#12 `, or a photo, document, video or audio with `#12` in its caption. The bot verifies order ownership and forwards it to the admin.
3. Agree on scope, price, deadline and included revision before beginning: `/quote 12 Обложка 1500 ₽, 2 дня, одна небольшая правка. Оплату обсудим отдельно.` This is a message, **not an invoice or payment confirmation**.
4. Produce the deliverable using your tools and review it yourself. Send the final file to your admin bot chat with caption `/deliver 12`; the bot copies that file to the customer. Press **Готово** after delivery.
5. Keep the brief, agreed terms and delivered files for support. Only use people's images or voices with their permission.

These commands are an initial operator workflow, not an automated production service. The shop accepts and tracks requests; you create and quality-check each result.

Local check: `python -m unittest discover -v`. The app requires Python 3.12 and uses only its standard library. A plain browser can preview the storefront, but order submission requires valid Telegram Mini App `initData`.

## Portfolio samples

All files under `assets/` are original demonstration concepts created for this project; they are **not customer cases**.

- `cover-concept.png`: fictional release artwork with added typography.
- `flower-cover-v2.png`: new original fictional cover direction.
- `site-demo.html`: a responsive working landing page concept for a fictional brand.
- `photoshoot-concept.png`: fictional adult model; demonstrates a visual style, not identity-preserving editing of a real customer.
- `video-concept.mp4`: five-second motion ad from an original still; demonstrates compositing and motion, not multi-shot generative video.
- `photo-motion-concept.mp4`: ten-second camera movement on an original portrait; it does **not** demonstrate lip sync or a speaking portrait.
- `music-sketch.mp3`: original instrumental sketch, not a completed custom song or voice clone. Source: `make_audio.py`.

No voice-cloning sample is included. Create one only with the speaker's documented permission. Do not advertise unavailable examples as completed client work.

## Next implementation

1. Agree on prices, revisions and turnaround per product before enabling checkout.
2. Add file intake, admin order history and reliable notification retries.
3. Add original completed examples for a custom song, speaking photo, and voice work before promoting those formats.
4. Test the full purchase, delivery, revision, support, and refund paths on mobile. Telegram digital services sold inside bots need a suitable Stars checkout flow.

This is a separate project. Do not place shop code in the existing Gifts Intelligence subscription bot repository.
