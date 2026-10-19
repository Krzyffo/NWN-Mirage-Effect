# NWN-Mirage

Desert heat haze and mirages for Neverwinter Nights: Enhanced Edition.

- **Shimmer:** distant ground and the horizon ripple like hot air. The effect grows with distance, so nearby things stay sharp.
- **Blur:** the hot distant air goes soft as well as rippling. The mirage water is blurred most.
- **Mirage water:** far ground just below the horizon mirrors the sky, like a lake that isn't there.
- **Follows the sun:** none at night, building up through the morning, strongest from 11:00 to 16:00.
- **Per area:** set by area variables. Interiors never get it.

It's a full-screen shader (`src/shaders/fsfbpostpr.shd`) that replaces the game's final post-processing pass. Beamdog's own pass still runs first, so sharpen, depth of field, vibrance and gamma keep working, and the mirage is added on top. Scripts control it through the `SetShaderUniform*` functions.

## Setup in a module

1. Get the two files: download `nwn_mirage.hak` and `nwn_mirage.erf` from the [latest release](https://github.com/Krzyffo/NWN-Mirage-Effect/releases/latest), or build them yourself (see [Building](#building)).
2. Copy `nwn_mirage.hak` into your NWN `hak` folder (normally `Documents\Neverwinter Nights\hak`). Then in the toolset, add it: Module Properties > Custom Content > add `nwn_mirage`.
3. Import the scripts: File > Import > `nwn_mirage.erf`.
4. Module Properties > Events:
   - **OnClientEnter:** `mirage_enter`. If the module already has a script there, add `ExecuteScript("mirage_enter", GetEnteringObject());` to it instead.
   - **OnPlayerChat** (optional, for testing): `mirage_chat`. If the module already has a script there, add `ExecuteScript("mirage_chat", OBJECT_SELF);` to it instead.
5. For each desert area: Area Properties > Advanced > Variables:

| Variable | Type | Default | Meaning |
|---|---|---|---|
| `MIRAGE` | float | - | Strength 0-1. Required; without it, the area has no mirage |
| `MIRAGE_NEAR` | float | 10 | Metres where the shimmer starts |
| `MIRAGE_FAR` | float | 40 | Metres where it is full strength; the mirage water lies beyond |
| `MIRAGE_WATER` | float | 0.6 | Mirage water strength 0-1 |
| `MIRAGE_BLUR` | float | 0.5 | Blur of the distant air 0-1; -1 = none (0 reads the same as unset) |
| `MIRAGE_ALLDAY` | int | 0 | 1 = ignore the time of day |

6. Build Module and save.

## Testing

Chat commands (with `mirage_chat` set up):

| Command | Effect |
|---|---|
| `/mirage` | Show the strength the player sees now |
| `/mirage 0.7` | Force a strength everywhere, any time of day |
| `/mirage off` | Force it off |
| `/mirage area` | Back to the area's own settings |
| `/mirage blur 0.8` | Force the blur (0-1); `/mirage blur area` to undo |
| `/mirage debug` | Debug view: red = shimmer, blue = mirage water |

Look out across a large open area. The effect is about distance, so it needs a view of 40 m or more.

If nothing changes at all, the game probably isn't running the post-processing pass. Turn on any post-processing effect in Options > Graphics (for example Vibrance or Sharpen) and try again. If the screen goes black or looks broken, the shader failed to compile on your graphics card: the error is in `nwclientLog1.txt` in your NWN user folder (the `logs` folder).

## Building

1. Unzip the [neverwinter.nim](https://github.com/niv/neverwinter.nim/releases) release for your system into `tools/neverwinter/`. The script compiler comes from it.
2. Run:

   ```bash
   py tools/build.py
   ```

   It writes `nwn_mirage.erf` and `nwn_mirage.hak` next to the script, in `tools/`. Copy the hak to your `hak` folder yourself; the build doesn't install anything.

The compiler needs your game's install folder. The build finds it in your Steam libraries. For a GOG or Beamdog copy, or if detection fails, name the folder that contains `data`:

```bash
py tools/build.py --nwn-root "C:\path\to\Neverwinter Nights"
```

Setting the `NWN_ROOT` environment variable to that folder works too.

To see what's inside a built file, run `py tools/build.py --list tools/nwn_mirage.hak`.

## Repository

- `src/shaders/`: the shader, packed into the hak.
- `src/nss/`: the control scripts: `mirage_inc` (area settings → shader), `mirage_enter` and `mirage_loop` (per-player update every 2 s), `mirage_chat` (test commands).
- `tools/build.py`: compiles the scripts and packs `nwn_mirage.erf` and `nwn_mirage.hak` next to itself (see [Building](#building)).
- `reference/` (not committed): Beamdog's stock shaders, extracted from the game for study.
