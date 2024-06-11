from unrealsdk import Log, GetEngine, RegisterHook, RemoveHook, FindClass, FindObject,  UObject, UFunction, FStruct, LoadPackage, KeepAlive  # type: ignore
from ..ModMenu import RegisterMod, SDKMod, Options, EnabledSaveType, ModTypes, Keybind

#used for moving the timer while the hud is up
def MoveKeys(caller: UObject, function: UFunction, params: FStruct):
    if CountDownInst.EnableMovement.CurrentValue and params.Event == 0:
        if params.Key == "Up":
            CountDownInst.yPosSlider.CurrentValue -= 1
        if params.Key == "Down":
            CountDownInst.yPosSlider.CurrentValue += 1
        if params.Key == "Left":
            CountDownInst.xPosSlider.CurrentValue -= 1
        if params.Key == "Right":
            CountDownInst.xPosSlider.CurrentValue += 1
        if params.Key == "MouseScrollUp":
            CountDownInst.SizeSlider.CurrentValue += 1
        if params.Key == "MouseScrollDown":
            CountDownInst.SizeSlider.CurrentValue -= 1
    return True

#registers the hooks needed when the action skill ends, also sets the first time
def EndActionSkill(caller: UObject, function: UFunction, params: FStruct):
    CountDownInst.TimeRemaining = int(round(GetCooldownTime(caller.MyWillowPC)))
    RegisterHook("WillowGame.WillowGameViewportClient.PostRender", "Postrender", onPostRender)
    RegisterHook("WillowGame.WillowPlayerController.PlayerTick", "PlayerTicks", PlayerTicks)
    return True

#this is used to check if the floats are close enough to ints for the timer
def is_close(value, threshold=1e-2):
    return abs(value - round(value)) < threshold

#checks the attributes current value
def GetCooldownTime(PC) -> float:
    cooldown_time, _ = CountDownInst.SkillAttrDef.GetValue(PC)
    return cooldown_time

#while playerticks is hooked, it updates the current value of how much time is left
#also logs the last time it updated so that if its >= 1 it will update right away
def PlayerTicks(caller: UObject, function: UFunction, params: FStruct):
    cooldown_time = GetCooldownTime(caller)
    if cooldown_time > 0:
        if is_close(cooldown_time) or (CountDownInst.LastCheck - cooldown_time) >= 1:
            CountDownInst.TimeRemaining = int(round(cooldown_time))
            CountDownInst.LastCheck = CountDownInst.TimeRemaining
    else:
        RemoveHook("WillowGame.WillowPlayerController.PlayerTick", "PlayerTicks")
        RemoveHook("WillowGame.WillowGameViewportClient.PostRender", "Postrender")
    return True

#Zeta made this, this sends the canvas update
def onPostRender(caller: UObject, function: UFunction, params: FStruct) -> bool:
    CountDownInst.displayFeedback(params)
    return True

class ActionSkillCountdown(SDKMod):
    Name: str = "Action Skill Countdown"
    Author: str = "ZetaDæmon and RedxYeti"
    Description: str = (
        "Adds a countdown timer to your hud for your action skill."
    )
    Version: str = "1.0"
    Types: ModTypes = ModTypes.Utility
    SaveEnabledState: EnabledSaveType = EnabledSaveType.LoadWithSettings

    TimeRemaining: int = 1

    def __init__(self) -> None:
        self.LastCheck = 0
        self.Options = []
        self.RedSlider = Options.Slider (
            Caption="Red",
            Description="Red value for the text colour.",
            StartingValue=255,
            MinValue=0,
            MaxValue=255,
            Increment=1,
            IsHidden=False
        )
        self.GreenSlider = Options.Slider (
            Caption="Green",
            Description="Green value for the text colour.",
            StartingValue=0,
            MinValue=0,
            MaxValue=255,
            Increment=1,
            IsHidden=False
        )
        self.BlueSlider = Options.Slider (
            Caption="Blue",
            Description="Blue value for the text colour.",
            StartingValue=0,
            MinValue=0,
            MaxValue=255,
            Increment=1,
            IsHidden=False
        )
        self.AlphaSlider = Options.Slider (
            Caption="Alpha",
            Description="Alpha value for the text colour.",
            StartingValue=215,
            MinValue=0,
            MaxValue=255,
            Increment=1,
            IsHidden=False
        )
        self.TextColour = Options.Nested (
            Caption = "Text Colour",
            Description = "Text colour for the farm counter.",
            Children = [self.RedSlider, self.GreenSlider, self.BlueSlider, self.AlphaSlider],
            IsHidden = False
        )
        self.SizeSlider = Options.Slider (
            Caption="Counter Size",
            Description="Counter scaling as a percentage.",
            StartingValue=110,
            MinValue=50,
            MaxValue=500,
            Increment=1,
            IsHidden=False
        )
        self.xPosSlider = Options.Slider (
            Caption="X Position",
            Description="X position for the counter as a percentage of the total screen.",
            StartingValue=0,
            MinValue=0,
            MaxValue=1000,
            Increment=1,
            IsHidden=False
        )
        self.yPosSlider = Options.Slider (
            Caption="Y Position",
            Description="Y position for the counter as a percentage of the total screen.",
            StartingValue=0,
            MinValue=0,
            MaxValue=1000,
            Increment=1,
            IsHidden=False
        )
        self.CounterPos = Options.Nested (
            Caption = "Counter Position",
            Description = "Text position for the farm counter.",
            Children = [self.xPosSlider, self.yPosSlider],
            IsHidden = False
        )
        self.FontChoice = Options.Spinner(
            Caption="Font",
            Description="Use this to pick your font.",
            StartingValue="WillowBody",
            Choices=["WillowBody",
                     "WillowHead",
                     "HUD",
                     "Engine 1",
                     "Engine 2"]
        )
        self.ShowInMenu = Options.Boolean(
            Caption="Show in Pause Menu",
            Description="When enabled, the timer will show in the pause menu for changing position and color.",
            StartingValue=False,
        )
        self.EnableMovement = Options.Boolean(
            Caption="Enable Movement Keys",
            Description="When enabled, you can use the arrow keys to move the timer and the scrollwheel to change the size.",
            StartingValue=False,
        )
        self.Options = [
            self.TextColour,
            self.CounterPos,
            self.SizeSlider,
            self.FontChoice,
            self.EnableMovement,
            self.ShowInMenu
        ]

    #Zeta made this, takes in the info from the function below to create the canvas objects
    def DisplayText(self, canvas, text, x, y, color, scalex, scaley) -> None:
        fontindex = self.FontChoice.Choices.index(self.FontChoice.CurrentValue)
        canvas.Font = FindObject("Font", self.Fonts[fontindex])

        trueX = canvas.SizeX * x
        trueY = canvas.SizeX * y

        canvas.SetPos(trueX, trueY, 0)
        
        try:
            canvas.SetDrawColorStruct(color)  # b, g, r, a
        except:
            pass
        canvas.DrawText(str(text), False, scalex, scaley)

    #Zeta made most of this
    #if it passes the checks, it takes in the settings and sends them to the canvas
    def displayFeedback(self, params):
        PC = GetEngine().GamePlayers[0].Actor
        if not params.Canvas:
            return True
        
        if PC.GetHUDMovie() is None or PC.bViewingThirdPersonMenu:
           if PC.GFxUIManager.IsMoviePlaying(PC.PauseMenuDefinition) and self.ShowInMenu.CurrentValue:
                this = "is for player configuration"
           else:
               return True
        
        if PC.MyWillowPawn.IsInjured() or PC.MyWillowPawn.DrivenVehicle is not None:
           return True
        
        canvas = params.Canvas
        self.DisplayText(
            canvas,
            self.TimeRemaining,
            self.xPosSlider.CurrentValue / 1000,
            self.yPosSlider.CurrentValue / 1000,
            (
                self.BlueSlider.CurrentValue,
                self.GreenSlider.CurrentValue,
                self.RedSlider.CurrentValue,
                self.AlphaSlider.CurrentValue
            ),
            self.SizeSlider.CurrentValue / 100,
            self.SizeSlider.CurrentValue / 100
        )
        return True

    def Enable(self):
        RegisterHook("WillowGame.ActionSkill.OnActionSkillEnded", "EndActionSkill", EndActionSkill)
        RegisterHook("WillowGame.WillowUIInteraction.InputKey", "MoveKeys", MoveKeys)
        self.SkillAttrDef = FindObject("AttributeDefinition", "D_Attributes.ActiveSkillCooldownResource.ActiveSkillCooldownCurrentValue")
        self.Fonts = [
            "UI_Fonts.Font_Willowbody_18pt",
            "UI_Fonts.Font_Willowhead_8pt",
            "UI_Fonts.Font_Hud_Medium",
            "EngineFonts.SmallFont",
            "EngineFonts.TinyFont"
        ]
        self.AltPressed = False
    def Disable(self):
        RemoveHook("WillowGame.WillowGameViewportClient.PostRender", "Postrender")
        RemoveHook("WillowGame.ActionSkill.OnActionSkillEnded", "EndActionSkill")

CountDownInst = ActionSkillCountdown()
RegisterMod(CountDownInst)