
from unrealsdk import Log, GetEngine, RegisterHook, RemoveHook, FindClass, FindObject,  UObject, UFunction, FStruct, ConstructObject, RunHook, LoadPackage, KeepAlive  # type: ignore
from ..ModMenu import EnabledSaveType, Options, RegisterMod, SDKMod, ClientMethod, ServerMethod, Hook
from typing import Any, Iterator, List, Optional

    
oidRunnerMin = Options.Slider(
    Caption="Runner Min Start Speed",
    Description="Minimum speed that you can start afterburn at for the runner.",
    StartingValue=1700,
    MinValue=0,
    MaxValue=3400,
    Increment=100,
)
oidRunnerSpeed = Options.Slider(
    Caption="Runner Speed",
    Description="The speed of afterburn for the runner.",
    StartingValue=3500,
    MinValue=0,
    MaxValue=10000,
    Increment=100,
)
oidRunnerTime = Options.Slider(
    Caption="Runner Duration",
    Description="Total time in seconds of afterburn for the runner.",
    StartingValue=4,
    MinValue=0,
    MaxValue=30,
    Increment=1,
)
oidRunnerRegenRate = Options.Slider(
    Caption="Runner Regen Rate",
    Description="How fast the afterburn for the runner regens.",
    StartingValue=20,
    MinValue=0,
    MaxValue=100,
    Increment=1,
)
oidRunnerRegenDelay = Options.Slider(
    Caption="Runner Regen Delay",
    Description="How long in seconds of afterburn for the runner to start regenerating.",
    StartingValue=5,
    MinValue=0,
    MaxValue=30,
    Increment=1,
)
oidRunners = Options.Nested (
    Caption = "Runner settings",
    Description = "Afterburn tweaks for Runners.",
    Children = [oidRunnerMin, oidRunnerSpeed, oidRunnerTime, oidRunnerRegenRate, oidRunnerRegenDelay],
    IsHidden = False
)

oidTechMin = Options.Slider(
    Caption="Technical Afterburn Start Speed",
    Description="Minimum speed that you can start afterburn at for the Technical.",
    StartingValue=2000,
    MinValue=0,
    MaxValue=5000,
    Increment=100,
)
oidTechSpeed = Options.Slider(
    Caption="Technical Afterburn Speed",
    Description="The speed of afterburn for the Technical.",
    StartingValue=4400,
    MinValue=0,
    MaxValue=10000,
    Increment=100,
)
oidTechTime = Options.Slider(
    Caption="Technical Duration",
    Description="Total time in seconds of afterburn for the Technical.",
    StartingValue=10,
    MinValue=0,
    MaxValue=60,
    Increment=1,
)
oidTechRegenRate = Options.Slider(
    Caption="Technical Regen Rate",
    Description="How fast the afterburn for the Technical regens.",
    StartingValue=20,
    MinValue=0,
    MaxValue=100,
    Increment=1,
)
oidTechRegenDelay = Options.Slider(
    Caption="Technical Regen Delay",
    Description="How long in seconds of afterburn for the Technical to start regenerating.",
    StartingValue=5,
    MinValue=0,
    MaxValue=30,
    Increment=1,
)
oidTechs = Options.Nested (
    Caption = "Technical settings",
    Description = "Afterburn tweaks for Technicals.",
    Children = [oidTechMin, oidTechSpeed, oidTechTime, oidTechRegenRate, oidTechRegenDelay],
    IsHidden = False
)

oidHoverMin = Options.Slider(
    Caption="Hovercraft Afterburn Start Speed",
    Description="Minimum speed that you can start afterburn at for the Hovercraft.",
    StartingValue=2500,
    MinValue=0,
    MaxValue=5000,
    Increment=100,
)
oidHoverSpeed = Options.Slider(
    Caption="Hovercraft Afterburn Speed",
    Description="The speed of afterburn for the Hovercraft.",
    StartingValue=4000,
    MinValue=0,
    MaxValue=10000,
    Increment=100,
)
oidHoverTime = Options.Slider(
    Caption="Hovercraft Duration",
    Description="Total time in seconds of afterburn for the Hovercraft.",
    StartingValue=10,
    MinValue=0,
    MaxValue=60,
    Increment=1,
)
oidHoverRegenRate = Options.Slider(
    Caption="Hovercraft Regen Rate",
    Description="How fast the afterburn for the Hovercraft regens.",
    StartingValue=20,
    MinValue=0,
    MaxValue=100,
    Increment=1,
)
oidHoverRegenDelay = Options.Slider(
    Caption="Hovercraft Regen Delay",
    Description="How long in seconds of afterburn for the Hovercraft to start regenerating.",
    StartingValue=5,
    MinValue=0,
    MaxValue=30,
    Increment=1,
)
oidHovers = Options.Nested (
    Caption = "Hovercraft settings",
    Description = "Afterburn tweaks for Hovercrafts.",
    Children = [oidHoverMin, oidHoverSpeed, oidHoverTime, oidHoverRegenRate, oidHoverRegenDelay],
    IsHidden = False
)
#when a car spawns, it applys the current settings to that vehicle definition
@Hook("WillowGame.WillowVehicle.PlaySpawnEffect")
def VehSpawned(caller: UObject, function: UFunction, params: FStruct):
    vehdef = caller.VehicleDef
    vehclassname = str(vehdef.Name).lower()
    if "runner" in vehclassname:
        vehdef.AfterburnerActivationSpeed = oidRunnerMin.CurrentValue
        vehdef.AfterburnerSpeed = oidRunnerSpeed.CurrentValue
        vehdef.AfterburnerBoostTime = oidRunnerTime.CurrentValue
        vehdef.AfterburnerPoolDefinition.BaseOnIdleRegenerationRate = oidRunnerRegenRate.CurrentValue
        vehdef.AfterburnerPoolDefinition.BaseOnIdleRegenerationDelay = oidRunnerRegenDelay.CurrentValue

    elif "technical" in vehclassname:
        vehdef.AfterburnerActivationSpeed = oidTechMin.CurrentValue
        vehdef.AfterburnerSpeed = oidTechSpeed.CurrentValue
        vehdef.AfterburnerBoostTime = oidTechTime.CurrentValue
        vehdef.AfterburnerPoolDefinition.BaseOnIdleRegenerationRate = oidTechRegenRate.CurrentValue
        vehdef.AfterburnerPoolDefinition.BaseOnIdleRegenerationDelay = oidTechRegenDelay.CurrentValue
    
    elif "hovercraft" in vehclassname:
        vehdef.AfterburnerActivationSpeed = oidHoverMin.CurrentValue
        vehdef.AfterburnerSpeed = oidHoverSpeed.CurrentValue
        vehdef.AfterburnerBoostTime = oidHoverTime.CurrentValue
        vehdef.AfterburnerPoolDefinition.BaseOnIdleRegenerationRate = oidHoverRegenRate.CurrentValue
        vehdef.AfterburnerPoolDefinition.BaseOnIdleRegenerationDelay = oidHoverRegenDelay.CurrentValue     
    return True

class AfterburnTweaks(SDKMod):
    Name = "Afterburn Tweaks"
    Description = "Adjust vehicle afterburn to your liking."
    Author = "RedxYeti"
    Version = "1.0"
    SaveEnabledState = EnabledSaveType.LoadWithSettings
    Options = [oidRunners, oidTechs, oidHovers]

AfterburnInst = AfterburnTweaks()
RegisterMod(AfterburnInst)
