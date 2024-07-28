odoo.define('point_of_sale.BookingListScreen', function (require) {
    'use strict';

    const Registries = require('point_of_sale.Registries');
    const IndependentToOrderScreen = require('point_of_sale.IndependentToOrderScreen');
    const {useListener, useAutofocus} = require('web.custom_hooks');


    class BookingListScreen extends IndependentToOrderScreen {
        constructor() {
            super(...arguments);
            useListener('click-booking', this._onClickBooking);
            useAutofocus({selector: '.search input'});
            this.state = {
                query: null,
                selectedBooking: this.props.booking,
                currentPartner: this.props.partner
            };
        }

        back() {
            this.props.resolve({confirmed: false, payload: false});
            this.trigger('close-temp-screen');
        }

        confirm() {
            this.props.resolve({confirmed: true, payload: this.state.selectedBooking});
            this.trigger('close-temp-screen');
        }

        _onClickBooking(event) {
            let booking = event.detail;
            if (this.state.selectedBooking === booking) {
                this.state.selectedBooking = null;
            } else {
                this.state.selectedBooking = booking;
            }
            this.confirm();
        }

        async updateBookingList(event) {
            this.state.query = event.target.value;
            const bookings = this.bookings;
            if (event.code === 'Enter' && bookings.length === 1) {
                this.state.selectedBooking = bookings[0];
                this.clickNext();
            } else {
                this.render();
            }
        }

        clickNext() {
            this.state.selectedBooking = this.nextButton.command === 'set' ? this.state.selectedBooking : null;
            this.confirm();
        }

        get bookings() {
            var res = this.env.pos.db.load('bookings', []);
            // if (this.state.currentPartner) {
            //     res = res.filter(r => r.partner_phone.includes(this.state.currentPartner.phone) || r.partner_name.includes(this.state.currentPartner.name.trim()))
            // }
            if (this.state.query && this.state.query.trim() !== '') {
                let query = this.state.query.trim()
                res = res.filter(r => r.partner_phone.includes(query) || r.name.includes(query) || r.partner_name.includes(query))
            }
            return res.sort(function (a, b) {
                return (a.name || '').localeCompare(b.name || '')
            });
        }

        isHighlighted(booking) {
            return booking === this.state.selectedBooking;
        }

        getName(booking) {
            return booking.name;
        }

        getTypeCustomer(booking) {
            return this._getBookingTypeCustomer().get(booking.type_customer).text;
        }

        getState(booking) {
            return booking.state_id ? booking.state_id[1] : '';
        }

        getUser(booking) {
            return booking.user_id ? booking.user_id[1] : '';
        }

        getDate(booking) {
            return moment(booking.date).format('DD/MM/YYYY');
        }

        getBranch(booking) {
            return booking.branch_id ? booking.branch_id[1] : '';
        }

        getSentDate(booking) {
            return moment(booking.date_sent).format('DD/MM/YYYY hh:mm:ss');
        }

        getStatus(booking) {
            return this._getBookingStatus().get(booking.state).text;
        }

        _getBookingTypeCustomer() {
            // We need the items to be ordered, therefore, Map is used instead of normal object.
            //      ('new', 'Khách hàng mới'),
            //      ('old', 'Khách hàng cũ'),
            //      ('find', 'Khách hàng tự tìm')
            const types = new Map();
            types.set('new', {
                text: 'Khách hàng mới',
            });
            types.set('old', {
                text: 'Khách hàng cũ',
            });
            types.set('find', {
                text: 'Khách hàng tự tìm',
            });
            return types;
        }

        _getBookingStatus() {
            // We need the items to be ordered, therefore, Map is used instead of normal object.
            //         ('draft', 'Nháp'),
            //         ('confirm', 'Chờ khách tới'),
            //         ('confirmed', 'Khách đã tới'),
            //         ('cancel_buy', 'Khách đã tới nhưng không mua'),
            //         ('cancel', 'Từ chối'),
            //         ('cancel_10', 'Hủy quá 10 ngày')
            const status = new Map();
            status.set('draft', {
                text: 'Nháp',
            });
            status.set('confirm', {
                text: 'Chờ khách tới',
            });
            status.set('confirmed', {
                text: 'Khách đã tới',
            });
            status.set('cancel_buy', {
                text: 'Khách đã tới nhưng không mua',
            });
            status.set('cancel', {
                text: 'Từ chối',
            });
            status.set('cancel_10', {
                text: 'Hủy quá 10 ngày',
            });
            return status;
        }
    }

    BookingListScreen.template = 'BookingListScreen';

    Registries.Component.add(BookingListScreen);

    return BookingListScreen;
});
