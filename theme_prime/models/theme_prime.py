# -*- coding: utf-8 -*-
# Copyright (c) 2019-Present Droggol Infotech Private Limited. (<https://www.droggol.com/>)

from odoo import api, models


class ThemePrime(models.AbstractModel):
    _inherit = 'theme.utils'

    @api.model
    def _reset_default_config(self):

        self.disable_view('theme_prime.template_header_style_1')
        self.disable_view('theme_prime.template_header_style_2')
        self.disable_view('theme_prime.template_header_style_3')
        self.disable_view('theme_prime.template_header_style_4')
        self.disable_view('theme_prime.template_header_style_5')
        self.disable_view('theme_prime.template_header_style_6')
        self.disable_view('theme_prime.template_header_style_7')
        self.disable_view('theme_prime.template_header_style_8')

        self.disable_view('theme_prime.template_footer_style_1')
        self.disable_view('theme_prime.template_footer_style_2')
        self.disable_view('theme_prime.template_footer_style_3')
        self.disable_view('theme_prime.template_footer_style_4')
        self.disable_view('theme_prime.template_footer_style_5')
        self.disable_view('theme_prime.template_footer_style_6')
        self.disable_view('theme_prime.template_footer_style_7')
        self.disable_view('theme_prime.template_footer_style_8')
        self.disable_view('theme_prime.template_footer_style_9')
        self.disable_view('theme_prime.template_footer_style_10')

        super(ThemePrime, self)._reset_default_config()
