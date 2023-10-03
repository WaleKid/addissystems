/** @odoo-module **/

import { patch } from '@web/core/utils/patch';

import { NavBar } from '@web/webclient/navbar/navbar';
import { AppsMenu } from "@addis_systems_theme/webclient/appsmenu/appsmenu";
import { AppsSearch } from "@addis_systems_theme/webclient/appssearch/appssearch";
import { AppsBar } from '@addis_systems_theme/webclient/appsbar/appsbar';

patch(NavBar.prototype, 'addis_systems_theme.NavBar', {
	getAppsMenuItems(apps) {
		return apps.map((menu) => {
			const appsMenuItem = {
				id: menu.id,
				name: menu.name,
				xmlid: menu.xmlid,
				appID: menu.appID,
				actionID: menu.actionID,
				href: this.getMenuItemHref(menu),
				action: () => this.menuService.selectMenu(menu),
			};
		    if (menu.webIconData) {
		        const prefix = (
		        	menu.webIconData.startsWith('P') ? 
	    			'data:image/svg+xml;base64,' : 
					'data:image/png;base64,'
	            );
		        appsMenuItem.webIconData = (
	    			menu.webIconData.startsWith('data:image') ? 
					menu.webIconData : 
					prefix + menu.webIconData.replace(/\s/g, '')
	            );
		    }
			return appsMenuItem;
		});
    },
});

patch(NavBar, 'addis_systems_theme.NavBar', {
    components: {
        ...NavBar.components,
        AppsMenu,
        AppsSearch,
        AppsBar,
    },
});
