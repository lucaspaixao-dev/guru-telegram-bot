from infra.repositories.league import LeagueRepository


class LoadLeagueInput(object):
    def __init__(
            self,
            league_name: str
    ):
        self.league_name = league_name


class LoadLeagueUseCase(object):
    def __init__(self, league_repository: LeagueRepository):
        self.__league_repository = league_repository

    def execute(self, input: LoadLeagueInput):
        matches_df, league = self.__league_repository.update_league(league_name=input.league_name)

        if matches_df is None:
            matches_df, league = self.__league_repository.load_league(league_name=input.league_name)

        return matches_df
