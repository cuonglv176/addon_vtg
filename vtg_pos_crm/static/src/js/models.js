odoo.define('vtg_pos_crm.models', function (require) {
    "use strict"

    const models = require('point_of_sale.models');

    models.load_models([
        {
            model: 'crm.lead.booking',
            label: 'Booking',
            fields: ['name', 'partner_id', 'partner_name', 'partner_phone', 'partner_address', 'branch_id',
                'category_id', 'date', 'slot_time', 'detail_ids', 'booking_log_note_ids', 'weekday',
                'state', 'date_sent', 'user_id', 'date_start', 'date_end', 'status_customer', 'state_id',
                'arrival_date', 'type_customer'],
            domain: (self) => {
                return [['state', '=', 'confirm']];
            },
            loaded: (self, res) => {
                self.db.addDataStore('bookings', res);
            }
        },
        {
            model: 'crm.lead.booking.log.note',
            label: 'Booking Log Note',
            fields: ['booking_id', 'state', 'note', 'content', 'contact_form', 'result'],
            domain: (self) => {
                return [['booking_id', 'in', self.db.getDataStoreIds()]]
            },
            loaded: (self, res) => {
                self.db.addDataStore('booking_log', res);
            }
        },
        {
            model: 'crm.lead.booking.detail',
            label: 'Booking Detail',
            fields: ['booking_id', 'product_id', 'qty'],
            loaded: (self, res) => {
                self.db.addDataStore('booking_detail', res);
            }
        },
        {
            model: 'vtg.branch',
            label: 'Branch',
            fields: ['name'],
            loaded: (self, res) => {
                self.db.addDataStore('branches', res);
            }
        },
    ], {after: 'pos.session'});

    models.load_fields('pos.order', ['booking_id']);

    const Order = models.Order.prototype;
    models.Order = models.Order.extend({
        set_booking: function (booking) {
            this.booking = booking;
            this.trigger('change');
        },
        get_booking: function () {
            return this.booking;
        },
        initialize: function (attr, options) {
            Order.initialize.apply(this, arguments);
            this.booking = this.get_booking();
            this.updatedBooking = false;
            this.save_to_db();
        },
        export_as_JSON: function () {
            var json = Order.export_as_JSON.apply(this, arguments);
            json.booking = this.get_booking();
            json.updatedBooking = this.updatedBooking;
            return json;
        },
        init_from_JSON: function (json) {
            Order.init_from_JSON.apply(this, arguments);
            this.booking = json.booking;
            this.updatedBooking = json.updatedBooking;
        },
        export_for_printing: function () {
            var json = Order.export_for_printing.apply(this, arguments);
            json.booking = this.get_booking();
            json.updatedBooking = this.updatedBooking;
            return json;
        },
    });

    return models;

});
