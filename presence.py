import time
from pypresence import Presence

class DiscordPresence:
    def __init__(self, client_id: str):
        self.rpc = Presence(client_id)
        self.rpc.connect()
        self.start_time = int(time.time())
        self.slide_index = 0

    # Here is what will be shown in your discord profile, fell free to customize but don't delete what inside {}
    def update(self, stats: dict):
        slides = [
            {
                "details": stats["rank"],
                "state": f'{stats["rr_delta"]} RR Change',
            },
            {
                "details": f'K/D: {stats["kd"]}',
                "state": f'In {stats["matches"]} matches',
            },
            {
                "details": f'Favorite Agent: {stats["favorite_agent"]}',
                "state": 'Не важно кто ты важно то что ты',
            },
        ]

        slide = slides[self.slide_index]
        self.slide_index = (self.slide_index + 1) % len(slides)

        self.rpc.update(
            **slide,
            start=self.start_time,
            large_image="valorant",
        )