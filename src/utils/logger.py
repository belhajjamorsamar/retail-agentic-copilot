"""
Configuration centralisée du logging.

Au lieu que chaque fichier définisse sa propre config (logging.basicConfig),
un seul endroit configure le format et le niveau — cohérence garantie dans
tout le projet, un seul endroit à modifier si on veut changer le format des
logs plus tard.
"""

import logging


def get_logger(name: str) -> logging.Logger:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    return logging.getLogger(name)