
from unrealsdk import Log, GetEngine, RegisterHook, RemoveHook, UObject, UFunction, FStruct # type: ignore
from ..ModMenu import EnabledSaveType, RegisterMod, SDKMod, Options, OptionManager, Keybind
from typing import Any
import os

#Takes in inputs when pressed, then filters them through the dictionary
#If the key is found, it adds the commands to an array
def DualBind(caller: UObject, function: UFunction, params: FStruct):
    if params.Event == 0:
        key = params.Key
        if key in DualBindsInst.Bindings:
            for command in DualBindsInst.Bindings[key]:
                DualBindsInst.Commands.append(command)

        if DualBindsInst.ShiftPressed and f"Shift + {key}" in DualBindsInst.Bindings:
            for command in DualBindsInst.Bindings[f"Shift + {key}"]:
                DualBindsInst.Commands.append(command)

        if DualBindsInst.ControlPressed and f"Control + {key}" in DualBindsInst.Bindings:
            for command in DualBindsInst.Bindings[f"Control + {key}"]:
                DualBindsInst.Commands.append(command)

        if DualBindsInst.AltPressed and f"Alt + {key}" in DualBindsInst.Bindings:
            for command in DualBindsInst.Bindings[f"Alt + {key}"]:
                DualBindsInst.Commands.append(command)
    return True

#this just tracks shift, ctrl, alt being pressed or released
#optionally, sends the last pressed key to the console
def ExtraKeyTracker(caller: UObject, function: UFunction, params: FStruct):
    if params.Event == 0:
        if oidShowKey.CurrentValue:
            Log(params.Key)

        if params.Key == "LeftShift":
           DualBindsInst.ShiftPressed = True
        
        if params.Key == "LeftControl":
           DualBindsInst.ControlPressed = True

        if params.Key == "LeftAlt":
           DualBindsInst.AltPressed = True
    
    if params.Event == 1:
        if params.Key == "LeftShift":
           DualBindsInst.ShiftPressed = False
        
        if params.Key == "LeftControl":
           DualBindsInst.ControlPressed = False

        if params.Key == "LeftAlt":
           DualBindsInst.AltPressed = False

    return True

#this is playerticks, much more reliable when multiple commands arent run on the same tick
#runs the oldest command then removes it from the array
#if its a player_behavior, it gets sent to HandleBehavior
def CommandsQueue(caller: UObject, function: UFunction, params: FStruct): 
    if len(DualBindsInst.Commands) > 0:
        command = DualBindsInst.Commands.pop(0)
        if str(command).lower() in DualBindsInst.Behaviors:
            HandleBehavior(caller, str(command).lower())
        else:
            caller.ConsoleCommand(command)
    return True

#these behaviors dont have console commands
#also has an option to refresh the bindings
def HandleBehavior(PC, Behavior):
    if Behavior == "melee":
        PC.Behavior_Melee()
    elif Behavior == "reload":
        PC.Behavior_Reload()
    elif Behavior == "throwgrenade":
        PC.Behavior_ThrowGrenade()
    elif Behavior == "updatebindings":
        resetBindings(PC)

#this just allows players to update thier bindings without closing the game
def resetBindings(PC):
    DualBindsInst.Bindings = DualBindsInst.BuildDualBinds()
    PC.GFxUIManager.ShowTrainingDialog("All dual binds updated!", "Dual Binds", 0)


oidShowKey = Options.Boolean(
    Caption= "Show Key in Console",
    Description= "Shows the name of the pressed keys in console.",
    StartingValue= False
)

class DualBinds(SDKMod):
    Name = "Dual Bind"
    Description = "Allows for keys to have multiple inputs. Check the readme for commands."
    Author = "RedxYeti"
    Version = "1.0"
    SaveEnabledState = EnabledSaveType.LoadWithSettings

    Options = [oidShowKey]

    def Enable(self):
        self.ShiftPressed = False
        self.ControlPressed = False
        self.AltPressed = False
        self.Behaviors = ["melee", "reload", "throwgrenade", "updatebindings"]
        self.Commands = []
        self.Bindings = self.BuildDualBinds()
        RegisterHook("WillowGame.WillowUIInteraction.InputKey", "DualBind", DualBind)
        RegisterHook("WillowGame.WillowUIInteraction.InputKey", "ExtraKeyTracker", ExtraKeyTracker)
        RegisterHook("WillowGame.WillowPlayerController.PlayerTick", "CommandQueue", CommandsQueue)
    
    def Disable(self):
        self.Bindings = None
        RemoveHook("WillowGame.WillowUIInteraction.InputKey", "DualBind")
        RemoveHook("WillowGame.WillowUIInteraction.InputKey", "ExtraKeyTracker")
        RemoveHook("WillowGame.WillowPlayerController.PlayerTick", "CommandQueue")

    def BuildDualBinds(self):
        ModDir = os.path.dirname(__file__)
        ModPath = os.path.join(ModDir, "DualBinds.ini")

        CommandsDict = {}
        with open(ModPath, 'r') as ini_file:
            for line in ini_file:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = list(map(str.strip, line.split(',')))
                key = str(parts[0])
                commands = [str(command) for command in parts[1:]]
                CommandsDict[key] = commands
        return CommandsDict

DualBindsInst = DualBinds()
RegisterMod(DualBindsInst)