import streamlit as st
import requests
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import matplotlib.pyplot as plt

# Configurações API (substitua pelas suas chaves!)
FOOTBALL_API_KEY = st.secrets["FOOTBALL_API_KEY"] if "FOOTBALL_API_KEY" in st.secrets else "SUA_CHAVE_AQUI"  # Use st.secrets para hospedar
ODDS_API_KEY = st.secrets["ODDS_API_KEY"] if "ODDS_API_KEY" in st.secrets else "SUA_CHAVE_AQUI"
LEAGUE_ID = 71

HEADERS_FOOTBALL = {'X-RapidAPI-Key': FOOTBALL_API_KEY, 'X-RapidAPI-Host': 'api-football-v1.p.rapidapi.com'}
HEADERS_ODDS = {'X-RapidAPI-Key': ODDS_API_KEY, 'X-RapidAPI-Host': 'odds-api.p.rapidapi.com'}

# Dados históricos para ML (simulados; adicione reais para melhor precisão)
historical_data = [
    [1, 50, 25, 3, 40, 30, 1], [2, 48, 28, 4, 42, 35, 1], [3, 55, 30, 1, 50, 25, -1],
    [5, 38, 40, 6, 35, 42, 0], [7, 32, 45, 8, 30, 48, -1], [9, 46, 32, 10, 28, 50, 1]
]
X = np.array([row[:-1] for row in historical_data])
y = np.array([row[-1] for row in historical_data])
model = LogisticRegression()
model.fit(X, y)

# Funções
def get_team_stats(team_name, season):
    url = f'https://api-football-v1.p.rapidapi.com/v3/teams?search={team_name}'
    response = requests.get(url, headers=HEADERS_FOOTBALL)
    if response.status_code != 200 or not response.json()['response']:
        return None
    team_id = response.json()['response'][0]['team']['id']
    url = f'https://api-football-v1.p.rapidapi.com/v3/teams/statistics?league={LEAGUE_ID}&season={season}&team={team_id}'
    response = requests.get(url, headers=HEADERS_FOOTBALL)
    if response.status_code == 200:
        stats = response.json()['response']
        return {
            'text': f"Jogos: {stats['fixtures']['played']['total']}, Vitórias: {stats['fixtures']['wins']['total']}, Derrotas: {stats['fixtures']['loses']['total']}, Empates: {stats['fixtures']['draws']['total']}, Gols Marcados: {stats['goals']['for']['total']['total']}, Sofridos: {stats['goals']['against']['total']['total']}, Cartões Amarelos: {stats['cards']['yellow']}, Vermelhos: {stats['cards']['red']}",
            'pos': int(stats.get('league', {}).get('standings', 10)),
            'goals_for': int(stats['goals']['for']['total']['total']),
            'goals_against': int(stats['goals']['against']['total']['total'])
        }
    return None

def get_odds(home_team, away_team, season):
    url = f'https://api-football-v1.p.rapidapi.com/v3/fixtures?league={LEAGUE_ID}&season={season}&team={home_team}&last=1'
    response = requests.get(url, headers=HEADERS_FOOTBALL)
    if response.status_code != 200 or not response.json()['response']:
        return "Odds indisponíveis."
    fixture_id = response.json()['response'][0]['fixture']['id']
    url = f'https://odds-api.p.rapidapi.com/v1/odds?sport=soccer_brazil_campeonato&fixture={fixture_id}'
    response = requests.get(url, headers=HEADERS_ODDS)
    if response.status_code == 200 and response.json().get('data'):
        odds = response.json()['data'][0]['odds']
        return "\n".join([f"{o['bookmaker']}: Casa {o.get('home_win', 'N/A')}, Empate {o.get('draw', 'N/A')}, Visitante {o.get('away_win', 'N/A')}" for o in odds])
    return "Odds indisponíveis."

def predict_ml(home_pos, home_goals_for, home_goals_against, away_pos, away_goals_for, away_goals_against):
    features = np.array([[home_pos, home_goals_for, home_goals_against, away_pos, away_goals_for, away_goals_against]])
    pred = model.predict(features)[0]
    probs = model.predict_proba(features)[0]
    result = "Casa vence" if pred == 1 else "Empate" if pred == 0 else "Visitante vence"
    return result, probs

# Interface Streamlit
st.title("Tendências de Futebol - Série A 2024/2025")
st.sidebar.header("Configurações")
season = st.sidebar.selectbox("Temporada", ["2023-2024", "2024-2025"], index=1)
home_team = st.text_input("Time da Casa (ex.: Flamengo)")
away_team = st.text_input("Time Visitante (ex.: Palmeiras)")

if st.button("Buscar Tendências + ML"):
    if not home_team or not away_team:
        st.error("Digite os dois times.")
    else:
        season_code = season.replace('-', '')
        home_data = get_team_stats(home_team, season_code)
        away_data = get_team_stats(away_team, season_code)
        
        if not home_data or not away_data:
            st.error("Um ou ambos os times não encontrados. Verifique o nome.")
        else:
            st.subheader(f"Estatísticas de {home_team}")
            st.write(home_data['text'])
            st.subheader(f"Estatísticas de {away_team}")
            st.write(away_data['text'])
            
            st.subheader("Odds de Apostas")
            odds = get_odds(home_team, away_team, season_code)
            st.write(odds)
            
            st.subheader("Previsão com Machine Learning")
            result, probs = predict_ml(home_data['pos'], home_data['goals_for'], home_data['goals_against'], away_data['pos'], away_data['goals_for'], away_data['goals_against'])
            st.write(f"Previsão: {result}")
            st.write(f"Probabilidades: Casa {probs[2]:.2f}, Empate {probs[1]:.2f}, Visitante {probs[0]:.2f}")
            
            # Gráfico
            fig, ax = plt.subplots()
            ax.bar(['Casa', 'Empate', 'Visitante'], [probs[2], probs[1], probs[0]], color=['blue', 'gray', 'red'])
            ax.set_ylabel('Probabilidade')
            st.pyplot(fig)

st.sidebar.markdown("**Times Disponíveis (exemplos):** Palmeiras, Botafogo, Flamengo, São Paulo, Corinthians, etc.")
st.sidebar.markdown("**Nota:** Dados de 2024/2025 são parciais. Use para entretenimento.")
