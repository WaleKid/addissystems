{
    'name': 'Addis Systems Invoice Exchange',
    'version': '16.0.1.0',
    'sequence': 1,
    'summary': 'Addis Systems Invoice Exchange',
    'description': """
        This is Addis Systems Invoice Exchange Module.
            ========================================
    """,
    'category': 'Addis Systems/Accounting',
    'author': 'Addis Systems/Beruk W.',
    'website': 'https://www.addissystems.et/',
    'license': 'LGPL-3',
    'depends': ['base', 'web', 'addis_systems_base', 'contacts', 'om_account_accountant', 'sale_management', 'purchase', 'point_of_sale'],
    'external_dependencies': {
        'python': ['pulsar-client', 'avro', 'avro-schema']
    },
    'data': [
        'views/InvoiceAndVendorFormInherited.xml',
        'reports/AddisSystemInvoiceReportInherit.xml',
        'views/AddisSystemsTemplate.xml',
        'views/AddisSystemsPaymentGateways.xml'
    ],
    'assets': {
        'web._assets_primary_variables': [],
        'web.assets_backend': [],
        'web.assets_frontend': [],
        'web.assets_tests': [],
        'web.qunit_suite_tests': [],
        'web.assets_qweb': [

        ],
    },
    'demo': [],
    'installable': True,
    'price': 49.99,
    'currency': 'ETB',
    'application': True,
    'auto_install': False
}
