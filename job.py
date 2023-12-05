import time

import schedule

import variables
from domain.usecases.job_train import JobTrainUseCase
from infra.repositories.league import LeagueRepository
from infra.repositories.model import ModelRepository

if __name__ == '__main__':
    league_repository = LeagueRepository(available_leagues_filepath=variables.available_leagues_filepath,
                                         saved_leagues_directory=variables.saved_leagues_directory)

    model_repository = ModelRepository(models_checkpoint_directory=variables.models_checkpoint_directory)

    train_use_case = JobTrainUseCase(league_repository=league_repository, model_repository=model_repository)
    train_use_case.execute()
    print("done")
    # schedule.every().day().at("02:00").do(train_use_case.execute())

    # while True:
    #     schedule.run_pending()
    #     time.sleep(1)
