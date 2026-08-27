# copadomundo

## Pipeline Transfermarkt

Este projeto pode receber dados de elenco/valor de mercado por uma API compatÃ­vel com Transfermarkt e transformar isso em features por seleÃ§Ã£o.

> ObservaÃ§Ã£o: o Transfermarkt nÃ£o oferece uma API pÃºblica oficial estÃ¡vel. Use um wrapper/serviÃ§o autorizado e configure a URL base dele nas variÃ¡veis abaixo.

### 1. Configurar credenciais

```powershell
$env:TRANSFERMARKT_API_BASE_URL="https://sua-api-transfermarkt.com"
$env:TRANSFERMARKT_API_KEY="sua-chave-se-a-api-usar-token"
```

Se a API usar outro tipo de autenticaÃ§Ã£o, ajuste `api/transfermarkt/client.py`.

### 2. Conferir o mapa de seleÃ§Ãµes

Edite `data/transfermarkt_teams.json` com os IDs esperados pela sua API:

```json
[
  { "team": "Brazil", "club_id": "3439" },
  { "team": "France", "club_id": "3377" }
]
```

### 3. Coletar e normalizar elencos

```powershell
python -m api.transfermarkt.ingest --season-id 2024
```

SaÃ­das:

- `data/raw/transfermarkt_<team>_<season>.json`: resposta bruta da API.
- `data/processed/transfermarkt_players_<season>.csv`: jogadores normalizados.
- `data/processed/transfermarkt_team_features_<season>.csv`: features agregadas por seleÃ§Ã£o.

### 4. Juntar com o dataset do modelo

```powershell
python -m api.transfermarkt.merge_features `
  --features data/processed/transfermarkt_team_features_2024.csv `
  --output data/final_matches_with_transfermarkt.csv
```

O arquivo final adiciona colunas `home_transfermarkt_*`, `away_transfermarkt_*` e diferenÃ§as como `transfermarkt_squad_value_eur_difference`.

## Pipeline football-data.org

Use esta integraÃ§Ã£o para baixar dados do plano gratuito do `football-data.org` sem estourar o limite padrÃ£o de `10 requisiÃ§Ãµes por minuto`.

### 1. Configurar token

```powershell
$env:FOOTBALL_DATA_API_TOKEN="seu-token"
```

O token nÃ£o fica salvo no repositÃ³rio. O cliente usa um intervalo padrÃ£o de `6,2s` entre chamadas e faz retry automÃ¡tico em `429 Too Many Requests`.

### 2. Baixar partidas e seleÃ§Ãµes de uma competiÃ§Ã£o

Exemplos com competiÃ§Ãµes do plano free:

- `WC`: World Cup
- `EC`: European Championship
- `BSA`: BrasileirÃ£o SÃ©rie A
- `PL`: Premier League

```powershell
python -m api.football_data.ingest --competition WC --season 2022 --status FINISHED
```

TambÃ©m dÃ¡ para limitar por intervalo de datas:

```powershell
python -m api.football_data.ingest `
  --competition BSA `
  --season 2024 `
  --date-from 2024-04-01 `
  --date-to 2024-12-31
```

SaÃ­das:

- `data/raw/football_data_<competition>_<season>_matches.json`
- `data/raw/football_data_<competition>_<season>_teams.json`
- `data/processed/football_data_<competition>_<season>_matches.csv`
- `data/processed/football_data_<competition>_<season>_teams.csv`

### 3. ObservaÃ§Ãµes sobre limite

- O plano gratuito aceita poucas competiÃ§Ãµes e `10 calls/min`.
- Prefira baixar por competiÃ§Ã£o e temporada, nÃ£o por muitas janelas pequenas.
- O script atual faz apenas `2` chamadas por execuÃ§Ã£o: uma para partidas e uma para equipes.
- Nos testes deste projeto em `2026-08-27`, `BSA --season 2024` funcionou, mas `WC --season 2022` retornou `403`, entÃ£o o acesso histÃ³rico pode variar por competiÃ§Ã£o e filtro mesmo com o token vÃ¡lido.
