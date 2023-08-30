odoo.define('addis_systems_point_of_sales.default_customer', function(require){
    'use strict';
    const { PosGlobalState, Order} = require('point_of_sale.models');
    const Registries = require('point_of_sale.Registries');
    var core = require('web.core');
    var _t = core._t;

    const POSOderDefaultCustomer = (Order) => class POSOderDefaultCustomer extends Order {
        constructor(obj, options) {
            super(...arguments);
            if (this.pos.config.auto_customer_id) {
                var default_customer = this.pos.config.auto_customer_id[0];
                var partner = this.pos.db.get_partner_by_id(default_customer);

                this.set_partner(partner);
            }
        }
    }
    Registries.Model.extend(Order, POSOderDefaultCustomer);
});
