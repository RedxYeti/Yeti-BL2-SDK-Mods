from unrealsdk import FindObject, GetEngine #type: ignore
import os
import json
import time

lasttime = 0

def save_to_json(file_path, unique_ids_data):
    global lasttime
    if os.path.exists(file_path) and not os.access(file_path, os.W_OK):
        #read only
        if time.time() - lasttime > 120:
            lasttime = time.time()
            PC = GetEngine().GamePlayers[0].Actor
            Hud = PC.GetHUDMovie()
            if Hud:
                Hud.ClearTrainingText()
                Message = f"<font size='20'>Your current save json is read only!</font>"
                Hud.AddTrainingText(Message, "Projectile Randomizer", 5, (), "", False, 0, PC.PlayerReplicationInfo, True)
        return
    
    data = {}
    for unique_id, values in unique_ids_data.items():
        item_entry = {
            "Item Name": values[3],  
            "Item Part": str(values[0]),
            "Firing Mode": str(values[1]),
            "Projectile": str(values[2])
        }
        data[unique_id] = item_entry
    
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)


def load_from_json(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    
    SavedIDs = {'UniqueIDs': {}}
    for unique_id, entry in data.items():
        NewList = []
        
        item_part = entry["Item Part"]
        firing_mode = entry["Firing Mode"]
        projectile = entry["Projectile"]
        Name = entry["Item Name"]

        value_list = [item_part, firing_mode, projectile, Name]

        for value in value_list:
            if value is None:
                NewList.append(None)
            elif value is Name:
                NewList.append(Name)
            else:
                split_parts = value.split(' ', 1)
                part1 = split_parts[0] 
                part2 = split_parts[1] if len(split_parts) > 1 else ''
                part2 = SanitizeName(part2)

                NewObject = FindObject(part1, part2)
                NewList.append(NewObject)

        SavedIDs['UniqueIDs'][int(unique_id)] = NewList
    return SavedIDs


def append_to_file(TextFile, entry):
    base_dir = os.path.dirname(__file__)
    file_path = os.path.join(base_dir, "Saves", TextFile)
    with open(file_path, 'a') as file:
        file.write(entry + '\n')

def PrepFiles():
    subdir = 'Saves'
    base_dir = os.path.dirname(__file__)
    dir_path = os.path.join(base_dir, subdir)

    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    

def GetSaveLocation(PlayerSaveID):
    subdir = 'Saves'
    base_dir = os.path.dirname(__file__)
    dir_path = os.path.join(base_dir, subdir)

    file_path = os.path.join(dir_path, f"{PlayerSaveID}.json")

    if not os.path.exists(file_path):
        with open(file_path, 'w') as file:
            json.dump({}, file, indent=4)

    return file_path

SanitizeName = lambda InputName: InputName.split('&')[0]
