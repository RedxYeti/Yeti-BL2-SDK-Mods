from unrealsdk import RegisterHook, RemoveHook, UObject, UFunction, FStruct,Log #type: ignore
from unrealsdk import FindObject, KeepAlive, LoadPackage, ConstructObject #type: ignore
from Mods.ModMenu import EnabledSaveType, RegisterMod, SDKMod, OptionManager, Options#type: ignore
from typing import Any
from math import sqrt
import unrealsdk#type: ignore
from Mods import ModMenu#type: ignore

ItemDictionary = {}

oidChests = Options.Boolean(
    Caption="Chest Items",
    Description="With this enabled, enabled options will be automatically picked up from chests.",
    StartingValue=True,
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
    Children = [oidChests, oidHealthVials, oidShieldBoosters, oidMoney, oidEridium,
                oidSeraphCrystal, oidTorgueToken , oidMoonstones, oidAmmoNest],
    IsHidden = False
)

def SetAutoPickup(Pickupable, bAuto):
    if Pickupable:
        Log(f"setting {str(Pickupable).split(' ')[1]} to {bAuto}")
        Pickupable.bAutomaticallyPickup = bAuto
    return

def dist(a, b) -> float:
    return sqrt((b.X - a.X)**2 + (b.Y - a.Y)**2 + (b.Z - a.Z)**2)

def InteractParticles(caller: UObject, function: UFunction, params: FStruct):
    if not oidChests.CurrentValue or not caller.Base or caller.Base.Class.Name != "WillowInteractiveObject":
        return True

    if caller.Inventory and caller.Inventory.Class.Name == "WillowUsableItem" and not caller.Inventory.Class.Name == "WillowMissionItem":
        BaseIO = caller.Base.ConsumerHandle.PID
        if caller.Base.InteractiveObjectDefinition.Name == "InteractiveObj_MilitaryCrate":
            caller.AdjustPickupPhysicsAndCollisionForBeingDropped()

        if BaseIO in APT.InteractiveObjects.keys() and APT.InteractiveObjects[BaseIO] and caller.bPickupable:
            APT.InteractiveObjects[BaseIO][0].TouchedPickupable(caller)
            APT.InteractiveObjects[BaseIO][0].CurrentPickupable = None
            APT.InteractiveObjects[BaseIO][0].CurrentTouchedPickupable = None

    return True

def UsedBy(caller: UObject, function: UFunction, params: FStruct):
    APT.InteractiveObjects[caller.ConsumerHandle.PID] = [params.User.Controller]
    return True

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
    Version = "1.0"
    SaveEnabledState = EnabledSaveType.LoadWithSettings

    Options = [oidMainNest]
    ShieldNames = ["Shield Booster", "IED Booster", "Slammer", "Big Boom Blaster Booster"]
    LastUser = None
    InteractiveObjects = {}

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

    def Enable(self) -> None:
        RegisterHook("WillowGame.WillowPlayerController.TouchedPickupable", "TouchedPickup", TouchedPickup)
        RegisterHook("WillowGame.WillowInteractiveObject.UsedBy", "UsedBy", UsedBy)
        RegisterHook("WillowGame.WillowPickup.SetInteractParticles", "InteractParticles", InteractParticles)
        RegisterHook("WillowGame.WillowScrollingList.AddListItem", "CreateButton", CreateButton)
        RegisterHook("WillowGame.WillowPlayerController.WillowClientDisableLoadingMovie", "DisableLoadingMovie", DisableLoadingMovie)

    def Disable(self) -> None:
        RemoveHook("WillowGame.WillowPlayerController.TouchedPickupable", "TouchedPickup")
        RemoveHook("WillowGame.WillowInteractiveObject.UsedBy", "UsedBy")
        RemoveHook("WillowGame.WillowPickup.SetInteractParticles", "InteractParticles")
        RemoveHook("WillowGame.WillowScrollingList.AddListItem", "CreateButton")
        RemoveHook("WillowGame.WillowPlayerController.WillowClientDisableLoadingMovie", "DisableLoadingMovie")

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