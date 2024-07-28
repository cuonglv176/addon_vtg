odoo.define('vtg_pos_crm.DB', function (require) {
    "use strict"

    const PosDB = require('point_of_sale.DB');


    PosDB.include({

        addDataStore: function (store_name, data) {
            this.save(store_name, data);
        },

        getDataStoreIds: function (store_name) {
            let data = this.load(store_name, []);
            return data.map((item) => {
                return item.id;
            });
        },

    });

    return PosDB;

});
