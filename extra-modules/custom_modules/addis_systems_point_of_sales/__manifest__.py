{
    'name': 'Addis Systems Point of Sales',
    'version': '16.0.1.0',
    'sequence': 1,
    'summary': 'Addis Systems Point of Sales',
    'description': """
        This is Addis Systems Point of Sales Module for shops and restaurants.
            ========================================
    """,
    'category': 'Addis Systems/Point of Sale',
    'author': 'Addis Systems/Beruk W.',
    'website': 'https://www.addissystems.et/',
    'license': 'LGPL-3',
    'depends': ['base', 'web', 'addis_systems_base', 'point_of_sale', 'addis_systems_invoice_exchange'],
    'external_dependencies': {
        'python': []
    },
    'data': [
        'views/point_of_sales_config_inherited.xml',
        'views/point_of_sales_index_inherited.xml'
    ],
    'assets': {
        'point_of_sale.assets': [
            # XML for point of sale
            'addis_systems_point_of_sales/static/src/xml/screens/clear_button.xml',
            'addis_systems_point_of_sales/static/src/xml/screens/clear_order_line.xml',
            'addis_systems_point_of_sales/static/src/xml/screens/invoice_button.xml',
            'addis_systems_point_of_sales/static/src/xml/screens/addis_systems_branding.xml',
            'addis_systems_point_of_sales/static/src/xml/screens/product_screen.xml',
            'addis_systems_point_of_sales/static/src/xml/screens/customer_view.xml',
            'addis_systems_point_of_sales/static/src/xml/screens/remove_unneeded_buttons.xml',
            'addis_systems_point_of_sales/static/src/xml/receipt/pos_receipt.xml',
            # Javascript for point of sale
            'addis_systems_point_of_sales/static/src/js/screens/clear_button.js',
            'addis_systems_point_of_sales/static/src/js/screens/clear_order_line.js',
            'addis_systems_point_of_sales/static/src/js/screens/auto_invoice.js',
            'addis_systems_point_of_sales/static/src/js/models.js',
            'addis_systems_point_of_sales/static/src/js/screens/default_customer.js',
            # scss for point of sale
            ('after', 'point_of_sale/static/src/scss/pos.scss', 'addis_systems_point_of_sales/static/src/scss/point_of_sales.scss'),
            ('after', 'point_of_sale/static/src/scss/pos_variables_extra.scss', 'addis_systems_point_of_sales/static/src/scss/point_of_sales_variables.scss'),
        ],
        'web._assets_primary_variables': [],
        'web.assets_backend': [

        ],
        'web.assets_frontend': [],
        'web.assets_tests': [],
        'web.qunit_suite_tests': [],
        'web.assets_qweb': [],
    },
    'demo': [],
    'installable': True,
    'price': 49.99,
    'currency': 'ETB',
    'application': True,
    'auto_install': False
}
