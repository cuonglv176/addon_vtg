/** @odoo-module **/
import SystrayMenu from 'web.SystrayMenu';
import Widget from 'web.Widget';

var ExampleWidget = Widget.extend({
    template: 'SaleOrderSystray',
    events: {
        'click #create_so': '_onClick',
    },
    _onClick: function () {
        // this.do_action({
        //     type: 'ir.actions.act_window',
        //     name: 'Sale Order',
        //     res_model: 'sale.order',
        //     view_mode: 'form',
        //     views: [[false, 'form']],
        //     target: 'new'
        // });
        ev.stopPropagation();
        this.$('.dropdown-toggle').dropdown('toggle');
        var targetAction = $(ev.currentTarget);
        var actionXmlid = targetAction.data('action_xmlid');
        if (actionXmlid) {
            this.do_action(actionXmlid);
        } else {
            this.do_action({
                type: 'ir.actions.act_window',
                name: targetAction.data('model_name'),
                url_portal: targetAction.data('url_portal'),
                views: [[false, 'activity'], [false, 'kanban'], [false, 'list'], [false, 'form']],
                view_mode: 'activity',
                res_model: targetAction.data('res_model'),
                domain: [['activity_ids.user_id', '=', session.uid]],
            });
        }
    },
});
SystrayMenu.Items.push(ExampleWidget);
export default ExampleWidget;