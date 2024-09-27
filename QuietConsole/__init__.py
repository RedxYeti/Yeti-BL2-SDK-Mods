from unrealsdk import RegisterHook, RemoveHook, UObject, UFunction, FStruct, Log #type: ignore
from Mods.ModMenu import EnabledSaveType, RegisterMod, SDKMod


def QuietConsoleOutput(caller: UObject, function: UFunction, params: FStruct):
    if str(params.Text).startswith("[BEHAVIOR]"):
        return False
    else:
        return True


class QuietConsole(SDKMod):
    Name = "Quiet Console"
    Description = f"Disables most things printed to console by Gearbox."
    Author = "RedxYeti"
    Version = "1.1"
    SaveEnabledState = EnabledSaveType.LoadWithSettings

    def Enable(self) -> None:
        RegisterHook("WillowGame.Behavior_DebugMessage.ApplyBehaviorToContext", "QuietConsoleMain", lambda c,f,p: False)
        RegisterHook("WillowGame.LocalItemMessage.ClientItemReceive", "QuietConsoleMain", lambda c,f,p: False)
        RegisterHook("WillowGame.LocalWeaponMessage.ClientWeaponReceive", "QuietConsoleMain", lambda c,f,p: False)
        RegisterHook("WillowGame.ReceivedAmmoMessage.ClientAmmoReceive", "QuietConsoleMain", lambda c,f,p: False)
        RegisterHook("WillowGame.ReceivedCreditsMessage.ClientCreditReceive", "QuietConsoleMain", lambda c,f,p: False)
        RegisterHook("WillowGame.ChallengeFeedbackMessage.GetString", "QuietConsoleMain", lambda c,f,p: False)
        RegisterHook("WillowGame.MissionFeedbackMessage.GetString", "QuietConsoleMain", lambda c,f,p: False)
        RegisterHook("WillowGame.FastTravelStationDiscoveryMessage.GetString", "QuietConsoleMain", lambda c,f,p: False)
        RegisterHook("WillowGame.ExperienceFeedbackMessage.GetString", "QuietConsoleMain", lambda c,f,p: False)
        RegisterHook("Engine.GameMessage.GetString", "QuietConsoleMain", lambda c,f,p: False)
        RegisterHook("Engine.Console.OutputText", "QuietConsoleOutput", QuietConsoleOutput)


    def Disable(self) -> None:
        RemoveHook("WillowGame.Behavior_DebugMessage.ApplyBehaviorToContext", "QuietConsoleMain")
        RemoveHook("WillowGame.LocalItemMessage.ClientItemReceive", "QuietConsoleMain")
        RemoveHook("WillowGame.LocalWeaponMessage.ClientWeaponReceive", "QuietConsoleMain")
        RemoveHook("WillowGame.ReceivedAmmoMessage.ClientAmmoReceive", "QuietConsoleMain")
        RemoveHook("WillowGame.ReceivedCreditsMessage.ClientCreditReceive", "QuietConsoleMain")
        RemoveHook("WillowGame.ChallengeFeedbackMessage.GetString", "QuietConsoleMain")
        RemoveHook("WillowGame.MissionFeedbackMessage.GetString", "QuietConsoleMain")
        RemoveHook("WillowGame.FastTravelStationDiscoveryMessage.GetString", "QuietConsoleMain")
        RemoveHook("WillowGame.ExperienceFeedbackMessage.GetString", "QuietConsoleMain")
        RemoveHook("Engine.GameMessage.GetString", "QuietConsoleMain")
        RemoveHook("Engine.Console.OutputText", "QuietConsoleOutput")

QC = QuietConsole()
RegisterMod(QuietConsole())