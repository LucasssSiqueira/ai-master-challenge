"""Parâmetros do Lead Scorer. Ajustes de negócio acontecem aqui, não no código."""
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@dataclass(frozen=True)
class ScoringConfig:
    # "Hoje" do pipeline. O dataset termina em 31/12/2017; usar a data real deixaria
    # todos os deals com ~9 anos de idade.
    reference_date: pd.Timestamp = pd.Timestamp("2017-12-31")

    # Pesos dos componentes (somam 100). Escolhidos pelo backtest: com 50/30/20, a chance
    # (AUC 0,50) só somava ruído; 60/40/0 capturou mais valor ganho em 8 de 9 meses.
    # A chance continua calculada e exibida como informação.
    weight_value: float = 60.0
    weight_timing: float = 40.0
    weight_prob: float = 0.0

    # Nenhum deal do histórico levou mais que 138 dias entre engajamento e fechamento.
    stale_days: int = 138

    # Shrinkage bayesiano: um vendedor×produto precisa de ~k deals fechados para
    # que o histórico próprio pese tanto quanto a média do time.
    k_shrinkage: float = 50.0
    # Distância da média (em pontos de win rate) que leva a chance a 0 ou 20 pontos.
    prob_spread: float = 0.10

    # Faixas entre deals ativos (Engaging dentro do ciclo): score >= percentil 75 = Alta,
    # >= percentil 40 = Média. Empates no corte sobem de faixa, então a Alta pode passar de 25%.
    high_quantile: float = 0.75
    medium_quantile: float = 0.40


DEFAULT_CONFIG = ScoringConfig()

# Correções de inconsistências encontradas na fonte.
PRODUCT_FIXES = {"GTXPro": "GTX Pro"}
SECTOR_FIXES = {"technolgy": "technology"}

STAGES = {"Prospecting", "Engaging", "Won", "Lost"}
OPEN_STAGES = {"Prospecting", "Engaging"}
