/** @odoo-module **/

import { session } from "@web/session";
import { url } from "@web/core/utils/urls";
import { Dropdown } from "@web/core/dropdown/dropdown";

export class AppsMenu extends Dropdown {
    setup() {
    	super.setup();
    	if (this.env.services.company.currentCompany.has_background_image) {
            this.backgroundImageUrl = url('/web/image', {
                model: 'res.company',
                field: 'background_image',
                id: this.env.services.company.currentCompany.id,
            });
    	} else {
    		this.backgroundImageUrl = '';
    	}
    	this.env.bus.on("ACTION_MANAGER:UI-UPDATED", this, ev => this.close());
    }
}

Object.assign(AppsMenu, {
    template: 'addis_systems_base.AppsMenu',
});