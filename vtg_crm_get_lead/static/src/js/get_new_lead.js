odoo.define('button_near_get_lead.kanban_button', function (require) {
    "use strict";
    var KanbanController = require('web.KanbanController');
    var KanbanView = require('web.KanbanView');
    var viewRegistry = require('web.view_registry');
    var rpc = require('web.rpc');
    var session = require('web.session');

    var GetLeadKanbanButton = KanbanController.include({
        buttons_template: 'button_near_create.button',
        events: _.extend({}, KanbanController.prototype.events, {
            'click .open_get_new_lead': '_GetLeadKanban',
        }),

        _GetLeadKanban: function () {
            var self = this;
            var uid = session.user_id
            var user = {}
            user.id = uid
            rpc.query({
                model: 'crm.lead', method: 'get_new_lead', args: [user],
            }).then(function (action) {
                // return  data
                return self.do_action(action);
            });
        }

    });
    var GetLeadKanbanButtonView = KanbanView.extend({
        config: _.extend({}, KanbanView.prototype.config, {
            Controller: GetLeadKanbanButton
        }),
    });
    viewRegistry.add('button_in_kanban', GetLeadKanbanButtonView);
});