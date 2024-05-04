import requests as req
import time
import sys
from datetime import datetime

from typing import Tuple

region_tagline_dict = {
    'EUNE' : 'europe'
}

tagline_region_dict = {
    'europe' : 'EUNE'
}

def get_tagline(region: str):
    return tagline_region_dict[region]
    
def get_region_from_tagline(tagline: str):
    return region_tagline_dict[tagline]

class RiotApi:
    def __init__(self, key: str, region: str):
        self.api_key = key
        self.selected_region = region
        self.root_request = 'https://' + region + '.api.riotgames.com'

    def execute_request(self, api_request):

        # TODO: Use library for request wait times
        result = req.get(api_request)
        time_to_sleep = 5.0
        while result.status_code == 429 or result.status_code == 503: # Rate limit exceeded or service unavailable ???????
            print(f"\n\n\nNeed to sleep. error_code: {result.status_code}")
            time.sleep(time_to_sleep)
            result = req.get(api_request)
            time_to_sleep += 5.0
        
        # TODO: Better error handling
        if result.status_code == 200: # OK
            return result
        else:
            print(result)
            raise Exception('Handle error')

    def set_region(self, region: str):
        self.selected_region = region
        self.root_request = 'https://' + region + '.api.riotgames.com'

    def get_player_from_uuid(player_uuid: str):
        pass

    def get_player_from_summoner_name(summoner_name: str):
        pass

    def get_account_from_riot_id(self, riot_name: str, riot_tag: str):
        #'https://europe.api.riotgames.com/riot/account/v1/accounts/by-riot-id/CJLOR2/EUNE?api_key=RGAPI-cbf5d9bf-930d-4489-9181-8b0fe6ac8642'
        api_request = self.root_request + '/riot/account/v1/accounts/by-riot-id/' + riot_name + '/' + riot_tag + '?api_key=' + self.api_key
        result = self.execute_request(api_request).json()
        return result
    
    def get_matches_from_puuid(self, puuid: str, start_date: int, end_date: int): # TODO: Default is 20 games, control num with param
        #"https://europe.api.riotgames.com/lol/match/v5/matches/by-puuid/ubD8VSQx-85GcWmO8UbSqz2kaex8zw2FSaSaOGRgQ_FJ_YdGqlZohc7bLGbUKGMJlDSAFPNBFu-PWQ/ids?type=ranked&startTime=&start=0&count=20&api_key=RGAPI-cbf5d9bf-930d-4489-9181-8b0fe6ac8642"
        
        if start_date == 0 and end_date == 0: # Get last 20 games
            api_request = self.root_request + '/lol/match/v5/matches/by-puuid/' + puuid + '/ids?type=ranked&start=0&count=20&api_key=' + self.api_key
            result = self.execute_request(api_request).json()
            return result
        
        # Or get games from timestamps
        api_request = self.root_request + '/lol/match/v5/matches/by-puuid/' + puuid + '/ids?type=ranked' + \
        '&startTime=' + str(start_date) + '&endTime=' + str(end_date) + '&start=0&count=20&api_key=' + self.api_key
        result = self.execute_request(api_request).json()
        return result
    
    def get_match_stats(self, match_id: str):
        #https://europe.api.riotgames.com/lol/match/v5/matches/EUN1_3589088922?api_key=RGAPI-cbf5d9bf-930d-4489-9181-8b0fe6ac8642
        api_request = self.root_request + '/lol/match/v5/matches/' + match_id + '?api_key=' + self.api_key
        result = self.execute_request(api_request).json()
        return result

    def get_summoner_from_puuid(self, puuid: str):
        #https://eun1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/tv14BHPWywhlS7Lff-YJ-OKqvTC4l73FS9r-Uc84EndudYrZHS_nmxGdZhBdow034q_szPIla4k-iA?api_key=RGAPI-c512a757-1456-41ea-afd9-5df1e41a6eff
        if self.selected_region == 'europe':
            api_request = 'https://eun1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/' + puuid + '?api_key=' + self.api_key
            result = self.execute_request(api_request).json()
            return result
        pass

    def get_player_rank_from_id(self, player_id: str):
        #https://eun1.api.riotgames.com/lol/league/v4/entries/by-summoner/DJVAbPvNZ2DYBaUPwvLHn1RqaVZlUp8Yxn_BJ1fnuYK1IQM?api_key=RGAPI-c512a757-1456-41ea-afd9-5df1e41a6eff
        
        if self.selected_region == 'europe':
            api_request = 'https://eun1.api.riotgames.com/lol/league/v4/entries/by-summoner/' + player_id + '?api_key=' + self.api_key
            result = self.execute_request(api_request).json()
            return result

    # Function returns a list of players or None and error code
    def get_players_stats_from_match(self, match_stats) -> Tuple[list, str]:
        # Kills, Deaths, Assists, Role!!!, PUUIDS, GameName/TagLine, Pings Number, Champion, Won/Lost
        # Discriminate between ranked/summoner's rift vs ranked/arena(2v2)&flex, wards placed/taken down

        general_info = match_stats['info']                      
        date = datetime.fromtimestamp(general_info['gameCreation'] / 1000).strftime('%Y-%m-%d %H:%M:%S')
        match_id = match_stats['metadata']['matchId']
        is_ranked = general_info['gameMode'] == 'CLASSIC'
        is_ranked = general_info['gameType'] == 'MATCHED_GAME'

        if not is_ranked:
            return players, 'Game is not ranked!'
        
        players = general_info['participants']

        player_list = []
        for p in players:
            ping_count = p['allInPings'] + p['assistMePings'] + \
            p['basicPings'] + p['commandPings'] + p['dangerPings'] + \
            p['enemyMissingPings'] + p['enemyVisionPings'] + \
            p['getBackPings'] + p['holdPings'] + p['needVisionPings'] + \
            p['onMyWayPings'] + p['pushPings'] + p['visionClearedPings']

            riot_name = None
            tag_line = None

            
            """
            First need to check if riotIdGameName is a key because
            some player have riotIdName
            """

            if 'riotIdGameName' in p:
                if p['riotIdGameName'] == '' and p['riotIdTagline'] == '':
                    riot_name = p['summonerName']
                    tag_line = get_tagline(self.selected_region)
                else:
                    riot_name = p['riotIdGameName']
                    tag_line = p['riotIdTagline']
            else:
                if p['riotIdName'] == '' and p['riotIdTagline'] == '':
                    riot_name = p['summonerName']
                    tag_line = get_tagline(self.selected_region)

            # TODO: Must run a thorough scan on players, some have undefined roles
            role = None
            role = p['teamPosition']
            if role == "UTILITY":
                role = "SUPPORT"

            player = {
                'champion': {
                    'name': p['championName'], 
                    'id': str(p['championId'])
                },
                'kills': p['kills'],
                'deaths': p['deaths'],
                'assists': p['assists'],
                'pingCount': ping_count,
                'missingPings': p['enemyMissingPings'],
                'win': p['win'] ,
                'puuid': p['puuid'],
                'name': riot_name,
                'tag': tag_line,
                'role': role,
                'matchId': match_id,
                'damage': p['totalDamageDealtToChampions'],
                'date': date,
                'cs': p['totalMinionsKilled']
            }

            player_list.append(player)
    
        return player_list


