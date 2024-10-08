from unrealsdk import RegisterHook, RemoveHook, UObject, UFunction, FStruct,Log #type: ignore
from Mods.ModMenu import EnabledSaveType, RegisterMod, SDKMod


def EnableRagdoll(caller: UObject, function: UFunction, params: FStruct):
    if not caller.CollisionComponent:
        return True
        
    caller.CollisionComponent.SetRBCollidesWithChannel(16, False)#Dead pawns
    caller.CollisionComponent.SetRBCollidesWithChannel(24, False)#willow pickups
    return False


class LootCollision(SDKMod):
    Name = "Loot Collision"
    Description = f"Disables loot collision with dead bodies and other loot."
    Author = "RedxYeti"
    Version = "1.0"
    SaveEnabledState = EnabledSaveType.LoadWithSettings

    def Enable(self) -> None:
        RegisterHook("WillowGame.WillowPickup.EnableRagdollCollision", "EnableRagdoll", EnableRagdoll)

    def Disable(self) -> None:
        RemoveHook("WillowGame.WillowPickup.EnableRagdollCollision", "EnableRagdoll")

LC = LootCollision()
RegisterMod(LootCollision())