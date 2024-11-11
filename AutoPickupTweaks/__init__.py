from unrealsdk import RegisterHook, RemoveHook, UObject, UFunction, FStruct,Log #type: ignore
from unrealsdk import FindClass, FindObject, KeepAlive, LoadPackage, ConstructObject #type: ignore
from Mods.ModMenu import EnabledSaveType, RegisterMod, SDKMod, OptionManager, Options#type: ignore
from typing import Any
from math import sqrt
import unrealsdk#type: ignore
from Mods import ModMenu#type: ignore

ItemDictionary = {}

oidPickupRadius = Options.Slider(
    Caption="Pickup Radius",
    Description="The horizontal distance for items to be automatically picked up. Default is 350.",
    StartingValue=350,
    MinValue=100,
    MaxValue=1000,
    Increment=50,
)

oidPickupHeight = Options.Slider(
    Caption="Pickup Height",
    Description="The verticle distance for items to be automatically picked up. Default is 20.",
    StartingValue=100,
    MinValue=20,
    MaxValue=350,
    Increment=10,
)

oidChests = Options.Boolean(
    Caption="Chest Items",
    Description="With this enabled, enabled options will be automatically picked up from chests.",
    StartingValue=True,
)

oidChestsAfterAnimation = Options.Boolean(
    Caption="   After Animation",
    Description="With this and Chest Items enabled, enabled options will only be picked up once the opening animation has finished. Requires mod to be re-enabled.",
    StartingValue=False,
)

oidHealthVials = Options.Boolean(
    Caption="Health Vials",
    Description="With this enabled, Health Vials will be automatically picked up.",
    StartingValue=True,
)

oidShieldBoosters = Options.Boolean(
    Caption="Shield Boosters",
    Description="With this enabled, Shield Boosters will be automatically picked up after they have landed.",
    StartingValue=False,
)

oidMoney = Options.Boolean(
    Caption="Money",
    Description="With this enabled, Money will be automatically picked up.",
    StartingValue=True,
)

oidEridium = Options.Boolean(
    Caption="Eridium",
    Description="With this enabled, Eridium will be automatically picked up.",
    StartingValue=False,
)

oidSeraphCrystal = Options.Boolean(
    Caption="Seraph Crystals",
    Description="With this enabled, Seraph Crystals will be automatically picked up.",
    StartingValue=False,
)

oidTorgueToken = Options.Boolean(
    Caption="Torgue Tokens",
    Description="With this enabled, Torgue Tokens will be automatically picked up.",
    StartingValue=False,
)

oidMoonstones = Options.Boolean(
    Caption="Moonstones",
    Description="With this enabled, Moonstones will be automatically picked up.",
    StartingValue=False,
)

oidARBullets = Options.Boolean(
    Caption="Assualt Rifle Bullets",
    Description="With this enabled, Assualt Rifle Bullets will be automatically picked up.",
    StartingValue=True,
)

oidSMGBullets = Options.Boolean(
    Caption="SMG Bullets",
    Description="With this enabled, MG Bullets will be automatically picked up.",
    StartingValue=True,
)

oidShotgunShells = Options.Boolean(
    Caption="Shotgun Shells",
    Description="With this enabled, Shotgun Shells will be automatically picked up.",
    StartingValue=True,
)

oidPistolBullets = Options.Boolean(
    Caption="Pistol Bullets",
    Description="With this enabled, Pistol Bullets will be automatically picked up.",
    StartingValue=True,
)

oidSniperBullets = Options.Boolean(
    Caption="Sniper Bullets",
    Description="With this enabled, Sniper Bullets will be automatically picked up.",
    StartingValue=True,
)

oidLaserCells = Options.Boolean(
    Caption="Laser Cells",
    Description="With this enabled, Laser Cells will be automatically picked up.",
    StartingValue=True,
)

oidRockets = Options.Boolean(
    Caption="Rockets",
    Description="With this enabled, Rocket Ammo will be automatically picked up.",
    StartingValue=True,
)

oidGrenades = Options.Boolean(
    Caption="Grenades",
    Description="With this enabled, Grenades will be automatically picked up.",
    StartingValue=True,
)

oidAmmoNest = Options.Nested (
    Caption = "Ammo Settings",
    Description = "Choose which ammo types auto pickup.",
    Children = [oidARBullets, oidSMGBullets, oidShotgunShells, oidPistolBullets,  
               oidSniperBullets, oidRockets, oidGrenades, oidLaserCells],
    IsHidden = False
)

oidMainNest = Options.Nested (
    Caption = "Auto Pickup Tweaks Options",
    Description = "All the settings for Auto Pickup Tweaks",
    Children = [oidPickupRadius, oidPickupHeight, oidChests, oidChestsAfterAnimation,
                oidHealthVials, oidShieldBoosters, oidMoney, oidEridium, oidSeraphCrystal,
                oidTorgueToken, oidMoonstones, oidAmmoNest],
    IsHidden = False
)

def SetAutoPickup(Pickupable, bAuto):
    if Pickupable:
        #Log(f"setting {str(Pickupable).split(' ')[1]} to {bAuto}")
        Pickupable.bAutomaticallyPickup = bAuto
    return

def Distance(a, b) -> float:
    return sqrt((b.X - a.X)**2 + (b.Y - a.Y)**2 + (b.Z - a.Z)**2)

def ClientDisplayPickupFailedMessage(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
    return not APT.BlockFailedMessage

def InteractParticles(caller: UObject, function: UFunction, params: FStruct):
    if not oidChests.CurrentValue or not caller.Base or caller.Base.Class.Name != "WillowInteractiveObject":
        return True

    if caller.Inventory and caller.Inventory.Class.Name == "WillowUsableItem" and not caller.Inventory.Class.Name == "WillowMissionItem":
        BaseIO = caller.Base.ConsumerHandle.PID
        if caller.Base.InteractiveObjectDefinition.Name == "InteractiveObj_MilitaryCrate":
            caller.AdjustPickupPhysicsAndCollisionForBeingDropped()
        
        if BaseIO in APT.InteractiveObjects.keys() and APT.InteractiveObjects[BaseIO] and caller.bPickupable:
            # Pickup but flag to prevent FULL icon if it occurs
            APT.BlockFailedMessage = True
            APT.InteractiveObjects[BaseIO][0].TouchedPickupable(caller)
            APT.InteractiveObjects[BaseIO][0].CurrentPickupable = None
            APT.InteractiveObjects[BaseIO][0].CurrentTouchedPickupable = None
            APT.BlockFailedMessage = False

    return True

def UsedBy(caller: UObject, function: UFunction, params: FStruct):
    # Check PlayerInteractionDistance 350 plus a bit for auto pickup on open
    if Distance(params.User.Location, caller.Location) <= 400:
        APT.InteractiveObjects[caller.ConsumerHandle.PID] = [params.User.Controller]
    else:
        # Set None for us the check the opened IO but not link to a PC for initial open
        APT.InteractiveObjects[caller.ConsumerHandle.PID] = None
    return True

def ChangeRemoteBehaviorSequenceState(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
    if caller.SequenceName == "Opened":
        IO = params.ContextObject
        if IO.Class.Name == "WillowInteractiveObject":
            if oidChestsAfterAnimation.CurrentValue:
                for p in IO.Attached:
                    InteractParticles(p, None, None)
            # Set free for anyone to pickup now that it's fully opened and the opener has picked up any
            APT.InteractiveObjects[IO.ConsumerHandle.PID] = None
    return True

def HandlePickupQuery(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
    """ Items attached to chests don't seem to fire the touched events, just SawPickupable and this one.
     WillowPlayerController.SawPickupable triggers when the interaction prompt appear for a pickup.
     This function triggers whenever you look at a pickup, allowing us to use a custom pickup distance.
    """
    Pickup = caller.Base
    if Pickup.Class.Name == "WillowPickup" and params.Other.Class.Name == "WillowPlayerPawn":
        if Pickup.Base:
            BaseIO = Pickup.Base.ConsumerHandle.PID
            # Only if NO player has dibsed this - so an already opened chest
            if BaseIO in APT.InteractiveObjects.keys() and not APT.InteractiveObjects[BaseIO] and Pickup.bPickupable:
                if Distance(params.Other.Location, caller.Location) <= oidPickupRadius.CurrentValue:
                    APT.InteractiveObjects[BaseIO] = [params.Other.Controller]
                    for p in Pickup.Base.Attached:
                        InteractParticles(p, None, None)
                    APT.InteractiveObjects[BaseIO] = None
    return True

# def SawPickupable(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
#     Log(f"SawPickupable {caller} {params}")
#     if not params.Pickup or not params.Pickup.ObjectPointer:
#          return True
#     Pickup = params.Pickup.ObjectPointer
#     if Pickup.Base:
#         BaseIO = Pickup.Base.ConsumerHandle.PID
#         # Only if NO player has dibsed this - so an already opened chest
#         if BaseIO in APT.InteractiveObjects.keys() and not APT.InteractiveObjects[BaseIO] and Pickup.bPickupable:
#             if Distance(Pickup.Location, caller.Pawn.Location) <= oidPickupDistance.CurrentValue:
#                 APT.InteractiveObjects[BaseIO] = [caller]
#                 for p in Pickup.Base.Attached:
#                     InteractParticles(p, None, None)
#                 APT.InteractiveObjects[BaseIO] = None
#     return True

def UpdateTouchRadius(caller: UObject, function: UFunction, params: FStruct):
    """ PlayerInteractionDistance affects both Pickups and InteractiveObjects,
     so we change it when setting a Pickups radius then change it back.
    """
    unrealsdk.DoInjectedCallNext()
    caller.CollisionComponent.SetCylinderSize(oidPickupRadius.CurrentValue, oidPickupHeight.CurrentValue)
    return False

def DisableLoadingMovie(caller: UObject, function: UFunction, params: FStruct):
    APT.InteractiveObjects = {}
    return True

def TouchedPickup(caller: UObject, function: UFunction, params: FStruct):
    if not params.Pickup or not params.Pickup.ObjectPointer:
        return True
    
    TouchedPickable = params.Pickup.ObjectPointer
    if str(TouchedPickable.Inventory.ItemName) in APT.ShieldNames and oidShieldBoosters.CurrentValue and TouchedPickable.bPickupable:
        if TouchedPickable.ImpactEffectPlayCount >= 1 or TouchedPickable.bPickupAtRest:
            caller.PickupPickupable(TouchedPickable, True)
    return True

def CreateButton(caller: UObject, function: UFunction, params: FStruct):
    if params.Caption == "$WillowMenu.WillowScrollingListDataProviderFrontEnd.Play_NewGame":
        global ItemDictionary
        APT.SeraphCrystalsAster = FindObject('UsableItemDefinition','GD_Aster_SeraphCrystal.UsableItems.Pickup_SeraphCrystal')
        APT.SeraphCrystalsIris = FindObject('UsableItemDefinition','GD_Iris_SeraphCrystal.UsableItems.Pickup_SeraphCrystal')
        APT.SeraphCrystalsOrchid = FindObject('UsableItemDefinition','GD_Orchid_SeraphCrystal.UsableItems.Pickup_SeraphCrystal')
        APT.SeraphCrystalsAsterSage = FindObject('UsableItemDefinition','GD_Sage_SeraphCrystal.UsableItems.Pickup_SeraphCrystal')
        APT.TorgueToken = FindObject('UsableItemDefinition','GD_Iris_TorgueToken.UsableItems.Pickup_TorgueToken')
        ItemDictionary = {
                oidMoney: [APT.SmallMoney, APT.LargeMoney, APT.CrystaliskMoney],
                oidEridium: [APT.SmallEridium, APT.LargeEridium],
                oidSeraphCrystal: [APT.SeraphCrystalsAster, APT.SeraphCrystalsIris, APT.SeraphCrystalsOrchid, APT.SeraphCrystalsAsterSage],
                oidTorgueToken: [APT.TorgueToken],
                oidMoonstones: [APT.SmallMoonstone, APT.LargeMoonstone],
                oidARBullets: [APT.ARBulletsNormal, APT.ARBulletsBoss],
                oidSMGBullets: [APT.SMGBulletsNormal, APT.SMGBulletsBoss],
                oidShotgunShells: [APT.ShotgunShellsNormal, APT.ShotgunShellsBoss],
                oidPistolBullets: [APT.PistolBulletsNormal, APT.PistolBulletsBoss],
                oidGrenades: [APT.GrenadesNormal, APT.GrenadesBoss],
                oidLaserCells: [APT.LaserCells],
                oidRockets: [APT.Rockets],
                oidSniperBullets: [APT.SniperBullets],
                oidHealthVials: [APT.HealthVialInstant, APT.HealthVialRegen],
            }
        
        for key in ItemDictionary.keys():
            for item in ItemDictionary[key]:
                SetAutoPickup(item, key.CurrentValue)

        RemoveHook("WillowGame.WillowScrollingList.AddListItem", "CreateButton")
    return True

class AutoPickupTweaks(SDKMod):
    Name = "Auto Pickup Tweaks"
    Description = f"Choose what picks up automatically"
    Author = "RedxYeti"
    Version = "1.1"
    SaveEnabledState = EnabledSaveType.LoadWithSettings

    Options = [oidMainNest]
    ShieldNames = ["Shield Booster", "IED Booster", "Slammer", "Big Boom Blaster Booster"]
    LastUser = None
    InteractiveObjects = {}
    BlockFailedMessage = False

    def __init__(self) -> None:
        self.HealthVialRegen = FindObject('UsableItemDefinition','GD_BuffDrinks.A_Item.BuffDrink_HealingRegen')
        self.HealthVialInstant = FindObject('UsableItemDefinition','GD_BuffDrinks.A_Item.BuffDrink_HealingInstant')

        self.SmallEridium = FindObject('UsableItemDefinition','GD_Currency.A_Item.EridiumStick')
        self.LargeEridium = FindObject('UsableItemDefinition','GD_Currency.A_Item.EridiumBar')

        self.SmallMoonstone = FindObject('UsableItemDefinition','GD_Currency.A_Item.Moonstone')
        self.LargeMoonstone = FindObject('UsableItemDefinition','GD_Currency.A_Item.MoonstoneCluster')

        self.SeraphCrystalsAster = FindObject('UsableItemDefinition','GD_Aster_SeraphCrystal.UsableItems.Pickup_SeraphCrystal')
        self.SeraphCrystalsIris = FindObject('UsableItemDefinition','GD_Iris_SeraphCrystal.UsableItems.Pickup_SeraphCrystal')
        self.SeraphCrystalsOrchid = FindObject('UsableItemDefinition','GD_Orchid_SeraphCrystal.UsableItems.Pickup_SeraphCrystal')
        self.SeraphCrystalsAsterSage = FindObject('UsableItemDefinition','GD_Sage_SeraphCrystal.UsableItems.Pickup_SeraphCrystal')

        self.TorgueToken = None

        self.SmallMoney = FindObject('UsableItemDefinition','GD_Currency.A_Item.Currency')
        self.LargeMoney = FindObject('UsableItemDefinition','GD_Currency.A_Item.Currency_Big')
        self.CrystaliskMoney = FindObject('UsableItemDefinition', 'GD_Currency.A_Item.Currency_Crystal')
        self.StolenMoney = None

        self.ARBulletsNormal = FindObject('UsableItemDefinition', 'GD_Ammodrops.Pickups.AmmoDrop_Assault_Rifle_Bullets')
        self.ARBulletsBoss = FindObject('UsableItemDefinition', 'GD_Ammodrops.Pickups_BossOnly.AmmoDropBoss_Assault_Rifle_Bullets')

        self.GrenadesNormal = FindObject('UsableItemDefinition', 'GD_Ammodrops.Pickups.AmmoDrop_Grenade_Protean')
        self.GrenadesBoss = FindObject('UsableItemDefinition', 'GD_Ammodrops.Pickups_BossOnly.AmmoDropBoss_Grenade_Protean')

        self.SMGBulletsNormal = FindObject('UsableItemDefinition', 'GD_Ammodrops.Pickups.AmmoDrop_Patrol_SMG_Clip')
        self.SMGBulletsBoss = FindObject('UsableItemDefinition', 'GD_Ammodrops.Pickups_BossOnly.AmmoDropBoss_Patrol_SMG_Clip')
 
        self.PistolBulletsNormal = FindObject('UsableItemDefinition', 'GD_Ammodrops.Pickups.AmmoDrop_Repeater_Pistol_Clip')
        self.PistolBulletsBoss = FindObject('UsableItemDefinition', 'GD_Ammodrops.Pickups_BossOnly.AmmoDropBoss_Repeater_Pistol_Clip')

        self.ShotgunShellsNormal = FindObject('UsableItemDefinition', 'GD_Ammodrops.Pickups.AmmoDrop_Shotgun_Shells')
        self.ShotgunShellsBoss = FindObject('UsableItemDefinition', 'GD_Ammodrops.Pickups_BossOnly.AmmoDropBoss_Shotgun_Shells')

        self.LaserCells = FindObject('UsableItemDefinition', 'GD_Ammodrops.Pickups.AmmoDrop_Laser_Cells')

        self.Rockets = FindObject('UsableItemDefinition', 'GD_Ammodrops.Pickups.AmmoDrop_Rocket_Launcher')

        self.SniperBullets = FindObject('UsableItemDefinition', 'GD_Ammodrops.Pickups.AmmoDrop_Sniper_Rifle_Cartridges')

    def EnableOnParticlesOrAfterAnimation(self) -> None:
        if oidChestsAfterAnimation.CurrentValue:
            RemoveHook("WillowGame.WillowPickup.SetInteractParticles", "InteractParticles")
        else:
            RegisterHook("WillowGame.WillowPickup.SetInteractParticles", "InteractParticles", InteractParticles)

    def Enable(self) -> None:
        RegisterHook("WillowGame.WillowPlayerController.TouchedPickupable", "TouchedPickup", TouchedPickup)
        RegisterHook("WillowGame.WillowInteractiveObject.UsedBy", "UsedBy", UsedBy)
        RegisterHook("WillowGame.WillowUsableItem.HandlePickupQuery", "HandlePickupQuery", HandlePickupQuery)
        RegisterHook("WillowGame.WillowScrollingList.AddListItem", "CreateButton", CreateButton)
        RegisterHook("WillowGame.WillowPlayerController.WillowClientDisableLoadingMovie", "DisableLoadingMovie", DisableLoadingMovie)
        RegisterHook("WillowGame.WillowPickup.UpdateTouchRadiusForAutomaticallyPickedUpInventory", "UpdateTouchRadius", UpdateTouchRadius)
        RegisterHook("WillowGame.WillowPlayerController.ClientDisplayPickupFailedMessage", "ClientDisplayPickupFailedMessage", ClientDisplayPickupFailedMessage)
        RegisterHook("GearboxFramework.Behavior_ChangeRemoteBehaviorSequenceState.ApplyBehaviorToContext", "ChangeRemoteBehaviorSequenceState", ChangeRemoteBehaviorSequenceState)
        self.EnableOnParticlesOrAfterAnimation()

    def Disable(self) -> None:
        RemoveHook("WillowGame.WillowPlayerController.TouchedPickupable", "TouchedPickup")
        RemoveHook("WillowGame.WillowInteractiveObject.UsedBy", "UsedBy")
        RemoveHook("WillowGame.WillowUsableItem.HandlePickupQuery", "HandlePickupQuery",)
        RemoveHook("WillowGame.WillowPickup.SetInteractParticles", "InteractParticles")
        RemoveHook("WillowGame.WillowScrollingList.AddListItem", "CreateButton")
        RemoveHook("WillowGame.WillowPlayerController.WillowClientDisableLoadingMovie", "DisableLoadingMovie")
        RemoveHook("WillowGame.WillowPickup.UpdateTouchRadiusForAutomaticallyPickedUpInventory", "UpdateTouchRadius")
        RemoveHook("WillowGame.WillowPlayerController.ClientDisplayPickupFailedMessage", "ClientDisplayPickupFailedMessage")
        RemoveHook("GearboxFramework.Behavior_ChangeRemoteBehaviorSequenceState.ApplyBehaviorToContext", "ChangeRemoteBehaviorSequenceState")

        #for key in ItemDictionary.keys():
        #    for item in self.ItemDictionary[key]:
        #        SetAutoPickup(item, key.StartingValue)

    def ModOptionChanged(self, option: OptionManager.Options.Base, new_val: Any) -> None:
        global ItemDictionary
        if option in ItemDictionary.keys():
            for item in ItemDictionary[option]:
                SetAutoPickup(item, new_val)
        return

APT = AutoPickupTweaks()
if __name__ == "__main__":
    unrealsdk.Log(f"[{APT.Name}] Manually loaded")
    for mod in ModMenu.Mods:
        if mod.Name == APT.Name:
            if mod.IsEnabled:
                mod.Disable()
            ModMenu.Mods.remove(mod)
            unrealsdk.Log(f"[{APT.Name}] Removed last instance")

            # Fixes inspect.getfile()
            APT.__class__.__module__ = mod.__class__.__module__
            break
RegisterMod(AutoPickupTweaks())
