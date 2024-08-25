import os
import sqlite3
import json


def initialize_database():
    database_structure = {
        'inv_channel': dict,
        'forgave': None,
        'invites': dict,
        'channel_activity': dict,
        'activity_blacklist': dict,
        'inviter_uses': dict,
        'user_activity': dict,
    }
    type_translation = {
        list: "[]",
        dict: "{}",
        None: "NULL"
    }

    conn = sqlite3.connect('malpkabot.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS malpkabot (
            key string,
            value string
        )
    ''')

    try:
        # Read JSON data from file
        with open('db.json', 'r') as json_file:
            data = json.load(json_file)

        # Insert data into SQLite table
        for key, value in data.items():
            json_string = json.dumps(value)
            cursor.execute("INSERT INTO malpkabot (key, value) VALUES (?, ?)", (key, json_string))

        # Commit the changes
        conn.commit()

        os.remove('db.json')
    except Exception as e:
        print(str(e))

    for key, value in database_structure.items():
        cursor.execute("SELECT * FROM malpkabot WHERE key = ?", (key, ))
        value = cursor.fetchone()
        if value is None:
            query = "INSERT INTO malpkabot (key, value) VALUES (?, ?)"
            cursor.execute(query, (key, type_translation[value]))
            conn.commit()

        cursor.execute("SELECT value FROM malpkabot WHERE key = ?", (key, ))
        value = cursor.fetchone()
        print(f"{key} — {value[0]}\n")

    print("\n==============================\nCREATED ALL MISSING DATABASES!\n==============================\n")
