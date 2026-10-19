// mirage_chat: module OnPlayerChat, optional, for trying the effect out.
//   /mirage          show the current strength
//   /mirage 0.7      force a strength everywhere (0.1..1)
//   /mirage off      force it off
//   /mirage area     back to the area's own settings
//   /mirage debug    toggle the debug view (red = shimmer, blue = water)
// If the module already has an OnPlayerChat script, add this line to it:
//     ExecuteScript("mirage_chat", OBJECT_SELF);

#include "mirage_inc"

void main()
{
    object oPC = GetPCChatSpeaker();
    string sMsg = GetStringLowerCase(GetPCChatMessage());
    if (GetStringLeft(sMsg, 7) != "/mirage") return;
    SetPCChatMessage("");  // keep test commands out of the chat

    string sArg = GetStringRight(sMsg, GetStringLength(sMsg) - 7);
    while (GetStringLeft(sArg, 1) == " ") sArg = GetStringRight(sArg, GetStringLength(sArg) - 1);

    if (sArg == "debug")
    {
        int bDebug = !GetLocalInt(oPC, MIRAGE_VAR_DEBUG);
        SetLocalInt(oPC, MIRAGE_VAR_DEBUG, bDebug);
        SendMessageToPC(oPC, "Mirage debug view " + (bDebug ? "on: red = shimmer, blue = mirage water." : "off."));
    }
    else if (sArg == "off")
    {
        SetLocalFloat(oPC, MIRAGE_VAR_OVERRIDE, -1.0);
        SendMessageToPC(oPC, "Mirage forced off. /mirage area to undo.");
    }
    else if (sArg == "area")
    {
        DeleteLocalFloat(oPC, MIRAGE_VAR_OVERRIDE);
        SendMessageToPC(oPC, "Mirage follows the area settings again.");
    }
    else if (sArg != "")
    {
        float f = StringToFloat(sArg);
        if (f <= 0.0 || f > 1.0)
        {
            SendMessageToPC(oPC, "Use a strength from 0.1 to 1, or off, area, debug.");
            return;
        }
        SetLocalFloat(oPC, MIRAGE_VAR_OVERRIDE, f);
        SendMessageToPC(oPC, "Mirage forced to " + FloatToString(f, 0, 2) + " everywhere. /mirage area to undo.");
    }
    MirageApply(oPC);
    if (sArg == "")
        SendMessageToPC(oPC, "Mirage strength here: " + FloatToString(GetLocalFloat(oPC, MIRAGE_VAR_SENT), 0, 2)
                             + " (" + IntToString(GetTimeHour()) + ":00).");
}
