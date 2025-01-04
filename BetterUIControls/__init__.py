import unrealsdk # type: ignore
from Mods import ModMenu # type: ignore

class BetterUIControls(ModMenu.SDKMod):
    Name = "Better UI Controls"
    Author = "Yeti"
    Description = "Enables movement keys to work like arrow keys for most menus."
    Version = "0.5"
    SupportedGames: ModMenu.Game = ModMenu.Game.BL2
    Types: ModMenu.ModTypes = ModMenu.ModTypes.Utility
    SaveEnabledState: ModMenu.EnabledSaveType = ModMenu.EnabledSaveType.LoadWithSettings

    ClassNames = ["WillowClassMod", "WillowGrenadeMod", "WillowArtifact", "WillowShield"]
    IndexTracker = [10, False]
    DialogBoxEventData = ("focusIn", 0, 0, 0, 0, 0, 0)

    @ModMenu.Hook("WillowGame.StatusMenuExGFxMovie.HandleInputKey")
    def StatusMenuExGFxMovie(self, caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:    
        Key = self.GetMovementKey(params.ukey, caller.WPCOwner)
        InputFunc = self.GetStatusFunc(caller, caller.GetCurrentTab())
        if Key:
            self.GlobalHandleInput(InputFunc, caller.GetControllerID(), Key, params.uevent)
            return True
        
        if params.ukey == caller.WPCOwner.PlayerInput.GetKeyForAction("Use"):
            InputFunc(caller.GetControllerID(), "Enter", params.uevent)
            return True

        if params.ukey == caller.WPCOwner.PlayerInput.GetKeyForAction("Reload") and params.uevent == 0 and caller.GetCurrentTab() == 3:
            Thing = caller.InventoryPanel.GetSelectedThing()
            if Thing:
                self.CycleMark(caller, Thing, True)
                return True
            
        return True
    

    @ModMenu.Hook("WillowGame.StatusMenuInventoryPanelGFxObject.StartEquip")
    def StartEquip(self, caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:    
        Thing = caller.GetSelectedThing()
        if not Thing or Thing.Class.Name not in self.ClassNames or caller.bInEquippedView:
            return True

        if caller.CanReady(Thing):
            caller.BackpackPanel.SaveState()
            caller.CompleteEquip()
            caller.ParentMovie.RefreshInventoryScreen(True)
            caller.BackpackPanel.RestoreState()
            return False
        return True
    

    @ModMenu.Hook("WillowGame.VendingMachineExGFxMovie.MainInputKey")
    def VendingMachineExGFxMovie(self, caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:    
        Key = self.GetMovementKey(params.ukey, caller.WPCOwner)
        if Key:
            self.GlobalHandleInput(caller.MainInputKey, caller.GetControllerID(), Key, params.uevent)
            return True
        
        if params.ukey == caller.WPCOwner.PlayerInput.GetKeyForAction("UseSecondary"):
            caller.MainInputKey(caller.GetControllerID(), "Enter", params.uevent)

        elif params.ukey == caller.WPCOwner.PlayerInput.GetKeyForAction("Reload") and params.uevent == 0:
            Thing = caller.TwoPanelInterface.GetSelectedThing()
            if Thing:
                self.CycleMark(caller, Thing, False)
        return True
    

    @ModMenu.Hook("WillowGame.VehicleSpawnStationGFxMovie.HandleKeyDefaults")
    def SharedInfoCardInputKey(self, caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:    
        if caller.bChoosingFamily:
            if params.uevent == 0 or params.uevent == 2:
                Key = self.GetMovementKey(params.ukey, caller.WPCOwner)
                if Key:
                   self.GlobalHandleInput(caller.VehicleFamilyInputKey, caller.GetControllerID(), Key, params.uevent)
        return True
    

    @ModMenu.Hook("WillowGame.WillowGFxDialogBox.HandleInputKey")
    def WillowGFxDialogBox(self, caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:    
        if params.uevent == 0 or params.uevent == 2:
            if params.ukey == caller.WPCOwner.PlayerInput.GetKeyForAction("MoveForward"):
                caller.OnWidget1Focused(self.DialogBoxEventData)
            elif params.ukey == caller.WPCOwner.PlayerInput.GetKeyForAction("MoveBackward"):
                caller.OnWidget0Focused(self.DialogBoxEventData)

        elif params.uevent == 1 and params.ukey == caller.WPCOwner.PlayerInput.GetKeyForAction("Use"):
            caller.Accepted(caller.GetControllerID())
        return True


    @ModMenu.Hook("WillowGame.QuestAcceptGFxMovie.HandleInputKey")
    def QuestAcceptGFxMovie(self, caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:    
        Key = self.GetMovementKey(params.ukey, caller.WPCOwner)
        if Key:
            self.GlobalHandleInput(caller.HandleInputKey, caller.GetControllerID(), Key, params.uevent)
        
        if params.ukey == caller.WPCOwner.PlayerInput.GetKeyForAction("Use"):
            caller.HandleInputKey(caller.GetControllerID(), "Enter", params.uevent)
        return True
    

    def HandleRewardInputKey(self, caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
        if params.uevent == 0:
            if caller.RewardObject.GetNumItems() > 1:
                if params.ukey == caller.WPCOwner.PlayerInput.GetKeyForAction("MoveForward"):
                    caller.extOnFocusedChoice(0)
                elif params.ukey == caller.WPCOwner.PlayerInput.GetKeyForAction("MoveBackward"):
                    caller.extOnFocusedChoice(1)

            if params.ukey == caller.WPCOwner.PlayerInput.GetKeyForAction("Use"):
                caller.AcceptReward(caller.RewardObject.RewardChoiceFocused)
        return True

    
    @ModMenu.Hook("WillowGame.FastTravelStationGFxMovie.HandleInputKey")
    def FastTravelStationGFxMovie(self, caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
        if caller.PreviousSelectionIndex == 0 or caller.PreviousSelectionIndex == -1:
            caller.PreviousSelectionIndex = 1
        if params.uevent == 0 or params.uevent == 2:
            if params.ukey == caller.WPCOwner.PlayerInput.GetKeyForAction("MoveForward"):
                caller.ScrollLocationListUp(caller.PreviousSelectionIndex)
            elif params.ukey == caller.WPCOwner.PlayerInput.GetKeyForAction("MoveBackward"):
                caller.ScrollLocationListDown(caller.PreviousSelectionIndex)

            elif params.ukey == caller.WPCOwner.PlayerInput.GetKeyForAction("Use"):
                    caller.extActivate(caller.PreviousSelectionIndex)
        
        return True
    

    @ModMenu.Hook("WillowGame.FrontendGFxMovie:DefaultHandleInputKey")
    def FilterButtonInput(self, caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
        ListIndex = caller.TheList.GetSelectedIndex()
        if self.IndexTracker[0] < 1: #this gross thing is here because when you hit an arrow key to wrap, it would go up/down an extra item because the arrow key was already down
            self.IndexTracker[0] += 1
            if self.IndexTracker[1]:
                caller.TheList.SetSelectedIndex(0)
            else:
                caller.TheList.SetSelectedIndex(len(caller.TheList.IndexToEventId) - 1)
        else:
            self.IndexTracker = [10, False]

        if params.ukey == caller.WPCOwner.PlayerInput.GetKeyForAction("Use") and params.uevent == 1:
            caller.TheList.OnClikEvent(("itemClick", 0, 0, 0, ListIndex, 0, 0))

        if params.uevent == 0 or params.uevent == 2:
            if params.ukey == caller.WPCOwner.PlayerInput.GetKeyForAction("MoveForward"):
                if ListIndex > 0:
                    ListIndex -= 1
                else:
                    ListIndex = len(caller.TheList.IndexToEventId) - 1
                caller.TheList.SetSelectedIndex(ListIndex)

            if params.ukey == caller.WPCOwner.PlayerInput.GetKeyForAction("MoveBackward"):
                if ListIndex < len(caller.TheList.IndexToEventId) - 1:
                    ListIndex += 1
                else:
                    ListIndex = 0
                caller.TheList.SetSelectedIndex(ListIndex)

            if params.ukey == "Up" and ListIndex == 0:
                self.IndexTracker = [0, False]

            if params.ukey == "Down" and ListIndex == len(caller.TheList.IndexToEventId) - 1:
                self.IndexTracker = [0, True]
        return True


    def GlobalHandleInput(self, Func, *Args) -> None:
        Func(*Args)
        return


    def GetStatusFunc(self, caller, ScreenNum) -> callable:
        if ScreenNum == 1: return caller.HandleInputKey
        elif ScreenNum == 2: return caller.HandleMapInputKey
        elif ScreenNum == 3: return caller.InventoryPanelInputKey
        elif ScreenNum == 4: return caller.HandleSkillsInputKey
        elif ScreenNum == 5: return caller.HandleInputKey
        

    def GetMovementKey(self, Key, PC) -> str:
        if Key == PC.PlayerInput.GetKeyForAction("MoveForward"):
            return "Up"
        elif Key == PC.PlayerInput.GetKeyForAction("MoveBackward"):
            return "Down"
        elif Key == PC.PlayerInput.GetKeyForAction("StrafeLeft"):
            return "Left"
        elif Key == PC.PlayerInput.GetKeyForAction("StrafeRight"):
            return "Right"
        else:
            return ""


    def CycleMark(self, Movie, Thing, bInStatusMenu):
        CurrentMark = Thing.GetMark()
        Panel = None
        if bInStatusMenu:
            if not Movie.InventoryPanel.bInEquippedView:
                Panel = Movie.InventoryPanel.BackpackPanel
                Panel.SaveState()

        elif not Movie.IsCurrentSelectionSell():
            return

        if CurrentMark >= 2:
            CurrentMark = 0
        else:
            CurrentMark += 1

        def SetMark(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            if Panel:
                Panel.RestoreState()
            unrealsdk.RemoveHook("WillowGame.WillowGameViewportClient.Tick", "SetMark")
            return True

        Thing.SetMark(CurrentMark)
        Movie.PlayUISound('MenuBack')
        if bInStatusMenu:
            Movie.RefreshInventoryScreen(True)
        else:
            Movie.Refresh()
        unrealsdk.RegisterHook("WillowGame.WillowGameViewportClient.Tick", "SetMark", SetMark)
        return
    

    def Enable(self) -> None:
        unrealsdk.RegisterHook("WillowGame.QuestAcceptGFxMovie.HandleRewardInputKey", "HandleRewardInputKey", self.HandleRewardInputKey)
        unrealsdk.RegisterHook("WillowGame.LatentRewardGFxMovie.HandleRewardInputKey", "HandleRewardInputKey", self.HandleRewardInputKey)
        super().Enable()

    def Disable(self) -> None:
        unrealsdk.RemoveHook("WillowGame.QuestAcceptGFxMovie.HandleRewardInputKey", "HandleRewardInputKey")
        unrealsdk.RemoveHook("WillowGame.LatentRewardGFxMovie.HandleRewardInputKey", "HandleRewardInputKey")
        super().Disable()

       
BUIC = BetterUIControls()
ModMenu.RegisterMod(BUIC)