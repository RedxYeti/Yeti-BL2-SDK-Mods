from unrealsdk import Log, GetEngine #type: ignore
from ..ModMenu import EnabledSaveType, Options, RegisterMod, SDKMod, Keybind, ClientMethod, ServerMethod

keybind = Keybind(Name="Kill Skill Key", Key="Z", OnPress=lambda: KillSkillInst.DeactivateSkill(GetEngine().GamePlayers[0].Actor))

class KillSkill(SDKMod):
    Name = "End Action Skill"
    Description = f"End your action skill when you press '{keybind.Key}'."
    Author = "RedxYeti"
    Version = "1.0"
    SaveEnabledState = EnabledSaveType.LoadWithSettings
    Keybinds = [keybind]

    def DeactivateSkill(self, PC):
        if PC.bWasActionSkillRunning:
            PC.ResetMapChangeTeleportFlags()

KillSkillInst = KillSkill()
RegisterMod(KillSkillInst)
