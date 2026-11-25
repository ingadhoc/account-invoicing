/** @odoo-module **/

import { registry } from "@web/core/registry";
import { user } from "@web/core/user";

/**
 * Thermal Receipt Print Helper
 * Opens thermal receipt in clean window for proper printing with auto-print dialog
 */

/**
 * Print thermal invoice by opening standalone report page
 * This avoids CSS conflicts from the backend DOM
 *
 * @param {string} reportName - Full report template name
 * @param {Array|number} invoiceIds - Invoice ID(s) to print
 */
export function printThermalReceipt(reportName, invoiceIds) {
    const ids = Array.isArray(invoiceIds) ? invoiceIds.join(',') : invoiceIds;
    // Forward the user context the same way the standard report action does
    // (see web/webclient/actions/reports/utils.js `getReportUrl`). The report
    // opens in a standalone window, so nothing else carries the active
    // companies: without `allowed_company_ids` the rendering environment falls
    // back to `res.users._get_company_ids()`, which does not expand branches,
    // and reading an invoice that belongs to a branch raises an AccessError.
    const context = encodeURIComponent(JSON.stringify(user.context));
    const reportUrl = `/report/html/${reportName}/${ids}?context=${context}`;

    // Open report in new tab/window
    const printWindow = window.open(reportUrl, '_blank');

    if (printWindow) {
        // Auto-trigger print dialog after page loads
        printWindow.addEventListener('load', function() {
            setTimeout(() => {
                printWindow.focus();
                printWindow.print();
            }, 500);
        });
    } else {
        console.error('Pop-up blocked. Please allow pop-ups for this site.');
    }
}

/**
 * Client Action Handler for thermal printing
 * Registered to handle 'thermal_print' action tag
 */
function thermalPrintAction(env, action) {
    const { report_name, invoice_id } = action.context;
    printThermalReceipt(report_name, invoice_id);
}

// Register the client action
registry.category("actions").add("thermal_print", thermalPrintAction);

// Make available globally for console testing
window.printThermalReceipt = printThermalReceipt;

export default {
    printThermalReceipt,
};
