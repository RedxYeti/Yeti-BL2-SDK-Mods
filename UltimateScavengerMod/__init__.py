from unrealsdk import Log, GetEngine, RegisterHook, RemoveHook, FindClass, FindObject,  UObject, UFunction, FStruct, LoadPackage, KeepAlive  # type: ignore
from Mods.ModMenu import EnabledSaveType, Options, RegisterMod, SDKMod #type: ignore
import unrealsdk #type: ignore
from typing import Any, Iterator, List, Optional
from .Rarity_Colors import GetRarityColorHex #type: ignore
from .HUDMessagesQueue import MessageQueue #type: ignore
import time
import math
message_queue = MessageQueue()

oidOneSlot = Options.Boolean(
    Caption="Only One Weapon Slot",
    Description="When enabled, weapons will only be equipped to your first slot. Other Weapons will be destroyed.",
    StartingValue=False,
)
oidOneZerker = Options.Boolean(
    Caption="OneZerker Style",
    Description="If you're using Only One Weapon Slot, your main weapon will be cloned. Otherwise, it will use the last weapon you had.",
    StartingValue=False,
) 
oidBackpack = Options.Boolean(
    Caption="Level Up Inventory Check",
    Description="When enabled, the mod will check through your inventory when you level up for items you can equip.",
    StartingValue=True,
) 
oidPickupOverLeveled = Options.Boolean(
    Caption="Pickup Overleveled Items",
    Description="When enabled, the mod will automatically pick up items higher than your level if you have space for it.",
    StartingValue=True,
) 
oidVendors = Options.Boolean(
    Caption="Vendor Items",
    Description="Using a vendor will give you all its items.",
    StartingValue=False,
) 
oidMoreInfo = Options.Boolean(
    Caption="More Informative Messages",
    Description="When enabled, the messages that show on screen tell more information about the item.",
    StartingValue=False,
)
oidEquippedSize = Options.Slider(
    Caption="Equipped Item Title Font Size",
    Description="Adjust the font size of the title of the message for example 'Shield Equipped'.",
    StartingValue=25,
    MinValue=4,
    MaxValue=30,
    Increment=1,
)
oidNameSize = Options.Slider(
    Caption="Item Name Font Size",
    Description="Adjust the font size of the names of items in the pop ups.",
    StartingValue=20,
    MinValue=4,
    MaxValue=30,
    Increment=1,
)
oidDescriptionSize = Options.Slider(
    Caption="Description Font Size",
    Description="Adjust the font size of the descrition entries in the pop ups.",
    StartingValue=14,
    MinValue=4,
    MaxValue=30,
    Increment=1,
)

#called when an item is dropped from inventory so it isnt re-added because dropfrom runs on the player
#could probably use 1 function for this
def Item_Thrown(caller: UObject, function: UFunction, params: FStruct):
    USMInst.Thrown = True
    return True
def Item_Thrown2(caller: UObject, function: UFunction, params: FStruct):
    if caller == GetEngine().GamePlayers[0].Actor.GetPawnInventoryManager():
        USMInst.Thrown = True
    return True
def Item_Thrown3(caller: UObject, function: UFunction, params: FStruct):
    USMInst.Thrown = True
    return True
#1 is from readied slots, 2 is from backpack, 3 is the hotkey to throw your weapon
def DidPlayerThrow() -> bool:
    if USMInst.Thrown:
        USMInst.Thrown = False
        return True
    else:
        return False

#this is from autopickup, im not a math guy
def dist(a, b) -> float:
    d = 0.0
    d = math.sqrt((b.X - a.X)**2 + (b.Y - a.Y)**2 + (b.Z - a.Z)**2)
    return d

#called when an interactive object def is used, behavior_attach was missing gambling machines
#sets a var to time so it only runs ticks for 3 seconds, even at 30 fps that should be enough
def Item_Used(caller: UObject, function: UFunction, params: FStruct) -> bool:
    USMInst.TicksRun = time.time()
    USMInst.TimetoRun = 6 if "slotmachine" in str(caller.Name).lower() else 3
    RegisterHook("WillowGame.WillowPlayerController.PlayerTick", "tick", runTicks)
    return True
#this is for interactive objects because theres no real way to get the loot
#checks for pickups within a set distance and filters them by class.name
#runs for 3 seconds because ticks are tied to framerate so real time is more consistant
#items are tracked by unique ids so funcs dont run on the same item twice
def runTicks(caller: UObject, function: UFunction, params: FStruct) -> bool:
    PC = GetEngine().GamePlayers[0].Actor
    PlayerInventory = PC.GetPawnInventoryManager()
    maxDist = 2800 #8x vanilla pickup distance
    
    for InvItem in PC.GetWillowGlobals().PickupList:
        UniqueID = InvItem.Inventory.DefinitionData.UniqueID
        distance = dist(InvItem.Location, PC.CalcViewActorLocation)
        if UniqueID not in USMInst.TickItems and InvItem.Inventory.Class.Name in USMInst.Classnames and PlayerInventory is not None and distance <= maxDist:
            NewItem = InvItem.Inventory
            ItemLevel = InvItem.Inventory.DefinitionData.ManufacturerGradeIndex
            Classname = InvItem.Inventory.Class.Name
            PlayerLevel = PC.Pawn.GetExpLevel()
            if ItemLevel <= PlayerLevel:
                if Classname != "WillowClassMod":
                    ProcessIncomingItem(NewItem, Classname, PC, PlayerInventory, True)
                elif Classname == "WillowClassMod" and NewItem.DefinitionData.ItemDefinition.PlayerClassRequirementMet(PC):
                    ProcessIncomingItem(NewItem, Classname, PC, PlayerInventory, True)
            elif oidPickupOverLeveled.CurrentValue and PlayerInventory.HasRoomInInventoryFor(InvItem):
                if Classname != "WillowClassMod":
                    PC.PickupPickupable(NewItem, False)
                    SendOverleveledMessage(Classname)
                elif Classname == "WillowClassMod" and NewItem.DefinitionData.ItemDefinition.PlayerClassRequirementMet(PC):
                    PC.PickupPickupable(NewItem, False)
                    SendOverleveledMessage(Classname)
            #tracks uniqueIDs so it doesnt run the function on the same item
            USMInst.TickItems.append(UniqueID)

    elapsed_time = time.time() - USMInst.TicksRun
    if elapsed_time >= USMInst.TimetoRun:
        USMInst.TickItems = []
        RemoveHook("WillowGame.WillowPlayerController.PlayerTick", "tick")
    return True

#checks for pickupables in the area after level up, useful at low levels
#optionally checks the players backpack for loot they can now equip
def LeveledUp(caller: UObject, function: UFunction, params: FStruct) -> bool:
    if params.bFeedback:#levelup is run when you first load your character, bfeedback is a real levelup
        USMInst.TicksRun = time.time()
        USMInst.TimetoRun = 1
        RegisterHook("WillowGame.WillowPlayerController.PlayerTick", "tick", runTicks)
        if oidBackpack.CurrentValue:
            CheckBackpack(caller, caller.GetPawnInventoryManager())
    return True
#takes all the items from the FArray and puts it into a py array, then processes the items
#without adding it to the py array first, the script would give up after a few inv items were processed
def CheckBackpack(PC, PlayerInventory):
    BackpackItems = []
    for items in PlayerInventory.Backpack:
        BackpackItems.append(items)

    for item in BackpackItems:
        if item is None:
            continue

        if item.Class.Name in USMInst.Classnames and item.DefinitionData.ManufacturerGradeIndex <= PC.Pawn.GetExpLevel():
            if item.DefinitionData.ItemDefinition is not None:
                if not item.DefinitionData.ItemDefinition.PlayerClassRequirementMet(PC):
                    continue
            ProcessIncomingItem(item, item.Class.Name, PC, PlayerInventory, False)


#hijacks the gear to be thrown, or throws it if it doesnt meet the requirements
def Item_Created(caller: UObject, function: UFunction, params: FStruct):
    PC = GetEngine().GamePlayers[0].Actor
    if PC is not None:
        Classname = caller.Class.Name
        PlayerInventory = PC.GetPawnInventoryManager()
        ItemLevel = caller.DefinitionData.ManufacturerGradeIndex
        if PC.Pawn is None or DidPlayerThrow():
            return True
        PlayerLevel = PC.Pawn.GetExpLevel()
        if Classname in USMInst.Classnames and not PC.bCinematicMode:
            if ItemLevel <= PlayerLevel and caller.DefinitionData.ItemDefinition.PlayerClassRequirementMet(PC):
                ProcessIncomingItem(caller, Classname, PC, PlayerInventory, False)
            elif oidPickupOverLeveled.CurrentValue and PlayerInventory.CountUnreadiedInventory() < PlayerInventory.GetUnreadiedInventoryMaxSize():
                if Classname != "WillowClassMod":
                    PlayerInventory.AddInventoryToBackpack(caller)
                    SendOverleveledMessage(Classname)
                elif Classname == "WillowClassMod" and caller.DefinitionData.ItemDefinition.PlayerClassRequirementMet(PC):
                    PlayerInventory.AddInventoryToBackpack(caller)
                    SendOverleveledMessage(Classname)
                else:
                    return True
            else:#item overleveled or option off
                return True
        else:#not in classnames or in cinematic
            return True
    else:#pc is none
        return True
    
#hijacks the weapon to be thrown, or throws it if it doesnt meet the requirements
def Weapon_Created(caller: UObject, function: UFunction, params: FStruct):
    PC = GetEngine().GamePlayers[0].Actor
    if PC is not None:
        if PC.Pawn is None or DidPlayerThrow():
            return True
        
        PlayerInventory = PC.GetPawnInventoryManager()
        PlayerLevel = PC.Pawn.GetExpLevel()
        ItemLevel = caller.DefinitionData.ManufacturerGradeIndex
      
        if ItemLevel <= PlayerLevel:
            if not PC.bWasCinematic: #frostburn canyon has some random weapon drop onload
                ProcessIncomingItem(caller, "WillowWeapon", PC, PlayerInventory, False)
            else:
                return True 
        elif oidPickupOverLeveled.CurrentValue and PlayerInventory.CountUnreadiedInventory() < PlayerInventory.GetUnreadiedInventoryMaxSize():
                PlayerInventory.AddInventoryToBackpack(caller)
                SendOverleveledMessage("WillowWeapon")
        else:#overleveled or option off
            return True
    else:#no PC
        return True

#mission reward functions
def Weapon_Received(caller: UObject, function: UFunction, params: FStruct):
    PC = GetEngine().GamePlayers[0].Actor
    PlayerInventory = PC.GetPawnInventoryManager()
    PlayerLevel = PC.Pawn.GetExpLevel()

    ClonedWeapon = BuildClone(PlayerInventory, params.DefinitionData, "WillowWeapon")

    ItemLevel = ClonedWeapon.DefinitionData.ManufacturerGradeIndex

    if ItemLevel <= PlayerLevel:
        ProcessIncomingItem(ClonedWeapon, "WillowWeapon", PC, PlayerInventory, False)
        return
    else:
        return True
    

#mission reward functions
def Item_Received(caller: UObject, function: UFunction, params: FStruct):
    PC = GetEngine().GamePlayers[0].Actor
    PlayerInventory = PC.GetPawnInventoryManager()
    PlayerLevel = PC.Pawn.GetExpLevel()

    ItemType = params.DefinitionData.ItemDefinition.InventoryClass.Name
    ItemLevel = params.DefinitionData.ManufacturerGradeIndex

    if ItemType in USMInst.Classnames:
        newItem = BuildClone(PlayerInventory, params.DefinitionData, ItemType)

        if ItemLevel <= PlayerLevel:
            if newItem.DefinitionData.ItemDefinition.PlayerClassRequirementMet(PC):
                ProcessIncomingItem(newItem, ItemType, PC, PlayerInventory, False)
            #wrong class
            else:
                return True
        #wrong level
        else:
            return True
    #reward was a skin or some shit
    else:
        return True

#This is basically the same as onezerker
#a port of DualWieldActionSkill.EquipInitialWeapons
def Zerker_Started(caller: UObject, function: UFunction, params: FStruct):
    PlayerInventory = caller.MyWillowPawn.InvManager

    if oidOneSlot.CurrentValue and PlayerInventory.GetWeaponInSlot(2) is None or oidOneZerker.CurrentValue:
        MainSlot = PlayerInventory.GetWeaponInSlot(1)
        if USMInst.LastGunzerkerWeapon is None or oidOneZerker.CurrentValue:
            USMInst.LastGunzerkerWeapon = MainSlot.DefinitionData

        ClonedlastWeapon = BuildClone(PlayerInventory, USMInst.LastGunzerkerWeapon, "WillowWeapon", True)

        PlayerInventory.AddInventoryToBackpack(ClonedlastWeapon)
        PlayerInventory.SetCurrentWeapon(MainSlot, False)
        PlayerInventory.ReadyBackpackInventory(ClonedlastWeapon, 2) 
        PlayerInventory.EquipWeaponFromSlot(2)

        MainSlot.RefillClip()
        ClonedlastWeapon.RefillClip()
        if caller.MyWillowPC.bInSprintState:
            caller.SetTimer(min(MainSlot.GetEquipTime(), ClonedlastWeapon.GetEquipTime()), False, "SprintTransition")
        caller.SetLeftSideControl()
        return False
    else:
        return True
    
#Action Skill Stuff
#Krieg just needs weapons not to be equipped or itll break his buzzaxe
#Gunzerker is another story
def Krieging(PC) -> bool:
   if PC.PlayerClass.Name == "CharClass_LilacPlayerClass" and PC.bWasActionSkillRunning:
       return True
   else:
       return False
def Gunzerking(PC) -> bool:
   if PC.PlayerClass.Name == "CharClass_Mercenary" and PC.bWasActionSkillRunning:
       return True
   else:
       return False
def Skill_Ended(caller: UObject, function: UFunction, params: FStruct):
    PC = GetEngine().GamePlayers[0].Actor
    PlayerInventory = PC.GetPawnInventoryManager()
    PlayerClass = PC.PlayerClass.Name
    if PlayerClass == "CharClass_Mercenary" and oidOneSlot.CurrentValue:
       PlayerInventory.RemoveFromInventory(PlayerInventory.GetWeaponInSlot(2))
       PlayerInventory.EquipWeaponFromSlot(1)
    return True

#Robs vendors as soon as the menu opens, including marcus. take that marcus.
def VendorUsed(caller: UObject, function: UFunction, params: FStruct):
    if not oidVendors.CurrentValue:
       return True
    
    CurrentVendor = caller.GetInstanceContextObject()
    Inventory = CurrentVendor.ShopInventory

    PC = GetEngine().GamePlayers[0].Actor
    PlayerInventory = PC.GetPawnInventoryManager()
    PlayerLevel = PC.Pawn.GetExpLevel()

    if Inventory is None:
        return True

    if len(Inventory) > 0:
        for item in Inventory:
            if item is None:
                continue

            if item.Class.Name in USMInst.Classnames and item.DefinitionData.ManufacturerGradeIndex <= PlayerLevel:
                if item.DefinitionData.ItemDefinition is not None:
                    if not item.DefinitionData.ItemDefinition.PlayerClassRequirementMet(PC):
                        continue
                ProcessIncomingItem(item, item.Class.Name, PC, PlayerInventory, False)
                CurrentVendor.RemoveSoldInventory(item)

        IotD = CurrentVendor.FeaturedItem
        if IotD is not None:
            if IotD.DefinitionData.ItemDefinition is not None:
                if IotD.DefinitionData.ItemDefinition.PlayerClassRequirementMet(PC):
                    ProcessIncomingItem(IotD, IotD.Class.Name, PC, PlayerInventory, False)
                    CurrentVendor.RemoveSoldInventory(IotD)
            else:
                ProcessIncomingItem(IotD, IotD.Class.Name, PC, PlayerInventory, False)
                CurrentVendor.RemoveSoldInventory(IotD)

    return True


#Adds the item thats being processed, returns the title of the message
def AddItem(NewItem, PC, bPickupable, Classname, PlayerInventory, ItemToReplace) -> str:
    if Classname == "WillowWeapon":
        LastWeaponWasEquipped = False

        if ItemToReplace is not None:
           USMInst.LastGunzerkerWeapon = ItemToReplace.DefinitionData

        if oidOneSlot.CurrentValue:
           DestroyAllWeapons(PC, PlayerInventory, PC.Pawn.Weapon)
        else:
            if ItemToReplace is not None and ItemToReplace == PC.Pawn.Weapon:
                PC.ForceUnzoom()
                PlayerInventory.ClearPendingFire(ItemToReplace, 0, False)
                PlayerInventory.ClearPendingFire(ItemToReplace, 1, False)
                PlayerInventory.RemoveFromInventory(ItemToReplace)
                LastWeaponWasEquipped = True
            elif ItemToReplace is not None:
                PlayerInventory.RemoveFromInventory(ItemToReplace)

        if bPickupable:
            PC.PickupPickupable(NewItem, False)
        else:
            PlayerInventory.AddInventoryToBackpack(NewItem)
            PlayerInventory.ReadyBackpackInventory(NewItem, USMInst.CurrentSlot)

        if LastWeaponWasEquipped and not Krieging(PC):
           PlayerInventory.EquipWeaponFromSlot(USMInst.CurrentSlot)

        if oidOneSlot.CurrentValue and Gunzerking(PC):
            if oidOneZerker.CurrentValue:
                ClonedWeapon: UObject = BuildClone(PlayerInventory, NewItem.DefinitionData, Classname, True)
                ItemToReplace = ClonedWeapon
            PlayerInventory.AddInventoryToBackpack(ItemToReplace)
            PlayerInventory.ReadyBackpackInventory(ItemToReplace, 2)
            PlayerInventory.EquipWeaponFromSlot(1)
            PlayerInventory.EquipWeaponFromSlot(2)

        Title = "Weapon Equipped Slot: " + str(USMInst.CurrentSlot)
        return Title
        
    else: #why cant everything be this simple
        if ItemToReplace is not None:
           PlayerInventory.RemoveFromInventory(ItemToReplace)

        if bPickupable:
            PC.PickupPickupable(NewItem, True)
        else:
            PlayerInventory.AddInventoryToBackpack(NewItem)
            PlayerInventory.ReadyBackpackInventory(NewItem)
            PlayerInventory.GiveGrenadeToPlayerIfGrenadeMod(NewItem)

        Title = f"{USMInst.GearTitles[USMInst.Classnames.index(Classname)]} Equipped"
        return Title

#this preps all the infomation additem and message queue need
#also adjusts the current weapon to replace
def ProcessIncomingItem(NewItem, sClassname, PC, PlayerInventory, bPickupable, bShowMessage = True):
    bWasOffhand = False
    if sClassname != "WillowWeapon":
        if not PC.IsUsingVehicleEx(False, None):
            ItemToReplace = PC.Pawn.GetEquippableItemInSlot(NewItem.GetEquipmentLocation())
        else:
            ItemToReplace = GetItemInSlot(PlayerInventory, NewItem.GetEquipmentLocation())
    else:
        if USMInst.CurrentSlot > PlayerInventory.GetWeaponReadyMax() or oidOneSlot.CurrentValue:
            USMInst.CurrentSlot = 1
        ItemToReplace = PlayerInventory.GetWeaponInSlot(USMInst.CurrentSlot)

        #skips the offhand slot
        if Gunzerking(PC) and not oidOneSlot.CurrentValue and not oidOneZerker.CurrentValue:
            if ItemToReplace == PC.Pawn.OffHandWeapon:
                bWasOffhand = True
                USMInst.CurrentSlot = PC.Pawn.Weapon.QuickSelectSlot
                ItemToReplace = PlayerInventory.GetWeaponInSlot(USMInst.CurrentSlot)
        

    #all of this is prepping the training message
    #it adds stuff to an array that gets sent to message queue. anything sent to the array is a new line.
    #less infomative is catered information, more information is the bulletpoints on item cards below stats
    Itemname = NewItem.GetInventoryCardString(False, True, True)
    ItemRarity = NewItem.GetRarityLevel()
    ItemRarityColor = GetRarityColorHex(ItemRarity)
    DefData = NewItem.DefinitionData
    ManufacturerName = DefData.ManufacturerDefinition.Grades[0].DisplayName
    equiplevel = DefData.ManufacturerGradeIndex
    StuffToAdd = []
    if sClassname == "WillowWeapon":
        typeName = DefData.WeaponTypeDefinition.Typename
        if not oidMoreInfo.CurrentValue:
            StuffToAdd.append(f"• Level: " + str(equiplevel) + ", " + ManufacturerName + " " + typeName)

        else:
            if typeName == "Pistol" or "Shotgun" or "Sniper":
                StuffToAdd.append(f"• " + GetWeaponSubType(ManufacturerName, typeName))
            else:
                StuffToAdd.append(typeName)

            StuffToAdd.append(f"• Level: " + str(equiplevel))
        
            if ManufacturerName is not None:
                StuffToAdd.append(f"• " + ManufacturerName)

            GlobalsDef = PC.GetWillowGlobals().GetGlobalsDefinition()
            for i in range(9):
                if NewItem.DoesDamageType(i) and GlobalsDef.ElementalFrameNames[i] not in USMInst.BannedNames:
                    ElementalFrame = GlobalsDef.ElementalFrameNames[i]
                    ElementName = "Slag" if ElementalFrame == "amp" else ElementalFrame
                    StuffToAdd.append(f"• " + ElementName)
                    break
            
            FunStuff = NewItem.GenerateFunStatsText()
            if FunStuff is not None:
                StuffToAdd.append(FunStuff)

        Title = AddItem(NewItem, PC, bPickupable, sClassname, PlayerInventory, ItemToReplace)

        if not oidOneSlot.CurrentValue:
            if bWasOffhand:
                USMInst.CurrentSlot += 2
            else:
                USMInst.CurrentSlot += 1
        else:
            USMInst.CurrentSlot = 1
    else:
        if not oidMoreInfo.CurrentValue:
            StuffToAdd.append(f"• Level: " + str(equiplevel) + ", " + ManufacturerName)
            if sClassname == "WillowClassMod" and NewItem.GenerateFunStatsText() is not None:
                StuffToAdd.append(NewItem.GenerateFunStatsText())
        else:
            StuffToAdd.append(f"• Level: " + str(equiplevel))
            if ManufacturerName is not None:
                StuffToAdd.append(f"• " + ManufacturerName)

            FunStuff = NewItem.GenerateFunStatsText()
            if FunStuff is not None:
                StuffToAdd.append(FunStuff)

        Title = AddItem(NewItem, PC, bPickupable, sClassname, PlayerInventory, ItemToReplace)

    if Title != "": #this is left over gunzerker stuff, but it looks nicer anyway
        TitleSize = oidEquippedSize.CurrentValue
        NameSize = oidNameSize.CurrentValue
        DescriptionSize = oidDescriptionSize.CurrentValue
        message_queue.add_message(TitleSize, NameSize, DescriptionSize, Itemname, ItemRarityColor, Title, *StuffToAdd)

class UltimateScav(SDKMod):
    Name = "Ultimate Scavenger Mod"
    Description = "Automatically equips items when they spawn."
    Author = "RedxYeti"
    Version = "1.4"
    SaveEnabledState = EnabledSaveType.LoadWithSettings
    Options = [oidOneSlot, 
               oidOneZerker, 
               oidBackpack,
               oidPickupOverLeveled,
               oidVendors,
               oidMoreInfo, 
               oidEquippedSize, 
               oidNameSize, 
               oidDescriptionSize]
    # oidManufacturer, oidRarity,
    def __init__(self) -> None:
        self.Classnames = ["WillowGrenadeMod", "WillowShield", "WillowArtifact", "WillowClassMod", "WillowWeapon"]
        self.GearTitles = ["Grenade Mod", "Shield", "Artifact", "Class Mod", "Weapon"]
        self.TickItems = []
        self.CurrentSlot = 1
        self.Thrown = False
        self.TicksRun = 0
        self.TimetoRun = 0
        self.NextTick = 0
        self.LastGunzerkerWeapon: UObject = None
        self.BannedNames = ['None', 'explosive']
        
    def Enable(self) -> None:
        RegisterHook("WillowGame.InteractiveObjectDefinition.OnUsedBy", "ItemUsed", Item_Used)
        RegisterHook("WillowGame.WillowItem.DropFrom", "ItemCreated", Item_Created)
        RegisterHook("WillowGame.WillowPlayerController.ReceiveItemReward", "ItemReceived", Item_Received)
        RegisterHook("WillowGame.WillowPlayerController.ReceiveWeaponReward", "WeaponReceived", Weapon_Received)
        RegisterHook("WillowGame.WillowPlayerController.ThrowInventory", "ItemThrown", Item_Thrown)
        RegisterHook("WillowGame.WillowInventoryManager.ThrowBackpackInventory", "ItemThrown2", Item_Thrown2)
        RegisterHook("Engine.PlayerController.ThrowWeapon", "ItemThrown3", Item_Thrown3)
        RegisterHook("WillowGame.WillowWeapon.DropFrom", "WeaponCreated", Weapon_Created)
        RegisterHook("WillowGame.DualWieldActionSkill.EquipInitialWeapons", "ZerkerStarted", Zerker_Started)
        RegisterHook("WillowGame.ActionSkill.OnActionSkillEnded", "SkillEnded", Skill_Ended)
        RegisterHook("WillowGame.WillowPlayerController.OnExpLevelChange", "LevelUp", LeveledUp)
        RegisterHook("WillowGame.VendingMachineExGFxMovie.Start", "VendorUsed", VendorUsed)
        
        #thanks onezerker :)
        LoadPackage("GD_Mercenary_Streaming_SF")
        self.NumWeapObj = FindObject(
            "NumberWeaponsEquippedExpressionEvaluator",
            "GD_Mercenary_Skills.ActionSkill.Skill_Gunzerking:ExpressionTree_0.NumberWeaponsEquippedExpressionEvaluator_0"
        )
        KeepAlive(self.NumWeapObj)
        self.NumWeapObj.NumberOfWeapons = 0
        
    def Disable(self) -> None:
        RemoveHook("WillowGame.InteractiveObjectDefinition.OnUsedBy", "ItemUsed")
        RemoveHook("WillowGame.WillowItem.DropFrom", "ItemCreated")
        RemoveHook("WillowGame.WillowPlayerController.ReceiveItemReward", "ItemReceived")
        RemoveHook("WillowGame.WillowPlayerController.ReceiveWeaponReward", "WeaponReceived")
        RemoveHook("WillowGame.WillowPlayerController.ThrowInventory", "ItemThrown")
        RemoveHook("WillowGame.WillowInventoryManager.ThrowBackpackInventory", "ItemThrown2")
        RemoveHook("Engine.PlayerController.ThrowWeapon", "ItemThrown3")
        RemoveHook("WillowGame.WillowWeapon.DropFrom", "WeaponCreated")
        RemoveHook("WillowGame.DualWieldActionSkill.EquipInitialWeapons", "ZerkerStarted")
        RemoveHook("WillowGame.ActionSkill.OnActionSkillEnded", "SkillEnded")
        RemoveHook("WillowGame.WillowPlayerController.OnExpLevelChange", "LevelUp")
        RemoveHook("WillowGame.VendingMachineExGFxMovie.Start", "VendorUsed")

        #thanks onezerker :)
        if self.NumWeapObj is not None:
            self.NumWeapObj.NumberOfWeapons = 2
            self.NumWeapObj.ObjectFlags.A &= ~0x4000
            self.NumWeapObj = None

USMInst = UltimateScav()
RegisterMod(USMInst)

#converts fstruct info into tuples 
#added an option to create bad unique ids
#thanks mopioid :)
def convert_struct(fstruct: Any, BadUniqueID: bool = False) -> Any:
    iterator: Optional[Iterator] = None
    try:
        iterator = iter(fstruct)
    except TypeError:
        pass

    if iterator:
        return [convert_struct(value, BadUniqueID) for value in iterator]

    struct_type = getattr(fstruct, "structType", None)
    if struct_type is None:
        return fstruct

    values: List[Any] = []

    while struct_type:
        attribute = struct_type.Children
        while attribute:
            attr_name = attribute.GetName()
            value = getattr(fstruct, attr_name)
            if BadUniqueID and attr_name == "UniqueID":
                value = 0
            values.append(convert_struct(value, BadUniqueID))
            attribute = attribute.Next
        struct_type = struct_type.SuperField

    return tuple(values)

#Used to clone rewards and gunzerker weapons
def BuildClone(PlayerInventory, ItemDefData, Classname, bGunzerking = False) -> Any:
    DefData = convert_struct(ItemDefData, bGunzerking)
    ClonedItem = GetEngine().GetCurrentWorldInfo().Spawn(FindClass(Classname))
    ClonedItem.InitializeFromDefinitionData(DefData, PlayerInventory.Instigator, True)
    if Classname == "WillowWeapon":
       ClonedItem.AdjustWeaponForBeingInBackpack()
    return ClonedItem

#this safely removes all weapons from the weapon slots
def DestroyAllWeapons(PC, PlayerInventory, MainWeapon):
    for i in range(1, 5):
        if PlayerInventory.GetWeaponInSlot(i) is not None:
            if PlayerInventory.GetWeaponInSlot(i) == MainWeapon:
                PC.ForceUnzoom()
                PlayerInventory.ClearPendingFire(MainWeapon, 0, False)
                PlayerInventory.ClearPendingFire(MainWeapon, 1, False)
            PlayerInventory.InventoryUnreadied(PlayerInventory.GetWeaponInSlot(i), False)

#this is a port of WillowInventoryManager.GetWeaponInSlot but for Gear
#used for when players are in vehicles, cant use PC.Pawn.GetEquippableItemInSlot
def GetItemInSlot(PlayerInventory, ItemSlot) -> UObject:
    ItemToCheck = PlayerInventory.ItemChain
    while ItemToCheck is not None:
        if ItemToCheck.GetEquipmentLocation() == ItemSlot and ItemToCheck.bReadied:
            return ItemToCheck
        ItemToCheck = ItemToCheck.Inventory
    return None

#just an extra set of messages for overleveled items
def SendOverleveledMessage(Classname):
    Title = f"Overleveled {USMInst.GearTitles[USMInst.Classnames.index(Classname)]} Added"
    message_queue.add_overleveled(Title)

#attempts to fix empty hands after getting weapons during zerker
#its basically a port of DualWieldActionSkill.EquipInitialWeapons just like onezerker uses
#but this is currently unused feces
def UpdateZerkerWeapons(PC: UObject, PlayerInventory, MainSlot, OffHandSlot):
    PC.Pawn.Weapon = PlayerInventory.GetWeaponInSlot(MainSlot)
    PC.Pawn.OffHandWeapon = PlayerInventory.GetWeaponInSlot(OffHandSlot)

    PlayerInventory.EquipWeaponFromSlot(MainSlot)
    PlayerInventory.SetCurrentWeapon(PC.Pawn.Weapon, False)
    PlayerInventory.ReadyBackpackInventory(PC.Pawn.OffHandWeapon, OffHandSlot) 
    PlayerInventory.EquipWeaponFromSlot(OffHandSlot)

    if PC.bInSprintState:
        PC.Pawn.MyActionSkill.SetTimer(min(PC.Pawn.Weapon.GetEquipTime(), PC.Pawn.OffHandWeapon.GetEquipTime()), False, "HoldOn")
    
    PC.Pawn.MyActionSkill.SetLeftSideControl()
    PC.Pawn.MyActionSkill.SetOffHandCrosshair(PC.Pawn.OffHandWeapon)

#this is extra info for the messages for people who dont know anything about the guns like me
def GetWeaponSubType(Manufacturer, WeaponType) -> str:
    subtypes = ["Machine Pistol ", "Semi-Auto ", "Revolver ", "Pump-Action ", "Break-Action ", "Bolt-Action "]
    if WeaponType == "Pistol":
        if Manufacturer == "Bandit Made" or Manufacturer == "Hyperion" or Manufacturer == "Tediore" or Manufacturer == "Vladof":
            return subtypes[0] + WeaponType
        elif Manufacturer == "Dahl":
            return subtypes[1] + WeaponType
        elif Manufacturer == "Jakobs" or Manufacturer == "Maliwan" or Manufacturer == "Torgue":
            return subtypes[2] + WeaponType
    elif WeaponType == "Shotgun":
        if Manufacturer == "Bandit Made" or Manufacturer == "Torgue":
            return subtypes[3] + WeaponType
        elif Manufacturer == "Hyperion" or Manufacturer == "Tediore":
            return subtypes[1] + WeaponType
        elif Manufacturer == "Jakobs":
            return subtypes[4] + WeaponType
    elif WeaponType == "Sniper Rifle":
        if Manufacturer == "Dahl" or Manufacturer == "Hyperion" or Manufacturer == "Maliwan" or Manufacturer == "Vladof":
            return subtypes[1] + WeaponType
        else:
            return subtypes[5] + WeaponType
    else:
        return WeaponType
    

#TODO
#make todo