from typing import Any
from unrealsdk import FindObject, KeepAlive, Log #type: ignore 
from Mods.ModMenu import EnabledSaveType, OptionManager, Options, RegisterMod, SDKMod #type: ignore

oidReviveTime = Options.Spinner(
    Caption="Revive Time",
    Description="How long it takes in seconds to revive a teammate. Five seconds is the vanilla setting.",
    StartingValue="5.0",
    Choices=["0.0", "0.5", "1.0", "1.5", "2.0", "2.5", "3.0", "3.5", "4.0", "4.5", "5.0", "5.5", "6.0", "6.5", "7.0", "7.5", "8.0", "8.5", "9.0", "9.5", "10.0"]
)

class FasterRevive(SDKMod):
    Name = "Revive Time Modifier"
    Description = f"Choose how long it takes to revive teammates."
    Author = "RedxYeti"
    Version = "1.0"
    SaveEnabledState = EnabledSaveType.LoadWithSettings
    Options = [oidReviveTime]

    def __init__(self) -> None:
        self.do = None
        #i have no idea if this is necessary

    def Enable(self):
        self.InjuredDef = FindObject("InjuredDefinition", "GD_PlayerShared.injured.PlayerInjuredDefinition")
        KeepAlive(self.InjuredDef)
        self.InjuredDef.ReviveDuration = float(oidReviveTime.CurrentValue)

    def Disable(self):
        self.InjuredDef.ReviveDuration = 5

    def ModOptionChanged(self, option: OptionManager.Options.Base, new_value: Any) -> None:
        if option.Caption == "Revive Time":
           self.InjuredDef.ReviveDuration = float(new_value)

FasterReviveInst = FasterRevive()

RegisterMod(FasterReviveInst)