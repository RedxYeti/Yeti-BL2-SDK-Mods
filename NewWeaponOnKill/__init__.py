from random import choice, choices, uniform
from typing import Any, Iterable, Callable
from unrealsdk import Log, ConstructObject, FindObject, GetEngine, FindAll, LoadPackage, KeepAlive, FindClass #type: ignore
from unrealsdk import RunHook, RemoveHook, RegisterHook, UObject, UFunction, FStruct #type: ignore
from ..ModMenu import EnabledSaveType, Options, RegisterMod, SDKMod, Keybind, OptionManager
from typing import Any
from .Rarity_Colors import GetRarityColorHex
def path_name(obj: UObject) -> str:
    return obj.PathName(obj) if obj else "None"

mode = Options.Spinner(
    Caption="Mode",
    Description="Change the way your random gun gets generated. Legit Weapons will pull from legitimate loot tables. Randomized balanced will use random parts from the same weapon. Randomized Mayhem will not is fully random parts.",
    StartingValue="Legit Weapons",
    Choices=["Legit Weapons", "Randomized Balanced", "Randomized Mayhem"],
)
PickWeaponTypes = Options.Spinner(
    Caption="Weapon Types",
    Description="Use this to pick what type of weapons spawn. Only works for Legit weapons and Randomized Balanced.",
    StartingValue="Any",
    Choices=["Any", "Pistols", "Snipers", "Rocket Launchers", "Shotguns", "Submachine Guns", "Rifles"],
)
Refillammo = Options.Boolean(
    Caption="Refill ammo on swap",
    Description="If enabled, you will get some ammo for the weapon that you rolled.",
    StartingValue=True,
)
ShowWeaponName = Options.Boolean(
    Caption="Show Weapon Name on Kill",
    Description="This will show your weapon name every time you get a kill.",
    StartingValue=True,
)
NumberOfKills = Options.Slider(
    Caption="Number of kills between swaps",
    Description="Set this number to the amount of kills it takes to swap weapons. Co-op is a total added together. Changing this will set your current count to 0.",
    StartingValue=1,
    MinValue=1,
    MaxValue=100,
    Increment=1
)
keybind = Keybind(Name="Randomize Weapon", Key="B", OnPress=lambda: KeybindHit())

def KeybindHit():
    NewWeaponOnKillInst.change_weapon(GetEngine().GamePlayers[0].Actor, 1, True)
    NewWeaponOnKillInst.change_weapon(GetEngine().GamePlayers[0].Actor, 2, True)

class NewWeaponOnKill(SDKMod):
    Name = "New Weapon On Kill"
    Description = f"Changes your Weapon everytime you get a kill or when you press '{keybind.Key}'."
    Author = "juso, mopioid, and RedxYeti"
    Version = "1.0"
    SaveEnabledState = EnabledSaveType.LoadWithSettings

    Options = [mode,NumberOfKills, Refillammo, PickWeaponTypes, ShowWeaponName]
    Keybinds = [keybind]

    def __init__(self) -> None:
        self.CurrentDefData = UObject = None
        self.WeaponParts = []
        self.WeaponTypeDefinition = []
        self.BalanceDefinition = []
        self.ManufacturerDefinition = []
        self.BodyPartDefinition = []
        self.GripPartDefinition = []
        self.BarrelPartDefinition = []
        self.SightPartDefinition = []
        self.StockPartDefinition = []
        self.ElementalPartDefinition = []
        self.Accessory1PartDefinition = []
        self.Accessory2PartDefinition = []
        self.MaterialPartDefinition = []
        self.PrefixPartDefinition = []
        self.TitlePartDefinition = []
        self.KillNumber = 0
        self.types = ("pistol", "sniper", "launcher", "shotgun", "smg", "assault")
        self.RarityLevel0 = "#CDC1AF"
        self.RarityLevel1 = "#FFFFFF"
        self.RarityLevel2 = "#0BD23D"
        self.RarityLevel3 = "#3C8EFF"
        self.RarityLevel4 = "#A83FE5"
        self.RarityLevel5 = "#FFB400"
        self.RarityLevel6 = "#CA00A8"
        self.RarityLevel7 = "#FFB400"
        self.RarityLevel8 = "#000000"
        self.RarityLevel9 = "#4747CF"
        self.RarityLevel10 = "#C7C7C7"
        self.RarityLevel11 = "#0DFFFF"
        self.RarityLevel12 = "#FFFF00"
        self.RarityLevel13 = "#B89AFF"
        self.RarityLevel14 = "#FFFFFF"
        self.RarityLevel15 = "#C83291"
        self.RarityLevel16 = "#FFFF00"
        self.RarityLevel17 = "#A1FFF2"
        
        self.RarityColors = (
            self.RarityLevel0,
            self.RarityLevel1,
            self.RarityLevel2,
            self.RarityLevel3,
            self.RarityLevel4,
            self.RarityLevel5,
            self.RarityLevel6,
            self.RarityLevel7,
            self.RarityLevel8,
            self.RarityLevel9,
            self.RarityLevel10,
            self.RarityLevel11,
            self.RarityLevel12,
            self.RarityLevel13,
            self.RarityLevel14,
            self.RarityLevel15,
            self.RarityLevel16,
            self.RarityLevel17
        )
        
    def Enable(self) -> None:
        RegisterHook("WillowGame.WillowPlayerPawn.KilledEnemy", "killenemy", hk_kill_enemy)
        RegisterHook("WillowGame.WillowPawn.SetSecondWindReason", "SecondWind", SecondWindReason)
        self.populate_lists()
        #thanks onezerker :)
        LoadPackage("GD_Mercenary_Streaming_SF")
        self.NumWeapObj = FindObject(
            "NumberWeaponsEquippedExpressionEvaluator",
            "GD_Mercenary_Skills.ActionSkill.Skill_Gunzerking:ExpressionTree_0.NumberWeaponsEquippedExpressionEvaluator_0"
        )
        KeepAlive(self.NumWeapObj)
        self.NumWeapObj.NumberOfWeapons = 0

    def Disable(self) -> None:
        RemoveHook("WillowGame.WillowPlayerPawn.KilledEnemy", "killenemy")
        RemoveHook("WillowGame.WillowPawn.SetSecondWindReason", "SecondWind")
        #thanks onezerker :)
        if self.NumWeapObj is not None:
            self.NumWeapObj.NumberOfWeapons = 2
            self.NumWeapObj.ObjectFlags.A &= ~0x4000
            self.NumWeapObj = None

    def ModOptionChanged(self, option: OptionManager.Options.Base, new_val: Any) -> None:  # noqa: N802, ANN401
        if option is NumberOfKills:
            self.KillNumber = 0


    def populate_lists(self) -> None:
        self.WeaponParts = FindAll("WeaponPartDefinition")
        self.FiringModes = FindAll("FiringModeDefinition")
        self.WeaponTypeDefinition = FindAll("WeaponTypeDefinition")
        self.BalanceDefinition = FindAll("WeaponBalanceDefinition")
        self.ManufacturerDefinition = FindAll("ManufacturerDefinition")
        self.BodyPartDefinition = [x for x in self.WeaponParts if ".body." in path_name(x).lower()]
        self.GripPartDefinition = [x for x in self.WeaponParts if ".grip." in path_name(x).lower()]
        self.BarrelPartDefinition = [x for x in self.WeaponParts if ".barrel." in path_name(x).lower()]
        self.SightPartDefinition = [x for x in self.WeaponParts if ".sight." in path_name(x).lower()]
        self.StockPartDefinition = [x for x in self.WeaponParts if ".stock." in path_name(x).lower()]
        self.ElementalPartDefinition = [x for x in self.WeaponParts if ".elemental." in path_name(x).lower()]
        self.Accessory1PartDefinition = [x for x in self.WeaponParts if ".accessory." in path_name(x).lower()]
        self.Accessory2PartDefinition = [x for x in self.WeaponParts if ".accessory." in path_name(x).lower()]
        self.MaterialPartDefinition = [x for x in self.WeaponParts if ".manufacturermaterials." in path_name(x).lower()]
        self.PrefixPartDefinition = [
            x for x in FindAll("WeaponNamePartDefinition") if ".prefix" in path_name(x).lower()
        ]
        self.TitlePartDefinition = [
            x for x in FindAll("WeaponNamePartDefinition") if ".title" in path_name(x).lower()
        ]

    #user choice for weapons
    def get_weapon_type_randomized(self) -> str:
        if PickWeaponTypes.CurrentValue == "Any":
            return choice(self.types)
        elif PickWeaponTypes.CurrentValue == "Pistols":
            return "pistol"
        elif PickWeaponTypes.CurrentValue == "Snipers":
            return "sniper"
        elif PickWeaponTypes.CurrentValue == "Launchers":
            return "launcher"
        elif PickWeaponTypes.CurrentValue == "Shotguns":
            return "shotgun"
        elif PickWeaponTypes.CurrentValue == "Submachine Guns":
            return "smg"
        else:
            return "assault"
    
    def get_weapon_type_legit(self) -> UObject:
        #Level 1 weapons only spawn in these pools
        if GetEngine().GamePlayers[0].Actor.Pawn.GetExpLevel() == 1:
            p0 = FindObject("ItemPoolDefinition", "GD_Itempools.EarlyGame.Pool_Knuckledragger_Pistol")
            p1 = FindObject("ItemPoolDefinition", "GD_Itempools.EarlyGame.Pool_Knuckledragger_Pistol_P2_P3")
            p2 = FindObject("ItemPoolDefinition", "GD_Itempools.EarlyGame.Pool_Knuckledragger_Pistol_P4")
            pCollection = (p0, p1, p2)
            return choice(pCollection)
        else:
            return get_random_item_pool(PickWeaponTypes.CurrentValue)
        
    def get_random_def_data(self, pc) -> tuple:
        weapon_type = self.get_weapon_type_randomized()
        
        def choice_c(seq: Iterable, weapon_type: str) -> UObject:
            parts = [x for x in seq if weapon_type in path_name(x).lower()]
            if parts:
                return choice(parts)
            return None

        exp_level = pc.Pawn.GetExpLevel()
        return (
            choice_c(self.WeaponTypeDefinition, weapon_type),
            choice_c(self.BalanceDefinition, weapon_type),
            choice(self.ManufacturerDefinition),
            exp_level,
            choice_c(self.BodyPartDefinition, weapon_type),
            choice_c(self.GripPartDefinition, weapon_type),
            choice_c(self.BarrelPartDefinition, weapon_type),
            choice_c(self.SightPartDefinition, weapon_type),
            choice_c(self.StockPartDefinition, weapon_type),
            choice(self.ElementalPartDefinition),
            choice(self.Accessory1PartDefinition),
            choice(self.Accessory2PartDefinition),
            choice_c(self.MaterialPartDefinition, weapon_type),
            choice(self.PrefixPartDefinition),
            choice(self.TitlePartDefinition),
            exp_level,
            exp_level,
        )

    def get_random_def_data_mayhem(self, pc) -> tuple:
        exp_level = pc.Pawn.GetExpLevel()
        return (
            choice(self.WeaponTypeDefinition),
            choice(self.BalanceDefinition),
            choice(self.ManufacturerDefinition),
            exp_level,
            choice(self.WeaponParts),
            choice(self.WeaponParts),
            choice(self.WeaponParts),
            choice(self.WeaponParts),
            choice(self.WeaponParts),
            choice(self.WeaponParts),
            choice(self.WeaponParts),
            choice(self.WeaponParts),
            choice(self.WeaponParts),
            choice(self.PrefixPartDefinition),
            choice(self.TitlePartDefinition),
            exp_level,
            exp_level,
        )
        
    #hand is for gunzerker
    def change_weapon(self, PC, hand, Hotkey: bool) -> None:
        pawn_inv_manager = PC.GetPawnInventoryManager()

        if hand != 2:
            max_size = pawn_inv_manager.GetUnreadiedInventoryMaxSize()
            CurrentAmount = pawn_inv_manager.CountUnreadiedInventory()
            #unzooms and clears out the quickslots before swapping
            #3 and 4 sends extra items to the backpack
            if pawn_inv_manager.GetWeaponInSlot(1) is not None:
                pawn_inv_manager.GetWeaponInSlot(1).ForceUnzoom(True)
                pawn_inv_manager.GetWeaponInSlot(1).ClearPendingFire(0)
                pawn_inv_manager.GetWeaponInSlot(1).ClearPendingFire(1)
                pawn_inv_manager.InventoryUnreadied(pawn_inv_manager.GetWeaponInSlot(1), False)
                

            if pawn_inv_manager.GetWeaponInSlot(2) is not None:
                pawn_inv_manager.InventoryUnreadied(pawn_inv_manager.GetWeaponInSlot(2), False)

            if pawn_inv_manager.GetWeaponInSlot(3) is not None and (CurrentAmount + 1) < max_size and Hotkey == False:
                pawn_inv_manager.InventoryUnreadied(pawn_inv_manager.GetWeaponInSlot(3), True)
                CurrentAmount = pawn_inv_manager.CountUnreadiedInventory()
            else:
                pawn_inv_manager.InventoryUnreadied(pawn_inv_manager.GetWeaponInSlot(3), False)

            if pawn_inv_manager.GetWeaponInSlot(4) is not None and (CurrentAmount + 1) < max_size and Hotkey == False:
                pawn_inv_manager.InventoryUnreadied(pawn_inv_manager.GetWeaponInSlot(4), True)
            else:
                pawn_inv_manager.InventoryUnreadied(pawn_inv_manager.GetWeaponInSlot(4), False)
            
            pawn_inv_manager.ChangedWeapon()

        willow_weapon = GetEngine().GetCurrentWorldInfo().Spawn(FindClass("WillowWeapon"))
        
        if mode.CurrentValue == "Legit Weapons":
            pool = self.get_weapon_type_legit()
            spawn_item(pool, PC, get_random_def_data_legit)
            definition_data = self.CurrentDefData
            if Hotkey == True and GetEngine().GetCurrentWorldInfo().NetMode == 3:
               definition_data = self.get_random_def_data(PC)
        else:
            definition_data = self.get_random_def_data_mayhem(PC) if mode.CurrentValue == "Randomized Mayhem" else self.get_random_def_data(PC)

        willow_weapon.InitializeFromDefinitionData(tuple(definition_data), pawn_inv_manager.Instigator, True)
        willow_weapon.AdjustWeaponForBeingInBackpack()
        
        if Refillammo.CurrentValue:
            pawn_inv_manager.GiveStoredAmmoBeforeGoingToBackpack(
                definition_data[0].AmmoResource, definition_data[0].StartingAmmoCount
            )

        pawn_inv_manager.AddInventoryToBackpack(willow_weapon)

        pawn_inv_manager.ReadyBackpackInventory(willow_weapon, hand) 
    
        HUDMovie = PC.GetHUDMovie()
        
        if HUDMovie is not None and ShowWeaponName.CurrentValue and hand != 2:
            Weapon = pawn_inv_manager.GetWeaponInSlot(1)
            Prefix: str = Weapon.GetInventoryCardString(False, True, True)
            RarityColor: str = GetRarityColorHex(Weapon.GetRarityLevel())
            Message: str = f"<font size='20' color='{RarityColor}'>{Prefix}</font>"
            HUDMovie.ClearTrainingText()
            HUDMovie.AddTrainingText(Message, "Current Weapon", 3, (), "", False, 0, PC.PlayerReplicationInfo, True)

NewWeaponOnKillInst = NewWeaponOnKill()

def SecondWindReason(caller: UObject, function: UFunction, params: FStruct):
    if params.Reason == 1:
        NewWeaponOnKillInst.change_weapon(caller.controller, 1, False)
    return True

def Krieging(PC, ClassName) -> bool:
    if ClassName == "CharClass_LilacPlayerClass" and PC.bWasActionSkillRunning:
        return True
    else:
        return False

def hk_kill_enemy(caller: UObject, function: UFunction, params: FStruct):
    Killer: UObject = caller.controller
    ClassName = Killer.PlayerClass.Name

    NewWeaponOnKillInst.KillNumber += 1 if not Krieging(Killer, ClassName) else 0

    if NewWeaponOnKillInst.KillNumber < NumberOfKills.CurrentValue:
        return
    
    NewWeaponOnKillInst.KillNumber = 0
    
    if ClassName != "CharClass_Mercenary" and ClassName != "CharClass_LilacPlayerClass":
        NewWeaponOnKillInst.change_weapon(Killer, 1, False)
    else:
        if ClassName == "CharClass_Mercenary":
            NewWeaponOnKillInst.change_weapon(Killer, 1, False)  
            NewWeaponOnKillInst.change_weapon(Killer, 2, False)
            if Killer.bWasActionSkillRunning:
                #thanks onezerker :)
                CallerInv = caller.InvManager
                offhand = CallerInv.GetWeaponInSlot(2)
                CallerInv.SetCurrentWeapon(offhand, True)
                caller.MyActionSkill.SetOffHandCrosshair(offhand)
        elif not Killer.bWasActionSkillRunning:
            NewWeaponOnKillInst.change_weapon(Killer, 1, False)
        #krieg needs no swaps during action skill or they bork

def spawn_item(pool: UObject, context: UObject, callback: Callable[[UObject], None]) -> None:
    spawner = ConstructObject("Behavior_SpawnLootAroundPoint")
    spawner.ItemPools = (pool,)
    spawner.SpawnVelocityRelativeTo = 1
    spawner.CustomLocation = ((float('inf'), float('inf'), float('inf')), None, "")

    def hook(caller: UObject, function: UFunction, params: FStruct) -> bool:
        if caller is spawner:
            if len(params.SpawnedLoot):
                callback(params.SpawnedLoot[0].Inv.DefinitionData)
            RemoveHook("WillowGame.Behavior_SpawnLootAroundPoint.PlaceSpawnedItems", f"LootRandomizer.{id(spawner)}")
        return True
    RunHook("WillowGame.Behavior_SpawnLootAroundPoint.PlaceSpawnedItems", f"LootRandomizer.{id(spawner)}", hook)

    spawner.ApplyBehaviorToContext(context, (), None, None, None, ())

def get_random_def_data_legit(defData: UObject) -> tuple:
    NewWeaponOnKillInst.CurrentDefData = [
        defData.WeaponTypeDefinition,
        defData.BalanceDefinition,
        defData.ManufacturerDefinition,
        defData.ManufacturerGradeIndex,
        defData.BodyPartDefinition,
        defData.GripPartDefinition,
        defData.BarrelPartDefinition,
        defData.SightPartDefinition,
        defData.StockPartDefinition,
        defData.ElementalPartDefinition,
        defData.Accessory1PartDefinition,
        defData.Accessory2PartDefinition,
        defData.MaterialPartDefinition,
        defData.PrefixPartDefinition,
        defData.TitleItemNamePartDefinition,
        defData.GameStage,
        defData.UniqueId,
    ]

#abandon all hope ye who enter here
item_pools = {
    "Any": [
        ("GD_Itempools.WeaponPools.Pool_Weapons_All", 12),
        ("GD_Itempools.WeaponPools.Pool_Weapons_All_01_Common", 10),
        ("GD_Itempools.WeaponPools.Pool_Weapons_All_02_Uncommon", 8),
        ("GD_Itempools.WeaponPools.Pool_Weapons_All_04_Rare", 5),
        ("GD_Itempools.WeaponPools.Pool_Weapons_All_05_VeryRare", 1.6),
        ("GD_Itempools.WeaponPools.Pool_Weapons_All_05_VeryRare_Alien", 0.4),
        ("GD_Itempools.WeaponPools.Pool_Weapons_All_06_Legendary", 1)
    ],
    "Pistols": [
        ("GD_Itempools.WeaponPools.Pool_Weapons_Pistols", 12),
        ("GD_Itempools.WeaponPools.Pool_Weapons_Pistols_01_Common", 10),
        ("GD_Itempools.WeaponPools.Pool_Weapons_Pistols_02_Uncommon", 8),
        ("GD_Itempools.WeaponPools.Pool_Weapons_Pistols_04_Rare", 5),
        ("GD_Itempools.WeaponPools.Pool_Weapons_Pistols_05_VeryRare", 1.6),
        ("GD_Itempools.WeaponPools.Pool_Weapons_Pistols_05_VeryRare_Alien", 0.4),
        ("GD_Itempools.WeaponPools.Pool_Weapons_Pistols_06_Legendary", 1)
    ],
    "Snipers": [
        ("GD_Itempools.WeaponPools.Pool_Weapons_SniperRifles", 12),
        ("GD_Itempools.WeaponPools.Pool_Weapons_SniperRifles_01_Common", 10),
        ("GD_Itempools.WeaponPools.Pool_Weapons_SniperRifles_02_Uncommon", 8),
        ("GD_Itempools.WeaponPools.Pool_Weapons_SniperRifles_04_Rare", 5),
        ("GD_Itempools.WeaponPools.Pool_Weapons_SniperRifles_05_VeryRare", 1.6),
        ("GD_Itempools.WeaponPools.Pool_Weapons_SniperRifles_05_VeryRare_Alien", 0.4),
        ("GD_Itempools.WeaponPools.Pool_Weapons_SniperRifles_06_Legendary", 1)
    ],
    "Rocket Launchers": [
        ("GD_Itempools.WeaponPools.Pool_Weapons_Launchers", 12),
        ("GD_Itempools.WeaponPools.Pool_Weapons_Launchers_01_Common", 10),
        ("GD_Itempools.WeaponPools.Pool_Weapons_Launchers_02_Uncommon", 8),
        ("GD_Itempools.WeaponPools.Pool_Weapons_Launchers_04_Rare", 5),
        ("GD_Itempools.WeaponPools.Pool_Weapons_Launchers_05_VeryRare", 1.6),
        ("GD_Itempools.WeaponPools.Pool_Weapons_Launchers_05_VeryRare_Alien", 0.4),
        ("GD_Itempools.WeaponPools.Pool_Weapons_Launchers_06_Legendary", 1)
    ],
    "Shotguns": [
        ("GD_Itempools.WeaponPools.Pool_Weapons_Shotguns", 12),
        ("GD_Itempools.WeaponPools.Pool_Weapons_Shotguns_01_Common", 10),
        ("GD_Itempools.WeaponPools.Pool_Weapons_Shotguns_02_Uncommon", 8),
        ("GD_Itempools.WeaponPools.Pool_Weapons_Shotguns_04_Rare", 5),
        ("GD_Itempools.WeaponPools.Pool_Weapons_Shotguns_05_VeryRare", 1.6),
        ("GD_Itempools.WeaponPools.Pool_Weapons_Shotguns_05_VeryRare_Alien", 0.4),
        ("GD_Itempools.WeaponPools.Pool_Weapons_Shotguns_06_Legendary", 1)
    ],
    "Submachine Guns": [
        ("GD_Itempools.WeaponPools.Pool_Weapons_SMG", 12),
        ("GD_Itempools.WeaponPools.Pool_Weapons_SMG_01_Common", 10),
        ("GD_Itempools.WeaponPools.Pool_Weapons_SMG_02_Uncommon", 8),
        ("GD_Itempools.WeaponPools.Pool_Weapons_SMG_04_Rare", 5),
        ("GD_Itempools.WeaponPools.Pool_Weapons_SMG_05_VeryRare", 1.6),
        ("GD_Itempools.WeaponPools.Pool_Weapons_SMG_05_VeryRare_Alien", 0.4),
        ("GD_Itempools.WeaponPools.Pool_Weapons_SMG_06_Legendary", 1)
    ],
    "Assault Rifles": [
        ("GD_Itempools.WeaponPools.Pool_Weapons_AssaultRifles", 12),
        ("GD_Itempools.WeaponPools.Pool_Weapons_AssaultRifles_01_Common", 10),
        ("GD_Itempools.WeaponPools.Pool_Weapons_AssaultRifles_02_Uncommon", 8),
        ("GD_Itempools.WeaponPools.Pool_Weapons_AssaultRifles_04_Rare", 5),
        ("GD_Itempools.WeaponPools.Pool_Weapons_AssaultRifles_05_VeryRare", 1.6),
        ("GD_Itempools.WeaponPools.Pool_Weapons_AssaultRifles_05_VeryRare_Alien", 0.4),
        ("GD_Itempools.WeaponPools.Pool_Weapons_AssaultRifles_06_Legendary", 1)
    ]
}

def get_random_item_pool(current_value):
    if current_value in item_pools:
        pools, weights = zip(*item_pools[current_value])
        return FindObject("ItemPoolDefinition", choices(pools, weights=weights, k=1)[0])
    else:
        pools, weights = zip(*item_pools["Any"])
        return FindObject("ItemPoolDefinition", choices(pools, weights=weights, k=1)[0])

RegisterMod(NewWeaponOnKillInst)