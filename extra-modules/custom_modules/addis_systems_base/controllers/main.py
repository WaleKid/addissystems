from odoo.http import Controller, request, route
from werkzeug.utils import redirect

DEFAULT_IMAGE = 'addis_systems_base/static/src/img/login_page_bg.jpg'


class DashboardBackground(Controller):

    @route(['/dashboard'], type='http', auth="public")
    def dashboard(self, **post):
        user = request.env.user
        company = user.company_id
        return redirect(DEFAULT_IMAGE)
