from odoo import models, fields, api
from odoo.http import request
import re


class AddisSystemsThemeIrAsset(models.Model):
    _inherit = 'ir.asset'

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get('theme_variables', False):
            for vals in vals_list:
                vals.pop('website_id', False)
        return super().create(vals_list)


class AddisSystemsThemeIrAttachment(models.Model):
    _inherit = 'ir.attachment'

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get('theme_variables', False):
            for vals in vals_list:
                vals.pop('website_id', False)
        return super().create(vals_list)


class AddisSystemsThemeIrHttp(models.AbstractModel):
    _inherit = "ir.http"

    def session_info(self):
        result = super(AddisSystemsThemeIrHttp, self).session_info()
        if request.env.user._is_internal():
            for company in request.env.user.company_ids:
                result['user_companies']['allowed_companies'][company.id].update({'has_background_image': bool(company.background_image)})
        result['pager_autoload_interval'] = int(self.env['ir.config_parameter'].sudo().get_param('addis_systems_base.autoload', default=30000))
        return result


class AddisSystemsThemeScssEditor(models.AbstractModel):
    _inherit = 'web_editor.assets'

    def _get_theme_variable(self, content, variable):
        regex = r'{0}\:?\s(.*?);'.format(variable)
        value = re.search(regex, content)
        return value and value.group(1)

    def _get_theme_variables(self, content, variables):
        return {var: self._get_theme_variable(content, var) for var in variables}

    def _replace_theme_variables(self, content, variables):
        for variable in variables:
            variable_content = '{0}: {1};'.format(variable['name'], variable['value'])
            regex = r'{0}\:?\s(.*?);'.format(variable['name'])
            content = re.sub(regex, variable_content, content)
        return content

    def get_theme_variables_values(self, url, bundle, variables):
        custom_url = self._make_custom_asset_url(url, bundle)
        content = self._get_content_from_url(custom_url)
        if not content:
            content = self._get_content_from_url(url)
        return self._get_theme_variables(content.decode('utf-8'), variables)

    def replace_theme_variables_values(self, url, bundle, variables):
        original = self._get_content_from_url(url).decode('utf-8')
        content = self._replace_theme_variables(original, variables)
        self.with_context(theme_variables=True).save_asset(url, bundle, content, 'scss')


class AddisSystemsThemeResCompany(models.Model):
    _inherit = 'res.company'

    background_image = fields.Binary(string='Apps Menu Background Images', attachment=True)


class AddisSystemsThemeResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)

    theme_favicon = fields.Binary(related='company_id.favicon', readonly=False)
    theme_background_image = fields.Binary(related='company_id.background_image', readonly=False)
    theme_color_brand = fields.Char(string='Theme Brand Color')
    theme_color_primary = fields.Char(string='Theme Primary Color')
    theme_color_menu = fields.Char(string='Theme Menu Color')
    theme_color_appbar_color = fields.Char(string='Theme AppBar Color')
    theme_color_appbar_background = fields.Char(string='Theme AppBar Background')

    def action_reset_theme_assets(self):
        self.env['web_editor.assets'].reset_asset('/addis_systems_base/static/src/colors.scss', 'web._assets_primary_variables', )
        return {'type': 'ir.actions.client', 'tag': 'reload', }

    def set_values(self):
        res = super(AddisSystemsThemeResConfigSettings, self).set_values()
        variables = ['o-brand-odoo', 'o-brand-primary', 'as-menu-color', 'as-appbar-color', 'as-appbar-background', ]
        colors = self.env['web_editor.assets'].get_theme_variables_values('/addis_systems_base/static/src/colors.scss', 'web._assets_primary_variables', variables)
        colors_changed = [self.theme_color_brand != colors['o-brand-odoo'], self.theme_color_primary != colors['o-brand-primary'], self.theme_color_menu != colors['as-menu-color'], self.theme_color_appbar_color != colors['as-appbar-color'],
                          self.theme_color_appbar_background != colors['as-appbar-background']]
        if (any(colors_changed)):
            variables = [{'name': 'o-brand-odoo', 'value': self.theme_color_brand or "#243742"},
                         {'name': 'o-brand-primary', 'value': self.theme_color_primary or "#5D8DA8"},
                         {'name': 'as-menu-color', 'value': self.theme_color_menu or "#f8f9fa"},
                         {'name': 'as-appbar-color', 'value': self.theme_color_appbar_color or "#dee2e6"},
                         {'name': 'as-appbar-background', 'value': self.theme_color_appbar_background or "#000000"},
                         ]
            self.env['web_editor.assets'].replace_theme_variables_values('/addis_systems_base/static/src/colors.scss', 'web._assets_primary_variables', variables)
        return res

    @api.model
    def get_values(self):
        res = super(AddisSystemsThemeResConfigSettings, self).get_values()
        variables = ['o-brand-odoo', 'o-brand-primary', 'as-menu-color', 'as-appbar-color', 'as-appbar-background', ]
        colors = self.env['web_editor.assets'].get_theme_variables_values('/addis_systems_base/static/src/colors.scss', 'web._assets_primary_variables', variables)
        res.update({'theme_color_brand': colors['o-brand-odoo'],
                    'theme_color_primary': colors['o-brand-primary'],
                    'theme_color_menu': colors['as-menu-color'],
                    'theme_color_appbar_color': colors['as-appbar-color'],
                    'theme_color_appbar_background': colors['as-appbar-background'],
                    })
        return res


class ResUsers(models.Model):
    _inherit = 'res.users'

    @property
    def SELF_READABLE_FIELDS(self):
        return super().SELF_READABLE_FIELDS + ['sidebar_type', ]

    @property
    def SELF_WRITEABLE_FIELDS(self):
        return super().SELF_WRITEABLE_FIELDS + ['sidebar_type', ]

    sidebar_type = fields.Selection(selection=[('invisible', 'Invisible'), ('small', 'Small'), ('large', 'Large')], string="Sidebar Type", default='large', required=True)
