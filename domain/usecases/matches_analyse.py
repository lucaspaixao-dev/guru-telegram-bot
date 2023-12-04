from datetime import datetime

import pandas as pd

from domain.usecases.predict import PredictUseCase, PredictInput
from infra.repositories.model import ModelRepository


class MatchesAnalyseInput(object):
    def __init__(
            self,
            league_name: str,
            matches_df: pd.DataFrame,
            home_team: str,
            away_team: str,
            odd_1: float,
            odd_x: float,
            odd_2: float,
            model_name: str
    ):
        self.league_name = league_name
        self.matches_df = matches_df
        self.home_team = home_team
        self.away_team = away_team
        self.odd_1 = odd_1
        self.odd_x = odd_x
        self.odd_2 = odd_2
        self.model_name = model_name


class MatchesAnalyseUseCase(object):
    def __init__(self, model_repository: ModelRepository):
        self.__predict_use_case = PredictUseCase(model_repository=model_repository)

    def execute(self, input: MatchesAnalyseInput):
        predict_input = PredictInput(
            matches_df=input.matches_df,
            home_team=input.home_team,
            away_team=input.away_team,
            odd_1=input.odd_1,
            odd_x=input.odd_x,
            odd_2=input.odd_2,
            model_name=input.model_name,
            league_name=input.league_name
        )
        predicted = self.__predict_use_case.execute(input=predict_input)

        if predicted.get("predicted") == 0:
            s_predicted = "H"

        elif predicted.get("predicted") == 1:
            s_predicted = "D"

        else:
            s_predicted = "A"

        return {
            "predict": s_predicted,
            "home_percentage": predicted.get("home"),
            "draw_percentage": predicted.get("draw"),
            "away_percentage": predicted.get("away")
        }
