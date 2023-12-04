import datetime
import logging

import telegram
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

import variables
from domain.usecases.create_league import CreateLeagueUseCase, CreateLeagueInput
from domain.usecases.load_league import LoadLeagueUseCase, LoadLeagueInput
from domain.usecases.neural_network import NeuralNetworkUseCase, NeuralNetworkInput
from domain.usecases.random_forest import RandomForestUseCase, RandomForestInput
from infra.repositories.league import LeagueRepository
from infra.repositories.model import ModelRepository
from domain.usecases.job_matches_analyse import JobMatchesAnalyseUseCase

from infra.clients.footystats.footystats import FootystatsClient

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


footstats_client = FootystatsClient()


async def predictions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="Realizando predições para os jogos de hoje 🧙‍")

    today_matches = footstats_client.get_today_matches()
    matches = []

    for match in today_matches:
        home_team_info = footstats_client.get_team_info(team_id=match.get('homeID'))[0]
        away_team_info = footstats_client.get_team_info(team_id=match.get('awayID'))[0]

        game_date = datetime.datetime.fromtimestamp(match.get('date_unix'))
        game_time_formatted = game_date.strftime("%H:%M")

        info_match = {
            "round": match.get('game_week'),
            "home_team": str(home_team_info.get('name')).upper(),
            "away_team": str(away_team_info.get('name')).upper(),
            "time": game_time_formatted,
            "stadium_name": match.get('stadium_name'),
            "odds_ft_1": match.get('odds_ft_1'),
            "odds_ft_x": match.get('odds_ft_x'),
            "odds_ft_2": match.get('odds_ft_2'),
        }

        matches.append(info_match)

    text = ""
    for m in matches:
        match_text = (f"⚽️ <b>{m.get('home_team')} x {m.get('away_team')}</b>\n "
                      f"🏟️ Local: <b>{m.get('stadium_name')}</b>\n "
                      f"⏰ Horário: <b>{m.get('time')}</b>\n "
                      f"📈 Odds: Casa: <b>{m.get('odds_ft_1')}</b>, "
                      f"Empate: <b>{m.get('odds_ft_x')}</b>, "
                      f"Visitante: <b>{m.get('odds_ft_2')}</b>\n\n")

        text += match_text

    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text=text,
                                   parse_mode=telegram.constants.ParseMode.HTML)


async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Aguarde")

    job = JobMatchesAnalyseUseCase(model_repository=model_repository, league_repository=league_repository)
    result = job.execute()

    msg = "<b>Jogos do dia:</b>\n\n"

    if "Brasileirão" in result:
        brazil_predictions = result.get("Brasileirão")

        brazil_msg = "Brasileirão 🇧🇷:\n"

        for p in brazil_predictions:
            if p.get('predict') == 'H':
                prediction = p.get("home_team")
            elif p.get('predict') == 'A':
                prediction = p.get("away_team")
            else:
                prediction = 'EMPATE'

            t = (f'⚽️ Rodada: {p.get("round")}\n'
                 f'⚽️ Partida: {p.get("home_team")} X {p.get("away_team")}\n'
                 f'⏰ Horário: {p.get("time")}\n'
                 f'🧙‍ Palpite: <b>{prediction}</b>\n'
                 f'📈 Porcentagem do {p.get("home_team")} ganhar é de <b>{p.get("home_percentage")}%</b>\n'
                 f'📈 Porcentagem do {p.get("away_team")} ganhar é de <b>{p.get("away_percentage")}%</b>\n'
                 f'📈 Porcentagem de EMPATE é de <b>{p.get("draw_percentage")}%</b>\n\n')

            brazil_msg += t
        msg += brazil_msg

    await context.bot.send_message(chat_id=update.effective_chat.id, text=msg,
                                   parse_mode=telegram.constants.ParseMode.HTML)


if __name__ == '__main__':
    application = ApplicationBuilder().token('6505692966:AAEIjOTJw8No1BuNwYaIYEiQwCfjMBXPpig').build()

    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    analyse_handler = CommandHandler('analyse', analyse)
    application.add_handler(analyse_handler)

    predictions_handler = CommandHandler('predictions', predictions)
    application.add_handler(predictions_handler)

    test_handler = CommandHandler('test', test)
    application.add_handler(test_handler)

    application.run_polling()
