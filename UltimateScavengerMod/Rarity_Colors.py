from unrealsdk import GetEngine, FindObject, Log # type: ignore
import re

class RarityLevels:
    def __init__(self):
        """
        GetRarityColorHex returns the hex value color for html style messages.
        example return "#FFFFFF" for white rarity

        GetRarityColorRGB returns a tuple RGB of the specified rarity.

        GetRartityColorRGBA returns a tuple RGBA of the specified rarity.
        """
        
RarityLevelsInst = RarityLevels()

def GetRarityColorHex(RarityLevel: int) -> str:
    PC = GetEngine().GamePlayers[0].Actor
    RarityLevel = 7 if RarityLevel == 8 or RarityLevel == 9 or RarityLevel == 10 else RarityLevel
    ItemRarityBase = PC.GetWillowGlobals().GetGlobalsDefinition().RarityLevelColors[RarityLevel].Color
    return '#{:02x}{:02x}{:02x}'.format(ItemRarityBase.R, ItemRarityBase.G, ItemRarityBase.B)


def GetRarityRGB(RarityLevel: int) -> tuple:
    PC = GetEngine().GamePlayers[0].Actor
    ItemRarityBase = PC.GetWillowGlobals().GetGlobalsDefinition().RarityLevelColors[RarityLevel].Color
    ColorsToRGB = (ItemRarityBase.R, ItemRarityBase.G, ItemRarityBase.B)

    return ColorsToRGB


def GetRarityRGBA(RarityLevel: int) -> tuple:
    PC = GetEngine().GamePlayers[0].Actor
    ItemRarityBase = PC.GetWillowGlobals().GetGlobalsDefinition().RarityLevelColors[RarityLevel].Color
    ColorsToRGBA = (ItemRarityBase.R, ItemRarityBase.G, ItemRarityBase.B, ItemRarityBase.A)

    return ColorsToRGBA