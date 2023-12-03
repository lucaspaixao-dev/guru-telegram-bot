from typing import Callable

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

from domain.models.model import Model
from domain.tunners.random_forest import RandomForestTuner, RandomForest
from infra.repositories.model import ModelRepository


class RandomForestInput(object):
    def __init__(
            self,
            league_name: str,
            matches_df: pd.DataFrame,
            metric_name: str = 'Accuracy',
            n_trials: int = 100,
            num_eval_samples: int = 50,
            random_seed: int = 0,
            metric_target: str = 'Home',
    ):
        self.league_name = league_name
        self.matches_df = matches_df
        self.metric_name = metric_name
        self.n_trials = n_trials
        self.num_eval_samples = num_eval_samples
        self.random_seed = random_seed
        self.metric_target = metric_target


class RandomForestUseCase(object):
    def __init__(self, model_repository: ModelRepository):
        self._metric_targets = {'Home': 0, 'Draw': 1, 'Away': 2}
        self.__model_repository = model_repository

    def execute(self, input: RandomForestInput):
        metric_name = input.metric_name
        metric_target = self._metric_targets[input.metric_target]

        if metric_name == 'Accuracy':
            metric = lambda y_true, y_pred: accuracy_score(y_true=y_true, y_pred=y_pred)
        elif metric_name == 'F1':
            metric = lambda y_true, y_pred: f1_score(y_true=y_true, y_pred=y_pred, average=None)[metric_target]
        elif metric_name == 'Precision':
            metric = lambda y_true, y_pred: precision_score(
                y_true=y_true, y_pred=y_pred, average=None)[metric_target]
        elif metric_name == 'Recall':
            metric = lambda y_true, y_pred: recall_score(
                y_true=y_true, y_pred=y_pred, average=None)[metric_target]
        else:
            raise NotImplementedError(f'Error: Metric "{metric_name}" has not been implemented yet')

        tuner = self.__construct_tunner(
            input=input,
            metric=metric,
        )

        best_params = tuner.tune()

        self.__train(
            x_train=tuner.x_train,
            y_train=tuner.y_train,
            x_test=tuner.x_test,
            y_test=tuner.y_test,
            best_params=best_params,
            input=input
        )

    def __construct_tunner(
            self,
            input: RandomForestInput,
            metric: Callable
    ):
        return RandomForestTuner(
            n_trials=input.n_trials,
            metric=metric,
            matches_df=input.matches_df,
            num_eval_samples=input.num_eval_samples,
            random_seed=input.random_seed
        )

    def __train(
            self,
            x_train: np.ndarray,
            y_train: np.ndarray,
            x_test: np.ndarray,
            y_test: np.ndarray,
            best_params: dict,
            input: RandomForestInput
    ):
        model = RandomForest(input_shape=x_train.shape[1:], random_seed=input.random_seed)

        self.__build_model(model=model, best_params=best_params)
        self._eval_metrics = model.train(
            x_train=x_train,
            y_train=y_train,
            x_test=x_test,
            y_test=y_test,
            use_over_sampling=best_params['user_over_sampling']
        )
        self.__model_repository.store_model(model=model, league_name=input.league_name)

    def __build_model(self, model: Model, best_params: dict):
        model.build_model(
            n_estimators=best_params['n_estimators'],
            max_features=best_params['max_features'],
            max_depth=best_params['max_depth'],
            min_samples_leaf=best_params['min_samples_leaf'],
            min_samples_split=best_params['min_samples_split'],
            bootstrap=best_params['bootstrap'],
            class_weight=best_params['class_weight'],
            is_calibrated=best_params['is_calibrated']
        )
