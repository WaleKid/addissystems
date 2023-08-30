# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Payment Provider: Addis Pay',
    'version': '2.0',
    'category': 'Accounting/Payment Providers',
    'sequence': 350,
    'summary': "A Ethiopia payment provider.",
    'depends': ['payment'],
    'data': [
        'views//AddisSystemsTemplate.xml',
        'views/AddisPayProviderFormView.xml',
        'views/AddisSystemsPaymentTemplates.xml',
        'data/AddisSystemsPaymentProviderData.xml',
    ],
    'application': False,
    # 'post_init_hook': 'post_init_hook',
    # 'uninstall_hook': 'uninstall_hook',
    'assets': {
        'web.assets_frontend': [
            'payment_adyen/static/src/js/AddisPayPaymentForm.js',
        ],
    },
    'license': 'LGPL-3',
}
