{
    'name': 'Addis Systems Catalogue & SO/PO Order Exchange',
    'version': '1.0',
    'sequence': 1,
    'summary': 'Addis Systems Catalogue & SO/PO Order Exchange',
    'description': """
        This is Addis Systems Catalogue & Sales Order/Purchase Order Exchange.
            ========================================
    """,
    'category': 'Addis Systems/Sales',
    'author': 'Addis Systems/Beruk W.',
    'website': 'https://www.addissystems.et/',
    'license': 'LGPL-3',
    'depends': ['base', 'web', 'addis_systems_base', 'contacts', 'stock', 'sale_management', 'purchase'],
    'external_dependencies': {
        'python': ['pulsar-client', 'avro', 'avro-schema']
    },
    'data': [
        'security/ir.model.access.csv',
        'views/PurchaseOrderInheritedView.xml',
        'views/SalesOrderInheritedView.xml',
        'views/CatalogueView.xml',
        'views/RequestForCatalogueView.xml',
        'views/CatalogueRequestView.xml',
        'views/CatalogueQuotationsView.xml',
        'views/CatalogueProductsView.xml',
        'data/CatalogueSequenceData.xml',
        'wizards/CatalogueQuotationCreateWizardView.xml'
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
    'pre_init_hook': '_pre_init_hook',
    'installable': True,
    'price': 49.99,
    'currency': 'ETB',
    'application': True,
    'auto_install': False
}
