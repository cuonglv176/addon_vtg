odoo.define('vtg_pos_order.models', function (require) {
    "use strict"

    const models = require('point_of_sale.models');

    // models.load_fields('pos.order.line', ['user_id', 'user_master_id', 'user_assistant_id']);

    var orderline_super = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        set_user: function (user_id) {
            this.user_id = user_id;
            this.trigger('change');
        },

        set_user_master: function (user_id) {
            this.user_master_id = user_id;
            this.trigger('change');
        },

        set_user_assistant: function (user_id) {
            this.user_assistant_id = user_id;
            this.trigger('change');
        },
        initialize: function (attr, options) {
            orderline_super.initialize.apply(this, arguments);
            this.user_id = this.user_id || options.user_id;
            this.user_master_id = this.user_master_id || options.user_master_id;
            this.user_assistant_id = this.user_assistant_id || options.user_assistant_id;
        },
        export_as_JSON: function () {
            var json = orderline_super.export_as_JSON.apply(this);
            json.user_id = this.user_id;
            json.user_master_id = this.user_master_id;
            json.user_assistant_id = this.user_assistant_id;
            return json;
        },
        init_from_JSON: function (json) {
            orderline_super.init_from_JSON.apply(this, arguments);
            this.user_id = json.user_id;
            this.user_master_id = json.user_master_id;
            this.user_assistant_id = json.user_assistant_id;
        },
        export_for_printing: function () {
            // var json = OrderLine.export_for_printing.apply(this, arguments);
            var json = orderline_super.export_for_printing.apply(this, arguments);
            json.user_id = this.user_id;
            json.user_master_id = this.user_master_id;
            json.user_assistant_id = this.user_assistant_id;
            return json;
        },
    });

    return models;

});
