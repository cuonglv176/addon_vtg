odoo.define('ev_web_notification.PortalSystrayActivityMenu', function (require) {

    var ajax = require("web.ajax");
    var publicWidget = require('web.public.widget');
    var session = require("web.session");
    var ServiceProviderMixin = require('web.ServiceProviderMixin');
    require("bus.BusService");

    var core = require('web.core');
    var QWeb = core.qweb;
    var _t = core._t;

    publicWidget.registry.PortalSystrayActivityMenu = publicWidget.Widget.extend(ServiceProviderMixin, {
        selector: '#top_menu_tcmotor',
        xmlDependencies: ['/ev_web_notification/static/src/xml/systray.xml'],
        events: {
            'click .o_mail_preview.o_systray_activity': 'onClickNotifyPreviewItem',
            'click .o_mark_as_read': 'onMarkAsRead',
            'show.bs.dropdown': 'onActivityMenuShow',
        },
        init: function () {
            this._super.apply(this, arguments);
            ServiceProviderMixin.init.call(this);
        },
        start: function () {
            let res = this._super.apply(this, arguments);
            this.start_polling();
            this.addNotifyMenuItem();
            core.bus.on('notification_updated', this, this._updateActivityPreview);
            this._updateCounterNotification();
            this._updateActivityPreview();
            return res;
        },
        onClickNotifyPreviewItem: function (event) {
            event.preventDefault();
            let self = this;
            let $self = $(event.currentTarget);
            let data = $self.data();
            if (data.status === 'unseen') {
                this._rpc({
                    model: 'mail.message',
                    method: 'update_status_message',
                    args: [data.message_id],
                }).then(function () {
                    self._updateActivityPreview();
                    self.do_action(data);
                });
            } else {
                this.do_action(data);
            }

        },
        onMarkAsRead: function (event) {
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
        onActivityMenuShow: function () {
            this._updateActivityPreview();
        },
        do_action: function(data){
            let funcAction = 'do_action_model';
            // let funcAction = 'do_action_'+data['res_model'].split('.').join('_');
            if (this.hasOwnProperty(funcAction)) {
                this[funcAction](data);
            } else {
                console.error('Chức năng đang được cập nhật, vui lòng thử lại sau.');
            }
        },
        do_action_model: function (data) {
            // Demo, Các model khác sử lý tương tự
            let origin = window.location.origin;
            let href = origin + data.url_portal;
            window.location.href = href;
        },
        addNotifyMenuItem: function () {
            this.$target.append(QWeb.render('ev_web_notification.systray.ActivityMenu'));
            this._$activitiesPreview = this.$target.find('.o_mail_systray_dropdown_items');
            this._$activitiesPreview.closest('.o_mail_systray_item').addClass('nav-item');
        },
        _getActivityData: function () {
            var self = this;
            if (!session.user_id){
                self._activities = [];
                self.activityCounter = 0;
                self.$('.o_notification_counter').text(self.activityCounter);
                self.$el.toggleClass('o_no_notification', !self.activityCounter);
                return Promise.resolve([]);
            }

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

        _getActivityModelViewID: function (model) {
            return this._rpc({
                model: model,
                method: 'get_activity_view_id'
            });
        },
        _updateActivityPreview: function () {
            var self = this;
            self._getActivityData().then(function () {
                self._$activitiesPreview.html(QWeb.render('ev_web_notification.systray.ActivityMenu.Previews', {
                    widget: self
                }));
            });
        },
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
        start_polling: function () {
            this.my_channel = "tcm_notification_" + session.user_id;
            this.all_channels = [this.my_channel]
            this.call("bus_service", "addChannel", this.my_channel);
            this.call("bus_service", "on", "notification", this, this.bus_notification);
            this.call("bus_service", "startPolling");
        },
        bus_notification: function (notifications) {
            var self = this;
            _.each(notifications, function (notification) {
                var channel = notification[0];
                var message = notification[1];
                if (
                    self.all_channels !== null &&
                    self.all_channels.indexOf(channel) > -1
                ) {
                    self.on_message(message);
                }
            });
        },
        on_message: function (message) {
            if (message.type === 'notification_updated') {
                core.bus.trigger('notification_updated', message);
            }
        },
    });

});