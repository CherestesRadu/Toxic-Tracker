import functools

from flask import (
    Blueprint, flash, g, redirect, request, session, url_for, current_app
)
from backend.db import get_db
import datetime
import time

blueprint = Blueprint('player', __name__, url_prefix='/player')

def player_exists_in_db(db, riot_name, riot_tag, table_name):
    entries = db.execute("SELECT * FROM " + table_name + " WHERE riot_name = ? AND riot_tag = ?", (riot_name, riot_tag,)).fetchone()
    if entries is None:
        return False
    return True

def is_table_empty(db, table_name):
    count = db.execute(f"SELECT count(*) FROM {table_name}").fetchone()
    return count['count(*)'] == 0

def insert_player_stats_in_db(db, riot_api, participants):
    for player in participants:
        params = (
            player['name'],
            player['tag'],
            player['matchId'],
            player['win'],
            player['champion']['name'],
            player['champion']['id'],
            player['kills'],
            player['deaths'],
            player['assists'],
            player['pingCount'],
            player['missingPings'],
            player['role'],
            player['damage'],
            player['cs'],
            player['date'],
            player['puuid'],
        )
    
        db.execute("""
                    INSERT INTO PlayerMatch (
                        riot_name,
                        riot_tag,
                        match_id,
                        win,
                        champion_name,
                        champion_id,
                        kills,
                        deaths,
                        assists,
                        ping_count,
                        missing_ping_count,
                        role,
                        damage,
                        cs,
                        date,
                        puuid
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                            ?, ?, ?, ?, ?, ?)
                    """, params)
        db.commit()
    
        db.execute('INSERT INTO MatchNewEntry (match_id, puuid) VALUES (?, ?)', (player['matchId'], player['puuid'],))
        db.commit()

def consume_entry_db(db):
    entries = db.execute('SELECT * FROM MatchNewEntry').fetchall()
    if entries is not None:
        for entry in entries:
            stats = db.execute('SELECT * FROM PlayerMatch WHERE match_id = ? AND puuid = ?', (entry['match_id'], entry['puuid'],)).fetchone()
            player = {
                'name': stats['riot_name'],
                'tag': stats['riot_tag'],
                'champion': {
                    'name': stats['champion_name'],
                    'id': stats['champion_id']
                },
                'kills': stats['kills'],
                'deaths': stats['deaths'],
                'assists': stats['assists'],
                'win': stats['win'],
                'puuid': stats['puuid']
            }

            champ_stat = db.execute("""
                        SELECT * FROM PlayerChampStats WHERE puuid = ? AND champion_name = ?
                        """, (player['puuid'], player['champion']['name'],)).fetchone()
            if champ_stat is None:
                db.execute("""
                            INSERT INTO PlayerChampStats (riot_name, riot_tag, champion_name, champion_id, kills, deaths, assists, winrate, puuid, times_played)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                player['name'], player['tag'], player['champion']['name'], player['champion']['id'],
                                player['kills'], player['deaths'], player['assists'], player['win'], player['puuid'], 1,
                            ))
                db.commit()
            else:
                def avg(a, b):
                    return float((a + b) / 2.0)

                kills = avg(champ_stat['kills'], player['kills'])
                deaths = avg(champ_stat['deaths'], player['deaths'])
                assists = avg(champ_stat['assists'], player['assists'])
                winrate = avg(champ_stat['winrate'], player['win'])
                times_played = champ_stat['times_played'] + 1

                db.execute("""UPDATE PlayerChampStats
                            SET kills = ?, deaths = ?, assists = ?, winrate = ?, times_played = ?
                            WHERE puuid = ? AND champion_name = ?
                            """, (kills, deaths, assists, winrate, times_played, player['puuid'], player['champion']['name'],))
                db.commit()

            db.execute("""DELETE FROM MatchNewEntry WHERE match_id = ? AND puuid = ?
                    """, (entry['match_id'], entry['puuid'],))
            db.commit()

@blueprint.route('/search', methods=['GET'])
def search_player():

    db = get_db()

    riot_name = 'CJLOR2'
    riot_tag = 'EUNE'

    from backend.riot import (RiotApi, get_region_from_tagline, get_tagline)
    import backend.config
    riot_api = RiotApi(backend.config.RIOT_API_KEY, 'europe')
    riot_account = riot_api.get_account_from_riot_id(riot_name, riot_tag)

    # Search PlayerMatches DB
    if not player_exists_in_db(db, riot_name, riot_tag, 'PlayerMatch'):
        matches = riot_api.get_matches_from_puuid(riot_account['puuid'], 0, 0)
        match_stats_list = [] 
        
        for match in matches:
            result = riot_api.get_match_stats(match)
            match_stats_list.append(result)

        participants = []
        for p in match_stats_list:
            participants += riot_api.get_players_stats_from_match(p)
        
        # Insert players in DB
        insert_player_stats_in_db(db, riot_api, participants)

        consume_entry_db(db)

    else:
        # Get calendar dates and get last match
        max_timestamp = 0
        dates = db.execute('SELECT date FROM PlayerMatch WHERE riot_name = ? AND riot_tag = ?', (riot_name, riot_tag,)).fetchall()
        for date in dates:
            date_object = datetime.datetime.strptime(date[0], "%Y-%m-%d %H:%M:%S")
            max_timestamp = max(max_timestamp, int(date_object.timestamp()))

        current_timestamp = int(time.time())

        matches = riot_api.get_matches_from_puuid(riot_account['puuid'], max_timestamp, current_timestamp)
        
        # TODO: Verifica ultimul timestamp sa fie apropiat de current_timestamp
        # Sau incearca de la ultimul pana la current pana cand ai toate meciurile

        first_ignore = True
        match_stats_list = []
        for match in matches:
            if first_ignore:
                first_ignore = False
                continue
            result = riot_api.get_match_stats(match)
            match_stats_list.append(result)

        participants = []
        for p in match_stats_list:
            participants += riot_api.get_players_stats_from_match(p)
        
        if len(participants) > 0:
            insert_player_stats_in_db(db, riot_api, participants)

        consume_entry_db(db)

    # Return JSON with user search result
    return 'Doamne ajuta!'


#@blueprint.route('/search', methods=['GET', 'POST'])
#def search_player():
#    # Search for player in MY DB
#
#    # TODO: front end
#    riot_name = "Labia Mariner"
#    riot_tag = "EUNE"
#
#    db = get_db()
#
#    from backend.riot import (RiotApi, get_region_from_tagline, get_tagline)
#    import backend.config
#    riot_api = RiotApi(backend.config.RIOT_API_KEY, get_region_from_tagline(riot_tag))
#    return str(update_player(db,riot_api, riot_name, riot_tag))

    #player = db.execute("""
    #            SELECT * FROM PlayerStats WHERE riot_name = ? AND riot_tag = ?
    #           """, (riot_name, riot_tag,)).fetchone()
    ## If doesn't exist, use riot api and get 20 matches
    #if player is None:
    #    from backend.riot import (RiotApi, get_region_from_tagline, get_tagline)
    #    import backend.config
    #    riot_api = RiotApi(backend.config.RIOT_API_KEY, get_region_from_tagline(riot_tag))
    #    account = riot_api.get_account_from_riot_id(riot_name, riot_tag)
    #    matches = riot_api.get_matches_from_puuid(account['puuid'])
    #    
    #    match_stats_list = []
    #    for match in matches:
    #        match_stats_list.append(riot_api.get_match_stats(match))
#
    #    stat_list = []
    #    for match_stats in match_stats_list:
    #        stat_list.append(riot_api.get_players_stats_from_match(match_stats))
#
    #    for stats in stat_list:
    #        for player in stats:
#
    #            m = db.execute("""
    #                        SELECT * FROM PlayerMatch WHERE match_id = ? AND riot_name = ? AND riot_tag = ?
    #                       """, (player['matchId'], player['name'], player['tag'],)).fetchone()
    #            if m is not None:
    #                continue
#
    #            params = (
    #                player['name'],
    #                player['tag'],
    #                player['matchId'],
    #                player['win'],
    #                player['champion']['name'],
    #                player['champion']['id'],
    #                player['kills'],
    #                player['deaths'],
    #                player['assists'],
    #                player['pingCount'],
    #                player['missingPings'],
    #                player['role'],
    #                player['damage'],
    #                player['cs'],
    #                player['date'],
    #                player['puuid'],
    #            )
#
    #            db.execute("""
    #                        INSERT INTO PlayerMatch (
    #                            riot_name,
    #                            riot_tag,
    #                            match_id,
    #                            win,
    #                            champion_name,
    #                            champion_id,
    #                            kills,
    #                            deaths,
    #                            assists,
    #                            ping_count,
    #                            missing_ping_count,
    #                            role,
    #                            damage,
    #                            cs,
    #                            date,
    #                            puuid
    #                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
    #                                ?, ?, ?, ?, ?, ?)
    #                       """, params)
    #            db.commit()
#
    #            db.execute("INSERT INTO MatchNewEntry (match_id, puuid) VALUES (?, ?)", (player['matchId'], player['puuid'],))
    #            db.commit()
    #else:
    #    # Update:
    #    # Get last calendar date
    #    # Update after
    #    pass
#
    #resolve_entries(db)
#
    #return "Da"
