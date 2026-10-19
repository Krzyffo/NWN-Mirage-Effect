// mirage_loop: per-player update, run on the player every MIRAGE_TICK
// seconds. Re-sends the shader settings, so the mirage follows the player
// between areas and the time of day.

#include "mirage_inc"

void main()
{
    object oPC = OBJECT_SELF;
    if (!GetIsObjectValid(oPC)) return;  // logged out: the loop ends
    MirageApply(oPC);
    DelayCommand(MIRAGE_TICK, ExecuteScript("mirage_loop", oPC));
}
