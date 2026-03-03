# Account Invoice Move Currency

This module extends Odoo's accounting functionality to enable dual-currency tracking on invoices. It allows storing invoice values in a secondary currency alongside the primary invoice currency, providing better visibility for businesses operating in multi-currency environments.

## Features

- **Secondary Currency Tracking**: Add a secondary currency to invoices to track values in an additional currency
- **Custom Exchange Rates**: Define specific exchange rates for the secondary currency independently from the primary currency
- **Real-time Rate Calculation**: Automatically calculate exchange rates based on company currency and selected secondary currency
- **Currency Change Integration**: Optionally save the original currency as secondary when changing invoice currency
- **Multi-currency Validation**: Prevent conflicts between primary and secondary currencies with built-in validation rules
- **Reporting Support**: Display secondary currency values on invoice reports

## Configuration

### Prerequisites

- Ensure currency rates are configured under Accounting > Configuration > Currencies

### Installation

1. Install the module from the Apps menu
2. The module will automatically extend invoice forms with secondary currency fields

## Usage

### Adding a Secondary Currency to an Invoice

1. Navigate to Accounting > Customers > Invoices (or Vendors > Bills)
2. Open a draft invoice
3. In the invoice form, locate the **Secondary Currency** field (visible only with multi-currency enabled)
4. Select a secondary currency from the dropdown
5. The **Account Move Secondary Currency Rate** will be automatically calculated
6. You can manually adjust the rate if needed
7. Save the invoice

### Important Constraints

- **Same Currency Restriction**: The secondary currency cannot be the same as the invoice currency
- **Company Currency Requirement**: Secondary currency can only be used when the invoice currency matches the company currency
- If these conditions are not met, the system will display a validation error

### Changing Invoice Currency

When using the "Change Currency" wizard:

1. Open a draft invoice
2. Use the currency change wizard (available from `account_ux` module)
3. Select the new currency
4. Check the **Save in secondary currency?** option if you want to preserve the original currency as the secondary currency
5. When changing to the company currency, this option allows tracking the original currency values
6. Confirm the change

### Example Use Case

**Scenario**: A company operates in USD but wants to track invoice values in EUR for reporting purposes.

1. Create an invoice with currency = USD (company currency)
2. Set Secondary Currency = EUR
3. The system calculates the EUR rate automatically (or enter manually)
4. The invoice values are now tracked in both USD (primary) and EUR (secondary)
5. The secondary currency information is available for reporting and analysis

## Technical Details

### Dependencies

- `account_ux`: Provides extended accounting functionality and the currency change wizard

### Models Extended

#### account.move

**New Fields:**
- `move_currency_id`: Many2one field to store the secondary currency
- `move_inverse_currency_rate`: Float field (16,4 digits) to store the exchange rate

**Methods:**
- `change_move_currency()`: Onchange method that calculates the exchange rate when secondary currency is selected
- `check_move_currency()`: Constraint method that validates currency selection rules

#### account.change.currency (TransientModel)

**New Fields:**
- `save_secondary_currency`: Boolean field to enable saving original currency as secondary
- `same_currency`: Computed field to determine if target currency matches company currency
- `currency_company_id`: Related field for company currency

**Methods:**
- `_compute_same_currency()`: Computes whether the target currency is the company currency
- `change_currency()`: Extended to handle secondary currency preservation logic

### Views

- **Invoice Form View**: Adds secondary currency fields to the invoice header (visible only for invoices/bills in multi-currency setups)
- **Change Currency Wizard**: Adds checkbox to save original currency as secondary
- **Invoice Report**: Shows secondary currency information on printed invoices

### Security

No additional security groups or access rights are required beyond standard Odoo accounting permissions.

## Known Issues / Limitations

- Secondary currency is only available when the invoice currency is the same as the company currency
- The secondary currency and invoice currency cannot be the same
- Exchange rate modifications are only allowed in draft state

## Bug Tracker

Bugs are tracked on [GitHub Issues](https://github.com/ingadhoc/account-invoicing/issues). In case of trouble, please check there if your issue has already been reported.

## Credits

### Authors

* ADHOC SA

### Contributors

* ADHOC SA <info@adhoc.com.ar>

### Maintainers

This module is maintained by ADHOC SA.

To learn more about ADHOC SA, visit [www.adhoc.com.ar](http://www.adhoc.com.ar).

## License

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.
