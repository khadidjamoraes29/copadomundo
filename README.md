# copadomundo

## Pipeline Transfermarkt

Este projeto pode receber dados de elenco/valor de mercado por uma API compatível com Transfermarkt e transformar isso em features por seleção.

> Observação: o Transfermarkt não oferece uma API pública oficial estável. Use um wrapper/serviço autorizado e configure a URL base dele nas variáveis abaixo.

### 1. Configurar credenciais

```powershell
$env:TRANSFERMARKT_API_BASE_URL="https://sua-api-transfermarkt.com"
$env:TRANSFERMARKT_API_KEY="sua-chave-se-a-api-usar-token"
```

Se a API usar outro tipo de autenticação, ajuste `api/transfermarkt/client.py`.

### 2. Conferir o mapa de seleções

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

Saídas:

- `data/raw/transfermarkt_<team>_<season>.json`: resposta bruta da API.
- `data/processed/transfermarkt_players_<season>.csv`: jogadores normalizados.
- `data/processed/transfermarkt_team_features_<season>.csv`: features agregadas por seleção.

### 4. Juntar com o dataset do modelo

```powershell
python -m api.transfermarkt.merge_features `
  --features data/processed/transfermarkt_team_features_2024.csv `
  --output data/final_matches_with_transfermarkt.csv
```

O arquivo final adiciona colunas `home_transfermarkt_*`, `away_transfermarkt_*` e diferenças como `transfermarkt_squad_value_eur_difference`.
