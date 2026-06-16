# -*- coding: utf-8 -*-
# Migration script V16.0.1.1 → V17.0.1.0
# Exécuté AVANT le chargement des modèles V17

import logging
_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """
    Pre-migration: handle DB-level changes before models are loaded.
    Currently no structural changes needed at pre-migration level.
    """
    if not version:
        return
    _logger.info("addons_osetude: pre-migration V16→V17 (version=%s)", version)
