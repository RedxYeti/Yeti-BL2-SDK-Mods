
from unrealsdk import Log, ConstructObject, GetEngine #type: ignore

import unrealsdk  # type: ignore

import random
from Mods.ModMenu import EnabledSaveType, Options, RegisterMod, SDKMod,  Hook, ClientMethod, ServerMethod, SettingsManager #type: ignore

RescalePlayers = Options.Boolean(
    Caption="Rescale Players",
    Description="Controls if player's scales are randomized on spawn and respawn.",
    StartingValue=True,
)
PlayingAlone = Options.Boolean(
    Caption="Alternate player scale",
    Description="Makes it so your camera scales with your current height. WARNING: NOT MULTIPLAYER SAFE",
    StartingValue=False,
)
RescaleNPCs = Options.Boolean(
    Caption="Rescale NPCs",
    Description="Controls if NPC's scale is randomized.",
    StartingValue=True,
)
WackyEnemyScale = Options.Boolean(
    Caption="Wacky NPC Scale",
    Description="With this enabled, the NPCS scale will not be uniform.",
    StartingValue=False,
)
RescaleVehiles = Options.Boolean(
    Caption="Rescale Vehiles",
    Description="Controls if vehicle's scale is randomized.",
    StartingValue=True,
)


class SillyScales(SDKMod):
    Name = "Silly Scales"
    Description = f"Scale randomizer."
    Author = "RedxYeti"
    Version = "1.0"
    SaveEnabledState = EnabledSaveType.LoadWithSettings

    Options = [RescalePlayers, PlayingAlone, RescaleNPCs, WackyEnemyScale, RescaleVehiles]

    def Enable(self) -> None:
        unrealsdk.RegisterHook("WillowGame.WillowAIPawn.PostSpawn", "PawnSpawned", PawnSpawned)
        unrealsdk.RegisterHook("WillowGame.WillowPlayerPawn.GetBestPlayerStartPoint", "PlayerSpawned", PlayerSpawned)
        unrealsdk.RegisterHook("WillowGame.WillowPlayerPawn.AwaitingRespawnActivateNozzle", "PlayerDowned", PlayerDowned)
        unrealsdk.RegisterHook("WillowGame.WillowVehicle.PostBeginPlay", "CarSpawned", CarSpawned)
        unrealsdk.RegisterHook("WillowGame.WillowPlayerPawn.SetBaseEyeheight", "BlockResize", Resize)


    def Disable(self) -> None:
        unrealsdk.RemoveHook("WillowGame.WillowAIPawn.PostSpawn", "PawnSpawned")
        unrealsdk.RemoveHook("WillowGame.WillowPlayerPawn.GetBestPlayerStartPoint", "PlayerSpawned")
        unrealsdk.RemoveHook("WillowGame.WillowPlayerPawn.AwaitingRespawnActivateNozzle", "PlayerDowned")
        unrealsdk.RemoveHook("WillowGame.WillowVehicle.PostBeginPlay", "CarSpawned")
        unrealsdk.RemoveHook("WillowGame.WillowPlayerPawn.SetBaseEyeheight", "BlockResize")

    def RandomizeScale(self, caller: unrealsdk.UObject, scaleAmount):
        changeScale = ConstructObject("Behavior_ChangeScale")
        changeScale.Scale = scaleAmount
        changeScale.ApplyBehaviorToContext(caller, (), None, None, None, ())
        UpdateCollision = ConstructObject("Behavior_UpdateCollision")
        UpdateCollision.ApplyBehaviorToContext(caller, (), None, None, None, ())

SillyScalesInst = SillyScales()

def PawnSpawned(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> None:
    if RescaleNPCs.CurrentValue:
        if WackyEnemyScale.CurrentValue and caller.Mesh is not None:
            WackyX = random.uniform(0.1, 2.5)
            WackyY = random.uniform(0.1, 2.5)
            WackyZ = random.uniform(0.1, 2.5)
            caller.Mesh.Scale3D = (WackyX, WackyY, WackyZ)
        else:
            newscale = random.uniform(0.1, 1.9)
            SillyScalesInst.RandomizeScale(caller, newscale)

    return True

def RescalePlayer(PlayertoScale: unrealsdk.UObject, newscale):
    RadiusScale = PlayertoScale.GetCollisionRadius() * newscale
    CollisionHeight = PlayertoScale.GetCollisionHeight() * newscale
    PlayertoScale.SetDrawScale3D((newscale, newscale, newscale))
    PlayertoScale.CollisionComponent.Behavior_ChangeCollisionSize(RadiusScale, CollisionHeight)
    PlayertoScale.BaseEyeHeight = 68 * newscale

def PlayerSpawned(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> None:
    if RescalePlayers.CurrentValue:
        newscale = random.uniform(0.2, 1.8)
        if PlayingAlone.CurrentValue:
            RescalePlayer(caller, newscale)
        else:
            SillyScalesInst.RandomizeScale(caller, newscale)
    
    return True

def PlayerDowned(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> None:
    if RescalePlayers.CurrentValue:
        newscale = random.uniform(0.2, 1.8)
        if PlayingAlone.CurrentValue:
            RescalePlayer(caller, newscale)
        else:
            SillyScalesInst.RandomizeScale(caller, newscale)

    return True

def CarSpawned(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> None:
    if RescaleVehiles.CurrentValue:
        newscale = random.uniform(0.1, 1.9)
        SillyScalesInst.RandomizeScale(caller, newscale)
    
    return True

def Resize(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> None:
    if RescalePlayers.CurrentValue and PlayingAlone.CurrentValue:
        caller.BaseEyeHeight = caller.BaseEyeHeight
    
    return True

RegisterMod(SillyScalesInst)