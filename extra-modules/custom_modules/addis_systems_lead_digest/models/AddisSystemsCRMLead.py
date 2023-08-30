from odoo import models, fields
from threading import Thread, Event, enumerate

import logging
from .addis_systems import addis_systems_consumer_controller as consumer

_logger = logging.getLogger(__name__)



class AddisSystemsLeadDigest(models.Model):
    _inherit = 'crm.lead'


    addis_systems_lead = fields.Boolean(string='Addis System', default=False)

    def _prepare_addis_systems_opportunity_quotation_context(self):
        self.ensure_one()
        quotation_context = {
            'default_opportunity_id': self.id,
            'default_partner_id': self.partner_id.id,
            'default_sale_order_template_id': self.env.ref('addis_systems_lead_digest.as_service_offer_template').id,
            'default_campaign_id': self.campaign_id.id,
            'default_medium_id': self.medium_id.id,
            'default_origin': self.name,
            'default_source_id': self.source_id.id,
            'default_company_id': self.company_id.id or self.env.company.id,
            'default_tag_ids': [(6, 0, self.tag_ids.ids)]
        }
        if self.team_id:
            quotation_context['default_team_id'] = self.team_id.id
        if self.user_id:
            quotation_context['default_user_id'] = self.user_id.id
        return quotation_context

    def action_new_quotation(self):
        if self.addis_systems_lead:
            action = self.env["ir.actions.actions"]._for_xml_id("sale_crm.sale_action_quotations_new")
            action['context'] = self._prepare_addis_systems_opportunity_quotation_context()
            action['context']['search_default_opportunity_id'] = self.id
            return action
        else:
            return super(AddisSystemsLeadDigest, self).action_new_quotation()

    def addis_system_crm_lead_consumer(self):
        all_active_thread_names = [thread.name for thread in enumerate()]

        lead_thread_name = 'addis_systems_crm_lead_listener'
        if lead_thread_name not in all_active_thread_names:
            _logger.info('Starting Thread %s for company: %s', lead_thread_name, self.env.company.name)
            lead_message_waiter_thread = Thread(target=consumer.addis_systems_lead_digest_async, args=(self, lead_thread_name), name=lead_thread_name)
            lead_message_waiter_thread.daemon = True
            lead_message_waiter_thread.start()
        else:
            _logger.info('Skipping Thread %s for company: %s', lead_thread_name, self.env.company.name)