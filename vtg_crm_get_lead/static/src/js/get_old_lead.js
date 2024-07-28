odoo.define('button_near_get_old_lead.kanban_button', function (require) {
    "use strict";
    var KanbanController = require('web.KanbanController');
    var KanbanView = require('web.KanbanView');
    var viewRegistry = require('web.view_registry');
    var rpc = require('web.rpc');
    var session = require('web.session');

    var GetOldLeadKanbanButton = KanbanController.include({
        buttons_template: 'button_near_create.button',
        events: _.extend({}, KanbanController.prototype.events, {
            'click .open_get_old_lead': '_GetOldLeadKanban',
        }),

        // _GetOldLeadKanban: function () {
        //     var self = this;
        //     var uid = session.user_id
        //     var user = {}
        //     user.id = uid
        //     rpc.query({
        //         model: 'crm.lead', method: 'get_old_lead', args: [user],
        //     }).then(function (data) {
        //         return data
        //     });
        // }
        _GetOldLeadKanban: function () {
            var self = this;
            var uid = session.user_id
            var user = {}
            user.id = uid
            rpc.query({
                model: 'crm.lead', method: 'get_old_lead', args: [user],
            }).then(function (action) {
                // return  data
                return self.do_action(action);
            });
        }

    });
    var GetOldLeadKanbanButtonView = KanbanView.extend({
        config: _.extend({}, KanbanView.prototype.config, {
            Controller: GetOldLeadKanbanButton
        }),
    });
    viewRegistry.add('button_in_kanban', GetOldLeadKanbanButtonView);
});