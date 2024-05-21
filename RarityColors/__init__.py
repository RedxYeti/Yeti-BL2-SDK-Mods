from unrealsdk import GetEngine, FindObject, Log # type: ignore
import re

class RarityLevels:
    def __init__(self):
        """
        GetRarityColorHex returns the hex value rarity color the default messaging system uses.
        example return "#FFFFFF" for white rarity

        GetRarityColorRGB returns a tuple RGB of the specified rarity.
        
        GetRartityColorRGBA returns a tuple RGBA of the specified rarity.
        """
        
RarityLevelsInst = RarityLevels()

def GetRarityColorHex(RarityLevel: int) -> str:
    PC = GetEngine().GamePlayers[0].Actor
    ItemRarityBase = PC.GetWillowGlobals().GetGlobalsDefinition().RarityLevelColors[RarityLevel].Color
    ColorsToBGRA = (ItemRarityBase.B, ItemRarityBase.G, ItemRarityBase.R, ItemRarityBase.A)
    LocalMessage = FindObject("WillowLocalMessage", "WillowGame.Default__WillowLocalMessage")
    ItemRarityColor = LocalMessage.OpenFontColorTag(ColorsToBGRA)

    pattern = r'<font color = "([^"]+)">'

    match = re.search(pattern, ItemRarityColor)

    if match:
        color_string = match.group(1)
        return color_string
    else:
        Log("Invalid Rarity Level")
    

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
