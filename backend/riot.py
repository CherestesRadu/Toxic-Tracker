import requests as req
import time
import sys

class RiotApi:
    def __init__(self, key: str, region: str):
        self.api_key = key
        self.selected_region = region
        self.root_request = 'https://' + region + '.api.riotgames.com'

    def execute_request(self, api_request):

        # TODO: Use library for request wait times
        result = req.get(api_request)
        time_to_sleep = 5.0
        while result.status_code == 429: # Rate limit exceeded
            time.sleep(time_to_sleep)
            result = req.get(api_request)
            time_to_sleep += 5.0
        

        # TODO: Better error handling
        if result.status_code == 200: # OK
            return result
        else:
            raise Exception('Handle error')

    def set_region(self, region: str):
        self.selected_region = region

    def get_player_from_uuid(player_uuid: str):
        pass

    def get_player_from_summoner_name(summoner_name: str):
        pass

    def get_account_from_riot_id(self, riot_id_name: str, tag: str):
        #'https://europe.api.riotgames.com/riot/account/v1/accounts/by-riot-id/CJLOR2/EUNE?api_key=RGAPI-cbf5d9bf-930d-4489-9181-8b0fe6ac8642'
        api_request = self.root_request + '/riot/account/v1/accounts/by-riot-id/' + riot_id_name + '/' + tag + '?api_key=' + self.api_key
        result = self.execute_request(api_request).json()
        return result
    
    def get_matches_from_puuid(self, puuid: str): # TODO: Default is 20 games, control num with param
        #"https://europe.api.riotgames.com/lol/match/v5/matches/by-puuid/ubD8VSQx-85GcWmO8UbSqz2kaex8zw2FSaSaOGRgQ_FJ_YdGqlZohc7bLGbUKGMJlDSAFPNBFu-PWQ/ids?type=ranked&start=0&count=20&api_key=RGAPI-cbf5d9bf-930d-4489-9181-8b0fe6ac8642"
        api_request = self.root_request + '/lol/match/v5/matches/by-puuid/' + puuid + '/ids?type=ranked&start=0&count=20&api_key=' + self.api_key
        result = self.execute_request(api_request).json()
        return result
    
    def get_match_stats(self, match_id: str):
        #https://europe.api.riotgames.com/lol/match/v5/matches/EUN1_3589088922?api_key=RGAPI-cbf5d9bf-930d-4489-9181-8b0fe6ac8642
        api_request = self.root_request + '/lol/match/v5/matches/' + match_id + '?api_key=' + self.api_key
        result = self.execute_request(api_request).json()
        return result

