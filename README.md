# iS Pricelist Visibility

## Overview

This module allows you to configure which pricelists should be visible in product views. When enabled, pricelist prices will be shown as additional columns in product list views and as badges in product form views.

## Features

- **Pricelist Configuration**: Add a checkbox "Allowed this Pricelist in Product Tree view" to each pricelist
- **Company-Aware**: Configuration is company-dependent, allowing different companies to show different pricelists
- **Dynamic Columns**: Pricelist prices automatically appear as columns in product tree views
- **Form View Display**: Pricelist prices shown as colored badges below the main price in product form views
- **Automatic Calculation**: Prices are calculated using Odoo's standard pricelist rules

## Configuration

1. Go to Sales → Configuration → Pricelists
2. Open a pricelist you want to show in product views
3. Enable the checkbox "Allowed this Pricelist in Product Tree view"
4. Save the pricelist

## Usage

### Product List Views

When viewing product templates or variants in list view:
- Enabled pricelists will appear as additional columns after the standard price field
- Columns are optional and can be hidden/shown using the column selector
- Prices are displayed with the pricelist's currency

### Product Form Views

When viewing a product in form view:
- Enabled pricelist prices appear as colored badges below the main price
- Each badge shows: Pricelist Name: Currency Symbol + Price
- Badges only appear if there are visible pricelists configured

## Technical Details

- **Module Name**: abi_pricelist_visibility
- **Version**: 17.0.1.0.0
- **Depends**: product, sale
- **Odoo Version**: 17.0

### Key Models Extended

- `product.pricelist`: Added `show_in_product_views` field (company-dependent boolean)
- `product.template`: Added computed fields for pricelist prices and display
- `product.product`: Added computed fields for pricelist prices and display

### Dynamic Field Generation

The module dynamically creates fields named `pricelist_price_{id}` for each visible pricelist and injects them into tree views using `fields_view_get()` override.

## Multi-Company Support

The `show_in_product_views` field is company-dependent, meaning:
- Each company can configure its own set of visible pricelists
- Users only see pricelists configured for their current company
- Switching companies will show different pricelist columns

## Author

iSolpa

## License

LGPL-3
