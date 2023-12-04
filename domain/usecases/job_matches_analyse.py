from datetime import datetime
from infra.clients.footystats.footystats import FootystatsClient
from infra.repositories.model import ModelRepository
from domain.usecases.matches_analyse import MatchesAnalyseUseCase, MatchesAnalyseInput
from infra.repositories.league import LeagueRepository
from domain.usecases.load_league import LoadLeagueUseCase, LoadLeagueInput


class JobMatchesAnalyseUseCase:
    def __init__(self, model_repository: ModelRepository, league_repository: LeagueRepository):
        self.__client = FootystatsClient()
        self.__matches_analyse_use_case = MatchesAnalyseUseCase(model_repository=model_repository)
        self.__leagues = self.__client.get_league_info()
        self.__load_league_use_case = LoadLeagueUseCase(league_repository=league_repository)

    def execute(self):
        predicts = dict()
        # leagues_to_analyze = [("Brasileirão", "Brazil Serie A"), ("Premiere League", "England Premier League")]
        leagues_to_analyze = [("Brasileirão", "Brazil Serie A")]

        for league_name, external_league_name in leagues_to_analyze:
            matches = self.__client.get_today_matches()
            league_predicts = self.__get_predicts(league_name, external_league_name, matches)

            if league_predicts:
                predicts[league_name] = league_predicts

        return predicts

    def __get_predicts(self, league_name: str, external_league_name: str, matches: list):
        league_id = self.__get_current_season_id(external_league_name)
        load_league_input = LoadLeagueInput(league_name=league_name)
        matches_df = self.__load_league_use_case.execute(input=load_league_input)

        league_predicts = []

        for m in matches:
            if m.get('competition_id') == league_id:
                home_team_info = self.__client.get_team_info(team_id=m.get('homeID'))[0]
                away_team_info = self.__client.get_team_info(team_id=m.get('awayID'))[0]
                game_date = datetime.fromtimestamp(m.get('date_unix'))
                game_time_formatted = game_date.strftime("%H:%M")

                predict = self.__get_match_predict(matches_df, home_team_info, away_team_info, m, league_name)

                final_predict = {
                    "league": league_name,
                    "round": m.get('game_week'),
                    "home_team": str(home_team_info.get('name')).upper(),
                    "away_team": str(away_team_info.get('name')).upper(),
                    "time": game_time_formatted,
                    "predict": predict.get('predict'),
                    "home_percentage": predict.get("home_percentage"),
                    "draw_percentage": predict.get("draw_percentage"),
                    "away_percentage": predict.get("away_percentage")
                }

                league_predicts.append(final_predict)

        return league_predicts

    def __get_match_predict(self, matches_df, home_team_info, away_team_info, match_data, league_name):
        model_names = ["nn", "rf.pickle"]
        predict = None

        for model_name in model_names:
            predict_input = MatchesAnalyseInput(
                matches_df=matches_df,
                home_team=home_team_info.get('name'),
                away_team=away_team_info.get('name'),
                odd_1=match_data.get('odds_ft_1'),
                odd_x=match_data.get('odds_ft_x'),
                odd_2=match_data.get('odds_ft_2'),
                league_name=league_name,
                model_name=model_name
            )

            predict_result = self.__matches_analyse_use_case.execute(input=predict_input)

            if predict is None:
                predict = predict_result

            elif predict_result.get('predict') == predict.get('predict'):
                return predict_result

            else:
                en_predict_input = MatchesAnalyseInput(
                    matches_df=matches_df,
                    home_team=home_team_info.get('name'),
                    away_team=away_team_info.get('name'),
                    odd_1=match_data.get('odds_ft_1'),
                    odd_x=match_data.get('odds_ft_x'),
                    odd_2=match_data.get('odds_ft_2'),
                    league_name=league_name,
                    model_name="Ensemble"
                )

                return self.__matches_analyse_use_case.execute(input=en_predict_input)

    def __get_current_season_id(self, external_league_name: str):
        for league in self.__leagues:
            if league.get('name') == external_league_name:
                seasons = league.get('season')
                return seasons[-1].get('id')

        return 0
