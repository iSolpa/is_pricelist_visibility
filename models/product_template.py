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

    pricelist_prices_compact = fields.Char(
        string='Pricelist Prices',
        compute='_compute_pricelist_prices',
        help='Compact pricelist prices for kanban view'
    )

    @api.depends('list_price')
    def _compute_pricelist_prices(self):
        """Compute pricelist prices for visible pricelists"""
        PricelistObj = self.env['product.pricelist']
        visible_pricelists = PricelistObj.get_visible_pricelists()
        
        for product in self:
            prices_data = []
            html_parts = []
            compact_parts = []
            
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
                display_name = pricelist.display_alias or pricelist.name
                html_parts.append(
                    f'<span class="d-inline-block text-center me-2 mb-1 px-2 py-1" '
                    f'style="background-color: #f0f0f0; border: 1px solid #ccc; border-radius: 4px;">'
                    f'<span style="font-size: 1em; font-weight: 500; color: #333;">'
                    f'{pricelist.currency_id.symbol}{price:.2f}</span><br/>'
                    f'<span style="font-size: 0.75em; color: #666;">'
                    f'{display_name}</span></span>'
                )
                compact_parts.append(
                    f'{pricelist.currency_id.symbol}{price:.2f} {display_name}'
                )
            
            product.pricelist_prices_info = json.dumps(prices_data)
            product.pricelist_prices_display = ' '.join(html_parts) if html_parts else ''
            product.pricelist_prices_compact = ' | '.join(compact_parts) if compact_parts else ''

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
            # Add price field
            price_field_name = f'pricelist_price_{pricelist.id}'
            if allfields and price_field_name not in allfields:
                continue
            res[price_field_name] = {
                'type': 'float',
                'string': pricelist.display_alias or pricelist.name,
                'readonly': True,
                'searchable': False,
                'sortable': False,
                'widget': 'monetary',
                'options': {'currency_field': f'currency_id_{pricelist.id}', 'field_digits': True},
            }
            # Add currency field
            currency_field_name = f'currency_id_{pricelist.id}'
            if allfields and currency_field_name not in allfields:
                continue
            res[currency_field_name] = {
                'type': 'many2one',
                'string': 'Currency',
                'relation': 'res.currency',
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
            col_label = pricelist.display_alias or pricelist.name
            pricelist_field = etree.Element('field', {
                'name': field_name,
                'string': col_label,
                'optional': 'show',
                'widget': 'monetary',
                'options': f"{{'currency_field': 'currency_id_{pricelist.id}', 'field_digits': True}}",
            })
            insert_after.addnext(pricelist_field)
            insert_after = pricelist_field

    @api.model
    def web_search_read(self, domain, specification, offset=0, limit=None, order=None, count_limit=None):
        """Handle dynamic pricelist fields in search read"""
        pricelist_specs = {}
        currency_specs = {}
        clean_spec = dict(specification)
        for key in list(clean_spec):
            if key.startswith('pricelist_price_'):
                pricelist_specs[key] = clean_spec.pop(key)
            elif key.startswith('currency_id_'):
                currency_specs[key] = clean_spec.pop(key)

        result = super().web_search_read(domain, clean_spec, offset=offset, limit=limit, order=order, count_limit=count_limit)

        if pricelist_specs and result.get('records'):
            record_ids = [r['id'] for r in result['records']]
            records = self.browse(record_ids)
            for i, record in enumerate(records):
                for field_name in pricelist_specs:
                    pricelist_id = int(field_name.replace('pricelist_price_', ''))
                    price = record.get_pricelist_price(pricelist_id)
                    result['records'][i][field_name] = price
                    
                    # Always set the currency field for monetary widget
                    currency_field_name = f'currency_id_{pricelist_id}'
                    pricelist = self.env['product.pricelist'].browse(pricelist_id)
                    result['records'][i][currency_field_name] = pricelist.currency_id.id

        return result

    def web_read(self, specification):
        """Handle dynamic pricelist fields in web read"""
        pricelist_specs = {}
        currency_specs = {}
        clean_spec = dict(specification)
        for key in list(clean_spec):
            if key.startswith('pricelist_price_'):
                pricelist_specs[key] = clean_spec.pop(key)
            elif key.startswith('currency_id_'):
                currency_specs[key] = clean_spec.pop(key)

        result = super().web_read(clean_spec)

        if pricelist_specs:
            for record_data in result:
                record = self.browse(record_data['id'])
                for field_name in pricelist_specs:
                    pricelist_id = int(field_name.replace('pricelist_price_', ''))
                    price = record.get_pricelist_price(pricelist_id)
                    record_data[field_name] = price
                    
                    # Always set the currency field for monetary widget
                    currency_field_name = f'currency_id_{pricelist_id}'
                    pricelist = self.env['product.pricelist'].browse(pricelist_id)
                    record_data[currency_field_name] = pricelist.currency_id.id

        return result
