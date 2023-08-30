from odoo import fields, models, api


class AddisBaseCRMLeadInherited(models.Model):
    _inherit = 'res.company'

    def addis_system_connection_init(self):
        super(AddisBaseCRMLeadInherited, self).addis_system_connection_init()
        self.env['crm.lead'].addis_system_crm_lead_consumer()

