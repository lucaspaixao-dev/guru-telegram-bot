from datetime import datetime

from infra.clients.footystats.footystats import FootystatsClient


class BrasileiraoMatchesAnalyseUseCase(object):
    def __init__(self):
        self.client = FootystatsClient()

    def execute(self, today_matches: list):
        leagues = self.client.get_league_info()
        league_id = 0

        for league in leagues:
            if league.get('name') == 'Brazil Serie A':
                seasons = league.get('season')
                league_id = seasons[-1].get('id')

        if league_id == 0:
            return None

        brazil_predicted_matches = []

        for m in today_matches:
            if m.get('competition_id') == league_id:
                home_team_info = self.client.get_team_info(team_id=m.get('homeID'))[0]
                away_team_info = self.client.get_team_info(team_id=m.get('awayID'))[0]

                game_date = datetime.fromtimestamp(m.get('date_unix'))
                game_time_formatted = game_date.strftime("%H:%M")

                match = {
                    "league": "Brasileirão",
                    "round": m.get('game_week'),
                    "home_team": str(home_team_info.get('name')).upper(),
                    "away_team": str(away_team_info.get('name')).upper(),
                    "time": game_time_formatted,
                    "predict": "",
                    "home_percentage": "",
                    "draw_percentage": "",
                    "away_percentage": ""
                }

                brazil_predicted_matches.append(match)


if __name__ == '__main__':
    today_matches = FootystatsClient().get_today_matches()
    analyse = BrasileiraoMatchesAnalyseUseCase()

    analyse.execute(today_matches=today_matches)
