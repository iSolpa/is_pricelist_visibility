from odoo import models, fields, api
import json


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    pricelist_prices_info = fields.Text(
        string='Pricelist Prices Info',
        compute='_compute_pricelist_prices',
        help='JSON data with visible pricelist prices'
    )
    
    pricelist_prices_display = fields.Html(
        string='Other Pricelists',
        compute='_compute_pricelist_prices',
        help='Display pricelist prices in form view'
    )

    @api.depends('list_price')
    def _compute_pricelist_prices(self):
        """Compute pricelist prices for visible pricelists"""
        PricelistObj = self.env['product.pricelist']
        visible_pricelists = PricelistObj.get_visible_pricelists()
        
        for product in self:
            prices_data = []
            html_parts = []
            
            for pricelist in visible_pricelists:
                price = pricelist._get_product_price(
                    product=product.product_variant_id,
                    quantity=1.0,
                    currency=pricelist.currency_id,
                )
                
                prices_data.append({
                    'pricelist_id': pricelist.id,
                    'pricelist_name': pricelist.name,
                    'price': price,
                    'currency_symbol': pricelist.currency_id.symbol,
                })
                
                # Build HTML display for form view
                html_parts.append(
                    f'<span class="badge bg-info me-1">'
                    f'{pricelist.name}: {pricelist.currency_id.symbol}{price:.2f}'
                    f'</span>'
                )
            
            product.pricelist_prices_info = json.dumps(prices_data)
            product.pricelist_prices_display = ' '.join(html_parts) if html_parts else ''

    def get_pricelist_price(self, pricelist_id):
        """Get price for a specific pricelist"""
        self.ensure_one()
        pricelist = self.env['product.pricelist'].browse(pricelist_id)
        if not pricelist.exists():
            return 0.0
        
        price = pricelist._get_product_price(
            product=self.product_variant_id,
            quantity=1.0,
            currency=pricelist.currency_id,
        )
        return price

    @api.model
    def _get_view(self, view_id=None, view_type='form', **options):
        """Dynamically add pricelist price fields to tree views"""
        arch, view = super()._get_view(view_id, view_type, **options)
        if view_type in ('tree', 'list'):
            self._add_pricelist_columns_to_tree(arch)
        return arch, view

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        """Include dynamic pricelist fields in field definitions"""
        res = super().fields_get(allfields, attributes)
        visible_pricelists = self.env['product.pricelist'].get_visible_pricelists()
        for pricelist in visible_pricelists:
            field_name = f'pricelist_price_{pricelist.id}'
            if allfields and field_name not in allfields:
                continue
            res[field_name] = {
                'type': 'float',
                'string': pricelist.name,
                'readonly': True,
                'searchable': False,
                'sortable': False,
            }
        return res

    def _add_pricelist_columns_to_tree(self, arch):
        """Add pricelist price columns dynamically to tree view"""
        from lxml import etree

        visible_pricelists = self.env['product.pricelist'].get_visible_pricelists()
        if not visible_pricelists:
            return

        # Find the list_price field or last field in tree
        list_price_field = arch.xpath("//field[@name='list_price']")

        if list_price_field:
            insert_after = list_price_field[0]
        else:
            fields = arch.xpath("//field")
            if fields:
                insert_after = fields[-1]
            else:
                return

        # Add pricelist columns
        for pricelist in visible_pricelists:
            field_name = f'pricelist_price_{pricelist.id}'
            pricelist_field = etree.Element('field', {
                'name': field_name,
                'string': pricelist.name,
                'optional': 'show',
            })
            insert_after.addnext(pricelist_field)
            insert_after = pricelist_field

    def read(self, fields=None, load='_classic_read'):
        """Override read to add dynamic pricelist price fields"""
        # Check if we're reading pricelist price fields
        if fields:
            pricelist_fields = [f for f in fields if f.startswith('pricelist_price_')]
            if pricelist_fields:
                # Read normally first
                result = super().read(fields=[f for f in fields if f not in pricelist_fields], load=load)
                
                # Add pricelist prices
                for record in result:
                    product = self.browse(record['id'])
                    for pfield in pricelist_fields:
                        # Extract pricelist_id from field name
                        pricelist_id = int(pfield.replace('pricelist_price_', ''))
                        price = product.get_pricelist_price(pricelist_id)
                        record[pfield] = price
                
                return result
        
        return super().read(fields=fields, load=load)
