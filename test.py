import os

import variables
from domain.usecases.create_league import CreateLeagueUseCase, CreateLeagueInput
from domain.usecases.job_matches_analyse import JobMatchesAnalyseUseCase
from domain.usecases.job_train import JobTrainUseCase
from domain.usecases.load_league import LoadLeagueUseCase, LoadLeagueInput
from domain.usecases.neural_network import NeuralNetworkUseCase, NeuralNetworkInput
from domain.usecases.random_forest import RandomForestUseCase, RandomForestInput
from infra.repositories.league import LeagueRepository
from infra.repositories.model import ModelRepository

if __name__ == '__main__':
    league_repository = LeagueRepository(available_leagues_filepath=variables.available_leagues_filepath,
                                         saved_leagues_directory=variables.saved_leagues_directory)

    model_repository = ModelRepository(models_checkpoint_directory=variables.models_checkpoint_directory)

    use_case = JobTrainUseCase(league_repository=league_repository, model_repository=model_repository)
    use_case.execute()
