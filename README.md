# iS Pricelist Visibility

## Overview

This module allows you to configure which pricelists should be visible in product views across all companies. When enabled, pricelist prices appear as additional columns in product list views and as styled price cards in product form views.

## Features

- **Pricelist Configuration**: Toggle "Allowed this Pricelist in Product Tree view" on each pricelist
- **Cross-Company Visibility**: Enabled pricelists are visible from any company — compare prices across the organization
- **Display Alias**: Optional short name per pricelist for compact display in product views
- **Dynamic Columns**: Pricelist prices automatically appear as optional columns in product tree views
- **Form View Display**: Pricelist prices shown as styled cards (price first, name below) after the product details section
- **Automatic Calculation**: Prices are calculated using Odoo's standard pricelist rules

## Configuration

1. Go to Sales → Configuration → Pricelists
2. Open a pricelist you want to show in product views
3. Enable the toggle "Allowed this Pricelist in Product Tree view"
4. Optionally set a **Display Alias** (short name) for compact display
5. Save the pricelist

## Usage

### Product List Views

When viewing product templates or variants in list view:
- Enabled pricelists appear as additional columns after the standard price field
- Columns are optional and can be hidden/shown using the column selector
- Column headers use the alias if set, otherwise the full pricelist name

### Product Form Views

When viewing a product in form view:
- Pricelist prices appear as cards below the product details section
- Each card shows the price (normal font) with the pricelist name below (smaller font)
- Cards only appear if there are visible pricelists configured

## Technical Details

- **Module Name**: is_pricelist_visibility
- **Version**: 17.0.1.0.4
- **Depends**: product, sale
- **Odoo Version**: 17.0

### Key Models Extended

- `product.pricelist`: Added `show_in_product_views` (Boolean) and `display_alias` (Char) fields
- `product.template`: Dynamic tree columns via `_get_view()`, price data via `web_search_read()`/`web_read()`
- `product.product`: Same dynamic column and price injection approach

### Dynamic Field Generation

The module dynamically creates fields named `pricelist_price_{id}` for each visible pricelist, injected into tree views via `_get_view()` override. Field metadata is registered via `fields_get()`. Price values are provided through `web_search_read()` and `web_read()` overrides.

## Cross-Company Support

The `show_in_product_views` toggle is global:
- Enabling it on any pricelist makes it visible to all users in all companies
- Users can compare prices across different company pricelists from a single view
- Each pricelist displays its own currency

## Author

Independent Solutions

## License

LGPL-3
