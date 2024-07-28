odoo.define('vtg_pos_order.UserLine', function(require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');

    class UserLine extends PosComponent {
        get highlight() {
            return this.props.user !== this.props.selectedUser? '' : 'highlight';
        }
    }
    UserLine.template = 'UserLine';

    Registries.Component.add(UserLine);

    return UserLine;
});
