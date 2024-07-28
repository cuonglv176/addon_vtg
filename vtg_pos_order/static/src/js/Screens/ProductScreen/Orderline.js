odoo.define('vtg_pos_order.Orderline', function (require) {
    'use strict';

    const Orderline = require('point_of_sale.Orderline');
    const Registries = require('point_of_sale.Registries');
    const {useListener} = require('web.custom_hooks');


    const VTGPosOrderline = (Orderline) =>
        class extends Orderline {
            constructor() {
                super(...arguments);
                useListener('click-user', this._clickUser);
                useListener('click-user-master', this._clickUserMaster);
                useListener('click-user-assistant', this._clickUserAssistant);
            }

            get_user() {
                return this.props.line.user_id;
            }

            get_user_master() {
                return this.props.line.user_master_id;
            }

            get_user_assistant() {
                return this.props.line.user_assistant_id;
            }

            async _clickUser() {
                const currentUser = this.get_user();
                const {confirmed, payload: newUser} = await this.showTempScreen(
                    'UserListScreen',
                    {user: currentUser}
                );
                if (confirmed) {
                    this.props.line.set_user(newUser);
                }
            }

            async _clickUserMaster() {
                const currentUserMaster = this.get_user_master();
                const {confirmed, payload: newUserMaster} = await this.showTempScreen(
                    'UserListScreen',
                    {user: currentUserMaster}
                );
                if (confirmed) {
                    this.props.line.set_user_master(newUserMaster);
                }
            }

            async _clickUserAssistant() {
                const currentUserAssistant = this.get_user_assistant();
                const {confirmed, payload: newUserAssistant} = await this.showTempScreen(
                    'UserListScreen',
                    {user: currentUserAssistant}
                );
                if (confirmed) {
                    this.props.line.set_user_assistant(newUserAssistant);
                }
            }

        };

    Registries.Component.extend(Orderline, VTGPosOrderline);

    return Orderline;
});
