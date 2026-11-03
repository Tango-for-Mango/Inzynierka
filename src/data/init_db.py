import sqlite3

def init_database():
    conn = sqlite3.connect("knowledge_base.db")
    cursor = conn.cursor()

    # Tabela postaci (Zagrożenia)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS champions (
            champ_name TEXT PRIMARY KEY,
            primary_damage TEXT,
            high_healing INTEGER,
            high_shielding INTEGER,
            high_crit INTEGER
        )
    """)

    # Tabela przedmiotów defensywnych (Rozwiązania)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS defensive_items (
            item_name TEXT,
            target_class TEXT,
            defends_against TEXT,
            is_anti_heal INTEGER,
            is_anti_shield INTEGER,
            is_anti_crit INTEGER
        )
    """)

    cursor.execute("DELETE FROM champions")
    cursor.execute("DELETE FROM defensive_items")

    # BAZA POSTACI: (Nazwa, Główny DMG, Czy_Leczy, Czy_Tarcze, Czy_Kryt)
    # 1 = Tak, 0 = Nie
    champions_data = [
        # Górna Aleja (Top)
        ("Aatrox", "AD", 1, 0, 0), ("Camille", "AD", 1, 0, 0), ("Darius", "AD", 1, 0, 0),
        ("Dr. Mundo", "AP", 1, 0, 0), ("Fiora", "AD", 1, 0, 0), ("Garen", "AD", 0, 0, 1),
        ("Gnar", "AD", 0, 0, 0), ("Gwen", "AP", 1, 0, 0), ("Illaoi", "AD", 1, 0, 0),
        ("Irelia", "AD", 1, 0, 0), ("Jax", "AD", 0, 0, 0), ("Jayce", "AD", 0, 0, 0),
        ("K'Sante", "AD", 0, 0, 0), ("Kled", "AD", 0, 0, 0), ("Malphite", "AP", 0, 0, 0),
        ("Mordekaiser", "AP", 0, 1, 0), ("Nasus", "AD", 1, 0, 0), ("Olaf", "AD", 1, 0, 0),
        ("Ornn", "AP", 0, 0, 0), ("Renekton", "AD", 1, 0, 0), ("Riven", "AD", 0, 1, 0), ("Rumble", "AP", 0, 0, 0),
        ("Sett", "AD", 0, 1, 0), ("Shen", "AP", 0, 1, 0), ("Sion", "AD", 0, 0, 0),
        ("Tahm Kench", "AP", 1, 1, 0), ("Teemo", "AP", 0, 0, 0), ("Tryndamere", "AD", 0, 0, 1),
        ("Urgot", "AD", 0, 0, 0), ("Volibear", "AP", 1, 0, 0), ("Yorick", "AD", 0, 0, 0),
        ("Zaahen", "AD", 1, 0, 0),

        # Dżungla (Jungle)
        ("Amumu", "AP", 0, 0, 0), ("Bel'Veth", "AD", 0, 0, 0), ("Briar", "AD", 1, 0, 0),
        ("Diana", "AP", 0, 0, 0), ("Ekko", "AP", 0, 0, 0), ("Elise", "AP", 0, 0, 0),
        ("Evelynn", "AP", 0, 0, 0), ("Fiddlesticks", "AP", 0, 0, 0), ("Gragas", "AP", 0, 0, 0),
        ("Graves", "AD", 0, 0, 1), ("Hecarim", "AD", 0, 0, 0), ("Ivern", "AP", 0, 1, 0),
        ("Jarvan IV", "AD", 0, 0, 0), ("Karthus", "AP", 0, 0, 0), ("Kayn", "AD", 1, 0, 0),
        ("Kha'Zix", "AD", 0, 0, 0), ("Kindred", "AD", 0, 0, 1), ("Lee Sin", "AD", 0, 0, 0),
        ("Lillia", "AP", 0, 0, 0), ("Master Yi", "AD", 0, 0, 0), ("Nidalee", "AP", 0, 0, 0),
        ("Nocturne", "AD", 0, 0, 0), ("Nunu & Willump", "AP", 1, 0, 0), ("Pantheon", "AD", 0, 0, 0),
        ("Poppy", "AD", 0, 0, 0), ("Rammus", "AP", 0, 0, 0), ("Rek'Sai", "AD", 0, 0, 0),
        ("Rengar", "AD", 0, 0, 1), ("Sejuani", "AP", 0, 0, 0), ("Shaco", "AD", 0, 0, 1),
        ("Skarner", "AD", 0, 0, 0), ("Trundle", "AD", 0, 0, 0), ("Udyr", "AD", 0, 1, 0),
        ("Vi", "AD", 0, 0, 0), ("Viego", "AD", 0, 0, 1), ("Warwick", "AD", 1, 0, 0),
        ("Wukong", "AD", 0, 0, 0,), ("Xin Zhao", "AD", 1, 0, 0), ("Zac", "AP", 1, 0, 0),

        # Środkowa Aleja (Mid)
        ("Ahri", "AP", 0, 0, 0), ("Akali", "AP", 0, 0, 0), ("Akshan", "AD", 0, 0, 1),
        ("Anivia", "AP", 0, 0, 0), ("Annie", "AP", 0, 0, 0), ("Aurelion Sol", "AP", 0, 0, 0),
        ("Azir", "AP", 0, 0, 0), ("Cassiopeia", "AP", 1, 0, 0), ("Fizz", "AP", 0, 0, 0),
        ("Galio", "AP", 0, 0, 0), ("Heimerdinger", "AP", 0, 0, 0), ("Hwei", "AP", 0, 0, 0),
        ("Kassadin", "AP", 0, 0, 0), ("Katarina", "AP", 0, 0, 0), ("LeBlanc", "AP", 0, 0, 0),
        ("Lissandra", "AP", 0, 0, 0), ("Lux", "AP", 0, 0, 0), ("Malzahar", "AP", 0, 0, 0),
        ("Naafiri", "AD", 0, 0, 0), ("Neeko", "AP", 0, 0, 0), ("Orianna", "AP", 0, 0, 0),
        ("Qiyana", "AD", 0, 0, 0), ("Ryze", "AP", 0, 0, 0), ("Smolder", "AD", 0, 0, 1),
        ("Sylas", "AP", 1, 0, 0), ("Syndra", "AP", 0, 0, 0), ("Taliyah", "AP", 0, 0, 0),
        ("Talon", "AD", 0, 0, 0), ("Twisted Fate", "AP", 0, 0, 0), ("Veigar", "AP", 0, 0, 0),
        ("Vex", "AP", 0, 0, 0), ("Viktor", "AP", 0, 0, 0), ("Vladimir", "AP", 1, 0, 0),
        ("Xerath", "AP", 0, 0, 0), ("Yasuo", "AD", 0, 1, 1), ("Yone", "AD", 0, 1, 1),
        ("Zed", "AD", 0, 0, 0), ("Zoe", "AP", 0, 0, 0),

        # Dolna Aleja (ADC)
        ("Aphelios", "AD", 1, 0, 1), ("Ashe", "AD", 0, 0, 1), ("Caitlyn", "AD", 0, 0, 1),
        ("Draven", "AD", 1, 0, 1), ("Ezreal", "AD", 0, 0, 0), ("Jhin", "AD", 0, 0, 1),
        ("Jinx", "AD", 0, 0, 1), ("Kai'Sa", "AP", 0, 1, 0), ("Kalista", "AD", 0, 0, 0),
        ("Kog'Maw", "AD", 0, 0, 0), ("Lucian", "AD", 0, 0, 1), ("Miss Fortune", "AD", 0, 0, 1),
        ("Nilah", "AD", 1, 0, 1), ("Samira", "AD", 0, 0, 1), ("Sivir", "AD", 0, 0, 1),
        ("Tristana", "AD", 0, 0, 1), ("Twitch", "AD", 0, 0, 1), ("Varus", "AD", 0, 0, 0),
        ("Vayne", "AD", 0, 0, 1), ("Xayah", "AD", 0, 0, 1),("Yunara", "AD", 0, 0, 1), ("Zeri", "AD", 0, 0, 1),

        # Wsparcie (Support)
        ("Alistar", "AP", 0, 0, 0), ("Bard", "AP", 0, 0, 0), ("Blitzcrank", "AP", 0, 0, 0),
        ("Braum", "AP", 0, 0, 0), ("Janna", "AP", 1, 1, 0), ("Karma", "AP", 0, 1, 0),
        ("Leona", "AP", 0, 0, 0), ("Lulu", "AP", 0, 1, 0), ("Milio", "AP", 0, 1, 0),
        ("Morgana", "AP", 0, 0, 0), ("Nami", "AP", 0, 0, 0), ("Nautilus", "AP", 0, 0, 0),
        ("Pyke", "AD", 0, 0, 0), ("Rakan", "AP", 0, 0, 0), ("Rell", "AP", 0, 0, 0),
        ("Renata Glasc", "AP", 0, 0, 0), ("Senna", "AD", 1, 0, 1), ("Seraphine", "AP", 1, 0, 0),
        ("Sona", "AP", 1, 0, 0), ("Soraka", "AP", 1, 0, 0), ("Taric", "AP", 1, 0, 0),
        ("Thresh", "AP", 0, 0, 0), ("Yuumi", "AP", 1, 0, 0), ("Zilean", "AP", 0, 0, 0), ("Zyra", "AP", 0, 0, 0)
    ]
    cursor.executemany("INSERT INTO champions VALUES (?, ?, ?, ?, ?)", champions_data)

    # BAZA PRZEDMIOTÓW: (Nazwa, Klasa_Kupująca, Na_Jaki_DMG, AntiHeal, AntiShield, AntiCrit)
    items_data = [
        # Opcje dla klas "Bruiser" (Wojownicy AD/AP)
        ("Maw of Malmortius", "Bruiser", "AP", 0, 0, 0),
        ("Death's Dance", "Bruiser", "AD", 0, 0, 0),
        ("Sterak's Gage", "Bruiser", "ALL", 0, 0, 0),
        ("Wit's End", "Bruiser", "AP", 0, 0, 0),
        ("Chempunk Chainsword", "Bruiser", "ALL", 1, 0, 0), # Anti-heal
        ("Randuin's Omen", "Bruiser", "AD", 0, 0, 1), # Współdzielone z tankami dla anti-crit
        ("Serpent's Fang", "Bruiser", "ALL", 0, 1, 0), # Anti-shield

        # Opcje dla klas "Assassin" (Zabójcy AD)
        ("Serpent's Fang", "Assassin", "ALL", 0, 1, 0), # Anti-shield
        ("Edge of Night", "Assassin", "AP", 0, 0, 0),
        ("Chempunk Chainsword", "Assassin", "ALL", 1, 0, 0),
        ("Maw of Malmortius", "Assassin", "AP", 0, 0, 0),
        ("Death's Dance", "Assassin", "AD", 0, 0, 0),
        ("Guardian Angel", "Assassin", "AD", 0, 0, 0),

        # Opcje dla klas "Mage" (Magowie AP)
        ("Zhonya's Hourglass", "Mage", "AD", 0, 0, 0),
        ("Banshee's Veil", "Mage", "AP", 0, 0, 0),
        ("Morellonomicon", "Mage", "ALL", 1, 0, 0), # Anti-heal
    

        # Opcje dla klas "ADC" (Strzelcy AD)
        ("Immortal Shieldbow", "ADC", "ALL", 0, 0, 0),
        ("Guardian Angel", "ADC", "AD", 0, 0, 0),
        ("Mortal Reminder", "ADC", "ALL", 1, 0, 0), # Anti-heal
        ("Maw of Malmortius", "ADC", "AP", 0, 0, 0),
        ("Mercurial Scimitar", "ADC", "AP", 0, 0, 0),
        ("Serpent's Fang", "ADC", "ALL", 0, 1, 0), # Anti-shield

        # Opcje dla klas "Tank" (Obrońcy)
        ("Thornmail", "Tank", "AD", 1, 0, 0), # Anti-heal
        ("Randuin's Omen", "Tank", "AD", 0, 0, 1), # Anti-crit
        ("Frozen Heart", "Tank", "AD", 0, 0, 0),
        ("Kaenic Rookern", "Tank", "AP", 0, 0, 0),
        ("Force of Nature", "Tank", "AP", 0, 0, 0),
        ("Spirit Visage", "Tank", "AP", 0, 0, 0),
        ("Jak'Sho, The Protean", "Tank", "ALL", 0, 0, 0),

        # Opcje dla klas "Support" (Wspierający, opcje hybrydowe)
        ("Mikael's Blessing", "Support", "ALL", 0, 0, 0),
        ("Locket of the Iron Solari", "Support", "ALL", 0, 0, 0),
        ("Knight's Vow", "Support", "AD", 0, 0, 0)
    ]
    cursor.executemany("INSERT INTO defensive_items VALUES (?, ?, ?, ?, ?, ?)", items_data)

    conn.commit()
    conn.close()
    print("Baza danych wiedzy championów i przedmiotów League of Legends została zaktualizowana.")

if __name__ == "__main__":
    init_database()