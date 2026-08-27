import { AccountMoveFormController } from "@account/components/account_move_form/account_move_form";
import { patch } from "@web/core/utils/patch";

patch(AccountMoveFormController.prototype, {
    /**
     * We clear the native `required` of the document number so drafts can be saved without it, which leaves
     * the constraint as the only guard on confirm: a modal that does not point at the field. Here we require
     * it on confirm instead, marking the field invalid and aborting the post.
     */
    async beforeExecuteActionButton(clickParams) {
        const record = this.model.root;
        if (
            clickParams.name === "action_post" &&
            record.data.l10n_latam_use_documents &&
            record.data.l10n_latam_manual_document_number &&
            !record.data.l10n_latam_document_number
        ) {
            await record.setInvalidField("l10n_latam_document_number");
            return false;
        }
        return super.beforeExecuteActionButton(...arguments);
    },
});
