/** @odoo-module **/

import { Component } from "@odoo/owl";

export class AppsBar extends Component {}

Object.assign(AppsBar, {
    template: 'addis_systems_base.AppsBar',
    props: {
    	apps: Array,
    },
});

