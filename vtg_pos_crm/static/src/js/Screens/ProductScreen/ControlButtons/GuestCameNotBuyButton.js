odoo.define('vtg_pos_crm.GuestCameNotBuyButton', function (require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const {useListener} = require('web.custom_hooks');
    const Registries = require('point_of_sale.Registries');

    class GuestCameNotBuyButton extends PosComponent {
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
            console.log('GuestCameNotBuyButton - this: ', this);
            var currenOrder = this.currentOrder
            if (!currenOrder){
                return
            }
            this.rpc({
                model: 'crm.lead.booking',
                method: 'action_cancel_buy',
                args: [this.currentBooking.id],
            }).then(function (result) {
                currenOrder.updatedBooking = true;
            });
            this.render();
        }
    }

    GuestCameNotBuyButton.template = 'GuestCameNotBuyButton';

    ProductScreen.addControlButton({
        component: GuestCameNotBuyButton,
        condition: function () {
            return this.env.pos.get_order().get_booking();
        },
    });

    Registries.Component.add(GuestCameNotBuyButton);

    return GuestCameNotBuyButton;
});
