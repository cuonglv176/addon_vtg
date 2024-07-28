odoo.define('vtg_pos_crm.GuestCameButton', function(require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const { useListener } = require('web.custom_hooks');
    const Registries = require('point_of_sale.Registries');

    class GuestCameButton extends PosComponent {
        constructor() {
            super(...arguments);
            useListener('click', this.onClick);
        }
        get isShowButton() {
            return !this.currentOrder.updatedBooking;
        }
        get currentOrder() {
            return this.env.pos.get_order();
        }
        get currentBooking() {
            return this.currentOrder.booking;
        }
        async onClick() {
            console.log('GuestCameButton - this: ', this);
            var currenOrder = this.currentOrder
            if (!currenOrder){
                return
            }
            this.rpc({
                model: 'crm.lead.booking',
                method: 'action_confirm_booking',
                args: [this.currentBooking.id],
            }).then(function (result) {
                currenOrder.updatedBooking = true;
            });
            currenOrder.trigger('change');
        }
    }
    GuestCameButton.template = 'GuestCameButton';

    ProductScreen.addControlButton({
        component: GuestCameButton,
        condition: function() {
            return this.env.pos.get_order().get_booking();
        },
    });

    Registries.Component.add(GuestCameButton);

    return GuestCameButton;
});
