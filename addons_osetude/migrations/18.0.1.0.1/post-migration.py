# -*- coding: utf-8 -*-
# Migration 18.0.1.0.0 → 18.0.1.0.1
# current_revision_id etait copie a la duplication (sale_order_revision, copy=True) :
# un devis duplique depuis une ancienne revision restait rattache a la revision
# courante et faussait le bouton "Revision prec.". On detache ces devis, reconnus
# a leur reference d'origine (unrevisioned_name) differente de celle de la revision.
# Les anciennes valeurs sont conservees dans _backup_osetude_18_0_1_0_1_revision_link
# (rollback : UPDATE sale_order s SET current_revision_id = b.current_revision_id
#             FROM _backup_osetude_18_0_1_0_1_revision_link b WHERE s.id = b.id;)

import logging
_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    cr.execute("""
        CREATE TABLE IF NOT EXISTS _backup_osetude_18_0_1_0_1_revision_link AS
        SELECT s.id, s.current_revision_id
          FROM sale_order s
          JOIN sale_order c ON c.id = s.current_revision_id
         WHERE s.unrevisioned_name IS DISTINCT FROM c.unrevisioned_name
    """)
    cr.execute("""
        UPDATE sale_order s SET current_revision_id = NULL
          FROM _backup_osetude_18_0_1_0_1_revision_link b
         WHERE s.id = b.id AND s.current_revision_id = b.current_revision_id
    """)
    _logger.info("addons_osetude: %s devis detaches d'une revision qui n'est pas la leur", cr.rowcount)
