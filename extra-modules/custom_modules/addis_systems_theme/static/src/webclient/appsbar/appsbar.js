/** @odoo-module **/

import { Component } from "@odoo/owl";

export class AppsBar extends Component {}

Object.assign(AppsBar, {
    template: 'addis_systems_theme.AppsBar',
    props: {
    	apps: Array,
    },
});

