odoo.define('ev.mail.Manager.Notification', function (require) {
    "use strict";

    require('bus.BusService');
    /**
     * Mail Notification Manager
     *
     * This part of the mail manager is responsible for receiving notifications on
     * the longpoll bus, which are data received from the server.
     */
    var MailManagerNotification = require('mail.Manager.Notification');

    var core = require('web.core');

    var _t = core._t;

    MailManagerNotification.include({

        /**
         * On receiving a notification that is specific to a user
         *
         * @private
         * @param {Object} data structure depending on the type
         * @param {integer} data.id
         */
        _handlePartnerNotification: function (data) {
            if (data.info === 'unsubscribe') {
                this._handlePartnerUnsubscribeNotification(data);
            } else if (data.type === 'toggle_star') {
                this._handlePartnerToggleStarNotification(data);
            } else if (data.type === 'mark_as_read') {
                this._handlePartnerMarkAsReadNotification(data);
            } else if (data.type === 'moderator') {
                this._handlePartnerMessageModeratorNotification(data);
            } else if (data.type === 'author') {
                this._handlePartnerMessageAuthorNotification(data);
            } else if (data.type === 'deletion') {
                this._handlePartnerMessageDeletionNotification(data);
            } else if (data.info === 'transient_message') {
                this._handlePartnerTransientMessageNotification(data);
            } else if (data.type === 'activity_updated') {
                this._handlePartnerActivityUpdateNotification(data);
            } else if (data.type === 'notification_updated') {
                this._handlePartnerSystemUpdateNotification(data);
            } else if (data.type === 'mail_failure') {
                this._handlePartnerMailFailureNotification(data);
            } else if (data.type === 'user_connection') {
                this._handlePartnerUserConnectionNotification(data);
            } else if (data.info === 'channel_seen') {
                this._handlePartnerChannnelSeenNotification(data);
            } else if (data.type === 'simple_notification') {
                var title = _.escape(data.title), message = _.escape(data.message);
                data.warning ? this.do_warn(title, message, data.sticky) : this.do_notify(title, message, data.sticky);
            } else if (data.info === 'channel_minimize') {
                this._handlePartnerChannelMinimizeNotification(data);
            } else {
                this._handlePartnerChannelNotification(data);
            }
        },

        /**
         * Called when an activity record has been updated on the server
         *
         * @private
         * @param {Object} data key, value to decide activity created or deleted
         */
        _handlePartnerSystemUpdateNotification: function (data) {
            this._mailBus.trigger('notification_updated', data);
        },
    });

    return MailManagerNotification;

});
