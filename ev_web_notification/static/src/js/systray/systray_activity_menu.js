odoo.define('ev_web_notification.systray.ActivityMenu', function (require) {
    "use strict";

    var core = require('web.core');
    var session = require('web.session');
    var SystrayMenu = require('web.SystrayMenu');
    var Widget = require('web.Widget');
    var QWeb = core.qweb;

    /**
     * Menu item appended in the systray part of the navbar, redirects to the next
     * activities of all app
     */
    var ActivityMenu = Widget.extend({
        name: 'ev_activity_menu',
        template: 'ev_web_notification.systray.ActivityMenu',
        events: {
            'click .o_mail_activity_action': '_onActivityActionClick',
            'click .o_mail_preview': '_onActivityFilterClick',
            'click .o_mark_as_read': '_onMarkAsRead',
            'show.bs.dropdown': '_onActivityMenuShow',
        },
        start: function () {
            this._$activitiesPreview = this.$('.o_mail_systray_dropdown_items');
            // this.call('mail_service', 'getMailBus').on('notification_updated', this, this._updateCounterNotification);
            this._updateCounterNotification();
            this._updateActivityPreview();
            return this._super();
        },
        //--------------------------------------------------
        // Private
        //--------------------------------------------------
        /**
         * Make RPC and get current user's activity details
         * @private
         */
        _getActivityData: function () {
            var self = this;

            return self._rpc({
                model: 'res.users',
                method: 'ev_systray_get_activities',
                args: [],
                kwargs: {context: session.user_context},
            }).then(function (data) {
                self._activities = data;
                self.activityCounter = _.reduce(data, function (total_count, p_data) {
                    return total_count + p_data.total_count || 0;
                }, 0);
                self.$('.o_notification_counter').text(self.activityCounter);
                self.$el.toggleClass('o_no_notification', !self.activityCounter);
            });
        },
        /**
         * Get particular model view to redirect on click of activity scheduled on that model.
         * @private
         * @param {string} model
         */
        _getActivityModelViewID: function (model) {
            return this._rpc({
                model: model,
                method: 'get_activity_view_id'
            });
        },
        /**
         * Update(render) activity system tray view on activity updation.
         * @private
         */
        _updateActivityPreview: function () {
            var self = this;
            self._getActivityData().then(function () {
                self._$activitiesPreview.html(QWeb.render('ev_web_notification.systray.ActivityMenu.Previews', {
                    widget: self
                }));
            });
        },
        /**
         * update counter based on activity status(created or Done)
         * @private
         * @param {Object} [data] key, value to decide activity created or deleted
         * @param {String} [data.type] notification type
         * @param {Boolean} [data.activity_deleted] when activity deleted
         * @param {Boolean} [data.activity_created] when activity created
         */
        _updateCounterNotification: function (data) {
            if (data) {
                if (data.notification_unseen) {
                    this.activityCounter++;
                }
                if (data.notification_seen && this.activityCounter > 0) {
                    this.activityCounter--;
                }
                this.$('.o_notification_counter').text(this.activityCounter);
                this.$el.toggleClass('o_no_notification', !this.activityCounter);
            }
        },

        //------------------------------------------------------------
        // Handlers
        //------------------------------------------------------------

        /**
         * Redirect to specific action given its xml id or to the activity
         * view of the current model if no xml id is provided
         *
         * @private
         * @param {MouseEvent} ev
         */
        _onActivityActionClick: function (ev) {
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

        /**
         * Redirect to particular model view
         * @private
         * @param {MouseEvent} event
         */
        _onMarkAsRead: function (event) {
            var data = _.extend({}, $(event.currentTarget).data(), $(event.target).data());
            var self = this;
            self._rpc({
                model: 'mail.message',
                method: 'message_read_all',
                args: [[]],
            }).then(function () {
                self._updateActivityPreview();
            });
        },

        /**
         * Redirect to particular model view
         * @private
         * @param {MouseEvent} event
         */
        _onActivityFilterClick: function (event) {
            // fetch the data from the button otherwise fetch the ones from the parent (.o_mail_preview).
            var data = _.extend({}, $(event.currentTarget).data(), $(event.target).data());
            var context = {};
            if (data.filter === 'my') {
                context['search_default_activities_overdue'] = 1;
                context['search_default_activities_today'] = 1;
            } else {
                context['search_default_activities_' + data.filter] = 1;
            }
            // Action update status mail_message when click
            var self = this;
            // Check status === 'unseen', then update status = 'seen'
            if (data.status === 'unseen') {
                this._rpc({
                    model: 'mail.message',
                    method: 'update_status_message',
                    args: [data.message_id],
                }).then(function () {
                    self._updateActivityPreview();
                });
            }
            // Necessary because activity_ids of ev_web_notification.activity.mixin has auto_join
            // So, duplicates are faking the count and "Load more" doesn't show up

            context['force_search_count'] = 1;
            context['allow_force_rule'] = 1;
            this.do_action({
                type: 'ir.actions.act_window',
                name: data.model_name,
                url_portal: data.url_portal,
                res_model: data.res_model,
                views: [[false, 'form']],
                res_id: data.res_id,
                domain: [['activity_user_id', '=', session.uid]],
                context: context,
            });
        },
        /**
         * @private
         */
        _onActivityMenuShow: function () {
            this._updateActivityPreview();
        },
    });

    SystrayMenu.Items.push(ActivityMenu);

    return ActivityMenu;

});
