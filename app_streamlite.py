import streamlit as st
import requests
import pandas as pd # Adicionado para facilitar a criação da tabela

# Configurações API (Puxam dos Secrets, como corrigido)
FOOTBALL_API_KEY = st.secrets.get("FOOTBALL_API_KEY")
ODDS_API_KEY = st.secrets.get("ODDS_API_KEY")
LEAGUE_ID = 71 # Brasileirão Série A (Exemplo)

# Headers (Cabeçalhos)
HEADERS_FOOTBALL = {'X-RapidAPI-Key': FOOTBALL_API_KEY, 'X-RapidAPI-Host': 'api-football-v1.p.rapidapi.com'}
HEADERS_ODDS = {'X-RapidAPI-Key': ODDS_API_KEY, 'X-RapidAPI-Host': 'odds-api.p.rapidapi.com'}

# --- FUNÇÕES DE BUSCA DE DADOS ---

def get_upcoming_fixtures(season, league_id):
    """Busca os próximos jogos (fixtures) da liga por data/rodada."""
    
    # Usamos o filtro 'next=20' para buscar os próximos 20 jogos
    url = f'https://api-football-v1.p.rapidapi.com/v3/fixtures?league={league_id}&season={season}&next=20'
    
    # Verifica se as chaves existem antes de fazer a requisição
    if not FOOTBALL_API_KEY:
        st.error("Chave 'FOOTBALL_API_KEY' não encontrada. Verifique o campo Secrets.")
        return []
        
    try:
        response = requests.get(url, headers=HEADERS_FOOTBALL)
        response.raise_for_status() 
        return response.json().get('response', [])
    except Exception as e:
        st.error(f"Erro ao buscar jogos: Verifique a temporada e a LEAGUE_ID ({league_id}). Erro: {e}")
        return []


def get_odds_for_fixture(fixture_id):
    """Puxa as odds para um único jogo (requer FOOTBALL_API_KEY e ODDS_API_KEY)"""
    url_odds = f'https://odds-api.p.rapidapi.com/v1/odds?sport=soccer_brazil_campeonato&fixture={fixture_id}'
    
    # Verifica se a chave de odds existe
    if not ODDS_API_KEY:
        return {'Casa': 'Chave Ausente', 'Empate': 'Chave Ausente', 'Visitante': 'Chave Ausente'}

    try:
        response_odds = requests.get(url_odds, headers=HEADERS_ODDS)
        response_odds.raise_for_status()
        data_odds = response_odds.json().get('data')

        if data_odds and data_odds[0].get('odds'):
            # Pega as odds do primeiro bookmaker ou 'N/A'
            o = data_odds[0]['odds'][0]
            return {
                'Casa': o.get('home_win', 'N/A'),
                'Empate': o.get('draw', 'N/A'),
                'Visitante': o.get('away_win', 'N/A')
            }
        return {'Casa': 'N/A', 'Empate': 'N/A', 'Visitante': 'N/A'}
    except requests.exceptions.HTTPError as e:
         # Se a API de Odds rejeitar a chave (403)
        if e.response.status_code == 403:
            return {'Casa': 'Chave Inválida', 'Empate': 'Chave Inválida', 'Visitante': 'Chave Inválida'}
        return {'Casa': 'Erro API', 'Empate': 'Erro API', 'Visitante': 'Erro API'}
    except Exception:
        return {'Casa': 'Erro Geral', 'Empate': 'Erro Geral', 'Visitante': 'Erro Geral'}


# --- INTERFACE STREAMLIT ---

st.title("⚽ Tendências e Odds da Série A 🇧🇷")
st.subheader("Próximos Jogos e Cotações de Apostas")

st.sidebar.header("Configurações")
# Usando o ano como filtro para a API de Futebol
season = st.sidebar.selectbox("Temporada (Ano)", ["2024", "2023"], index=0)

if st.button("Buscar Próximos Jogos e Odds"):
    
    # 1. Puxa os IDs dos próximos jogos
    fixtures = get_upcoming_fixtures(season, LEAGUE_ID)
    
    if not fixtures:
        st.warning("Nenhum jogo futuro encontrado. Verifique a chave ou o ano da temporada.")
    else:
        st.success(f"Encontrados {len(fixtures)} jogos futuros na temporada {season}. Buscando Odds...")
        
        data_for_table = []
        progress_bar = st.progress(0)
        
        for i, fixture in enumerate(fixtures):
            home_team = fixture['teams']['home']['name']
            away_team = fixture['teams']['away']['name']
            fixture_id = fixture['fixture']['id']
            match_date = fixture['fixture']['date'].split('T')[0] 

            # 2. Puxa as odds para o jogo
            odds_data = get_odds_for_fixture(fixture_id)

            data_for_table.append({
                'Data': match_date,
                'Partida': f"{home_team} vs {away_team}",
                'Odd Casa': odds_data['Casa'],
                'Odd Empate': odds_data['Empate'],
                'Odd Visitante': odds_data['Visitante'],
            })
            
            # Atualiza a barra de progresso
            progress_bar.progress((i + 1) / len(fixtures))
        
        st.markdown("---")
        st.subheader("Tabela de Odds dos Próximos Jogos (Primeiro Bookmaker)")
        df = pd.DataFrame(data_for_table)
        st.dataframe(df)
