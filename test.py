import json

import pandas as pd

if __name__ == '__main__':
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

        print(msg)
