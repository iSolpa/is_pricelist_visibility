{
    'name': 'iS Pricelist Visibility',
    'version': '17.0.1.0.0',
    'category': 'Sales',
    'summary': 'Show configurable pricelist prices in product views',
    'description': """
        Pricelist Visibility in Product Views
        =====================================
        
        This module allows you to:
        - Configure which pricelists should be visible in product views
        - Show pricelist prices as columns in product list views
        - Display pricelist prices in product form views
        - Company-aware configuration
        - Tag-style display for grid views
    """,
    'author': 'Independent Solutions',
    'depends': ['product', 'sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_pricelist_views.xml',
        'views/product_template_views.xml',
        'views/product_product_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
