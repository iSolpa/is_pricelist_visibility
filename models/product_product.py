from odoo import models, fields, api
import json


class ProductProduct(models.Model):
    _inherit = 'product.product'

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

    @api.depends('lst_price')
    def _compute_pricelist_prices(self):
        """Compute pricelist prices for visible pricelists"""
        PricelistObj = self.env['product.pricelist']
        visible_pricelists = PricelistObj.get_visible_pricelists()
        
        for product in self:
            prices_data = []
            html_parts = []
            
            for pricelist in visible_pricelists:
                price = pricelist._get_product_price(
                    product=product,
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
            product=self,
            quantity=1.0,
            currency=pricelist.currency_id,
        )
        return price

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        """Dynamically add pricelist price fields to tree views"""
        result = super().fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        
        if view_type == 'tree':
            result = self._add_pricelist_columns_to_tree(result)
        
        return result

    def _add_pricelist_columns_to_tree(self, result):
        """Add pricelist price columns dynamically to tree view"""
        from lxml import etree
        
        visible_pricelists = self.env['product.pricelist'].get_visible_pricelists()
        if not visible_pricelists:
            return result
        
        doc = etree.XML(result['arch'])
        
        # Find the lst_price field or last field in tree
        price_field = doc.xpath("//field[@name='lst_price']")
        
        if not price_field:
            price_field = doc.xpath("//field[@name='list_price']")
        
        if price_field:
            insert_after = price_field[0]
        else:
            # Insert after last field
            fields = doc.xpath("//field")
            if fields:
                insert_after = fields[-1]
            else:
                return result
        
        # Add pricelist columns
        for pricelist in visible_pricelists:
            field_name = f'pricelist_price_{pricelist.id}'
            
            # Add field to fields dict
            result['fields'][field_name] = {
                'type': 'char',
                'string': f'{pricelist.name}',
                'readonly': True,
            }
            
            # Create field element
            pricelist_field = etree.Element('field', {
                'name': field_name,
                'string': pricelist.name,
                'widget': 'monetary',
                'options': "{'currency_field': 'currency_id'}",
                'optional': 'show',
            })
            
            # Insert after price field
            insert_after.addnext(pricelist_field)
            insert_after = pricelist_field
        
        result['arch'] = etree.tostring(doc, encoding='unicode')
        return result

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
