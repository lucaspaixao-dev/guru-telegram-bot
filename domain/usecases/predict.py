import numpy as np
import pandas as pd

from domain.models.ensemble import get_ensemble_predictions
from domain.processing.training import construct_input_from_team_names
from infra.repositories.model import ModelRepository


class PredictInput(object):
    def __init__(
            self,
            matches_df: pd.DataFrame,
            home_team: str,
            away_team: str,
            odd_1: float,
            odd_x: float,
            odd_2: float,
            model_name: str,
            league_name: str
    ):
        self.matches_df = matches_df
        self.home_team = home_team
        self.away_team = away_team
        self.odd_1 = odd_1
        self.odd_x = odd_x
        self.odd_2 = odd_2
        self.model_name = model_name
        self.league_name = league_name


class PredictUseCase(object):
    def __init__(self, model_repository: ModelRepository):
        self.__model_repository = model_repository

    def execute(self, input: PredictInput):
        x = construct_input_from_team_names(
            matches_df=input.matches_df,
            home_team=input.home_team,
            away_team=input.away_team,
            odd_1=input.odd_1,
            odd_x=input.odd_x,
            odd_2=input.odd_2
        )

        if input.model_name == 'Ensemble':
            models = [
                self.__model_repository.load_model(
                    league_name=input.league_name, model_name=name, input_shape=x.shape[1:], random_seed=0
                )
                for name in self.__model_repository.get_all_models(league_name=input.league_name)
            ]
            y_pred, predict_proba = get_ensemble_predictions(x=x, models=models)
        else:
            model = self.__model_repository.load_model(
                league_name=input.league_name, model_name=input.model_name, input_shape=x.shape[1:], random_seed=0
            )
            y_pred, predict_proba = model.predict(x=x)

        predicted = y_pred[0]
        predict_proba = predict_proba.flatten()
        predict_proba = np.round(predict_proba, 2)

        return {
            "predicted": predicted,
            "home": predict_proba[0],
            "draw": predict_proba[1],
            "away": predict_proba[2]
        }
