import os

from domain.usecases.create_league import CreateLeagueUseCase, CreateLeagueInput
from domain.usecases.job_matches_analyse import JobMatchesAnalyseUseCase
from domain.usecases.load_league import LoadLeagueUseCase, LoadLeagueInput
from domain.usecases.neural_network import NeuralNetworkUseCase, NeuralNetworkInput
from domain.usecases.random_forest import RandomForestUseCase, RandomForestInput
from infra.repositories.league import LeagueRepository
from infra.repositories.model import ModelRepository


class JobTrainUseCase(object):
    def __init__(self, league_repository: LeagueRepository, model_repository: ModelRepository):
        self.__league_repository = league_repository
        self.__create_league_use_case = CreateLeagueUseCase(league_repository=league_repository)
        self.__load_league_use_case = LoadLeagueUseCase(league_repository=league_repository)
        self.__neural_network_use_case = NeuralNetworkUseCase(model_repository=model_repository)
        self.__random_forest_use_case = RandomForestUseCase(model_repository=model_repository)
        self.__job_matches_analyse = JobMatchesAnalyseUseCase(league_repository=league_repository,
                                                              model_repository=model_repository)

    def execute(self, country: str):
        self.__delete_predicts()

        if country == "Brazil":
            self.__process(country="Brazil", official_league_name='Serie-A', custom_league_name='Brasileirão')

        if country == "England":
            self.__process(country="England", official_league_name='Premier-League',
                           custom_league_name='Premier-League')

        self.__job_matches_analyse.execute()

    def __process(self, country: str, official_league_name: str, custom_league_name: str):
        input_params = {
            'country': country,
            'official_league_name': official_league_name,
            'custom_league_name': custom_league_name,
            'last_n_matches': 3,
            'goal_diff_margin': 2
        }

        self.__process_league(**input_params)

    def __process_league(self, country: str, official_league_name: str, custom_league_name: str,
                         last_n_matches: int, goal_diff_margin: int):
        input = CreateLeagueInput(
            country=country,
            official_league_name=official_league_name,
            custom_league_name=custom_league_name,
            last_n_matches=last_n_matches,
            goal_diff_margin=goal_diff_margin
        )

        print(f"Attempting to create league {custom_league_name}")
        create_league_result = self.__create_league_use_case.execute(input=input)

        if create_league_result[2] is None:
            print(f"League already exists {custom_league_name}, loading...")

            load_league_input = LoadLeagueInput(league_name=custom_league_name)
            matches_df = self.__load_league_use_case.execute(input=load_league_input)
        else:
            matches_df = create_league_result[2]

        self.__train_neural_network(custom_league_name, matches_df)
        self.__train_random_forest(custom_league_name, matches_df)

    def __train_neural_network(self, custom_league_name, matches_df):
        print(f"NN train for league {custom_league_name}")
        nn_input = NeuralNetworkInput(league_name=custom_league_name, matches_df=matches_df)
        self.__neural_network_use_case.execute(input=nn_input)
        print("NN completed")

    def __train_random_forest(self, custom_league_name, matches_df):
        print(f"RF train for league {custom_league_name}")
        rf_input = RandomForestInput(league_name=custom_league_name, matches_df=matches_df)
        self.__random_forest_use_case.execute(input=rf_input)
        print("RF completed")

    def __delete_predicts(self):
        files = os.listdir("storage/predicts")
        for file in files:
            os.remove(file)  # delete all files
