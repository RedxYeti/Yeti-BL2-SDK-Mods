
from unrealsdk import Log, GetEngine, RegisterHook, RemoveHook, FindClass, FindObject,  UObject, UFunction, FStruct, ConstructObject, RunHook, LoadPackage, KeepAlive  # type: ignore
from ..ModMenu import EnabledSaveType, Options, RegisterMod, SDKMod, ClientMethod, ServerMethod, Hook, Keybind
from typing import Any, Iterator, List, Optional
import math
import time
#this is from autopickup, im not a math guy
def dist(a, b) -> float:
    d = 0.0
    d = math.sqrt((b.X - a.X)**2 + (b.Y - a.Y)**2 + (b.Z - a.Z)**2)
    return d
    
#called when any input is pressed, but only looks for secondary use being released
#then looks for nearby vending machines that are ammo machines
def SecondaryUsed(caller: UObject, function: UFunction, params: FStruct):
    PC = GetEngine().GamePlayers[0].Actor
    if params.Key == PC.PlayerInput.GetKeyForAction("UseSecondary") and params.Event == 1:
        Objects = PC.GetWillowGlobals().ClientInteractiveObjects
        for Object in Objects:
            if Object.Class.Name == "WillowVendingMachine":
                if dist(Object.Location, PC.CalcViewActorLocation) <= 350 and Object.ShopType == 1:
                    HUDMovie = PC.GetHudMovie()
                    if HUDMovie is not None:
                        Cost = GetTotalCost(PC, Object)
                        ShowMessage(PC, HUDMovie, Cost)
                        RefillAmmoKeyInst.StartTime = time.time()
                        RefillAmmoKeyInst.PC = PC
                        RefillAmmoKeyInst.HUDMovie = HUDMovie
                        RefillAmmoKeyInst.Object = Object
                        RemoveHook("WillowGame.WillowUIInteraction.InputKey", "SecondaryUsed")
                        RegisterHook("WillowGame.WillowUIInteraction.InputKey", "Confirmation", CheckConfirmation)
                        RegisterHook("WillowGame.WillowPlayerController.PlayerTick", "TimeoutTicks", StartTimeOut)
                        break
    return True

#checks how many of an ammo type is needed to max out the value
def GetAmountNeeded(PC, Index) -> int:
    CurrentAmount = RefillAmmoKeyInst.CurrentAmount[Index].GetValue(PC)
    CurrentAmount = CurrentAmount[0]
    MaxAmount = RefillAmmoKeyInst.MaxAmount[Index].GetValue(PC)
    MaxAmount = MaxAmount[0]
    AmmoPer = RefillAmmoKeyInst.AmmoPer[Index]
    if CurrentAmount < MaxAmount:
        needed = (MaxAmount - CurrentAmount + AmmoPer - 1) // AmmoPer  # Ceiling division
    else:
        needed = 0
    return int(needed)

#finds the start of the usable items, while ignoring grenade mods
#then uses that start point to create a new array to find how much it costs for all the ammo needed
def GetTotalCost(PC, Object) -> int:
    TotalCost = 0
    RefillAmmoKeyInst.Usables = []
    
    for i in range(len(Object.ShopInventory)):
        if Object.ShopInventory[i] is not None and Object.ShopInventory[i].Class.Name == "WillowUsableItem":
            RefillAmmoKeyInst.Usables = Object.ShopInventory[i:i+7]
            break
    
    RefillAmmoKeyInst.AmountsNeeded = []
    for Usable in RefillAmmoKeyInst.Usables:
        AmountNeeded = GetAmountNeeded(PC, RefillAmmoKeyInst.Usables.index(Usable))
        RefillAmmoKeyInst.AmountsNeeded.append(AmountNeeded)
        if AmountNeeded > 0:
            TotalCost += Object.GetSellingPriceForInventory(Usable, PC, AmountNeeded)

    return TotalCost


"""
Grenade = 3
Assault Rifle = 54
Pistol = 54
Launcher = 12
Shotgun = 24
SMG = 72
Sniper = 18
"""

#handles showing a hud message depending on the conditions
def ShowMessage(PC, HUDMovie, Cost):
    bEnoughCash = True if PC.PlayerReplicationInfo.GetCurrencyOnHand(0) >= Cost else False
    if HUDMovie is not None:
        HUDMovie.ClearTrainingText()
        if bEnoughCash:
            if Cost == 0:
                title = "Buy Max Ammo Failed!"
                message = "You already have max ammo!"
                ResetHooks()
            else:
                title = "Buy Max Ammo?"
                CurrentCash = PC.PlayerReplicationInfo.GetCurrencyOnHand(0)
                AcceptKey = PC.PlayerInput.GetKeyForAction("UseSecondary")
                message = f"Your Cash: ${CurrentCash}<br>Total Cost: ${Cost}<br>Accept: {AcceptKey}"
        else:
            title = "Buy Max Ammo Failed!"
            message = "Not Enough Cash!"
            ResetHooks()
            
        HUDMovie.AddTrainingText(message, title, 5, (), "", False, 0, PC.PlayerReplicationInfo, True)

#waits for the secondary use key to be released, adds the ammo if confirmed
def CheckConfirmation(caller: UObject, function: UFunction, params: FStruct):
    if not RefillAmmoKeyInst.AlreadyBought and params.Event == 1:
        if params.Key == RefillAmmoKeyInst.PC.PlayerInput.GetKeyForAction("UseSecondary"):
            AmmoToBuy = [(Index, AmountNeeded) for Index, AmountNeeded in enumerate(RefillAmmoKeyInst.AmountsNeeded) if AmountNeeded > 0]
            for Index, AmountNeeded in AmmoToBuy:
                CurrentItem = RefillAmmoKeyInst.Usables[Index]
                RefillAmmoKeyInst.Object.PlayerBuyItem(CurrentItem, RefillAmmoKeyInst.PC, AmountNeeded)
                
            RefillAmmoKeyInst.AlreadyBought = True
        if RefillAmmoKeyInst.HUDMovie is not None:
            RefillAmmoKeyInst.HUDMovie.ClearTrainingText()
    return True

#this is an auto time out for the hud message
def StartTimeOut(caller: UObject, function: UFunction, params: FStruct):
    if time.time() - RefillAmmoKeyInst.StartTime >= 5 or dist(RefillAmmoKeyInst.Object.Location, RefillAmmoKeyInst.PC.CalcViewActorLocation) > 350 or RefillAmmoKeyInst.AlreadyBought:
        if RefillAmmoKeyInst.HUDMovie is not None:
            RefillAmmoKeyInst.HUDMovie.ClearTrainingText()
        ResetHooks()
    return True

#unhooks everything and restarts the first press
def ResetHooks():
    RefillAmmoKeyInst.AlreadyBought = False
    RemoveHook("WillowGame.WillowUIInteraction.InputKey", "SecondaryUsed")
    RemoveHook("WillowGame.WillowUIInteraction.InputKey", "Confirmation")
    RemoveHook("WillowGame.WillowPlayerController.PlayerTick", "TimeoutTicks")
    RegisterHook("WillowGame.WillowUIInteraction.InputKey", "SecondaryUsed", SecondaryUsed)

class RefillAmmoKey(SDKMod):
    Name = "Refill Ammo Key"
    Description = "Adds a key on ammo vendors to refill your ammo, similar to Borderlands 3."
    Author = "RedxYeti"
    Version = "1.0"
    SaveEnabledState = EnabledSaveType.LoadWithSettings

    def Enable(self) -> None:
        self.AlreadyBought = False
        self.StartTime = 0
        self.PC = None
        self.HUDMovie = None
        self.Object = None
        self.AmountsNeeded = []
        self.Usables = []

        #sets vars to the relevant resource pools
        # Grenade
        self.GrenadeCurrent = FindObject("ResourcePoolAttributeDefinition", "D_Attributes.Ammo_Grenade_Protean.Ammo_Grenade_ProteanCurrentValue")
        self.GrenadeMax = FindObject("ResourcePoolAttributeDefinition", "D_Attributes.Ammo_Grenade_Protean.Ammo_Grenade_ProteanMaxValue")
        # Assault Rifle
        self.AssaultRifleCurrent = FindObject("ResourcePoolAttributeDefinition", "D_Attributes.AmmoResource_Combat_Rifle.Ammo_Combat_Rifle_CurrentValue")
        self.AssaultRifleMax = FindObject("ResourcePoolAttributeDefinition", "D_Attributes.AmmoResource_Combat_Rifle.Ammo_Combat_Rifle_MaxValue")
        # Shotgun
        self.ShotgunCurrent = FindObject("ResourcePoolAttributeDefinition", "D_Attributes.AmmoResource_Combat_Shotgun.Ammo_Combat_Shotgun_CurrentValue")
        self.ShotgunMax = FindObject("ResourcePoolAttributeDefinition", "D_Attributes.AmmoResource_Combat_Shotgun.Ammo_Combat_Shotgun_MaxValue")
        # SMG
        self.SMGCurrent = FindObject("ResourcePoolAttributeDefinition", "D_Attributes.AmmoResource_Patrol_SMG.Ammo_Patrol_SMG_CurrentValue")
        self.SMGMax = FindObject("ResourcePoolAttributeDefinition", "D_Attributes.AmmoResource_Patrol_SMG.Ammo_Patrol_SMG_MaxValue")
        #Pistol
        self.PistolCurrent = FindObject("ResourcePoolAttributeDefinition", "D_Attributes.AmmoResource_Repeater_Pistol.Ammo_Repeater_Pistol_CurrentValue")
        self.PistolMax = FindObject("ResourcePoolAttributeDefinition", "D_Attributes.AmmoResource_Repeater_Pistol.Ammo_Repeater_Pistol_MaxValue")
        #Launcher
        self.LauncherCurrent = FindObject("ResourcePoolAttributeDefinition", "D_Attributes.AmmoResource_Rocket_Launcher.Ammo_Rocket_Launcher_CurrentValue")
        self.LauncherMax = FindObject("ResourcePoolAttributeDefinition", "D_Attributes.AmmoResource_Rocket_Launcher.Ammo_Rocket_Launcher_MaxValue")
        # Sniper
        self.SniperCurrent = FindObject("ResourcePoolAttributeDefinition", "D_Attributes.AmmoResource_Sniper_Rifle.Ammo_Sniper_Rifle_CurrentValue")
        self.SniperMax = FindObject("ResourcePoolAttributeDefinition", "D_Attributes.AmmoResource_Sniper_Rifle.Ammo_Sniper_Rifle_MaxValue")

        self.AmmoPer = [
            3,  # Grenade
            54,  # AssaultRifle
            54,  # Pistol
            12,  # Launcher
            24,  # Shotgun
            72,  # SMG
            18,  # Sniper
        ]

        self.CurrentAmount = [
            self.GrenadeCurrent,
            self.AssaultRifleCurrent,
            self.PistolCurrent,
            self.LauncherCurrent,
            self.ShotgunCurrent,
            self.SMGCurrent,
            self.SniperCurrent,
        ]

        self.MaxAmount = [
            self.GrenadeMax,
            self.AssaultRifleMax,
            self.PistolMax,
            self.LauncherMax,
            self.ShotgunMax,
            self.SMGMax,
            self.SniperMax,
        ]


        RegisterHook("WillowGame.WillowUIInteraction.InputKey", "SecondaryUsed", SecondaryUsed)
    
    def Disable(self) -> None:
        RemoveHook("WillowGame.WillowUIInteraction.InputKey", "SecondaryUsed")
        RemoveHook("WillowGame.WillowUIInteraction.InputKey", "Confirmation")
        RemoveHook("WillowGame.WillowPlayerController.PlayerTick", "TimeoutTicks")
       

RefillAmmoKeyInst = RefillAmmoKey()
RegisterMod(RefillAmmoKeyInst)
