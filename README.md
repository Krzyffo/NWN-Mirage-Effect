# NWN-Mirage

Desert heat haze and mirages for Neverwinter Nights: Enhanced Edition.

- **Shimmer:** distant ground and the horizon ripple like hot air. The effect grows with distance, so nearby things stay sharp.
- **Mirage water:** far ground just below the horizon mirrors the sky, like a lake that isn't there.
- **Follows the sun:** none at night, building up through the morning, strongest from 11:00 to 16:00.
- **Per area:** set by area variables. Interiors never get it.

It's a full-screen shader (`src/shaders/fsfbpostpr.shd`) that replaces the game's final post-processing pass. Beamdog's own pass still runs first, so sharpen, depth of field, vibrance and gamma keep working, and the mirage is added on top. Scripts control it through the `SetShaderUniform*` functions.

## Setup in a module

1. Build: `py tools/build.py`. This writes `build/nwn_mirage.erf` (scripts) and `build/nwn_mirage.hak` (shader) and copies the hak into your NWN `hak` folder.
2. In the toolset, add the hak: Module Properties > Custom Content > add `nwn_mirage`.
3. Import the scripts: File > Import > `build/nwn_mirage.erf`.
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
| `/mirage debug` | Debug view: red = shimmer, blue = mirage water |

Look out across a large open area. The effect is about distance, so it needs a view of 40 m or more.

If nothing changes at all, the game probably isn't running the post-processing pass. Turn on any post-processing effect in Options > Graphics (for example Vibrance or Sharpen) and try again. If the screen goes black or looks broken, the shader failed to compile on your graphics card: the error is in `nwclientLog1.txt` in your NWN user folder (the `logs` folder).

## Repository

- `src/shaders/`: the shader, packed into the hak.
- `src/nss/`: the control scripts: `mirage_inc` (area settings → shader), `mirage_enter` and `mirage_loop` (per-player update every 2 s), `mirage_chat` (test commands).
- `tools/build.py`: compiles, packs and installs. The compiler comes from the [neverwinter.nim](https://github.com/niv/neverwinter.nim/releases) release, unzipped into `tools/neverwinter/`.
- `reference/` (not committed): Beamdog's stock shaders, extracted from the game for study.
