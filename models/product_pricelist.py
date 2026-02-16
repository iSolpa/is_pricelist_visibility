from odoo import models, fields, api


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    show_in_product_views = fields.Boolean(
        string='Allowed this Pricelist in Product Tree view',
        help='If enabled, this pricelist prices will be shown as columns in product list views and in product form views.',
        default=False,
    )

    @api.model
    def get_visible_pricelists(self):
        """Get all pricelists marked as visible, across all companies"""
        return self.search([
            ('show_in_product_views', '=', True),
        ])
