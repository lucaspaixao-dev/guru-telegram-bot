import schedule
import time

import variables
from domain.usecases.job_train import JobTrainUseCase
from infra.repositories.league import LeagueRepository
from infra.repositories.model import ModelRepository


def execute():
    league_repository = LeagueRepository(available_leagues_filepath=variables.available_leagues_filepath,
                                         saved_leagues_directory=variables.saved_leagues_directory)

    model_repository = ModelRepository(models_checkpoint_directory=variables.models_checkpoint_directory)

    use_case = JobTrainUseCase(league_repository=league_repository, model_repository=model_repository)
    use_case.execute(country="England")


if __name__ == '__main__':
    schedule.every().monday.at("02:00").do(execute)
    schedule.every().friday.at("02:00").do(execute)
    while True:
        schedule.run_pending()
        time.sleep(1)
