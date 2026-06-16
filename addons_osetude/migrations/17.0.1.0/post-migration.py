# -*- coding: utf-8 -*-
# Migration script V16.0.1.1 → V17.0.1.0
# Exécuté APRÈS le chargement des modèles V17

import logging
_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """
    Post-migration: handle data transformations after V17 models are loaded.
    """
    if not version:
        return
    _logger.info("addons_osetude: post-migration V16→V17 (version=%s)", version)

    # Exemple: migrer purchase.order.line.account_analytic_id → analytic_distribution
    # Cette migration est déjà gérée par OpenUpgrade pour les champs standard.
    # Si des données custom nécessitent une migration, les ajouter ici.
