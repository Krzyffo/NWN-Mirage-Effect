// mirage_enter: module OnClientEnter. Starts the player's mirage loop.
//
// If the module already has an OnClientEnter script, keep it and add this
// line to it instead:
//     ExecuteScript("mirage_enter", GetEnteringObject());

#include "mirage_inc"

void main()
{
    object oPC = GetEnteringObject();
    if (!GetIsObjectValid(oPC)) oPC = OBJECT_SELF;  // run through ExecuteScript
    if (!GetIsPC(oPC)) return;

    // Uniforms are not kept across logins, and one loop per player is enough.
    if (GetLocalInt(oPC, MIRAGE_VAR_LOOP))
    {
        MirageApply(oPC);
        return;
    }
    SetLocalInt(oPC, MIRAGE_VAR_LOOP, TRUE);
    ExecuteScript("mirage_loop", oPC);
}
