odoo.define('pos_delete_orderline.DeleteOrderLines', function(require) {
    'use strict';
        const Registries = require('point_of_sale.Registries');
        const Orderline = require('point_of_sale.Orderline');
        const OrderWidget = require('point_of_sale.OrderWidget');

        const OrderLineDelete = (Orderline) =>
           class extends Orderline {
           async clear_button_fun() {
                       this.trigger('numpad-click-input', { key: 'Backspace' });
                       this.trigger('numpad-click-input', { key: 'Backspace' });
            }
            };
        Registries.Component.extend(Orderline, OrderLineDelete);
        return OrderWidget;

    });

