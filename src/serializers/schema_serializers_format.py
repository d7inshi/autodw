BASE_FORMAT = """hero_power : hero_id (1, 2, 3) , power_id ( 1, 18, 26 ) | superpower : id ( 1, 2, 3 ) , power_name ( Agility, Accelerated Healing, Lantern Power Ring ) | hero_power.power_id=superpower.id"""
M_SCHEMA_FORMAT = """
 [DB_ID] superhero 
 [Schema]
#Table: hero_power
[
(hero_id: INTEGER, Primary Key, the id of the hero Maps to superhero(id), Examples: [1, 2, 3]),
(power_id: INTEGER, the id of the power Maps to superpower(id), Examples: [1, 18, 26])
]
#Table: superpower
[
(id: INTEGER, Primary Key, the unique identifier of the superpower, Examples: [1, 2, 3]),
(power_name: TEXT, the superpower name, Examples: [Agility, Accelerated Healing, Lantern Power Ring])
]
 [Foreign keys]
hero_power.power_id=superpower.id 
"""