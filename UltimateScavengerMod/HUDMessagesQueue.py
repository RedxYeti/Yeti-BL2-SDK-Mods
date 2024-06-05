import time
from threading import Thread, Event
from unrealsdk import GetEngine, Log  # type: ignore

class MessageQueue:
    """
    This isnt anything fancy, just a queue that takes in messages.
    Clears out old info using duplicate titles before pushing them.
    """
    def __init__(self):
        self.queue = []
        self.stop_event = Event()
        self.display_thread = Thread(target=self.process_queue)
        self.display_thread.start()
        self.noMessageTicks = 0

    def add_message(self, TitleSize, NameSize, DescriptionSize, item_name, item_rarity_color, title, *ExtraInfo):
        MainName = [f"<font size='{NameSize}' color='{item_rarity_color}'>{item_name}</font>"]
        ExtraInfo = [f"<font size='{DescriptionSize}' color='white'>{Info}</font>" for Info in ExtraInfo]
        message = "<br>".join(MainName + ExtraInfo)
        self.queue.append((message, title, TitleSize))

    def process_queue(self):
        while not self.stop_event.is_set():
            if self.queue:
                titles = set()
                filtered_queue = []
                for message, title, TitleSize in reversed(self.queue):
                    if title not in titles:
                        filtered_queue.append((message, title, TitleSize))
                        titles.add(title)
                self.queue = list(reversed(filtered_queue))
                message, title, TitleSize = self.queue.pop(0)
                queue_length = len(self.queue)
                training_text_time = 3 if queue_length > 2 else 5

                PC = GetEngine().GamePlayers[0].Actor
                HUDMovie = PC.GetHudMovie()
                if HUDMovie is not None:
                    HUDMovie.ClearTrainingText()
                    title = f"<font size='{TitleSize}'>{title}</font>"
                    HUDMovie.AddTrainingText(message, title, training_text_time, (), "", False, 0, PC.PlayerReplicationInfo, True)
                    time.sleep(training_text_time)
            else:
                time.sleep(0.5)


    def stop(self):
        self.stop_event.set()
        self.display_thread.join()

    def reset_queue(self):
        self.stop()
        self.queue = []
        self.stop_event.clear()
        self.display_thread = Thread(target=self.process_queue)
        self.display_thread.start()
