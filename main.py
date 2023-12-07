import json
import logging
import os
from datetime import time

import pandas as pd
import telegram
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes
from telegram.ext import CommandHandler

import variables
from infra.repositories.league import LeagueRepository
from infra.repositories.model import ModelRepository

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

league_repository = LeagueRepository(available_leagues_filepath=variables.available_leagues_filepath,
                                     saved_leagues_directory=variables.saved_leagues_directory)

model_repository = ModelRepository(models_checkpoint_directory=variables.models_checkpoint_directory)


async def get_predictions(context: ContextTypes.DEFAULT_TYPE):
    path = 'storage/predicts/predicts.csv'
    chat_id = context.job.chat_id

    if (os.path.exists(path) and os.path.isfile(path)):
        matches_df = pd.read_csv(f'storage/predicts/predicts.csv')
        matches_df = matches_df.reset_index()

        dict_predictions = {}

        for index, row in matches_df.iterrows():
            league = row[1]

            json_acceptable_string = row[2].replace("'", "\"")
            predictions = json.loads(json_acceptable_string)

            dict_predictions[league] = predictions

        if dict_predictions:
            msg = "<b>Jogos do dia:</b>\n\n"

            for index, value in dict_predictions.items():
                if index == "Brasileirão":
                    flag = "🇧🇷"
                else:
                    flag = "🏴󠁧󠁢󠁥󠁮󠁧󠁿"

                msg_header = f"{flag} <b>{index}:</b> \n"

                for p in value:
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

                    msg_header += t

                msg += msg_header

            await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode=telegram.constants.ParseMode.HTML)

def remove_job_if_exists(name: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Remove job with given name. Returns whether job was removed."""
    if context.job_queue:
        current_jobs = context.job_queue.get_jobs_by_name(name)
        if not current_jobs:
            return False
        for job in current_jobs:
            job.schedule_removal()
        return True
    return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_message.chat_id
    remove_job_if_exists(str(chat_id), context)

    t = time(hour=7, minute=30, second=0)
    context.job_queue.run_daily(get_predictions, t, days=tuple(range(6)), name=str(chat_id), chat_id=chat_id)

    msg = "<b>Bem vindo ao bot de palpites de apostas esportivas!</b>\n\n"
    msg += ("<b>Todos os dias você irá receber palpites dos jogos da lista de ligas abaixo."
            "Todas os palpites foram utilizandos algoritmos de machine learn 🖥️</b>\n\n")

    msg += "<b>Ligas disponíveis:</b>\n"
    msg += "- 🇧🇷 <b>Brasileirão</b>\n"
    msg += "- 🏴󠁧󠁢󠁥󠁮󠁧󠁿 <b>Premiere League</b>\n\n"

    msg += "<b>Espero que você faça muitos greens!</b> 🤑🟢✅"

    await context.bot.send_message(chat_id=update.effective_chat.id, text=msg,
                                   parse_mode=telegram.constants.ParseMode.HTML)


if __name__ == '__main__':
    application = ApplicationBuilder().token('6505692966:AAEIjOTJw8No1BuNwYaIYEiQwCfjMBXPpig').build()

    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    application.run_polling(allowed_updates=Update.ALL_TYPES)
