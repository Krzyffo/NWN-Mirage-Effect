// mirage_inc: drives the heat haze shader (src/shaders/fsfbpostpr.shd).
//
// An area gets the mirage from its variables (Area Properties > Advanced >
// Variables), all optional except MIRAGE:
//   MIRAGE         float  strength 0..1; 0 or missing = no mirage here
//   MIRAGE_NEAR    float  metres where the shimmer starts (default 10)
//   MIRAGE_FAR     float  metres where it is full strength (default 40)
//   MIRAGE_WATER   float  fake water below the horizon, 0..1 (default 0.6)
//   MIRAGE_BLUR    float  blur of the hot distant air, 0..1 (default 0.5;
//                         -1 = none, since 0 reads the same as missing)
//   MIRAGE_ALLDAY  int    1 = ignore the time of day
// Without MIRAGE_ALLDAY the heat follows the sun: none at night, building
// up through the morning, strongest from 11:00 to 16:00.

const string MIRAGE_VAR          = "MIRAGE";
const string MIRAGE_VAR_NEAR     = "MIRAGE_NEAR";
const string MIRAGE_VAR_FAR      = "MIRAGE_FAR";
const string MIRAGE_VAR_WATER    = "MIRAGE_WATER";
const string MIRAGE_VAR_BLUR     = "MIRAGE_BLUR";
const string MIRAGE_VAR_ALLDAY   = "MIRAGE_ALLDAY";
const string MIRAGE_VAR_DEBUG    = "MIRAGE_DEBUG";    // on the player, set by /mirage debug
const string MIRAGE_VAR_OVERRIDE = "MIRAGE_FORCE";    // on the player, set by /mirage <n>
const string MIRAGE_VAR_FORCE_BLUR = "MIRAGE_FORCE_BLUR";  // on the player, set by /mirage blur <n>
const string MIRAGE_VAR_SENT     = "MIRAGE_SENT";     // last strength sent to the player
const string MIRAGE_VAR_LOOP     = "MIRAGE_LOOP";     // the player's loop is running

const float MIRAGE_DEFAULT_NEAR  = 10.0;
const float MIRAGE_DEFAULT_FAR   = 40.0;
const float MIRAGE_DEFAULT_WATER = 0.6;
const float MIRAGE_DEFAULT_BLUR  = 0.5;
const float MIRAGE_TICK          = 2.0;     // seconds between updates

// The shader's uniforms: scriptableFloat1..5 and scriptableInt1.
const int MIRAGE_U_STRENGTH = SHADER_UNIFORM_1;
const int MIRAGE_U_NEAR     = SHADER_UNIFORM_2;
const int MIRAGE_U_FAR      = SHADER_UNIFORM_3;
const int MIRAGE_U_WATER    = SHADER_UNIFORM_4;
const int MIRAGE_U_BLUR     = SHADER_UNIFORM_5;
const int MIRAGE_U_DEBUG    = SHADER_UNIFORM_1;

float MirageGetFloat(object oArea, string sVar, float fDefault)
{
    // GetLocalFloat cannot tell 0.0 from missing, so a 0 means "default".
    float f = GetLocalFloat(oArea, sVar);
    return f > 0.0 ? f : fDefault;
}

// 0..1: how hot it is at this hour.
float MirageSunFactor()
{
    float fHour = IntToFloat(GetTimeHour()) + IntToFloat(GetTimeMinute()) / 60.0;
    if (fHour < 8.0 || fHour >= 19.0) return 0.0;
    if (fHour < 11.0) return (fHour - 8.0) / 3.0;
    if (fHour < 16.0) return 1.0;
    return (19.0 - fHour) / 3.0;
}

// Strength the player should see now, in the area they are in.
float MirageStrength(object oPC)
{
    float fForce = GetLocalFloat(oPC, MIRAGE_VAR_OVERRIDE);
    if (fForce != 0.0) return fForce < 0.0 ? 0.0 : fForce;  // -1 = forced off

    object oArea = GetArea(oPC);
    if (!GetIsObjectValid(oArea) || GetIsAreaInterior(oArea)) return 0.0;
    float fStrength = GetLocalFloat(oArea, MIRAGE_VAR);
    if (fStrength <= 0.0) return 0.0;
    if (!GetLocalInt(oArea, MIRAGE_VAR_ALLDAY)) fStrength *= MirageSunFactor();
    return fStrength;
}

// Blur for the player: /mirage blur, else the area's, else the default.
float MirageBlurAmount(object oPC, object oArea)
{
    float f = GetLocalFloat(oPC, MIRAGE_VAR_FORCE_BLUR);
    if (f == 0.0) f = MirageGetFloat(oArea, MIRAGE_VAR_BLUR, MIRAGE_DEFAULT_BLUR);
    return f < 0.0 ? 0.0 : f;
}

// Sends the current settings to the player's shader.
void MirageApply(object oPC)
{
    object oArea = GetArea(oPC);
    float fStrength = MirageStrength(oPC);
    SetShaderUniformFloat(oPC, MIRAGE_U_STRENGTH, fStrength);
    SetShaderUniformFloat(oPC, MIRAGE_U_NEAR,  MirageGetFloat(oArea, MIRAGE_VAR_NEAR,  MIRAGE_DEFAULT_NEAR));
    SetShaderUniformFloat(oPC, MIRAGE_U_FAR,   MirageGetFloat(oArea, MIRAGE_VAR_FAR,   MIRAGE_DEFAULT_FAR));
    SetShaderUniformFloat(oPC, MIRAGE_U_WATER, MirageGetFloat(oArea, MIRAGE_VAR_WATER, MIRAGE_DEFAULT_WATER));
    SetShaderUniformFloat(oPC, MIRAGE_U_BLUR,  MirageBlurAmount(oPC, oArea));
    SetShaderUniformInt(oPC, MIRAGE_U_DEBUG, GetLocalInt(oPC, MIRAGE_VAR_DEBUG));
    SetLocalFloat(oPC, MIRAGE_VAR_SENT, fStrength);
}
