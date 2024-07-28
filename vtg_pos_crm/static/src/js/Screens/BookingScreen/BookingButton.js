odoo.define('vtg_pos_crm.BookingButton', function (require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');
    const ProductScreen = require('point_of_sale.ProductScreen');

    class BookingButton extends PosComponent {

        get currentOrder() {
            return this.env.pos.get_order();
        }

        get booking() {
            this.currentOrder.get_booking();
        }

        syncBooking() {
            var self = this;
            this.rpc({
                model: 'crm.lead.booking',
                method: 'search_read',
                domain: [
                    ['state', '=', 'confirm'],
                ],
            }).then(function (result) {
                self.env.pos.db.addDataStore('bookings', result);
            });
        }

        async onClick() {
            const currentBooking = this.booking;
            const currentPartner = this.currentOrder.get_client();

            this.syncBooking()

            const {confirmed, payload: newBooking} = await this.showTempScreen(
                'BookingListScreen',
                {booking: currentBooking, partner: currentPartner}
            );
            if (confirmed) {
                console.log('confirmed Booking', confirmed);
                this.currentOrder.set_booking(newBooking);
                this.currentOrder.updatedBooking = false;
                if (!this.currentOrder.get_client()) {
                    let order_partner = this.env.pos.db.get_partner_by_id(newBooking.partner_id[0])
                    if(order_partner){
                        this.currentOrder.set_client(order_partner);
                    }

                }
            }
        }
    }

    BookingButton.template = 'BookingButton';

    ProductScreen.addControlButton({
        component: BookingButton,
        condition: function () {
            return true;
        },
    });

    Registries.Component.add(BookingButton);

    return BookingButton;
});
