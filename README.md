# NEURAW — магазин цифровых услуг

Mobile-first Telegram Mini App. The shop accepts briefs, stores orders in SQLite, notifies the admin in Telegram, and tracks order status. Payment is not enabled; cost and timing are agreed before work begins.

## Deploy on Railway

Create a **separate** Railway service from this repository using the Dockerfile. Add a persistent volume mounted at `/data`. Set the four environment variables shown in `.env.example`; `SHOP_BOT_TOKEN` is a **new shop bot's** BotFather token, `SHOP_ADMIN_ID` is your numeric Telegram user ID, and `SHOP_WEBAPP_URL` is the service's public HTTPS URL with a trailing slash. Do not commit real secrets. Run one replica only: the server uses Telegram long polling and a local SQLite volume.

Start the bot in Telegram. Its **Открыть магазин** button opens the Mini App. A customer submits a brief; the admin gets a message with **В работу / Готово / Отменить** buttons. The customer gets a status message, and can check **Мои заявки** in the app or `/my` in the bot. If the admin notification fails temporarily, the order stays in SQLite; check the server log and the database before following up.

Local check: `python -m unittest discover -v`. The app requires Python 3.12 and uses only its standard library. A plain browser can preview the storefront, but order submission requires valid Telegram Mini App `initData`.

## Portfolio samples

All files under `assets/` are original demonstration concepts created for this project; they are **not customer cases**.

- `cover-concept.png`: fictional release artwork with added typography.
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
