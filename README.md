# NEURAW — магазин цифровых услуг

Mobile-first visual prototype for a future Telegram Mini App. Open `index.html` in a browser. The UI is a demo: forms do not submit, payment and order storage are not connected.

## Portfolio samples

All files under `assets/` are original demonstration concepts created for this project; they are **not customer cases**.

- `cover-concept.png`: fictional release artwork with added typography.
- `photoshoot-concept.png`: fictional adult model; demonstrates a visual style, not identity-preserving editing of a real customer.
- `video-concept.mp4`: five-second motion ad from an original still; demonstrates compositing and motion, not multi-shot generative video.
- `photo-motion-concept.mp4`: ten-second camera movement on an original portrait; it does **not** demonstrate lip sync or a speaking portrait.
- `music-sketch.mp3`: original instrumental sketch, not a completed custom song or voice clone. Source: `make_audio.py`.

No voice-cloning sample is included. Create one only with the speaker's documented permission. Do not advertise unavailable examples as completed client work.

## Next implementation

1. Replace demo form with a Telegram Mini App frontend using `Telegram.WebApp.initData` and server-side signature/age verification.
2. Save orders and service briefs in a database; notify admins and provide status updates.
3. Agree on prices and turnaround per product before enabling checkout. Telegram digital services sold inside bots use Stars, with a pre-checkout acknowledgement and a verified successful-payment update.
4. Add original completed examples for a custom song, speaking photo, and voice work before promoting those formats.
5. Test the full purchase, delivery, revision, support, and refund paths on mobile.

This is a separate project. Do not place shop code in the existing Gifts Intelligence subscription bot repository.
