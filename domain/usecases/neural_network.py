from typing import Callable

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

from domain.models.model import Model
from domain.models.tf.nn import FCNet
from domain.tunners.neural_network import FCNetTuner
from infra.repositories.model import ModelRepository


class NeuralNetworkInput(object):
    def __init__(
            self,
            league_name: str,
            matches_df: pd.DataFrame,
            metric_name: str = 'Accuracy',
            n_trials: int = 100,
            num_eval_samples: int = 50,
            random_seed: int = 0,
            metric_target: str = 'Home',
            epochs: int = 80,
            early_stopping_epochs: int = 35,
            learning_rate_decay_factor: float = 0.2,
            learning_rate_decay_epochs: int = 10,
            min_layers: int = 3,
            max_layers: int = 5,
            min_units: int = 32,
            max_units: int = 128,
            units_increment: int = 16
    ):
        self.metric_name = metric_name
        self.metric_target = metric_target
        self.league_name = league_name
        self.random_seed = random_seed
        self.matches_df = matches_df
        self.n_trials = n_trials
        self.num_eval_samples = num_eval_samples
        self.epochs = epochs
        self.early_stopping_epochs = early_stopping_epochs
        self.learning_rate_decay_factor = learning_rate_decay_factor
        self.learning_rate_decay_epochs = learning_rate_decay_epochs
        self.min_layers = min_layers
        self.max_layers = max_layers
        self.min_units = min_units
        self.max_units = max_units
        self.units_increment = units_increment


class NeuralNetworkUseCase(object):
    def __init__(self, model_repository: ModelRepository):
        self._metric_targets = {'Home': 0, 'Draw': 1, 'Away': 2}
        self.__model_repository = model_repository

    def execute(self, input: NeuralNetworkInput):
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
            input: NeuralNetworkInput,
            metric: Callable
    ):
        return FCNetTuner(
            n_trials=input.n_trials,
            metric=metric,
            matches_df=input.matches_df,
            num_eval_samples=input.num_eval_samples,
            epochs=input.epochs,
            early_stopping_epochs=input.early_stopping_epochs,
            learning_rate_decay_factor=float(input.learning_rate_decay_factor),
            learning_rate_decay_epochs=input.learning_rate_decay_epochs,
            min_layers=input.min_layers,
            max_layers=input.max_layers,
            min_units=input.min_units,
            max_units=input.max_units,
            units_increment=input.units_increment,
            random_seed=input.random_seed
        )

    def __build_model(self, model: Model, best_params: dict, input: NeuralNetworkInput):
        num_hidden_layers = best_params['num_hidden_layers']
        hidden_layers = [best_params[f'layer_{i}'] for i in range(num_hidden_layers)]
        activations = [best_params[f'activation_{i}'] for i in range(num_hidden_layers)]
        batch_normalizations = [best_params[f'bn_{i}'] for i in range(num_hidden_layers)]
        regularizations = [best_params[f'regularization_{i}'] for i in range(num_hidden_layers)]
        dropouts = [best_params[f'dropout_{i}'] for i in range(num_hidden_layers)]

        model.build_model(
            epochs=input.epochs,
            batch_size=best_params['batch_size'],
            early_stopping_epochs=input.early_stopping_epochs,
            learning_rate_decay_factor=input.learning_rate_decay_factor,
            learning_rate_decay_epochs=input.learning_rate_decay_epochs,
            learning_rate=best_params['learning_rate'],
            noise_range=best_params['noise_range'],
            hidden_layers=hidden_layers,
            batch_normalizations=batch_normalizations,
            activations=activations,
            regularizations=regularizations,
            dropouts=dropouts,
            optimizer=best_params['optimizer']
        )

    def __train(
            self,
            x_train: np.ndarray,
            y_train: np.ndarray,
            x_test: np.ndarray,
            y_test: np.ndarray,
            best_params: dict,
            input: NeuralNetworkInput
    ):
        model = FCNet(input_shape=x_train.shape[1:], random_seed=input.random_seed)

        self.__build_model(model=model, best_params=best_params, input=input)
        self._eval_metrics = model.train(
            x_train=x_train,
            y_train=y_train,
            x_test=x_test,
            y_test=y_test,
            use_over_sampling=best_params['user_over_sampling']
        )
        self.__model_repository.store_model(model=model, league_name=input.league_name)
