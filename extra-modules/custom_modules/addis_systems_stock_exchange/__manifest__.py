{
    'name': 'Addis Systems Inventory Exchange',
    'version': '16.0.1.0',
    'sequence': 1,
    'summary': 'Addis Systems Inventory Exchange',
    'description': """
        This is Addis Systems Inventory Exchange Module.
            ========================================
    """,
    'category': 'Addis Systems/Inventory',
    'author': 'Addis Systems/Beruk W.',
    'website': 'https://www.addissystems.et/',
    'license': 'LGPL-3',
    'depends': ['base', 'web', 'addis_systems_base', 'contacts', 'stock', 'addis_systems_catalogue_and_order_exchange'],
    'external_dependencies': {
        'python': ['pulsar-client', 'avro', 'avro-schema']
    },
    'data': [
        'data/AddisSystemsDispatchSequenceData.xml',
        'views/AddisSystemsStockPicking.xml'
    ],
    'assets': {
        'web._assets_primary_variables': [],
        'web.assets_backend': [],
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
