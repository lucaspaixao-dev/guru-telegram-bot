from infra.repositories.league import LeagueRepository


class CreateLeagueInput(object):
    def __init__(
            self,
            country: str,
            official_league_name: str,
            custom_league_name: str,
            last_n_matches: int,
            goal_diff_margin: int
    ):
        self.country = country
        self.official_league_name = official_league_name
        self.custom_league_name = custom_league_name
        self.last_n_matches = last_n_matches
        self.goal_diff_margin = goal_diff_margin


class CreateLeagueUseCase(object):
    def __init__(self, league_repository: LeagueRepository):
        self.__league_repository = league_repository

    def execute(self, input: CreateLeagueInput, ):
        columns = self.__get_columns()
        selected_home_columns = [col for i, col in enumerate(columns.get('home_columns'))]
        selected_away_columns = [col for i, col in enumerate(columns.get('away_columns'))]

        all_leagues = self.__league_repository.get_all_available_leagues()

        matches_df, league = self.__league_repository.create_league(
            league=all_leagues[(input.country, input.official_league_name)],
            last_n_matches=input.last_n_matches,
            goal_diff_margin=input.goal_diff_margin,
            statistic_columns=selected_home_columns + selected_away_columns,
            league_name=input.custom_league_name
        )

        return input.custom_league_name, league, matches_df

    def __get_columns(self):
        all_columns = self.__league_repository.get_all_available_columns()

        home_columns = [col for col in all_columns if col[0] == 'H']
        away_columns = [col for col in all_columns if col[0] == 'A']

        return {
            'home_columns': home_columns,
            'away_columns': away_columns
        }
