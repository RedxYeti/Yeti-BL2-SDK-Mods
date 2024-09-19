from unrealsdk import Log, GetEngine, UObject, FindAll, FindObject, ConstructObject, FindClass #type: ignore
from unrealsdk import KeepAlive, FStruct, UFunction, RegisterHook, RemoveHook, LoadPackage #type: ignore
from Mods.ModMenu import EnabledSaveType, Options, RegisterMod, SDKMod, Game, Hook #type: ignore
from random import choice, uniform, randint
from typing import Any, Iterator, List, Optional
from Mods.ProjectileRandomizer.Lists import Packages, GlobFMVarsList, GlobGrenadeVarsList, GlobProjVarList, SillyStrings, GlobWeaponVarsList, EvilMapNames, TPSNames #type: ignore
from Mods.ProjectileRandomizer.SaveSystem import GetSaveLocation, save_to_json, load_from_json, PrepFiles#type: ignore
import os
import unrealsdk #type: ignore
from Mods import ModMenu #type: ignore



if Game.GetCurrent() == Game.BL2:
    oidMaxFiringModes = Options.Slider(
        Caption="Max Firing Modes",
        Description="Max amount of firing modes that will get loaded. \n Lower this or Max Projectiles if you're experiencing crashes.",
        StartingValue=250,
        MinValue=100,
        MaxValue=269,
        Increment=1,
    ) 
    oidMaxProjectiles = Options.Slider(
        Caption="Max Projectiles",
        Description="Max amount of projectiles that will get loaded. \n Lower this or Max Firing Modes if you're experiencing crashes.",
        StartingValue=730,
        MinValue=100,
        MaxValue=765,
        Increment=1,
    )   
else:
    oidMaxFiringModes = Options.Slider(
        Caption="Max Firing Modes",
        Description="Max amount of firing modes that will get loaded. \n Lower this or Max Projectiles if you're experiencing crashes.",
        StartingValue=150,
        MinValue=100,
        MaxValue=182,
        Increment=1,
    )
    oidMaxProjectiles = Options.Slider(
        Caption="Max Projectiles",
        Description="Max amount of projectiles that will get loaded. \n Lower this or Max Firing Modes if you're experiencing crashes.",
        StartingValue=540,
        MinValue=100,
        MaxValue=572,
        Increment=1,
    )

oidDropWeapons = Options.Boolean(
    Caption="Enemies Drop Weapons",
    Description="With this enabled, enemies will drop the weapons theyre using (even weapons that shouldn't drop). Leave this off if youre using Cold Dead Hands.",
    StartingValue=False,
)

def GenerateName(DefData, bWeapon):
    if bWeapon:
        Item = GetEngine().GetCurrentWorldInfo().Spawn(FindClass("WillowWeapon"))
    else:
        Item = GetEngine().GetCurrentWorldInfo().Spawn(FindClass("WillowGrenadeMod"))
    Item.InitializeFromDefinitionData(tuple(DefData), None, True)
    return Item.GetInventoryCardString(False, True, True)

def CreateDictEntry(UniqueID, ItemPart, FiringMode, Projectile, Name):
    if UniqueID not in ProjRandomInst.ItemInfoDict['UniqueIDs'].keys():
        ItemInfo = [ItemPart, FiringMode, Projectile, Name]
        ProjRandomInst.ItemInfoDict['UniqueIDs'][UniqueID] = ItemInfo


def GameSave(caller: UObject, function: UFunction, params: FStruct):
    if caller.GetCachedSaveGame().SaveGameId == -1:#most likely a new character
        return True
    
    if ProjRandomInst.GameSaveCalled <= 0:
        ProjRandomInst.GameSaveCalled += 1
        return True

    if ProjRandomInst.PlayerID != -1 and ProjRandomInst.SavePath is None:
        ProjRandomInst.PlayerID = caller.GetCachedSaveGame().SaveGameId
        ProjRandomInst.SavePath = GetSaveLocation(ProjRandomInst.PlayerID)
    
    save(caller, False)
    return True

def BlockStation(caller: UObject, function: UFunction, params: FStruct):
    return False

def PlayerTickPackages(caller: UObject, function: UFunction, params: FStruct):
    if not ProjRandomInst.TickTracker: 
        GetEngine().GetCurrentWorldInfo().TimeDilation = 16
        ProjRandomInst.TickTracker = True
        ProjRandomInst.PreppingPackages = True
        
        RegisterHook("WillowGame.TravelStation.PostBeginPlay", "BlockStation", BlockStation)

        if ProjRandomInst.IsBL2:
            UsedNames = ["none", "dungeons_p"]
        else:
            UsedNames = EvilMapNames.copy()

        ProjRandomInst.TravelStations = []
        ProjRandomInst.FoundMapNames = []

        LevelStations = list(caller.GetWillowGlobals().GetFastTravelStationsLookup().FastTravelStationLookupList)
        TravelStations = list(caller.GetWillowGlobals().GetFastTravelStationsLookup().LevelTravelStationLookupList)
        for station in TravelStations: LevelStations.append(station)
        for Station in LevelStations:
            if Station.StationLevelName not in ProjRandomInst.FoundMapNames: 
                if str(Station.StationLevelName).lower() not in UsedNames:
                    ProjRandomInst.TravelStations.append(Station)
                    ProjRandomInst.FoundMapNames.append(Station.StationLevelName)

        ProjRandomInst.TravelStations.reverse()
        
    if len(ProjRandomInst.TravelStations) > 0:
        MaxFM = oidMaxFiringModes.CurrentValue
        MaxProj =  oidMaxProjectiles.CurrentValue 
        
        if len(ProjRandomInst.AllFiringModes) >= MaxFM and len(ProjRandomInst.AllProjectiles) >= MaxProj:
            ProjRandomInst.TravelStations = []
            return True
        else:
            if ProjRandomInst.AreaLoaded and not caller.IsLoadingMoviePlaying():
                ProjRandomInst.AreaLoaded = False

                NextStation = ProjRandomInst.TravelStations.pop(0)
                caller.ServerTeleportPlayerToStation(NextStation)

                if len(ProjRandomInst.AllFiringModes) < MaxFM:
                    find_and_keep_alive("FiringModeDefinition", ProjRandomInst.AllFiringModes)

                if len(ProjRandomInst.AllProjectiles) < MaxProj:
                    find_and_keep_alive("ProjectileDefinition", ProjRandomInst.AllProjectiles)

                Log(f"Total Firing Modes: {len(ProjRandomInst.AllFiringModes)}/{MaxFM}")
                Log(f"Total Projectiles: {len(ProjRandomInst.AllProjectiles)}/{MaxProj}")   
                
                ProjRandomInst.LastStation = NextStation

                RemoveHook("WillowGame.WillowPlayerController.PlayerTick", "PlayerTickPackages")
                return True
            
    elif len(ProjRandomInst.TravelStations) <= 0 and (len(ProjRandomInst.AllFiringModes) < oidMaxFiringModes.CurrentValue or len(ProjRandomInst.AllProjectiles) < oidMaxProjectiles.CurrentValue):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        directory = os.path.abspath(os.path.join(base_dir, os.pardir, os.pardir, os.pardir, os.pardir))

        names = []
        blacklist = ['skin', 'head', 'audio', 'core', 'engine', 'gameframework', 'gearboxframework',
                     'gfxui', 'ipdrv', 'onlinesubsystemsteamworks', 'startup', 'willowgame']

        for root, dirs, files in os.walk(directory):
            for filename in files:
                lowername = filename.lower()
                if '.upk' in lowername:
                    if not any(item in lowername for item in blacklist):
                        name, _ = os.path.splitext(filename)
                        names.append(name)

        MaxFM = oidMaxFiringModes.CurrentValue
        MaxProj = oidMaxProjectiles.CurrentValue
        for name in names:
            if (len(ProjRandomInst.AllFiringModes) < oidMaxFiringModes.CurrentValue or len(ProjRandomInst.AllProjectiles) < oidMaxProjectiles.CurrentValue):
                LoadPackage(name)

                if len(ProjRandomInst.AllFiringModes) < MaxFM:
                    find_and_keep_alive("FiringModeDefinition", ProjRandomInst.AllFiringModes)
                if len(ProjRandomInst.AllProjectiles) < MaxProj:
                    find_and_keep_alive("ProjectileDefinition", ProjRandomInst.AllProjectiles)

                if ProjRandomInst.IsBL2:  
                    caller.ConsoleCommand("obj garbage")
                else:
                    GetEngine().GetCurrentWorldInfo().ForceGarbageCollection(True)

                Log(f"Total Firing Modes: {len(ProjRandomInst.AllFiringModes)}/{oidMaxFiringModes.CurrentValue}")
                Log(f"Total Projectiles: {len(ProjRandomInst.AllProjectiles)}/{oidMaxProjectiles.CurrentValue}")
            else:
                break

        return True
    
    else:
        Log(f"Total Firing Modes: {len(ProjRandomInst.AllFiringModes)}/{oidMaxFiringModes.CurrentValue}")
        Log(f"Total Projectiles: {len(ProjRandomInst.AllProjectiles)}/{oidMaxProjectiles.CurrentValue}")     
        GetEngine().GetCurrentWorldInfo().TimeDilation = 1
        caller.ReturnToTitleScreen(True)
        ProjRandomInst.PreppingPackages = False
        ProjRandomInst.SeenMaxMessage = True
        ProjRandomInst.LoadFromText = True
        ProjRandomInst.PlayerLoad = True
        GetEngine().GetCurrentWorldInfo().ForceGarbageCollection(True)
        RemoveHook("WillowGame.TravelStation.PostBeginPlay", "BlockStation")
        RemoveHook("WillowGame.WillowPlayerController.PlayerTick", "PlayerTickPackages")
    return True

def AreaLoaded(caller: UObject, function: UFunction, params: FStruct):
    PC = GetEngine().GamePlayers[0].Actor
    if len(ProjRandomInst.AllFiringModes) < oidMaxFiringModes.CurrentValue:
        find_and_keep_alive("FiringModeDefinition", ProjRandomInst.AllFiringModes)
        
    if len(ProjRandomInst.AllProjectiles) < oidMaxProjectiles.CurrentValue:
        find_and_keep_alive("ProjectileDefinition", ProjRandomInst.AllProjectiles)

    if ProjRandomInst.PreppingPackages:
        RegisterHook("WillowGame.WillowPlayerController.PlayerTick", "PlayerTickPackages", PlayerTickPackages)
        ProjRandomInst.AreaLoaded = True
    else:
        if ProjRandomInst.IsBL2:  
            PC.ConsoleCommand("obj garbage")
        else:
            GetEngine().GetCurrentWorldInfo().ForceGarbageCollection(True)

    ProjRandomInst.AIPawnProjectiles = {'AIPawns': {}}
    ProjRandomInst.AIPawnBeams = {'AIPawnBeams': {}}

    if ProjRandomInst.PlayerLoad: 
        PlayerLoad()
        
    for InvItem in PC.GetWillowGlobals().PickupList:
        if InvItem and InvItem.Class.Name in ProjRandomInst.Classnames:
            LoadFromDict(InvItem.Inventory, InvItem.Inventory.DefinitionData.UniqueID)
    return True

    
def CharacterChange(caller: UObject, function: UFunction, params: FStruct):
    SaveID = caller.DisplayedCharacterDataList[caller.SelectedDataIndex].SaveDataId
    if SaveID != -1:
        ProjRandomInst.PlayerID = int(SaveID)
        ProjRandomInst.SavePath = GetSaveLocation(SaveID)
        ProjRandomInst.LoadFromText = True
        ProjRandomInst.PlayerLoad = True
        ProjRandomInst.GameSaveCalled = 0
    return True

def PlayerLoad():
    if ProjRandomInst.PreppingPackages:
        ProjRandomInst.PlayerID = -1
        ProjRandomInst.SavePath = None
        ProjRandomInst.LoadFromText = False
        ProjRandomInst.PlayerLoad = False
        return

    caller = GetEngine().GamePlayers[0].Actor
    SaveID = caller.GetCachedSaveGame().SaveGameId
    if caller.GetCachedSaveGame().SaveGameId == -1:
        return

    if ProjRandomInst.SavePath is None and SaveID != -1:
       ProjRandomInst.SavePath = GetSaveLocation(SaveID)

    if ProjRandomInst.LoadFromText == True:
        ProjRandomInst.UniqueIDs = []
        ProjRandomInst.ItemInfoDict = load_from_json(ProjRandomInst.SavePath)
        for key in ProjRandomInst.ItemInfoDict['UniqueIDs'].keys(): 
            ProjRandomInst.UniqueIDs.append(key)
        ProjRandomInst.LoadFromText = False

    ItemArray = []
    Inventory = caller.GetPawnInventoryManager()

    ItemToCheck = Inventory.ItemChain
    while ItemToCheck is not None:
        ItemArray.append(ItemToCheck)
        ItemToCheck = ItemToCheck.Inventory

    ItemToCheck = list(Inventory.Backpack)
    for items in ItemToCheck:
        if items is not None:
            ItemArray.append(items)

    for i in range(1,5):
        if Inventory.GetWeaponInSlot(i) is not None:
            ItemArray.append(Inventory.GetWeaponInSlot(i))

    for item in ItemArray:
        UniqueID = item.DefinitionData.UniqueID
        if UniqueID in ProjRandomInst.ItemInfoDict['UniqueIDs'].keys():
            LoadFromDict(item, UniqueID)

    ProjRandomInst.PlayerLoad = False
    return True

def LoadFromDict(item, UniqueID):
    if UniqueID not in ProjRandomInst.ItemInfoDict['UniqueIDs'].keys():
        return
    
    ItemInfo = ProjRandomInst.ItemInfoDict['UniqueIDs'][UniqueID]
    if item.Class.Name == "WillowWeapon":
        DefData = get_def_data(item.DefinitionData)
        BarrelPart = ItemInfo[0]
        FiringMode = ItemInfo[1] 
        Projectile = ItemInfo[2]

        if BarrelPart is not None:
            NewBarrel = DupeObject(BarrelPart, GlobWeaponVarsList, "WeaponPartDefinition")
            DefData[6] = NewBarrel
            item.InitializeFromDefinitionData(tuple(DefData), None, True)
            if Projectile:
                newFM = DupeObject(FiringMode, GlobFMVarsList, "FiringModeDefinition")
                NewProjectile = DupeObject(Projectile, GlobProjVarList, "ProjectileDefinition")

                NewProjectile.bUseCustomAimDirection = False

                if NewProjectile.SpeedFormula.BaseValueConstant <= 0.0:
                    NewProjectile.SpeedFormula = (uniform(1500, 4500), None, None, 1)

                newFM.ProjectileDefinition = NewProjectile
                NewBarrel.CustomFiringModeDefinition = newFM
            else:
                NewBarrel.CustomFiringModeDefinition = FiringMode

    elif item.Class.Name == "WillowGrenadeMod":
        DefData = get_item_data(item.DefinitionData)
        DeliveryPart = ItemInfo[0]
        Projectile = ItemInfo[2]

        if DeliveryPart and Projectile:
            NewDelivery = DupeObject(DeliveryPart, GlobGrenadeVarsList, "GrenadeModPartDefinition")
            NewProjectile = ProjRandomInst.GetProjectile(Projectile)[1]
            NewProjectile.Resource = ProjRandomInst.GrenadeResource
            NewProjectile.ResourceCost = ProjRandomInst.ResourceCost
            NewProjectile.FlashIconName = "frag"
            NewDelivery.CustomProjectileDefinition = NewProjectile
            DefData[5] = NewDelivery
            item.InitializeFromDefinitionData(tuple(DefData), None, True)

def SaveQuitItems(caller: UObject, function: UFunction, params: FStruct):
    ProjRandomInst.PlayerLoad = True
    ProjRandomInst.LoadFromText = True
    save(caller, True)
    return True

def save(caller, bCleanArray):
    if ProjRandomInst.PreppingPackages:
        return

    ItemArray = []
    Inventory = caller.GetPawnInventoryManager()
    ItemToCheck = Inventory.ItemChain
    while ItemToCheck is not None:
        ItemArray.append(ItemToCheck)
        ItemToCheck = ItemToCheck.Inventory

    ItemToCheck = list(Inventory.Backpack)
    for items in ItemToCheck:
        if items is not None:
            ItemArray.append(items)

    for i in range(1,5):
        if Inventory.GetWeaponInSlot(i) is not None:
            ItemArray.append(Inventory.GetWeaponInSlot(i))


    IDs = [item.DefinitionData.UniqueID for item in ItemArray]
    SaveDict = ProjRandomInst.ItemInfoDict['UniqueIDs'].copy()
    keys_to_remove = [key for key in SaveDict if key not in IDs]
    for key in keys_to_remove:
        del SaveDict[key]
        if bCleanArray and key in ProjRandomInst.UniqueIDs:
            ProjRandomInst.UniqueIDs.remove(key)

    if ProjRandomInst.SavePath is None:
        ProjRandomInst.PlayerID = caller.GetCachedSaveGame().SaveGameId
        if ProjRandomInst.PlayerID == -1:#most likely a new character
            return True
        ProjRandomInst.SavePath = GetSaveLocation(ProjRandomInst.PlayerID)

    save_to_json(ProjRandomInst.SavePath, SaveDict)
    return True


def VendorUsed(caller: UObject, function: UFunction, params: FStruct):
    RegisterHook("WillowGame.WillowPlayerController.PlayerTick", "CheckVendors", CheckVendors)
    return True

def CheckVendors(caller: UObject, function: UFunction, params: FStruct):
    RemoveHook("WillowGame.WillowPlayerController.PlayerTick", "CheckVendors")
    caller = GetEngine().GamePlayers[0].Actor
    Objects = caller.GetWillowGlobals().ClientInteractiveObjects
    Keys = ProjRandomInst.ItemInfoDict['UniqueIDs'].keys()

    for Object in Objects:

        if Object is None:
            continue

        if  Object.Class.Name != "WillowVendingMachine":
            continue

        VendingMachine = Object
        FeaturedItem = VendingMachine.FeaturedItem
        if VendingMachine.ShopType == 0:
            for item in VendingMachine.ShopInventory:
                if item is not None and item.Class.Name == "WillowWeapon": 
                    if item.DefinitionData.UniqueId not in Keys:
                        InitializeFromDefData(item)
                    else:
                        LoadFromDict(item, item.DefinitionData.UniqueId)

            if FeaturedItem is not None and FeaturedItem.Class.Name == "WillowWeapon": 
                if FeaturedItem.DefinitionData.UniqueId not in Keys:
                    InitializeFromDefData(FeaturedItem)
                else:
                    LoadFromDict(FeaturedItem, FeaturedItem.DefinitionData.UniqueId)


        elif VendingMachine.ShopType == 1:
            for item in VendingMachine.ShopInventory:
                if item is not None and item.Class.Name == "WillowGrenadeMod":
                    if item.DefinitionData.UniqueId not in Keys:
                        InitializeFromItemData(item)
                    else:
                        LoadFromDict(item, item.DefinitionData.UniqueId)
                        
            if FeaturedItem is not None and FeaturedItem.Class.Name == "WillowGrenadeMod":
                if FeaturedItem.DefinitionData.UniqueId not in Keys:
                    InitializeFromItemData(FeaturedItem)
                else:
                    LoadFromDict(FeaturedItem, FeaturedItem.DefinitionData.UniqueId)

    return True

def InitializeFromDefData(Item):
    DefData = get_def_data(Item.DefinitionData)
    if DefData[16] not in ProjRandomInst.UniqueIDs and DefData[6]:
        DefData[6] = UpdateBarrel(DefData)
        Item.InitializeFromDefinitionData(tuple(DefData), None, True)

def InitializeFromItemData(Item):
    DefData = get_item_data(Item.DefinitionData)
    if DefData[16] not in ProjRandomInst.UniqueIDs and DefData[5]:
        DefData[5] = UpdateDelivery(DefData)
        Item.InitializeFromDefinitionData(tuple(DefData), None, True)

#Edits the definition data right before sending it to the ui
def MissionReward(caller: UObject, function: UFunction, params: FStruct):
    RewardData = convert_struct(caller.RewardData)
    RewardDataList = list(RewardData)

    for i in range(2):
        if RewardDataList[1][i] and 'WeaponTypeDefinition' in str(RewardDataList[1][i][0]):
            DefData = list(RewardDataList[1][i])
            DefData[6] = UpdateBarrel(DefData)
            RewardDataList[1][i] = tuple(DefData)

    for i in range(2):
        if RewardDataList[2][i] and 'GrenadeModDefinition' in str(RewardDataList[2][i][0]):
            DefData = list(RewardDataList[2][i])
            DefData[5] = UpdateDelivery(DefData)
            UpdateProjectile(DefData[5].CustomProjectileDefinition)
            RewardDataList[2][i] = tuple(DefData)

    RewardData = tuple(RewardDataList)
    caller.RewardData = RewardData
    return True
  
def find_and_keep_alive(definition, all_types_list):
    current_types = FindAll(definition)
    for new_type in current_types:
        if new_type not in all_types_list and new_type not in ProjRandomInst.DupedItems:
            all_types_list.append(new_type)
            KeepAlive(new_type)
    return current_types

def CombatProjectile(caller: UObject, function: UFunction, params: FStruct):

    PID = params.ContextObject.ConsumerHandle.PID

    if PID not in ProjRandomInst.AIPawnProjectiles['AIPawns'].keys():
        NewProjectile = choice(ProjRandomInst.AllProjectiles)
        NewProjectile = ProjRandomInst.GetProjectile(NewProjectile)[1]
        ProjRandomInst.AIPawnProjectiles['AIPawns'][PID] = [NewProjectile]

    caller.ProjectileDef = ProjRandomInst.AIPawnProjectiles['AIPawns'][PID][0]

    return True

def CombatShot(caller: UObject, function: UFunction, params: FStruct):
    PackageName = str(params.ContextObject.Outer).lower()
    if "bunker" in PackageName or "deathtrap" in PackageName:
        caller.FiringModeDefinition = choice(ProjRandomInst.AllFiringModes)
    return True

def CombatBeam(caller: UObject, function: UFunction, params: FStruct):
    PID = params.ContextObject.ConsumerHandle.PID
    if PID not in ProjRandomInst.AIPawnBeams['AIPawnBeams'].keys():
        NewFM = ProjRandomInst.randomFM()
        NewFM = NewFM[0] if NewFM[1] is None else NewFM[1]
        ProjRandomInst.AIPawnBeams['AIPawnBeams'][PID] = [NewFM]

    caller.FiringModeDefinition = ProjRandomInst.AIPawnBeams['AIPawnBeams'][PID][0]
    return True

def SpawnedProjectile(caller: UObject, function: UFunction, params: FStruct):
    ClassName = params.ContextObject.Class.Name
    if not ProjRandomInst.IsBL2:
        if ClassName == "OzSupportDrone":
            return True
        ProjName = str(caller.ProjectileDefinition).split(' ')[1]
        for name in TPSNames:
            if name == ProjName:
                return True
        
    if ClassName == "WillowPlayerPawn" or ClassName == "WillowAIPawn":
        NewProjectile = choice(ProjRandomInst.AllProjectiles)
        NewProjectile = DupeObject(NewProjectile, GlobProjVarList, "ProjectileDefinition")
        UpdateProjectile(NewProjectile)
        caller.ProjectileDefinition = NewProjectile

    elif ClassName == "WillowPlayerController" and params.ContextObject.Pawn.IsInjured():
        if params.ContextObject.PlayerClass.Name == "CharClass_LilacPlayerClass":
            caller.ProjectileDefinition = ProjRandomInst.GetProjectile()[1]
    return True

def UpdateProjectile(Projectile):#basically just turns certain projectiles into grenade flight path
    if Projectile.SpeedFormula.BaseValueConstant == 0.0:
        Projectile.GravityScaling = 0.8
        Projectile.UpwardVelocityBonus = 270
        Projectile.SpeedFormula.BaseValueConstant = 1700


def PostPawnInventory(caller: UObject, function: UFunction, params: FStruct):
    PawnWeapon = caller.Weapon
    if PawnWeapon is not None:
        DefData = get_def_data(PawnWeapon.DefinitionData)
        DefData[6] = UpdateBarrel(DefData)
        DupedWeapon = GetEngine().GetCurrentWorldInfo().Spawn(FindClass("WillowWeapon"))
        DupedWeapon.InitializeFromDefinitionData(tuple(DefData), None, True)

        if PawnWeapon.bDropOnDeath or oidDropWeapons.CurrentValue:
            DupedWeapon.bDropOnDeath = True
            caller.InvManager.RemoveFromInventory(PawnWeapon)
        else:
            DupedWeapon.bDropOnDeath = False

        DupedWeapon.GiveTo(caller, True)
    return True

def PlayerTickEditItems(caller: UObject, function: UFunction, params: FStruct):
    if len(ProjRandomInst.AllFiringModes) >= oidMaxFiringModes.CurrentValue and len(ProjRandomInst.AllProjectiles) >= oidMaxProjectiles.CurrentValue:
        if ProjRandomInst.SeenMaxMessage == False and not ProjRandomInst.PreppingPackages:
            ProjRandomInst.SeenMaxMessage = True
            caller.GFxUIManager.ShowTrainingDialog("Max amount of Firing Modes and Projectiles reached! <br>Have Fun!", "Projectile Randomizer", 0)

    for InvItem in caller.GetWillowGlobals().PickupList:
        if InvItem is None:
            continue
        Item = InvItem.Inventory
        Classname = Item.Class.Name
        if Classname in ProjRandomInst.Classnames and Item.DefinitionData.UniqueID not in ProjRandomInst.UniqueIDs:
            if Classname == "WillowWeapon":
                InitializeFromDefData(Item)
            else:
                InitializeFromItemData(Item)
    return True

def SpawnVeh(caller: UObject, function: UFunction, params: FStruct):
    if caller.VehicleDef and caller.VehicleDef.Seats:
        for seat in caller.VehicleDef.Seats:
            if seat.WeaponBalanceDefinition and seat.WeaponBalanceDefinition.InventoryDefinition:
                seat.WeaponBalanceDefinition.InventoryDefinition.DefaultFiringModeDefinition = choice(ProjRandomInst.AllFiringModes)

    return True

def UpdateBarrel(DefData):
    ProjRandomInst.UniqueIDs.append(DefData[16])
    NewFM = ProjRandomInst.randomFM()
    Name = str(GenerateName(DefData, True))
    CreateDictEntry(DefData[16], DefData[6], NewFM[0], NewFM[2], Name)
    NewBarrel = DupeObject(DefData[6], GlobWeaponVarsList, "WeaponPartDefinition")
    NewBarrel.CustomFiringModeDefinition = NewFM[0] if NewFM[1] is None else NewFM[1]
    return NewBarrel

def UpdateDelivery(DefData):
    ProjRandomInst.UniqueIDs.append(DefData[16])
    NewDelivery = DupeObject(DefData[5], GlobGrenadeVarsList, "GrenadeModPartDefinition")
    NewProjectile = ProjRandomInst.GetProjectile()
    Name = str(GenerateName(DefData, False))
    CreateDictEntry(DefData[16], DefData[5], None, NewProjectile[0], Name)
    NewProjectile[1].Resource = ProjRandomInst.GrenadeResource
    NewProjectile[1].ResourceCost = ProjRandomInst.ResourceCost
    NewProjectile[1].FlashIconName = "frag"
    NewDelivery.CustomProjectileDefinition = NewProjectile[1]
    return NewDelivery

SanitizeName = lambda InputName: InputName.split('&')[0]
#most of this is from part notifier
def SetItemCardEx(caller: UObject, function: UFunction, params: FStruct) -> bool:
    """
    This function is called whenever an item card is created - exactly when we need to add
    all the parts text.
    """
    # If we don't actually have an item then there's no need to do anything special
    item = params.InventoryItem.ObjectPointer
    if item is None:
        return True

    # Get the default text and convert it as needed
    text = item.GenerateFunStatsText()
    if text is None:
        text = ""

    ClassName = item.Class.Name
    if ClassName not in ProjRandomInst.Classnames:
        return True
    
    if ClassName == "WillowWeapon":
        BarrelPart = item.DefinitionData.BarrelPartDefinition
        if BarrelPart is None:
            return True

        FiringMode = item.DefinitionData.BarrelPartDefinition.CustomFiringModeDefinition
        if FiringMode is None:
            return True
        else:
            Proj = FiringMode.ProjectileDefinition
            FiringModeName = SanitizeName(FiringMode.Name)
            if FiringModeName == "":
                FiringModeName = "Unnamed"
            if "explosive" in text and not ProjRandomInst.IsBL2:
                text += "<br>"
            text += f"<font size='14' color='#CC0000'>Firing Mode:</font> <font size='14' color='#FFFFFF'> {str(FiringModeName)}</font>"
            if Proj is not None:
                text += "<br>"
                ProjName = SanitizeName(Proj.Name)
                text += f"<font size='14' color='#FF8000'>Projectile:</font> <font size='14' color='#FFFFFF'> {str(ProjName)}</font>"
    else:
        Delivery = item.DefinitionData.BetaItemPartDefinition
        if Delivery is None:
            return True
        else:
            Proj = Delivery.CustomProjectileDefinition
            ProjName = SanitizeName(Proj.Name)
            text += f"<font size='14' color='#FF8000'>Projectile:</font> <font size='14' color='#FFFFFF'> {str(ProjName)}</font>"


    # `SetItemCardEx` is actually quite complex, so rather than replicate it, we'll just
    #  write our text, then let the it run as normal, but block it from overwriting the text
    def SetFunStats(caller: UObject, function: UFunction, params: FStruct) -> bool:
        RemoveHook("WillowGame.ItemCardGFxObject.SetFunStats", "FunStats")
        return False

    RegisterHook("WillowGame.ItemCardGFxObject.SetFunStats", "FunStats", SetFunStats)

    caller.SetFunStats(text)

    return True

def AchievementBlock(caller: UObject, function: UFunction, params: FStruct):
    return False

def CreateButton(caller: UObject, function: UFunction, params: FStruct):
    if params.Caption == "$WillowMenu.WillowScrollingListDataProviderFrontEnd.Play_Continue":
        if not ProjRandomInst.SeenMaxMessage:
            caller.AddListItem(25371, "PREP PROJECTILE RANDOMIZER", False, False)
        else:
            RegisterHook("WillowGame.WillowPlayerController.ReturnToTitleScreen", "SaveQuitItems", SaveQuitItems)
    return True

def ButtonPressed(caller: UObject, function: UFunction, params: FStruct):
    if params.EventID == 25371:
        RemoveHook("WillowGame.WillowPlayerController.ReturnToTitleScreen", "SaveQuitItems")
        ProjRandomInst.PreppingPackages = True
        params.TheList.MyOwnerMovie.OnClose()
        RegisterHook("WillowGame.WillowPlayerController.PlayerTick", "PlayerTickPackages", PlayerTickPackages)
        RemoveHook("WillowGame.WillowScrollingListDataProviderFrontEnd.HandleClick", "ButtonPressed")
    return True

def get_def_data(defData) -> Any:
        return [
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

def get_item_data(defData: UObject) -> Any:
    return [
        defData.ItemDefinition,
        defData.BalanceDefinition,
        defData.ManufacturerDefinition,
        defData.ManufacturerGradeIndex,
        defData.AlphaItemPartDefinition,
        defData.BetaItemPartDefinition,
        defData.GammaItemPartDefinition,
        defData.DeltaItemPartDefinition,
        defData.EpsilonItemPartDefinition,
        defData.ZetaItemPartDefinition,
        defData.EtaItemPartDefinition,
        defData.ThetaItemPartDefinition,
        defData.MaterialItemPartDefinition,
        defData.PrefixItemNamePartDefinition,
        defData.TitleItemNamePartDefinition,
        defData.GameStage,
        defData.UniqueId,
    ]

#frankenstiened convert struct
def convert_struct(fstruct: Any, depth: int = 0, max_depth: int = 10) -> Any:
    if depth > max_depth:
        return fstruct

    try:
        iterator: Optional[Iterator] = None
        try:
            iterator = iter(fstruct)
        except TypeError:
            pass

        if iterator:
            return [convert_struct(value, depth + 1, max_depth) for value in iterator]

        struct_type = getattr(fstruct, "structType", None)
        if struct_type is None:
            return fstruct

        values: List[Any] = []

        while struct_type:
            attribute = struct_type.Children
            while attribute:
                attr_name = attribute.GetName()
                value = getattr(fstruct, attr_name)
                if attr_name in ProjRandomInst.StringNames:
                    values.append(str(value))#few attr causing issues if theyre strings
                else:
                    values.append(convert_struct(value, depth + 1, max_depth))
                attribute = attribute.Next
            struct_type = struct_type.SuperField

        return tuple(values)
    except Exception as e:
        Log(f"Error in convert_struct: {e}, fstruct: {fstruct}")
        raise

#this will dupe an object, even if the object doesnt exist
def DupeObject(ObjectToDupe, GlobalsList, ClassType: str):
    try:
        ObjectName = ObjectToDupe.Name 
    except:
        ObjectName =  "Unnamed"
    NewName = f"{ObjectName}&{str(uniform(1,20000))}"#hack way of keeping names unique
    NewObject = ConstructObject(ClassType, ProjRandomInst.MainPackage, NewName)
    varslist = GlobalsList
    for var in varslist:
        try:
            setattr(NewObject, var, getattr(ObjectToDupe, var))
        except AttributeError:
            #Log(f"passed on >> {var} from >> {ObjectToDupe}")
            pass
        except:
            #Log(f"DupeObject {var}")
            struct = getattr(ObjectToDupe, var)
            setattr(NewObject, var, convert_struct(struct))

    KeepAlive(NewObject)
    ProjRandomInst.DupedItems.append(NewObject)
    return NewObject

class ProjRandom(SDKMod):
    Name = "Projectile Randomizer"
    Description = f"Randomizes Projectiles."
    Author = "RedxYeti"
    Version = "1.0"
    SaveEnabledState = EnabledSaveType.LoadWithSettings

    Options = [oidMaxFiringModes, oidMaxProjectiles, oidDropWeapons] 

    def Enable(self) -> None:
        if Game.GetCurrent() == Game.BL2:
            self.IsBL2 = True
        else:
            self.IsBL2 = False
        self.LoadedMapsPath = None
        self.LastStation = None

        self.GameSaveCalled = 0
        self.PreppingPackages = False
        self.SeenMaxMessage = False
        
        self.LoadedMaps = []
        self.TravelStations = []
        self.FoundMapNames = []
        self.AreaLoaded = True

        self.CurrentFT = -1
        self.TickTracker = False

        PrepFiles()
        
        self.FirstSave = True
        self.PlayerLoad = True
        self.LoadFromText = True
        self.SavePath = None
        self.PlayerID = -1

        self.Classnames = ["WillowWeapon", "WillowGrenadeMod"]
        self.UniqueIDs = []
        self.RecentlyUsedFM = []
        self.RecentlyUsedProj = []

        self.ItemInfoDict = {'UniqueIDs': {}}
        self.AIPawnProjectiles = {'AIPawns': {}}
        self.AIPawnBeams = {'AIPawnBeams': {}}

        self.MainPackage = ConstructObject("Package", None, "ProjectileRandomizerPackage")
        KeepAlive(self.MainPackage)

        self.GrenadeResource = FindObject("ResourceDefinition", "D_Resources.AmmoResources.Ammo_Grenade_Protean")
        self.ResourceCost = (1, None, None, 1)

        self.AllFiringModes = []
        self.AllProjectiles = []
        self.DupedItems = []

        self.StringNames = SillyStrings
        self.Packages = Packages

        for package in self.Packages:
            LoadPackage(package)
            find_and_keep_alive("FiringModeDefinition", self.AllFiringModes)
            find_and_keep_alive("ProjectileDefinition", self.AllProjectiles)

        RegisterHook("WillowGame.WillowPlayerController.WillowClientDisableLoadingMovie", "AreaLoaded", AreaLoaded)
        RegisterHook("WillowGame.WillowAIPawn.PostStartingInventoryAdded", "PostInv", PostPawnInventory)
        RegisterHook("WillowGame.MissionRewardGFxObject.SetUpRewardsPage", "MissionReward", MissionReward)
        RegisterHook("WillowGame.WillowPlayerController.ReturnToTitleScreen", "SaveQuitItems", SaveQuitItems)
        RegisterHook("WillowGame.WillowPlayerController.PlayerTick", "PlayerTickEditItems", PlayerTickEditItems)
        RegisterHook("WillowGame.Behavior_SpawnProjectile.ApplyBehaviorToContext", "SpawnedProjectile", SpawnedProjectile)
        RegisterHook("WillowGame.Behavior_AIThrowProjectileAtTarget.ApplyBehaviorToContext", "CombatProjectile", CombatProjectile)
        RegisterHook("WillowGame.Behavior_FireBeam.ApplyBehaviorToContext", "CombatBeam", CombatBeam)
        RegisterHook("WillowGame.Behavior_FireShot.ApplyBehaviorToContext", "CombatShot", CombatShot)
        RegisterHook("WillowGame.WillowPlayerController.ClientUnlockAchievement", "AchievementBlock", AchievementBlock)
        RegisterHook("WillowGame.WillowGFxLobbyLoadCharacter.BeginClose", "CharacterChange", CharacterChange)
        RegisterHook("WillowGame.WillowVehicle.PostBeginPlay", "SpawnVeh", SpawnVeh)
        RegisterHook("WillowGame.WillowVendingMachine.GenerateInventory", "GenerateInventory", CheckVendors)
        RegisterHook("WillowGame.ItemCardGFxObject.SetItemCardEx", "SetItemCardEx", SetItemCardEx)
        RegisterHook("WillowGame.WillowPlayerController.GeneratePlayerSaveGame", "GameSave", GameSave)
        RegisterHook("WillowGame.VendingMachineExGFxMovie.Start", "VendorUsed", VendorUsed)
        RegisterHook("WillowGame.WillowScrollingList.AddListItem", "CreateButton", CreateButton)
        RegisterHook("WillowGame.WillowScrollingListDataProviderFrontEnd.HandleClick", "ButtonPressed", ButtonPressed)
        
        if GetEngine().GamePlayers[0].Actor.GetFrontEndMovie():
            GetEngine().GamePlayers[0].Actor.GetFrontEndMovie().TheList.Refresh()

    def Disable(self) -> None:
        RemoveHook("WillowGame.WillowPlayerController.WillowClientDisableLoadingMovie", "AreaLoaded")
        RemoveHook("WillowGame.WillowAIPawn.PostStartingInventoryAdded", "PostInv")
        RemoveHook("WillowGame.MissionRewardGFxObject.SetUpRewardsPage", "MissionReward")
        RemoveHook("WillowGame.WillowPlayerController.ReturnToTitleScreen", "SaveQuitItems")
        RemoveHook("WillowGame.WillowPlayerController.PlayerTick", "PlayerTickEditItems")
        RemoveHook("WillowGame.Behavior_SpawnProjectile.ApplyBehaviorToContext", "SpawnedProjectile")
        RemoveHook("WillowGame.Behavior_AIThrowProjectileAtTarget.ApplyBehaviorToContext", "CombatProjectile")
        RemoveHook("WillowGame.Behavior_FireBeam.ApplyBehaviorToContext", "CombatBeam")
        RemoveHook("WillowGame.Behavior_FireShot.ApplyBehaviorToContext", "CombatShot")
        RemoveHook("WillowGame.WillowPlayerController.ClientUnlockAchievement", "AchievementBlock")
        RemoveHook("WillowGame.WillowGFxLobbyLoadCharacter.BeginClose", "CharacterChange")
        RemoveHook("WillowGame.WillowVehicle.PostBeginPlay", "SpawnVeh")
        RemoveHook("WillowGame.WillowVendingMachine.GenerateInventory", "GenerateInventory")
        RemoveHook("WillowGame.ItemCardGFxObject.SetItemCardEx", "SetItemCardEx")
        RemoveHook("WillowGame.WillowPlayerController.GeneratePlayerSaveGame", "GameSave")
        RemoveHook("WillowGame.VendingMachineExGFxMovie.Start", "VendorUsed")
        RemoveHook("WillowGame.WillowScrollingList.AddListItem", "CreateButton")
        RemoveHook("WillowGame.WillowScrollingListDataProviderFrontEnd.HandleClick", "ButtonPressed")
        RemoveHook("WillowGame.TravelStation.PostBeginPlay", "BlockStation")
        RemoveHook("WillowGame.WillowPlayerController.PlayerTick", "PlayerTickPackages")

        if GetEngine().GamePlayers[0].Actor.GetFrontEndMovie():
            GetEngine().GamePlayers[0].Actor.GetFrontEndMovie().TheList.Refresh()

        
    def randomFM(self):
        FiringMode = choice(self.AllFiringModes)
        if len(self.AllFiringModes) > round(oidMaxFiringModes.CurrentValue / 2):
            while FiringMode in self.RecentlyUsedFM:
                FiringMode = choice(self.AllFiringModes)

        if FiringMode not in self.RecentlyUsedFM:
            self.RecentlyUsedFM.append(FiringMode)

        if len(self.RecentlyUsedFM) >= round(oidMaxFiringModes.CurrentValue / 2):
            self.RecentlyUsedFM.pop(0)

        if randint(1,2) == 1:
            return [FiringMode, None, None]
        else:
            while FiringMode.ProjectileDefinition is None:
                FiringMode = choice(self.AllFiringModes)

            newFM = DupeObject(FiringMode, GlobFMVarsList, "FiringModeDefinition")

            NewProj = choice(self.AllProjectiles)
            if len(self.AllProjectiles) > round(oidMaxProjectiles.CurrentValue / 3):
                while NewProj in self.RecentlyUsedProj:
                    NewProj = choice(self.AllProjectiles)

            if  NewProj not in self.RecentlyUsedProj:
                self.RecentlyUsedProj.append(NewProj)

            if len(self.RecentlyUsedProj) >= round(oidMaxProjectiles.CurrentValue / 3):
                self.RecentlyUsedProj.pop(0)

            UpdateProj = DupeObject(NewProj, GlobProjVarList, "ProjectileDefinition")

            UpdateProj.bUseCustomAimDirection = False

            if UpdateProj.SpeedFormula.BaseValueConstant <= 0.0:
                UpdateProj.SpeedFormula = (uniform(1500, 4500), None, None, 1)
            
            newFM.ProjectileDefinition = UpdateProj
            return [FiringMode, newFM, NewProj]
    
    def GetProjectile(self, Projectile = None):
        if Projectile is None:
            Projectile = choice(self.AllProjectiles)
            if len(self.AllProjectiles) > round(oidMaxProjectiles.CurrentValue / 3):
                while Projectile in self.RecentlyUsedProj:
                    Projectile = choice(self.AllProjectiles)
                    
            if Projectile not in self.RecentlyUsedProj:
                self.RecentlyUsedProj.append(Projectile)

            if len(self.RecentlyUsedProj) >= round(oidMaxProjectiles.CurrentValue / 3):
                self.RecentlyUsedProj.pop(0)

        newProj = DupeObject(Projectile, GlobProjVarList, "ProjectileDefinition")

        UpdateProjectile(newProj)

        return [Projectile, newProj]

ProjRandomInst = ProjRandom()
if __name__ == "__main__":
    unrealsdk.Log(f"[{ProjRandomInst.Name}] Manually loaded")
    for mod in ModMenu.Mods:
        if mod.Name == ProjRandomInst.Name:
            if mod.IsEnabled:
                mod.Disable()
            ModMenu.Mods.remove(mod)
            unrealsdk.Log(f"[{ProjRandomInst.Name}] Removed last ProjRandomInst")

            # Fixes inspect.getfile()
            ProjRandomInst.__class__.__module__ = mod.__class__.__module__
            break
RegisterMod(ProjRandomInst)