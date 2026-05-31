from __future__ import annotations

import csv
from pathlib import Path


PRICE_BY_TIER = {
    "aaa": 59.99,
    "mid": 39.99,
    "indie": 19.99,
}

METACRITIC_BY_TIER = {
    "aaa": 84,
    "mid": 78,
    "indie": 75,
}

DEFAULT_TAGS_BY_GENRE = {
    "Action": ["combat", "fast-paced", "single-player"],
    "Adventure": ["story-driven", "exploration", "single-player"],
    "RPG": ["role-playing", "choices", "character build"],
    "Shooter": ["gunplay", "multiplayer", "competitive"],
    "Strategy": ["tactics", "management", "planning"],
    "Racing": ["racing", "cars", "time trials"],
    "Simulation": ["simulation", "management", "sandbox"],
    "Sports": ["sports", "competitive", "career mode"],
    "Horror": ["horror", "survival", "atmospheric"],
    "Puzzle": ["puzzle", "logic", "mind-bending"],
    "Indie": ["indie", "creative", "stylized"],
    "Casual": ["casual", "relaxing", "short sessions"],
}

GAME_ENTRIES = [
    {
        "title": "Grand Theft Auto V",
        "genres": ["Action", "Adventure"],
        "tags": ["open world", "heists", "crime"],
        "aliases": ["gta v", "gta 5", "grand theft auto v", "grand theft auto 5", "gtav"],
        "tier": "aaa",
    },
    {
        "title": "Red Dead Redemption 2",
        "genres": ["Action", "Adventure"],
        "tags": ["open world", "western", "story-driven"],
        "aliases": ["rdr2", "red dead redemption 2", "red dead 2"],
        "tier": "aaa",
    },
    {
        "title": "Baldur's Gate 3",
        "genres": ["RPG"],
        "tags": ["party", "choices", "story-driven"],
        "aliases": ["bg3", "baldurs gate 3", "baldur's gate 3"],
        "tier": "aaa",
    },
    {
        "title": "Cyberpunk 2077",
        "genres": ["Action", "RPG"],
        "tags": ["open world", "story-driven", "futuristic"],
        "aliases": ["cyberpunk", "cp2077"],
        "tier": "aaa",
    },
    {
        "title": "The Witcher 3 Wild Hunt",
        "genres": ["RPG", "Adventure"],
        "tags": ["open world", "story-driven", "fantasy"],
        "aliases": ["witcher 3", "the witcher 3"],
        "tier": "aaa",
    },
    {
        "title": "Elden Ring",
        "genres": ["RPG", "Action"],
        "tags": ["open world", "challenge", "fantasy"],
        "aliases": ["elden ring"],
        "tier": "aaa",
    },
    {
        "title": "Sekiro Shadows Die Twice",
        "genres": ["Action"],
        "tags": ["challenge", "combat", "single-player"],
        "aliases": ["sekiro"],
        "tier": "aaa",
    },
    {"title": "Dark Souls III", "genres": ["Action", "RPG"], "tier": "aaa"},
    {"title": "Dark Souls Remastered", "genres": ["Action", "RPG"], "tier": "aaa"},
    {"title": "Nioh 2", "genres": ["Action", "RPG"], "tier": "mid"},
    {"title": "Monster Hunter World", "genres": ["Action", "RPG"], "tier": "aaa"},
    {"title": "Monster Hunter Rise", "genres": ["Action", "RPG"], "tier": "aaa"},
    {"title": "Dragon's Dogma 2", "genres": ["RPG", "Action"], "tier": "aaa"},
    {"title": "Starfield", "genres": ["RPG", "Adventure"], "tier": "aaa"},
    {"title": "Divinity Original Sin 2", "genres": ["RPG", "Strategy"], "tier": "aaa"},
    {"title": "Pathfinder Wrath of the Righteous", "genres": ["RPG"], "tier": "mid"},
    {"title": "Dragon Age Inquisition", "genres": ["RPG", "Adventure"], "tier": "aaa"},
    {"title": "Mass Effect Legendary Edition", "genres": ["RPG", "Action"], "tier": "aaa"},
    {"title": "Fallout 4", "genres": ["RPG", "Action"], "tier": "aaa"},
    {"title": "Fallout New Vegas", "genres": ["RPG"], "tier": "mid"},
    {"title": "The Elder Scrolls V Skyrim", "genres": ["RPG", "Adventure"], "tier": "aaa"},
    {"title": "The Elder Scrolls IV Oblivion", "genres": ["RPG", "Adventure"], "tier": "mid"},
    {"title": "Kingdom Come Deliverance", "genres": ["RPG", "Adventure"], "tier": "mid"},
    {"title": "Star Wars Jedi Fallen Order", "genres": ["Action", "Adventure"], "tier": "aaa"},
    {"title": "Star Wars Jedi Survivor", "genres": ["Action", "Adventure"], "tier": "aaa"},
    {"title": "Assassin's Creed Valhalla", "genres": ["Action", "Adventure"], "tier": "aaa"},
    {"title": "Assassin's Creed Odyssey", "genres": ["Action", "Adventure"], "tier": "aaa"},
    {"title": "Assassin's Creed Origins", "genres": ["Action", "Adventure"], "tier": "aaa"},
    {"title": "Watch Dogs Legion", "genres": ["Action", "Adventure"], "tier": "aaa"},
    {"title": "Watch Dogs 2", "genres": ["Action", "Adventure"], "tier": "aaa"},
    {"title": "Far Cry 5", "genres": ["Action", "Adventure"], "tier": "aaa"},
    {"title": "Far Cry 6", "genres": ["Action", "Adventure"], "tier": "aaa"},
    {"title": "Just Cause 4", "genres": ["Action", "Adventure"], "tier": "mid"},
    {"title": "Mafia Definitive Edition", "genres": ["Action", "Adventure"], "tier": "mid"},
    {"title": "Hitman 3", "genres": ["Action", "Adventure"], "tier": "aaa"},
    {"title": "Metal Gear Solid V The Phantom Pain", "genres": ["Action", "Adventure"], "tier": "aaa"},
    {"title": "Ghost Recon Wildlands", "genres": ["Action", "Adventure"], "tier": "aaa"},
    {"title": "Ghost Recon Breakpoint", "genres": ["Action", "Adventure"], "tier": "aaa"},
    {"title": "Horizon Zero Dawn", "genres": ["Action", "Adventure"], "tier": "aaa"},
    {"title": "Horizon Forbidden West", "genres": ["Action", "Adventure"], "tier": "aaa"},
    {"title": "Tomb Raider", "genres": ["Action", "Adventure"], "tier": "mid"},
    {"title": "Rise of the Tomb Raider", "genres": ["Action", "Adventure"], "tier": "mid"},
    {"title": "Shadow of the Tomb Raider", "genres": ["Action", "Adventure"], "tier": "mid"},
    {"title": "Uncharted Legacy of Thieves", "genres": ["Action", "Adventure"], "tier": "aaa"},
    {"title": "God of War", "genres": ["Action", "Adventure"], "tier": "aaa"},
    {"title": "Marvel's Spider-Man Remastered", "genres": ["Action", "Adventure"], "tier": "aaa"},
    {"title": "Marvel's Spider-Man Miles Morales", "genres": ["Action", "Adventure"], "tier": "aaa"},
    {"title": "Control", "genres": ["Action", "Adventure"], "tier": "mid"},
    {"title": "Death Stranding", "genres": ["Adventure", "Simulation"], "tier": "mid"},
    {"title": "Days Gone", "genres": ["Action", "Adventure"], "tier": "mid"},
    {"title": "The Last of Us Part I", "genres": ["Action", "Adventure"], "tier": "aaa"},
    {"title": "Diablo IV", "genres": ["RPG", "Action"], "tier": "aaa"},
    {"title": "Diablo III", "genres": ["RPG", "Action"], "tier": "aaa"},
    {"title": "Path of Exile", "genres": ["RPG", "Action"], "tier": "mid"},
    {"title": "Torchlight II", "genres": ["RPG", "Action"], "tier": "indie"},
    {"title": "Grim Dawn", "genres": ["RPG", "Action"], "tier": "indie"},
    {"title": "Hades", "genres": ["Action", "Indie"], "tier": "indie"},
    {"title": "Hades II", "genres": ["Action", "Indie"], "tier": "indie"},
    {"title": "Hollow Knight", "genres": ["Adventure", "Indie"], "tier": "indie"},
    {"title": "Ori and the Blind Forest", "genres": ["Adventure", "Indie"], "tier": "indie"},
    {"title": "Ori and the Will of the Wisps", "genres": ["Adventure", "Indie"], "tier": "indie"},
    {"title": "Dead Cells", "genres": ["Action", "Indie"], "tier": "indie"},
    {"title": "Celeste", "genres": ["Adventure", "Indie"], "tier": "indie"},
    {"title": "Cuphead", "genres": ["Action", "Indie"], "tier": "indie"},
    {"title": "Stardew Valley", "genres": ["Simulation", "Indie"], "tier": "indie"},
    {"title": "Terraria", "genres": ["Adventure", "Indie"], "tier": "indie"},
    {"title": "Valheim", "genres": ["Adventure", "Indie"], "tier": "indie"},
    {"title": "Minecraft", "genres": ["Simulation", "Adventure"], "tier": "mid"},
    {"title": "No Man's Sky", "genres": ["Adventure", "Simulation"], "tier": "mid"},
    {"title": "Subnautica", "genres": ["Adventure", "Survival"], "tier": "indie"},
    {"title": "Subnautica Below Zero", "genres": ["Adventure", "Survival"], "tier": "indie"},
    {"title": "Sea of Thieves", "genres": ["Adventure", "Action"], "tier": "mid"},
    {"title": "Sea of Stars", "genres": ["RPG", "Indie"], "tier": "indie"},
    {"title": "Outer Wilds", "genres": ["Adventure", "Indie"], "tier": "indie"},
    {"title": "Disco Elysium", "genres": ["RPG", "Indie"], "tier": "indie"},
    {"title": "Persona 5 Royal", "genres": ["RPG"], "tier": "aaa"},
    {"title": "Persona 4 Golden", "genres": ["RPG"], "tier": "mid"},
    {"title": "Yakuza 0", "genres": ["Action", "Adventure"], "tier": "mid"},
    {"title": "Like a Dragon Infinite Wealth", "genres": ["RPG", "Adventure"], "tier": "aaa"},
    {"title": "Final Fantasy VII Remake", "genres": ["RPG", "Action"], "tier": "aaa"},
    {"title": "Final Fantasy XIV", "genres": ["RPG", "Adventure"], "tier": "aaa"},
    {"title": "Final Fantasy XVI", "genres": ["RPG", "Action"], "tier": "aaa"},
    {"title": "Dragon Quest XI", "genres": ["RPG"], "tier": "aaa"},
    {"title": "Tales of Arise", "genres": ["RPG"], "tier": "aaa"},
    {"title": "NieR Automata", "genres": ["Action", "RPG"], "tier": "aaa"},
    {"title": "Octopath Traveler II", "genres": ["RPG"], "tier": "aaa"},
    {"title": "Triangle Strategy", "genres": ["Strategy", "RPG"], "tier": "mid"},
    {"title": "Call of Duty Modern Warfare III", "genres": ["Shooter"], "tier": "aaa"},
    {"title": "Call of Duty Warzone", "genres": ["Shooter"], "tier": "aaa"},
    {"title": "Battlefield 2042", "genres": ["Shooter"], "tier": "aaa"},
    {"title": "Battlefield 1", "genres": ["Shooter"], "tier": "aaa"},
    {"title": "Apex Legends", "genres": ["Shooter"], "tier": "mid"},
    {"title": "Valorant", "genres": ["Shooter"], "tier": "mid"},
    {"title": "Counter-Strike 2", "genres": ["Shooter"], "tier": "mid"},
    {"title": "Overwatch 2", "genres": ["Shooter"], "tier": "aaa"},
    {"title": "Rainbow Six Siege", "genres": ["Shooter"], "tier": "aaa"},
    {"title": "Destiny 2", "genres": ["Shooter", "RPG"], "tier": "aaa"},
    {"title": "Halo Infinite", "genres": ["Shooter"], "tier": "aaa"},
    {"title": "Titanfall 2", "genres": ["Shooter"], "tier": "aaa"},
    {"title": "Doom Eternal", "genres": ["Shooter"], "tags": ["fast-paced", "arena combat", "single-player"], "tier": "aaa"},
    {"title": "Doom 2016", "genres": ["Shooter"], "tags": ["fast-paced", "arena combat", "single-player"], "tier": "aaa"},
    {"title": "Wolfenstein II The New Colossus", "genres": ["Shooter"], "tier": "aaa"},
    {"title": "BioShock Infinite", "genres": ["Shooter", "Adventure"], "tier": "mid"},
    {"title": "Borderlands 3", "genres": ["Shooter", "RPG"], "tier": "aaa"},
    {"title": "Borderlands 2", "genres": ["Shooter", "RPG"], "tier": "mid"},
    {"title": "The Division 2", "genres": ["Shooter", "RPG"], "tier": "aaa"},
    {"title": "Payday 3", "genres": ["Shooter", "Action"], "tier": "aaa"},
    {"title": "Payday 2", "genres": ["Shooter", "Action"], "tier": "mid"},
    {"title": "Civilization VI", "genres": ["Strategy"], "tier": "aaa"},
    {"title": "Civilization V", "genres": ["Strategy"], "tier": "mid"},
    {"title": "Total War Warhammer III", "genres": ["Strategy"], "tier": "aaa"},
    {"title": "Total War Three Kingdoms", "genres": ["Strategy"], "tier": "aaa"},
    {"title": "Age of Empires IV", "genres": ["Strategy"], "tier": "aaa"},
    {"title": "Age of Empires II Definitive Edition", "genres": ["Strategy"], "tier": "mid"},
    {"title": "StarCraft II", "genres": ["Strategy"], "tier": "aaa"},
    {"title": "XCOM 2", "genres": ["Strategy"], "tier": "aaa"},
    {"title": "Crusader Kings III", "genres": ["Strategy"], "tier": "aaa"},
    {"title": "Stellaris", "genres": ["Strategy"], "tier": "aaa"},
    {"title": "Hearts of Iron IV", "genres": ["Strategy"], "tier": "aaa"},
    {"title": "Cities Skylines", "genres": ["Simulation", "Strategy"], "tier": "mid"},
    {"title": "Cities Skylines II", "genres": ["Simulation", "Strategy"], "tier": "aaa"},
    {"title": "RimWorld", "genres": ["Simulation", "Strategy"], "tier": "indie"},
    {"title": "Factorio", "genres": ["Simulation", "Strategy"], "tier": "indie"},
    {"title": "Forza Horizon 5", "genres": ["Racing"], "tier": "aaa"},
    {"title": "Forza Motorsport", "genres": ["Racing"], "tier": "aaa"},
    {"title": "F1 23", "genres": ["Racing"], "tier": "aaa"},
    {"title": "Need for Speed Heat", "genres": ["Racing"], "tier": "aaa"},
    {"title": "Assetto Corsa", "genres": ["Racing"], "tier": "mid"},
    {"title": "Dirt Rally 2.0", "genres": ["Racing"], "tier": "mid"},
    {"title": "The Crew Motorfest", "genres": ["Racing"], "tier": "aaa"},
    {"title": "Microsoft Flight Simulator", "genres": ["Simulation"], "tier": "aaa"},
    {"title": "Euro Truck Simulator 2", "genres": ["Simulation"], "tier": "mid"},
    {"title": "Farming Simulator 22", "genres": ["Simulation"], "tier": "mid"},
    {"title": "Planet Coaster", "genres": ["Simulation"], "tier": "mid"},
    {"title": "Planet Zoo", "genres": ["Simulation"], "tier": "mid"},
    {"title": "The Sims 4", "genres": ["Simulation", "Casual"], "tier": "mid"},
    {"title": "EA Sports FC 24", "genres": ["Sports"], "tier": "aaa"},
    {"title": "NBA 2K24", "genres": ["Sports"], "tier": "aaa"},
    {"title": "Madden NFL 24", "genres": ["Sports"], "tier": "aaa"},
    {"title": "Phasmophobia", "genres": ["Horror", "Indie"], "tier": "indie"},
    {"title": "Outlast 2", "genres": ["Horror"], "tier": "mid"},
    {"title": "Amnesia The Dark Descent", "genres": ["Horror"], "tier": "indie"},
    {"title": "The Evil Within 2", "genres": ["Horror"], "tier": "mid"},
    {"title": "Little Nightmares II", "genres": ["Horror", "Adventure"], "tier": "indie"},
    {"title": "Resident Evil 4", "genres": ["Horror", "Action"], "tier": "aaa"},
    {"title": "Resident Evil 2", "genres": ["Horror", "Action"], "tier": "aaa"},
    {"title": "Resident Evil Village", "genres": ["Horror", "Action"], "tier": "aaa"},
    {"title": "Resident Evil 7", "genres": ["Horror"], "tier": "aaa"},
    {"title": "Dead Space", "genres": ["Horror", "Action"], "tier": "aaa"},
    {"title": "Alan Wake 2", "genres": ["Horror", "Adventure"], "tier": "aaa"},
    {"title": "Metro Exodus", "genres": ["Shooter", "Adventure"], "tier": "aaa"},
    {"title": "Metro Last Light", "genres": ["Shooter", "Adventure"], "tier": "mid"},
    {"title": "Metro 2033", "genres": ["Shooter", "Adventure"], "tier": "mid"},
    {"title": "Portal 2", "genres": ["Puzzle"], "tier": "mid"},
    {"title": "The Witness", "genres": ["Puzzle"], "tier": "indie"},
    {"title": "Baba Is You", "genres": ["Puzzle", "Indie"], "tier": "indie"},
    {"title": "Slay the Spire", "genres": ["Strategy", "Indie"], "tier": "indie"},
    {"title": "Vampire Survivors", "genres": ["Indie", "Action"], "tier": "indie"},
    {"title": "Hollow Knight Silksong", "genres": ["Adventure", "Indie"], "tier": "indie"},
    {"title": "Cuphead The Delicious Last Course", "genres": ["Action", "Indie"], "tier": "indie"},
    {"title": "The Binding of Isaac Rebirth", "genres": ["Action", "Indie"], "tier": "indie"},
    {"title": "Enter the Gungeon", "genres": ["Action", "Indie"], "tier": "indie"},
    {"title": "Risk of Rain 2", "genres": ["Action", "Indie"], "tier": "indie"},
    {"title": "Rogue Legacy 2", "genres": ["Action", "Indie"], "tier": "indie"},
    {"title": "Slime Rancher", "genres": ["Casual", "Simulation"], "tier": "indie"},
    {"title": "Slime Rancher 2", "genres": ["Casual", "Simulation"], "tier": "indie"},
    {"title": "Among Us", "genres": ["Casual", "Indie"], "tier": "indie"},
    {"title": "Fall Guys", "genres": ["Casual", "Indie"], "tier": "indie"},
    {"title": "It Takes Two", "genres": ["Adventure", "Casual"], "tier": "mid"},
    {"title": "A Way Out", "genres": ["Adventure", "Action"], "tier": "mid"},
    {"title": "Journey", "genres": ["Adventure", "Indie"], "tier": "indie"},
    {"title": "Firewatch", "genres": ["Adventure", "Indie"], "tier": "indie"},
    {"title": "Life is Strange", "genres": ["Adventure", "Indie"], "tier": "indie"},
    {"title": "Life is Strange True Colors", "genres": ["Adventure"], "tier": "mid"},
    {"title": "Oxenfree", "genres": ["Adventure", "Indie"], "tier": "indie"},
    {"title": "Oxenfree II", "genres": ["Adventure", "Indie"], "tier": "indie"},
    {"title": "Streets of Rage 4", "genres": ["Action", "Indie"], "tier": "indie"},
    {"title": "Teenage Mutant Ninja Turtles Shredder's Revenge", "genres": ["Action", "Indie"], "tier": "indie"},
    {"title": "Hotline Miami", "genres": ["Action", "Indie"], "tier": "indie"},
    {"title": "Hotline Miami 2", "genres": ["Action", "Indie"], "tier": "indie"},
    {"title": "Inscryption", "genres": ["Strategy", "Indie"], "tier": "indie"},
    {"title": "Return of the Obra Dinn", "genres": ["Puzzle", "Indie"], "tier": "indie"},
    {"title": "Tunic", "genres": ["Adventure", "Indie"], "tier": "indie"},
    {"title": "Dave the Diver", "genres": ["Casual", "Indie"], "tier": "indie"},
    {"title": "Dredge", "genres": ["Adventure", "Indie"], "tier": "indie"},
    {"title": "The Stanley Parable Ultra Deluxe", "genres": ["Puzzle", "Indie"], "tier": "indie"},
    {"title": "Superliminal", "genres": ["Puzzle", "Indie"], "tier": "indie"},
    {"title": "Katana ZERO", "genres": ["Action", "Indie"], "tier": "indie"},
    {"title": "Braid", "genres": ["Puzzle", "Indie"], "tier": "indie"},
    {"title": "Limbo", "genres": ["Puzzle", "Indie"], "tier": "indie"},
    {"title": "Inside", "genres": ["Puzzle", "Indie"], "tier": "indie"},
    {"title": "Human Fall Flat", "genres": ["Puzzle", "Casual"], "tier": "indie"},
    {"title": "Golf With Your Friends", "genres": ["Casual", "Sports"], "tier": "indie"},
    {"title": "Rocket League", "genres": ["Sports", "Action"], "tier": "mid"},
    {"title": "For the King", "genres": ["Strategy", "RPG"], "tier": "indie"},
    {"title": "For the King II", "genres": ["Strategy", "RPG"], "tier": "indie"},
    {"title": "Warframe", "genres": ["Shooter", "RPG"], "tier": "mid"},
    {"title": "Gears 5", "genres": ["Shooter", "Action"], "tier": "aaa"},
    {"title": "Remnant II", "genres": ["Shooter", "RPG"], "tier": "aaa"},
    {"title": "Remnant From the Ashes", "genres": ["Shooter", "RPG"], "tier": "mid"},
    {"title": "Sifu", "genres": ["Action"], "tier": "mid"},
    {"title": "Returnal", "genres": ["Action"], "tier": "aaa"},
    {"title": "Armored Core VI", "genres": ["Action"], "tier": "aaa"},
    {"title": "Lies of P", "genres": ["Action", "RPG"], "tier": "aaa"},
    {"title": "Persona 3 Reload", "genres": ["RPG"], "tier": "aaa"},
    {"title": "Metaphor ReFantazio", "genres": ["RPG"], "tier": "aaa"},
    {"title": "Banishers Ghosts of New Eden", "genres": ["Adventure", "RPG"], "tier": "aaa"},
    {"title": "Helldivers 2", "genres": ["Shooter", "Action"], "tier": "aaa"},
    {"title": "Palworld", "genres": ["Adventure", "Simulation"], "tier": "mid"},
    {"title": "Enshrouded", "genres": ["Adventure", "RPG"], "tier": "mid"},
    {"title": "Lethal Company", "genres": ["Horror", "Indie"], "tier": "indie"},
    {"title": "Gris", "genres": ["Adventure", "Indie"], "tier": "indie"},
    {"title": "Spiritfarer", "genres": ["Adventure", "Indie"], "tier": "indie"},
    {"title": "A Short Hike", "genres": ["Adventure", "Indie"], "tier": "indie"},
    {"title": "Loop Hero", "genres": ["Strategy", "Indie"], "tier": "indie"},
    {"title": "Frostpunk", "genres": ["Strategy", "Simulation"], "tier": "mid"},
    {"title": "Project Zomboid", "genres": ["Simulation", "Indie"], "tier": "indie"},
    {"title": "The Long Dark", "genres": ["Adventure", "Simulation"], "tier": "mid"},
    {"title": "Dead by Daylight", "genres": ["Horror", "Action"], "tier": "mid"},
    {"title": "Kena Bridge of Spirits", "genres": ["Adventure", "Action"], "tier": "mid"},
    {"title": "Hi-Fi Rush", "genres": ["Action"], "tier": "mid"},
]


SUPPLEMENTAL_SERIES = [
    {
        "titles": [
            "Assassin's Creed II",
            "Assassin's Creed Brotherhood",
            "Assassin's Creed Revelations",
            "Assassin's Creed IV Black Flag",
            "Assassin's Creed Rogue",
            "Assassin's Creed Unity",
            "Assassin's Creed Syndicate",
            "Assassin's Creed Mirage",
        ],
        "genres": ["Action", "Adventure"],
        "tags": ["open world", "stealth", "historical"],
        "tier": "aaa",
    },
    {
        "titles": [
            "Far Cry 3",
            "Far Cry 4",
            "Far Cry Primal",
            "Far Cry New Dawn",
            "Far Cry Blood Dragon",
        ],
        "genres": ["Action", "Adventure"],
        "tags": ["open world", "shooting", "chaos"],
        "tier": "aaa",
    },
    {
        "titles": [
            "Call of Duty 4 Modern Warfare",
            "Call of Duty Modern Warfare 2",
            "Call of Duty Modern Warfare",
            "Call of Duty Black Ops",
            "Call of Duty Black Ops II",
            "Call of Duty Black Ops III",
            "Call of Duty WWII",
            "Call of Duty Vanguard",
        ],
        "genres": ["Shooter"],
        "tags": ["military", "multiplayer", "cinematic"],
        "tier": "aaa",
    },
    {
        "titles": [
            "Battlefield 3",
            "Battlefield 4",
            "Battlefield Hardline",
            "Battlefield V",
        ],
        "genres": ["Shooter"],
        "tags": ["large-scale", "multiplayer", "warfare"],
        "tier": "aaa",
    },
    {
        "titles": [
            "Need for Speed Most Wanted",
            "Need for Speed Most Wanted 2012",
            "Need for Speed Rivals",
            "Need for Speed Payback",
            "Need for Speed Unbound",
        ],
        "genres": ["Racing"],
        "tags": ["street racing", "cars", "arcade"],
        "tier": "aaa",
    },
    {
        "titles": [
            "Tomb Raider Legend",
            "Tomb Raider Anniversary",
            "Tomb Raider Underworld",
            "Lara Croft and the Guardian of Light",
            "Lara Croft and the Temple of Osiris",
        ],
        "genres": ["Action", "Adventure"],
        "tags": ["platforming", "puzzles", "exploration"],
        "tier": "mid",
    },
    {
        "titles": [
            "Mass Effect",
            "Mass Effect 2",
            "Mass Effect 3",
            "Mass Effect Andromeda",
        ],
        "genres": ["RPG", "Action"],
        "tags": ["choices", "sci-fi", "story-driven"],
        "tier": "aaa",
    },
    {
        "titles": [
            "Dragon Age Origins",
            "Dragon Age II",
            "Dragon Age Inquisition",
        ],
        "genres": ["RPG"],
        "tags": ["choices", "party", "fantasy"],
        "tier": "aaa",
    },
    {
        "titles": [
            "Resident Evil 0",
            "Resident Evil HD Remaster",
            "Resident Evil 3",
            "Resident Evil 5",
            "Resident Evil 6",
            "Resident Evil Revelations",
            "Resident Evil Revelations 2",
        ],
        "genres": ["Horror", "Action"],
        "tags": ["survival", "zombies", "atmospheric"],
        "tier": "aaa",
    },
    {
        "titles": [
            "Final Fantasy VII Remake Intergrade",
            "Final Fantasy VIII Remastered",
            "Final Fantasy IX",
            "Final Fantasy X X-2 HD Remaster",
            "Final Fantasy XII The Zodiac Age",
            "Final Fantasy XV Royal Edition",
            "Crisis Core Final Fantasy VII Reunion",
        ],
        "genres": ["RPG"],
        "tags": ["story-driven", "fantasy", "turn-based"],
        "tier": "aaa",
    },
    {
        "titles": [
            "Persona 3 Portable",
            "Persona 5 Strikers",
            "Persona 5 Tactica",
        ],
        "genres": ["RPG"],
        "tags": ["story-driven", "social links", "turn-based"],
        "tier": "aaa",
    },
    {
        "titles": [
            "Yakuza Kiwami",
            "Yakuza Kiwami 2",
            "Yakuza 3 Remastered",
            "Yakuza 4 Remastered",
            "Yakuza 5 Remastered",
            "Yakuza 6 The Song of Life",
            "Judgment",
            "Lost Judgment",
        ],
        "genres": ["Action", "Adventure"],
        "tags": ["crime", "story-driven", "brawling"],
        "tier": "mid",
    },
    {
        "titles": [
            "Borderlands The Pre-Sequel",
            "Tiny Tina's Wonderlands",
        ],
        "genres": ["Shooter", "RPG"],
        "tags": ["loot", "co-op", "chaos"],
        "tier": "aaa",
    },
    {
        "titles": [
            "Civilization IV",
            "Civilization Revolution",
            "Beyond Earth",
        ],
        "genres": ["Strategy"],
        "tags": ["4x", "turn-based", "empire building"],
        "tier": "mid",
    },
    {
        "titles": [
            "Age of Empires III Definitive Edition",
            "Age of Mythology",
            "Age of Mythology Retold",
        ],
        "genres": ["Strategy"],
        "tags": ["real-time strategy", "base building", "historical"],
        "tier": "mid",
    },
    {
        "titles": [
            "XCOM Enemy Unknown",
            "XCOM Enemy Within",
            "XCOM Chimera Squad",
        ],
        "genres": ["Strategy"],
        "tags": ["tactics", "squad", "aliens"],
        "tier": "mid",
    },
    {
        "titles": [
            "Mortal Kombat 9",
            "Mortal Kombat X",
            "Mortal Kombat 11",
            "Mortal Kombat 1",
        ],
        "genres": ["Action"],
        "tags": ["fighting", "competitive", "combo"],
        "tier": "aaa",
    },
    {
        "titles": [
            "Street Fighter IV",
            "Street Fighter V",
            "Street Fighter 6",
            "Ultra Street Fighter IV",
        ],
        "genres": ["Action"],
        "tags": ["fighting", "competitive", "combo"],
        "tier": "aaa",
    },
    {
        "titles": [
            "Tekken 6",
            "Tekken 7",
            "Tekken 8",
            "Tekken Tag Tournament 2",
        ],
        "genres": ["Action"],
        "tags": ["fighting", "competitive", "3d"],
        "tier": "aaa",
    },
    {
        "titles": [
            "Sonic Generations",
            "Sonic Mania",
            "Sonic Forces",
            "Sonic Frontiers",
        ],
        "genres": ["Action", "Adventure"],
        "tags": ["platforming", "speed", "colorful"],
        "tier": "mid",
    },
    {
        "titles": [
            "Batman Arkham Asylum",
            "Batman Arkham City",
            "Batman Arkham Origins",
            "Batman Arkham Knight",
        ],
        "genres": ["Action", "Adventure"],
        "tags": ["combat", "stealth", "story-driven"],
        "tier": "aaa",
    },
    {
        "titles": [
            "Dishonored",
            "Dishonored 2",
            "Dishonored Death of the Outsider",
        ],
        "genres": ["Action", "Adventure"],
        "tags": ["stealth", "choices", "story-driven"],
        "tier": "mid",
    },
    {
        "titles": [
            "Deus Ex",
            "Deus Ex Human Revolution",
            "Deus Ex Mankind Divided",
        ],
        "genres": ["RPG", "Action"],
        "tags": ["choices", "stealth", "cyberpunk"],
        "tier": "mid",
    },
    {
        "titles": [
            "Saints Row",
            "Saints Row 2",
            "Saints Row The Third",
            "Saints Row IV",
            "Saints Row 2022",
        ],
        "genres": ["Action", "Adventure"],
        "tags": ["open world", "crime", "chaos"],
        "tier": "mid",
    },
    {
        "titles": [
            "Dying Light",
            "Dying Light 2 Stay Human",
        ],
        "genres": ["Action", "Horror"],
        "tags": ["survival", "parkour", "co-op"],
        "tier": "aaa",
    },
    {
        "titles": [
            "Dead Island",
            "Dead Island Riptide",
            "Dead Island 2",
        ],
        "genres": ["Action", "Horror"],
        "tags": ["survival", "co-op", "zombies"],
        "tier": "mid",
    },
    {
        "titles": [
            "Star Wars Knights of the Old Republic",
            "Star Wars Knights of the Old Republic II",
            "Star Wars Jedi Knight II Jedi Outcast",
            "Star Wars Jedi Knight Jedi Academy",
            "Star Wars Battlefront II",
            "Star Wars Squadrons",
            "Star Wars The Force Unleashed",
        ],
        "genres": ["Action", "Adventure"],
        "tags": ["sci-fi", "story-driven", "combat"],
        "tier": "mid",
    },
    {
        "titles": [
            "Halo The Master Chief Collection",
            "Halo Reach",
            "Halo Combat Evolved",
            "Halo 2",
            "Halo 3",
            "Halo 4",
        ],
        "genres": ["Shooter"],
        "tags": ["sci-fi", "story-driven", "multiplayer"],
        "tier": "aaa",
    },
    {
        "titles": [
            "BioShock",
            "BioShock 2",
        ],
        "genres": ["Shooter", "Adventure"],
        "tags": ["story-driven", "atmospheric", "single-player"],
        "tier": "mid",
    },
    {
        "titles": [
            "Middle-earth Shadow of Mordor",
            "Middle-earth Shadow of War",
        ],
        "genres": ["Action", "Adventure"],
        "tags": ["open world", "combat", "fantasy"],
        "tier": "aaa",
    },
    {
        "titles": [
            "Splinter Cell",
            "Splinter Cell Chaos Theory",
            "Splinter Cell Blacklist",
        ],
        "genres": ["Action"],
        "tags": ["stealth", "tactical", "single-player"],
        "tier": "mid",
    },
    {
        "titles": [
            "Sniper Elite 3",
            "Sniper Elite 4",
            "Sniper Elite 5",
        ],
        "genres": ["Shooter"],
        "tags": ["stealth", "tactical", "sniping"],
        "tier": "mid",
    },
    {
        "titles": [
            "Wolfenstein The New Order",
            "Wolfenstein The Old Blood",
            "Wolfenstein Youngblood",
        ],
        "genres": ["Shooter"],
        "tags": ["story-driven", "action", "alternate history"],
        "tier": "aaa",
    },
    {
        "titles": [
            "Hitman",
            "Hitman 2",
        ],
        "genres": ["Action"],
        "tags": ["stealth", "tactical", "sandbox"],
        "tier": "aaa",
    },
    {
        "titles": [
            "Just Cause 3",
            "Sleeping Dogs Definitive Edition",
            "Mad Max",
            "The Division",
            "Forza Horizon 4",
        ],
        "genres": ["Action", "Adventure"],
        "tags": ["open world", "combat", "story-driven"],
        "tier": "mid",
    },
]


YEARLY_FRANCHISES = [
    {
        "template": "F1 {year}",
        "years": list(range(2018, 2026)),
        "genres": ["Racing"],
        "tags": ["formula 1", "racing", "simulation"],
        "tier": "aaa",
    },
    {
        "template": "NBA 2K{year}",
        "years": list(range(2018, 2026)),
        "genres": ["Sports"],
        "tags": ["basketball", "career mode", "competitive"],
        "tier": "aaa",
    },
    {
        "template": "Madden NFL {year}",
        "years": list(range(2018, 2026)),
        "genres": ["Sports"],
        "tags": ["football", "career mode", "competitive"],
        "tier": "aaa",
    },
    {
        "template": "FIFA {year}",
        "years": [2018, 2019, 2020, 2021, 2022, 2023],
        "genres": ["Sports"],
        "tags": ["football", "career mode", "competitive"],
        "tier": "aaa",
    },
    {
        "template": "EA Sports FC {year}",
        "years": [24, 25],
        "genres": ["Sports"],
        "tags": ["football", "career mode", "competitive"],
        "tier": "aaa",
    },
    {
        "template": "Football Manager {year}",
        "years": list(range(2018, 2026)),
        "genres": ["Simulation", "Sports"],
        "tags": ["management", "football", "strategy"],
        "tier": "mid",
    },
    {
        "template": "WWE 2K{year}",
        "years": list(range(2018, 2026)),
        "genres": ["Sports"],
        "tags": ["wrestling", "career mode", "competitive"],
        "tier": "mid",
    },
    {
        "template": "MotoGP {year}",
        "years": list(range(2018, 2026)),
        "genres": ["Racing"],
        "tags": ["motorcycles", "racing", "simulation"],
        "tier": "mid",
    },
]


def _build_series_entries(series_definitions: list[dict]) -> list[dict]:
    entries: list[dict] = []
    for series in series_definitions:
        titles = series.get("titles") or []
        genres = series.get("genres") or ["Action"]
        tags = series.get("tags") or DEFAULT_TAGS_BY_GENRE.get(genres[0], [])
        tier = series.get("tier", "aaa")
        for title in titles:
            entries.append({"title": title, "genres": genres, "tags": tags, "tier": tier})
    return entries


def _build_yearly_entries(series_definitions: list[dict]) -> list[dict]:
    entries: list[dict] = []
    for series in series_definitions:
        template = series.get("template")
        years = series.get("years") or []
        genres = series.get("genres") or ["Action"]
        tags = series.get("tags") or DEFAULT_TAGS_BY_GENRE.get(genres[0], [])
        tier = series.get("tier", "mid")
        if not template:
            continue
        for year in years:
            title = template.format(year=year)
            entries.append({"title": title, "genres": genres, "tags": tags, "tier": tier})
    return entries


def _dedupe_entries(entries: list[dict]) -> list[dict]:
    seen: set[str] = set()
    deduped: list[dict] = []
    for entry in entries:
        title = str(entry.get("title", "")).strip().lower()
        if not title or title in seen:
            continue
        seen.add(title)
        deduped.append(entry)
    return deduped


ALL_GAME_ENTRIES = _dedupe_entries(
    GAME_ENTRIES
    + _build_series_entries(SUPPLEMENTAL_SERIES)
    + _build_yearly_entries(YEARLY_FRANCHISES)
)


def build_games_database(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    if len(ALL_GAME_ENTRIES) < 300:
        raise ValueError("Game dataset must contain at least 300 entries")

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "game_id",
                "title",
                "genres",
                "description",
                "tags",
                "aliases",
                "typical_price",
                "metacritic_avg",
            ],
        )
        writer.writeheader()

        for entry in ALL_GAME_ENTRIES:
            title = entry["title"]
            genres = entry.get("genres") or ["Action"]
            tags = entry.get("tags") or DEFAULT_TAGS_BY_GENRE.get(genres[0], [])
            aliases = entry.get("aliases") or []
            tier = entry.get("tier", "aaa")

            description = (
                f"{title} is a {genres[0].lower()} game focused on {tags[0]} and {tags[1]}. "
                f"Expect {tags[-1]} moments with clear progression and satisfying goals."
            )

            alias_set = {title.lower(), _normalize_alias(title)}
            alias_set.update({alias.lower() for alias in aliases})

            writer.writerow(
                {
                    "game_id": _slugify(title),
                    "title": title,
                    "genres": ",".join(genres),
                    "description": description,
                    "tags": ",".join(tags),
                    "aliases": ",".join(sorted(alias_set)),
                    "typical_price": PRICE_BY_TIER.get(tier, 59.99),
                    "metacritic_avg": METACRITIC_BY_TIER.get(tier, 80),
                }
            )


def _slugify(text: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "-" for ch in text)
    return "-".join(part for part in cleaned.split("-") if part)


def _normalize_alias(text: str) -> str:
    return "".join(ch.lower() for ch in text if ch.isalnum())
