# AI Vocal Trainer — Mobile (Expo)

React Native + Expo app. Record a song, tell the app which track it was,
upload to the backend, and get AI coaching.

## Setup

```bash
cd mobile
npm install
```

## Configure backend URL

In `app.json` edit `expo.extra.apiBaseUrl`.

- iOS simulator: `http://localhost:8000`
- Android emulator: `http://10.0.2.2:8000`
- Real device (Expo Go on phone): `http://<your-LAN-IP>:8000`
  (run `ipconfig getifaddr en0` on macOS, then start the server with
  `uvicorn app.main:app --host 0.0.0.0 --port 8000`)

## Run

```bash
npx expo start
```

Press `i` for iOS simulator, `a` for Android, or scan the QR code with
Expo Go on your phone.

## Microphone permission

The first time you hit "録音開始", the OS asks for mic permission. If you
deny it, open system settings and re-enable it for Expo Go / the app.
