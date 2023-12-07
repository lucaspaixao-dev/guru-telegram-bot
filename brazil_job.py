import time
from datetime import datetime

import schedule

import variables
from domain.usecases.job_train import JobTrainUseCase
from infra.repositories.league import LeagueRepository
from infra.repositories.model import ModelRepository


def execute():
    league_repository = LeagueRepository(available_leagues_filepath=variables.available_leagues_filepath,
                                         saved_leagues_directory=variables.saved_leagues_directory)

    model_repository = ModelRepository(models_checkpoint_directory=variables.models_checkpoint_directory)

    use_case = JobTrainUseCase(league_repository=league_repository, model_repository=model_repository)
    use_case.execute(country="Brazil")


if __name__ == '__main__':
    current_month = datetime.now().month
    current_year = datetime.now().year

    if current_year == "2024":
        schedule.every().tuesday.at("02:00").do(execute)
        schedule.every().thursday.at("02:00").do(execute)
        while True:
            schedule.run_pending()
            time.sleep(1)
