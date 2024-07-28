odoo.define('vtg_pos_order.UserListScreen', function (require) {
    'use strict';

    const {debounce} = owl.utils;
    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');

    class UserListScreen extends PosComponent {
        constructor() {
            super(...arguments);

            this.state = {
                query: null,
                selectedUser: this.props.user,
            };
            this.updateUserList = debounce(this.updateUserList, 70);
        }

        // Lifecycle hooks
        back() {
            this.props.resolve({confirmed: false, payload: false});
            this.trigger('close-temp-screen');
        }

        confirm() {
            this.props.resolve({confirmed: true, payload: this.state.selectedUser});
            this.trigger('close-temp-screen');
        }

        get users() {
            var res = this.env.pos.users;
            if (this.state.query && this.state.query.trim() !== '') {
                let query = this.state.query.trim()
                res = res.filter(r => r.name.includes(query) || r.name.includes(query))
            }
            return res.sort(function (a, b) {
                return (a.name || '').localeCompare(b.name || '')
            });
        }

        get isNextButtonVisible() {
            return this.state.selectedUser ? true : false;
        }

        /**
         * Returns the text and command of the next button.
         * The command field is used by the clickNext call.
         */
        get nextButton() {
            if (!this.props.user) {
                return {command: 'set', text: this.env._t('Set User')};
            } else if (this.props.user && this.props.user === this.state.selectedUser) {
                return {command: 'deselect', text: this.env._t('Deselect User')};
            } else {
                return {command: 'set', text: this.env._t('Change User')};
            }
        }

        async updateUserList(event) {
            this.state.query = event.target.value;
            const users = this.users;
            if (event.code === 'Enter' && users.length === 1) {
                this.state.selectedUser = users[0];
                this.clickNext();
            } else {
                this.render();
            }
        }

        clickUser(event) {
            let user = event.detail.user;
            if (this.state.selectedUser === user) {
                this.state.selectedUser = null;
            } else {
                this.state.selectedUser = user;
            }
            this.render();
        }

        clickNext() {
            this.state.selectedUser = this.nextButton.command === 'set' ? this.state.selectedUser : null;
            this.confirm();
        }

        async searchUser() {
            let result = await this.getNewUser();
            this.env.pos.db.add_partners(result);
            if (!result.length) {
                await this.showPopup('ErrorPopup', {
                    title: '',
                    body: this.env._t('No user found'),
                });
            }
            this.render();
        }

        async getNewUser() {
            var domain = [];
            if (this.state.query) {
                domain = [
                    '|',
                    ["name", "ilike", this.state.query],
                    ["email", "ilike", this.state.query],
                ];
            }
            var result = await this.rpc({
                model: 'res.user',
                method: 'search',
                args: [domain],
                kwargs: {
                    limit: 10,
                },
            }, {
                timeout: 3000,
                shadow: true,
            });

            return result;
        }
    }

    UserListScreen.template = 'UserListScreen';

    Registries.Component.add(UserListScreen);

    return UserListScreen;
});
