# Plume UI Redesign Roadmap

This document is the plan we are executing. It started from a Codex audit of the current tkinter surfaces; it has been edited down to decisions, tokens, and phased work. Open questions are listed at the bottom — answer them before the phase that depends on them.

## Goals

- Make Plume look like a 2026 productivity tool, not a 1990s utility.
- Keep the floating widget unobtrusive, legible over arbitrary backgrounds, and never focus-stealing on Windows.
- Add a real error visual state (today the product has 4 states on paper but only 3 on screen).
- Centralize colors, fonts, and spacing so the three surfaces stop drifting.

## Non-goals

- No PyQt, no Electron, no web view.
- No new heavy dependency in phase 1. customtkinter is a fallback for dialogs only, considered after the ttk pass.
- No rework of product behavior (modes, hotkey, capture/replace flow, prompts).

## Decisions

1. Render the floating widget entirely with Pillow into a PhotoImage on a Canvas. Already depends on Pillow, gives antialiased rings/arcs, best perceived-quality jump per hour.
2. Modernize settings and wizard with ttk.Style plus a small local theme helper. Reconsider customtkinter only if the result is still weak.
3. Ship dark theme only for now. Light theme tokens stay in the file as future work.
4. Do not grow the widget window to 72px for a drop shadow. Windows color-key transparency is binary, so a soft shadow will halo or vanish. Ship without an external shadow; rely on ring + contrast. Revisit Linux-only shadow after phase 1 lands.
5. Keep all 5 mode labels as text (FR, EN, F>E, E>F, T~). Decide T~ vs T in phase 1 once we see the Pillow-rendered version at real size.
6. Keep native tk.Menu for the right-click popup and tray. Replacing the popup risks focus theft on Windows; not worth it before the bigger wins land.
7. Preserve all current platform tricks: overrideredirect, -topmost, Windows -transparentcolor, WS_EX_NOACTIVATE, Linux X11 shape mask.

## Current UI inventory (reference)

From `plume/widget.py`, `plume/settings.py`, `plume/wizard.py`, `plume/tray.py`, `plume/app.py`.

Floating widget:

- Size `52x52`, bg key `#0d0d0d`, alpha `0.82` idle / `1.0` hover.
- Ring `3px`, outer pad `5px`, two stacked ovals on a Canvas.
- Font `("Arial", 14, "bold")`, label `#ffffff`.
- Mode colors (ring / fill / hover):
  - FR `#6366f1` / `#312e81` / `#3730a3`
  - EN `#2563eb` / `#1e3a8a` / `#1e40af`
  - F>E `#d97706` / `#78350f` / `#92400e`
  - E>F `#7c3aed` / `#3b0764` / `#4c1d95`
  - T~ `#0d9488` / `#134e4a` / `#115e59`
- Busy: fill `#1e1b4b`, label `"..."`, font 18, pulse `90ms`, cycles through `#ffffff`.
- Success: fill `#059669`, ring `#34d399`, check mark, 1500ms hold.
- Error: no visual state — collapses to `set_idle()`.

Settings/wizard:

- Bg `#1e1e2e`, text `#cdd6f4`, entry bg `#313244`, primary `#6366f1`, secondary `#45475a`.
- Hard-coded Arial: headings 16/18 bold, body 11, labels 10, helper 9.
- Settings width `440`, wizard `480x340`, both `padx=30, pady=20`.
- Entries `relief="flat"`, `ipady=4`. Buttons `padx=12-14, pady=6`. Listbox `height=4`, no padding/border.
- Standard OS-decorated Toplevels.

Tray: plain 64x64 Pillow ellipse, fill `#4a90e2`. No branding, no state.

## Why it feels dated

- Widget alpha 0.82 makes the label itself translucent — modern floating tools keep text crisp.
- 3px hard ring + flat fills + no antialiasing on a 52px object reads as a status LED.
- 90ms white-flash busy pulse feels like a mechanical indicator, not progress.
- No error state at all.
- Arial 14 bold is cramped, especially for `F>E` / `E>F`.
- Dialogs are vertical stacks of raw tk widgets with no grouping, no hierarchy, no hover/focus states.
- Single purple-blue slab background with insufficient contrast between surface layers.
- Inputs: no border, no radius, no horizontal padding, only `ipady=4`.
- Tray icon is an unbranded blue dot.

## Design tokens (locked for phase 1)

Colors:

```text
app-bg              #0B0D12
surface             #11141B
surface-elevated    #181C25
surface-hover       #202636
border              #2A3142
border-strong       #3A4358
text-primary        #F4F7FB
text-secondary      #A8B0C2
text-muted          #747E94
danger              #F87171
success             #34D399
warning             #FBBF24
```

Mode accents (ring / deep fill), restyled but semantically preserved:

- FR `#7C83FF` / `#252A63`
- EN `#4C9DFF` / `#173B68`
- F>E `#F5A524` / `#4A3415`
- E>F `#B07CFF` / `#352052`
- T~ `#2DD4BF` / `#123F3B`

Typography (resolved at runtime via `tkinter.font.families()` with first-match fallback):

- Windows stack: `Segoe UI Variable`, `Segoe UI`, `Arial`, `sans-serif`.
- Linux stack: `Ubuntu`, `Noto Sans`, `DejaVu Sans`, `Arial`, `sans-serif`.
- Widget label: 12-13px, weight 700.
- Dialog heading: 18px, weight 700. Section heading: 13px, weight 700.
- Body: 11-12px regular. Field labels/helper: 10px regular `text-secondary`.

Spacing scale: `4, 8, 12, 16, 20, 24, 32`. Dialog outer padding `24`. Label-to-input `6`, field-to-field `14`. Button padding `14-16` x `8-10`.

Radius scale: widget `999`, controls `10`, panels `14`, chips `8`. Native tk widgets cannot radius — use Pillow for the widget and accept rectangular ttk controls (with modern spacing/colors) for dialogs.

## Phase plan

Each phase is a self-contained change that ships value on its own. Do not start a phase until the previous one is reviewed in the app.

### Phase 1 — Floating widget rebuild (biggest win)

- Create `plume/theme.py` with color tokens, font picker, spacing constants, mode color map.
- Rewrite the widget renderer in `plume/widget.py` to draw into a Pillow `Image` at 3x scale, downsample with LANCZOS, blit via `ImageTk.PhotoImage` onto the Canvas.
- Neutral deep fill (`surface`), mode color as a thin 2px ring, label in `text-primary` at full opacity.
- Drop widget alpha to 1.0 — translucency was hurting readability. Achieve "subtle" via color choice, not alpha.
- Idle / hover / busy / success / error all rendered through the same Pillow pipeline.
  - Busy: mode-colored rotating arc, 900ms cycle, eased with `t*t*(3-2*t)`. No white flashing.
  - Success: emerald tint + check, 180ms in / 650ms hold / 250ms out.
  - Error: red tint + `!`, 180ms flash, 220ms two-step shake, 900ms hold, return idle. Wire this in `app.py` where errors currently fall through to `set_idle()`.
- Decide T~ vs T after seeing the new rendering at real size.
- Preserve overrideredirect, -topmost, transparent color key, WS_EX_NOACTIVATE, X11 shape mask. Window stays at 52px (no shadow growth — see decision 4).

Acceptance: widget looks visibly modern on both Linux and Windows. Error state is reachable from a forced FixerError. No regression on focus behavior in Windows.

### Phase 2 — Theme module + dialog cleanup pass

- Move all `_BG`, `_FG`, `_ENTRY_BG`, `_PRIMARY`, `_SECONDARY` constants out of `settings.py` and `wizard.py` into `theme.py`.
- Apply ttk.Style globally: TButton, TEntry, TLabel, TFrame, TListbox where possible.
- Widen settings to 520-560px, outer padding 24, field gaps per spacing scale.
- Group fields into sections with section headings and muted helper text.
- Replace yellow warning emoji block in tones section with a compact muted callout: border `#4A3A18`, bg `#1F1A10`, text `#E6C76E`.
- Tones list: bordered surface, row padding 10x8, selected row fill `surface-hover`, teal accent strip on active tone.

Acceptance: settings dialog has clear hierarchy and consistent spacing. All color/font literals come from `theme.py`.

#### Codex Review

Phase 2 is cleaner than the original UI, but the settings page still reads old because it remains a raw Tk form with a dark skin. The screenshot shows several dated signals: the font appears bitmap-like or has fallen back to `TkDefaultFont`, the entries are sharp 1px bordered rectangles, the tones area still uses a visibly native `Listbox`, the all-caps section labels feel more like terminal/admin UI than a polished productivity app, and the secondary buttons read as old desktop/HTML controls. The titlebar also clashes with the app theme, which makes the whole dialog feel less intentionally designed. The next pass should fix typography first by forcing a modern fallback such as `Noto Sans`, `DejaVu Sans`, `Ubuntu`, or `Segoe UI`, replace the tones `Listbox` with custom padded rows, avoid native-looking `tk.Button` for the main actions, wrap entries in taller padded control containers with focus borders, and shift the layout from a simple vertical form into grouped settings panels. If the goal is the fastest visible jump for settings and wizard, customtkinter is now worth reconsidering for dialogs while keeping the floating widget Pillow-rendered.

#### Codex Phase 2 Implementation

Codex moved Phase 2 from a lightly themed Tk form to a deliberately composed customtkinter settings sheet. The settings window is now a fixed `640x720` frameless modal with a custom Plume titlebar, draggable header, close control, app-owned border, and no native Linux titlebar color clash. The content was reorganized into two rounded cards instead of one long vertical stack: a `Connexion` card for API URL/key/model/hotkey, and a `Tons personnalisés` card for tone management. The model and hotkey fields now sit in a two-column row to reduce height and improve scanability; all entries use `CTkEntry` at `38px` height with tokenized colors, borders, radius, and modern font sizing. The tones area no longer uses a native `Listbox`; it is a `CTkScrollableFrame` with custom `38px` rows, hover states, selected row state, and a teal active-tone dot. Tone actions were moved into the card header, and the warning was kept as a compact rounded callout inside the card. Typography fallback was also hardened: if Tk cannot detect a modern installed family, Linux now falls back to `DejaVu Sans` and Windows to `Segoe UI` instead of `TkDefaultFont`, because that bitmap/default fallback was one of the strongest "old app" signals. Verification run: `uv run ruff check plume/settings.py plume/theme.py`, `uv run mypy plume/settings.py plume/theme.py`, `uv run python -m compileall plume/settings.py plume/theme.py`, selected tests `tests/test_config.py tests/test_notifier.py`, and a brief local tkinter instantiation of `SettingsDialog`.

#### Codex Regression Fix

Claude's follow-up compressed the settings dialog from `640x720` to `640x660` without removing enough content, so the bottom of the sheet clipped: the footer actions and warning callout could fall below the visible window. It also made the tones list a `CTkScrollableFrame` unconditionally, which produced an ugly scrollbar even for one or two tones and made the list feel broken. Codex restored the stable `640x720` window height, replaced the unconditional scrollable tones list with a fixed-height `CTkFrame` for one or two tones, and only switches to `CTkScrollableFrame` when there are more than two tones. The tones list is now `104px` high, keeps the custom `38px` rows, removes the needless scrollbar in the common case, and rebuilds the container automatically if the tone count crosses the scroll threshold after adding or deleting tones. Verification run: `uv run ruff check plume/settings.py plume/theme.py`, `uv run mypy plume/settings.py plume/theme.py`, `uv run python -m compileall plume/settings.py plume/theme.py`, plus a brief runtime instantiation of `SettingsDialog`.

#### Codex Radius Fix

The rounded corners introduced through customtkinter looked visibly jagged/notched on Linux/X11, especially on the outer shell, cards, entries, buttons, tones list, callout, and tone rows. Codex removed the dialog radii at the theme-token level by setting `R_PANEL`, `R_CONTROL`, and `R_CHIP` to `0`, while keeping `R_PILL` available for true circular/pill surfaces elsewhere. The result is intentionally square, cleaner, and more consistent than broken antialiased corners. Verification run: `uv run ruff check plume/settings.py plume/theme.py`, `uv run mypy plume/settings.py plume/theme.py`, `uv run python -m compileall plume/settings.py plume/theme.py`, and a screenshot pass of the square-corner dialog.

#### Codex Tone Editor Fix

The custom tone editor was still the weakest surface after the settings redesign: it used the same frameless shell but felt like an unfinished leftover modal, with stacked labels, a large textbox, weak hierarchy, and footer controls that could be swallowed by the expanding content area. Codex rebuilt `ToneEditor` as a compact `560x500` modal that matches the settings sheet: app-owned titlebar, square-corner shell, clear heading, short helper text, one elevated form card, `Nom affiché` entry, `Instruction` textbox, example helper copy, and a reserved footer strip with `Annuler` and `Enregistrer`. The footer is now packed before the expandable form card so the buttons always stay visible. `ToneEditor` also uses the shared `_center()` helper for predictable placement after the layout is built. Verification run: `uv run ruff check plume/settings.py plume/theme.py`, `uv run mypy plume/settings.py plume/theme.py`, `uv run python -m compileall plume/settings.py plume/theme.py`, and screenshot checks before/after the footer reservation fix.

### Phase 3 — First-run wizard refresh

- Reuse phase 2 components.
- Add top progress indicator (three 6px dots or thin segmented bar).
- Done step shows a success circle rendered via Pillow, not just text.
- Plain button labels: `Continue`, `Back`, `Save`, `Launch Plume`. No arrows in text.
- Bump to 520x380 if needed for the new padding.

Acceptance: wizard feels like the same product as the redesigned settings.

### Phase 4 — Tray icon refresh

- Generate a branded tray icon with Pillow: dark circle `surface`, 2px indigo accent ring, white `P` glyph.
- Keep pystray's native menu — OS-native tray menus are expected.

Acceptance: tray icon reads as Plume, not a generic blue dot.

### Phase 5 (optional, deferred) — Stretch

- Linux-only soft shadow behind the widget (Pillow shadow PNG in a larger Toplevel, shape mask updated to cover shadow).
- Light theme tokens wired up + setting to toggle.
- Custom popup Toplevel to replace tk.Menu, only if dialog/widget polish exposes the menu as the remaining weak link. Must not steal focus on Windows.

Do not start phase 5 unless phases 1-4 are shipped and someone explicitly asks for more.

## Risks and things to validate

- X11 shape mask: if the widget window size ever changes, regenerate the pixmap or you get clickable square corners. Test before committing any size change.
- Windows -transparentcolor is binary. Never antialias edges into the key color — render the transparent margin as the exact key color, the visible circle as solid pixels.
- ttk theming parity across Linux distros is famously inconsistent. Budget real time for phase 2; accept imperfect parity with Windows. If results disappoint, evaluate customtkinter for dialogs only.
- `Image`/`PhotoImage` lifetime in Tk: keep references on the widget instance or images get garbage-collected and disappear.
- Re-applying WS_EX_NOACTIVATE: if the root or any Toplevel is recreated, the flag must be re-set.
- PyInstaller bundle size: phase 1-4 add no new deps. Track bundle size before/after anyway.

## Open questions

- T~ or T for the rewrite-tone label? Decide after seeing the new Pillow render in phase 1.
- Do we want a Linux-only widget shadow at all, or is phase 5 wasted effort? Decide after phase 1 ships.
- Light theme: ship in phase 5, or never? No user has asked for it yet.
