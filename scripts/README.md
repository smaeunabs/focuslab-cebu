# Google review auto-updater

`update-google-reviews.py` pulls the live rating + review count for FocusLab
from Google (Places API) and rewrites the two spots in `index.html` that
show it: the visible "★★★★★ 4.9 · 10 Google reviews" widget and the
`aggregateRating` JSON-LD block. If the numbers changed, it commits and
pushes, which triggers Vercel to redeploy.

## One-time setup

1. **Get an API key.** console.cloud.google.com -> create/select a project ->
   APIs & Services > Library -> enable **Places API (New)** -> APIs &
   Services > Credentials -> Create Credentials > API key. Restrict it to
   Places API (New) only. This is free at this call volume (one call a
   week, well under the monthly free credit).
2. **Set up `.env`.** In the repo root:
   ```
   cp .env.example .env
   ```
   Paste the API key into `GOOGLE_PLACES_API_KEY`.
3. **Find the Place ID** (once):
   ```
   python3 scripts/update-google-reviews.py --find-place-id
   ```
   Copy the correct `id` into `.env` as `GOOGLE_PLACE_ID`.
4. **Dry run** to confirm it reads correctly without changing anything:
   ```
   python3 scripts/update-google-reviews.py --dry-run
   ```
5. **Real run** (updates the file, commits, pushes if numbers changed):
   ```
   python3 scripts/update-google-reviews.py
   ```

## Scheduling it for every Saturday (runs locally, e.g. via Claude Code)

macOS's `cron` is deprecated in favor of `launchd`. Create
`~/Library/LaunchAgents/com.focuslab.review-sync.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.focuslab.review-sync</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/python3</string>
    <string>/Users/sheilamaeunabia/focuslab-cebu/scripts/update-google-reviews.py</string>
  </array>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Weekday</key>
    <integer>6</integer> <!-- 0 = Sunday ... 6 = Saturday -->
    <key>Hour</key>
    <integer>9</integer>
    <key>Minute</key>
    <integer>0</integer>
  </dict>
  <key>StandardOutPath</key>
  <string>/tmp/focuslab-review-sync.log</string>
  <key>StandardErrorPath</key>
  <string>/tmp/focuslab-review-sync.log</string>
</dict>
</plist>
```

Then load it:
```
launchctl load ~/Library/LaunchAgents/com.focuslab.review-sync.plist
```

This runs every Saturday at 9:00am (only while your Mac is on/awake at that
time; if it's asleep, launchd runs it at the next wake). Check
`/tmp/focuslab-review-sync.log` to confirm it ran and what it did.

To unload/stop it:
```
launchctl unload ~/Library/LaunchAgents/com.focuslab.review-sync.plist
```

## Why this can't run from Cowork itself

This script needs to `git push` to deploy, which requires your local
GitHub credentials — those only exist on your machine, not in Cowork's
sandbox. That's why the schedule above runs locally (via `launchd`, or you
can ask Claude Code to run `python3 scripts/update-google-reviews.py` for
you each Saturday instead of using launchd, if you'd rather trigger it by
hand/chat).
