from unrealsdk import RegisterHook, RemoveHook, UObject, UFunction, FStruct #type: ignore
from Mods.ModMenu import EnabledSaveType, RegisterMod, SDKMod


def QuietConsoleDebug(caller: UObject, function: UFunction, params: FStruct):
    return False

def QuietConsolePKMI(caller: UObject, function: UFunction, params: FStruct):
    return False

def QuietConsolePKMW(caller: UObject, function: UFunction, params: FStruct):
    return False

def QuietConsolePKMA(caller: UObject, function: UFunction, params: FStruct):
    return False

def QuietConsolePKMC(caller: UObject, function: UFunction, params: FStruct):
    return False

def QuietConsoleChal(caller: UObject, function: UFunction, params: FStruct):
    return False

def QuietConsoleMission(caller: UObject, function: UFunction, params: FStruct):
    return False

def QuietConsoleFT(caller: UObject, function: UFunction, params: FStruct):
    return False

def QuietConsoleLevelUp(caller: UObject, function: UFunction, params: FStruct):
    return False

def QuietConsoleGM(caller: UObject, function: UFunction, params: FStruct):
    return False


class QuietConsole(SDKMod):
    Name = "Quiet Console"
    Description = f"Disables most things printed to console by Gearbox."
    Author = "RedxYeti"
    Version = "1.0"
    SaveEnabledState = EnabledSaveType.LoadWithSettings

    def Enable(self) -> None:
        RegisterHook("WillowGame.Behavior_DebugMessage.ApplyBehaviorToContext", "QuietConsoleDebug", QuietConsoleDebug)
        RegisterHook("WillowGame.LocalItemMessage.ClientItemReceive", "ClientItemReceive", QuietConsolePKMI)
        RegisterHook("WillowGame.LocalWeaponMessage.ClientWeaponReceive", "QuietConsolePKMW", QuietConsolePKMW)
        RegisterHook("WillowGame.ReceivedAmmoMessage.ClientAmmoReceive", "QuietConsolePKMA", QuietConsolePKMA)
        RegisterHook("WillowGame.ReceivedCreditsMessage.ClientCreditReceive", "QuietConsolePKMC", QuietConsolePKMC)
        RegisterHook("WillowGame.ChallengeFeedbackMessage.GetString", "QuietConsoleChal", QuietConsoleChal)
        RegisterHook("WillowGame.MissionFeedbackMessage.GetString", "QuietConsoleMission", QuietConsoleMission)
        RegisterHook("WillowGame.FastTravelStationDiscoveryMessage.GetString", "QuietConsoleFT", QuietConsoleFT)
        RegisterHook("WillowGame.ExperienceFeedbackMessage.GetString", "QuietConsoleLevelUp", QuietConsoleLevelUp)
        RegisterHook("Engine.GameMessage.GetString", "QuietConsoleGM", QuietConsoleGM)

    def Disable(self) -> None:
        RemoveHook("WillowGame.Behavior_DebugMessage.ApplyBehaviorToContext", "QuietConsoleDebug")
        RemoveHook("WillowGame.LocalItemMessage.ClientItemReceive", "ClientItemReceive")
        RemoveHook("WillowGame.LocalWeaponMessage.ClientWeaponReceive", "QuietConsolePKMW")
        RemoveHook("WillowGame.ReceivedAmmoMessage.ClientAmmoReceive", "QuietConsolePKMA")
        RemoveHook("WillowGame.ReceivedCreditsMessage.ClientCreditReceive", "QuietConsolePKMC")
        RemoveHook("WillowGame.ChallengeFeedbackMessage.GetString", "QuietConsoleChal")
        RemoveHook("WillowGame.MissionFeedbackMessage.GetString", "QuietConsoleMission")
        RemoveHook("WillowGame.FastTravelStationDiscoveryMessage.GetString", "QuietConsoleFT")
        RemoveHook("WillowGame.ExperienceFeedbackMessage.GetString", "QuietConsoleLevelUp")
        RemoveHook("Engine.GameMessage.GetString", "QuietConsoleGM")

QC = QuietConsole()
RegisterMod(QuietConsole())