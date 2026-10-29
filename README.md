# Odoo 19 – Warranty Management & Vendor RMA

## Overview

This project is a custom Odoo 19 module designed to manage product warranties, customer warranty claims, vendor Return Merchandise Authorization (RMA), and product replacement workflows.

The module connects warranty management with inventory operations, sales deliveries, purchase orders, and vendor warranty coverage to support a structured after-sales service process.

## Key Features

- **Automatic Warranty Creation:** Creates warranty records based on product deliveries and serial/lot tracking.
- **Serial Number Tracking:** Links warranty records to specific products and serial numbers.
- **Warranty Configuration:** Supports customer warranty duration and vendor warranty duration in months.
- **Warranty Claims:** Allows customer warranty claims to be created, reviewed, accepted, and processed.
- **Vendor RMA Management:** Creates vendor return requests linked to the relevant warranty, vendor, and purchase information.
- **Vendor Warranty Coverage:** Calculates vendor warranty expiration based on the receipt date and configured warranty duration.
- **Warranty Expiration Warning:** Identifies expired or unknown vendor warranty coverage.
- **Inventory Integration:** Supports returning products to vendors and receiving replacement products through inventory transfers.
- **Replacement Workflow:** Tracks replacement receipts and supports completion of the vendor RMA process.
- **Workflow Validation:** Applies business rules to control RMA operations and prevent invalid actions.

## Business Workflow

The module supports the following workflow:

1. Configure the product's warranty duration and vendor warranty duration.
2. Receive the product from the vendor and assign a serial number.
3. Sell and deliver the product to the customer.
4. Automatically create a warranty record linked to the product, serial number, and customer.
5. Create and review a warranty claim.
6. Accept the claim and initiate a Vendor RMA.
7. Check vendor warranty coverage and expiration.
8. Return the defective product to the vendor.
9. Receive a replacement product when replacement is the selected resolution.
10. Complete the RMA workflow and track the final status.

## Odoo Integration
The module is designed for Odoo 19 and integrates with standard Odoo business operations, including:
Inventory Management
Sales Management
Purchase Management
Product and Serial Number Tracking
Warranty Claims and Vendor RMA Processing

## Technical Details
ERP: Odoo 19
Language: Python
Frontend: XML Views and Odoo interface components
Database: PostgreSQL
Architecture: Custom Odoo module using models, fields, business methods, views, and inventory operations

## Installation
Clone or download this repository.
Copy the module directory into your Odoo custom addons directory.
Ensure the custom addons directory is included in your Odoo configuration.
Restart the Odoo server.
Open Odoo and activate Developer Mode.
Update the Apps List.
Search for the module and install it.
Alternatively, upgrade an installed module using the Odoo command line:
python odoo-bin -c odoo.conf -d your_database -u your_module_name
Replace your_database and your_module_name with the appropriate values for your environment.

## Testing
The workflow should be tested in a development database using sample products, vendors, customers, purchase orders, and sales orders.
Recommended test scenarios include:
Automatic warranty creation after product delivery.
Correct serial number and customer association.
Warranty claim review and acceptance.
Vendor RMA creation and linking.
Vendor warranty coverage and expiration checks.
Vendor return transfer validation.
Replacement receipt and serial number assignment.
RMA resolution and cancellation rules.

## Project Goals
This project demonstrates practical Odoo 19 development skills, including:
Custom module development.
Business workflow automation.
Integration with standard Odoo applications.
Inventory transfer management.
Serial number traceability.
Business rule validation.
After-sales warranty and vendor return processes.

## License
Add the license applicable to this project and ensure that it is consistent with the module's manifest and any third-party dependencies.

## Author
Ibrahem Issa

GitHub: IbrahemIsbieh/Odoo-Warranty-Vendor-RMA
