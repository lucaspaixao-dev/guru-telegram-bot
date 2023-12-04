import requests


class FootystatsClient(object):
    def __init__(self):
        self.__api_key = "4e8734fa37e80bd0222340ecd1be45b4352545e56f40e9579b32fb055ea750b8"

    def get_today_matches(self):
        try:
            utc = '-03'
            date = '2023-12-06'
            return requests.get(
                url=f"https://api.football-data-api.com/todays-matches?key={self.__api_key}&timezone={utc}&date={date}"
            ).json().get('data')
        except Exception as e:
            print(e)
            raise e

    def get_team_info(self, team_id: int):
        try:
            return requests.get(
                url=f"https://api.football-data-api.com/team?key={self.__api_key}&team_id={team_id}"
            ).json().get('data')
        except Exception as e:
            print(e)
            raise e

    def get_league_info(self, ):
        try:
            return requests.get(
                url=f"https://api.football-data-api.com/league-list?key={self.__api_key}&chosen_leagues_only=true"
            ).json().get('data')
        except Exception as e:
            print(e)
            raise e
