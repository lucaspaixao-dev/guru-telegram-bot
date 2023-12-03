import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

import variables
from domain.usecases.create_league import CreateLeagueUseCase, CreateLeagueInput
from domain.usecases.load_league import LoadLeagueUseCase, LoadLeagueInput
from domain.usecases.neural_network import NeuralNetworkUseCase, NeuralNetworkInput
from domain.usecases.random_forest import RandomForestUseCase, RandomForestInput
from infra.repositories.league import LeagueRepository
from infra.repositories.model import ModelRepository

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

league_repository = LeagueRepository(available_leagues_filepath=variables.available_leagues_filepath,
                                     saved_leagues_directory=variables.saved_leagues_directory)

model_repository = ModelRepository(models_checkpoint_directory=variables.models_checkpoint_directory)

create_league_use_case = CreateLeagueUseCase(league_repository=league_repository)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Criando liga")
    input = CreateLeagueInput(
        country='Brazil',
        official_league_name='Serie-A',
        custom_league_name='Brasileirão',
        last_n_matches=3,
        goal_diff_margin=2
    )

    create_league_use_case.execute(input=input)

    await context.bot.send_message(chat_id=update.effective_chat.id, text="Liga criada!")


load_league_use_case = LoadLeagueUseCase(league_repository=league_repository)
neural_network_use_case = NeuralNetworkUseCase(model_repository=model_repository)
random_forest_use_case = RandomForestUseCase(model_repository=model_repository)


async def analyse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    league_name = 'Brasileirão'

    await context.bot.send_message(chat_id=update.effective_chat.id, text="Realizando análise, aguarde ⏳")
    load_input = LoadLeagueInput(
        league_name=league_name
    )
    matches_df = load_league_use_case.execute(input=load_input)

    await context.bot.send_message(chat_id=update.effective_chat.id, text="Neural Network 👀")
    nn_input = NeuralNetworkInput(
        league_name=league_name,
        matches_df=matches_df
    )
    neural_network_use_case.execute(input=nn_input)

    await context.bot.send_message(chat_id=update.effective_chat.id, text="Random Forest 👀")
    rf_input = RandomForestInput(
        league_name=league_name,
        matches_df=matches_df
    )
    random_forest_use_case.execute(input=rf_input)

    await context.bot.send_message(chat_id=update.effective_chat.id, text="Análise concluida ✅")


if __name__ == '__main__':
    application = ApplicationBuilder().token('6505692966:AAEIjOTJw8No1BuNwYaIYEiQwCfjMBXPpig').build()

    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    analyse_handler = CommandHandler('analyse', analyse)
    application.add_handler(analyse_handler)

    application.run_polling()
