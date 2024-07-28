# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ResCurrencyRate(models.Model):
    _inherit = 'res.currency.rate'

    # Overwrite mo rong so sau dau phay
    rate = fields.Float(string='Rate', digits=(16, 20), help='The rate of the currency to the currency of rate 1')
    x_rate = fields.Float(string='Rate ', digits=(16, 6))

    @api.onchange('x_rate')
    def onchange_x_rate(self):
        for r in self:
            if r.x_rate:
                r.rate = 1 / r.x_rate


class ResCurrency(models.Model):
    _inherit = "res.currency"

    def get_x_rate(self):
        for r in self:
            if r.rate:
                r.x_rate = round(1 / r.rate, 18)

    # Overwrite mo rong so sau dau phay
    rate = fields.Float(compute='_compute_current_rate', string='Current Rate', digits=(16, 20),
                        help='The rate of the currency to the currency of rate 1.')
    x_rate = fields.Float(string='Current Rate ', digits=(16, 6), compute=get_x_rate)



    def _get_x_rate(self, company, date):
        self.env['res.currency.rate'].flush(['x_rate', 'currency_id', 'company_id', 'name'])
        query = """SELECT COALESCE((SELECT r.x_rate FROM res_currency_rate r
                                  WHERE r.currency_id = c.id AND r.name <= %s
                                    AND (r.company_id IS NULL OR r.company_id = %s)
                               ORDER BY r.company_id, r.name DESC
                                  LIMIT 1), 1.0) AS x_rate
                   FROM res_currency c
                   WHERE c.id IN %s"""
        self._cr.execute(query, (date, company.id, tuple(self.ids)))
        currency_rates = self._cr.fetchall()
        return currency_rates and currency_rates[0] and currency_rates[0][0] or 1

    @api.model
    def _get_conversion_rate(self, from_currency, to_currency, company, date):
        # TruongNN
        current_rate = self._context.get('current_rate', False)
        return current_rate or super(ResCurrency, self)._get_conversion_rate(from_currency, to_currency, company, date)

    def _word(self, number):
        return {
            '0': 'không',
            '1': 'một',
            '2': 'hai',
            '3': 'ba',
            '4': 'bốn',
            '5': 'năm',
            '6': 'sáu',
            '7': 'bảy',
            '8': 'tám',
            '9': 'chín',
        }[number]

    def _unit(self, number_of_digits):
        return {
            '1': '',
            '2': 'nghìn',
            '3': 'triệu',
            '4': 'tỷ',
            '5': 'nghìn',
            '6': 'triệu',
            '7': 'tỷ ',
        }[number_of_digits]

    def _split_mod(self, value):
        res = ''

        if value == '000':
            return ''
        if len(value) == 3:
            tr = value[:1]
            ch = value[1:2]
            dv = value[2:3]
            if tr == '0' and ch == '0':
                res = self._word(dv) + ' '
            if tr != '0' and ch == '0' and dv == '0':
                res = self._word(tr) + ' trăm '
            if tr != '0' and ch == '0' and dv != '0':
                res = self._word(tr) + ' trăm lẻ ' + self._word(dv) + ' '
            if tr == '0' and int(ch) > 1 and int(dv) > 0 and dv != '5':
                res = self._word(ch) + ' mươi ' + self._word(dv)
            if tr == '0' and int(ch) > 1 and dv == '0':
                res = self._word(ch) + ' mươi '
            if tr == '0' and int(ch) > 1 and dv == '5':
                res = self._word(ch) + ' mươi lăm '
            if tr == '0' and ch == '1' and int(dv) > 0 and dv != '5':
                res = ' mười ' + self._word(dv) + ' '
            if tr == '0' and ch == '1' and dv == '0':
                res = ' mười '
            if tr == '0' and ch == '1' and dv == '5':
                res = ' mười lăm '
            if int(tr) > 0 and int(ch) > 1 and int(dv) > 0 and dv != '5':
                res = self._word(tr) + ' trăm ' + self._word(ch) + ' mươi ' + self._word(dv) + ' '
            if int(tr) > 0 and int(ch) > 1 and dv == '0':
                res = self._word(tr) + ' trăm ' + self._word(ch) + ' mươi '
            if int(tr) > 0 and int(ch) > 1 and dv == '5':
                res = self._word(tr) + ' trăm ' + self._word(ch) + ' mươi lăm '
            if int(tr) > 0 and ch == '1' and int(dv) > 0 and dv != '5':
                res = self._word(tr) + ' trăm mười ' + self._word(dv) + ' '
            if int(tr) > 0 and ch == '1' and dv == '0':
                res = self._word(tr) + ' trăm mười '
            if int(tr) > 0 and ch == '1' and dv == '5':
                res = self._word(tr) + ' trăm mười lăm '

        return res

    def _split(self, value):
        res = ''

        if value == '000':
            return ''
        if len(value) == 3:
            tr = value[:1]
            ch = value[1:2]
            dv = value[2:3]
            if tr == '0' and ch == '0':
                res = ' không trăm lẻ ' + self._word(dv) + ' '
            if tr != '0' and ch == '0' and dv == '0':
                res = self._word(tr) + ' trăm '
            if tr != '0' and ch == '0' and dv != '0':
                res = self._word(tr) + ' trăm lẻ ' + self._word(dv) + ' '
            if tr == '0' and int(ch) > 1 and int(dv) > 0 and dv != '5':
                if int(dv) == 1:
                    res = ' không trăm ' + self._word(ch) + ' mươi mốt'
                else:
                    res = ' không trăm ' + self._word(ch) + ' mươi ' + self._word(dv)
            if tr == '0' and int(ch) > 1 and dv == '0':
                res = ' không trăm ' + self._word(ch) + ' mươi '
            if tr == '0' and int(ch) > 1 and dv == '5':
                res = ' không trăm ' + self._word(ch) + ' mươi lăm '
            if tr == '0' and ch == '1' and int(dv) > 0 and dv != '5':
                res = ' không trăm mười ' + self._word(dv)
            if tr == '0' and ch == '1' and dv == '0':
                res = ' không trăm mười '
            if tr == '0' and ch == '1' and dv == '5':
                res = ' không trăm mười lăm '
            if int(tr) > 0 and int(ch) > 1 and int(dv) > 0 and dv != '5':
                if int(dv) == 1:
                    res = self._word(tr) + ' trăm ' + self._word(ch) + ' mươi mốt'
                else:
                    res = self._word(tr) + ' trăm ' + self._word(ch) + ' mươi ' + self._word(dv) + ' '
            if int(tr) > 0 and int(ch) > 1 and dv == '0':
                res = self._word(tr) + ' trăm ' + self._word(ch) + ' mươi '
            if int(tr) > 0 and int(ch) > 1 and dv == '5':
                res = self._word(tr) + ' trăm ' + self._word(ch) + ' mươi lăm '
            if int(tr) > 0 and ch == '1' and int(dv) > 0 and dv != '5':
                res = self._word(tr) + ' trăm mười ' + self._word(dv) + ' '
            if int(tr) > 0 and ch == '1' and dv == '0':
                res = self._word(tr) + ' trăm mười '
            if int(tr) > 0 and ch == '1' and dv == '5':
                res = self._word(tr) + ' trăm mười lăm '

        return res

    def _num2word(self, amount):
        if not amount:
            return 'Không'

        # delare
        in_word = ''
        split_mod = ''
        split_remain = ''
        num = int(amount)
        decimal = amount - num
        gnum = str(num)
        gdecimal = str(decimal)[2:]
        m = int(len(gnum) / 3)
        mod = len(gnum) - m * 3
        sign = '[+]'

        # sign
        if amount < 0:
            sign = '[-]'
        else:
            sign = ''

        # tách hàng lớn nhất
        if mod == 1:
            split_mod = '00' + str(num)[:1]
        elif mod == 2:
            split_mod = '0' + str(num)[:2]
        elif mod == 0:
            split_mod = '000'
        # tách hàng còn lại sau mod
        if len(str(num)) > 2:
            split_remain = str(num)[mod:]
        # đơn vị hàng mod
        im = m + 1
        if mod > 0:
            in_word = self._split_mod(split_mod) + ' ' + self._unit(str(im))
        # tách 3 trong split_remain
        i = m
        _m = m
        j = 1
        split3 = ''
        split3_ = ''
        while i > 0:
            split3 = split_remain[:3]
            split3_ = split3
            in_word = in_word + ' ' + self._split(split3)
            m = _m + 1 - j
            if int(split3_) != 0:
                in_word = in_word + ' ' + self._unit(str(m))
            split_remain = split_remain[3:]
            i = i - 1
            j = j + 1
        if in_word[:1] == 'k':
            in_word = in_word[10:]
        if in_word[:1] == 'l':
            in_word = in_word[2:]
        if len(in_word) > 0:
            in_word = sign + ' ' + str(in_word.strip()[:1]).upper() + in_word.strip()[1:]

        if decimal > 0:
            in_word += ' phẩy'
            for i in range(0, len(gdecimal)):
                in_word += ' ' + self._word(gdecimal[i])
            in_word += ' ' + 'đồng'
        else:
            in_word += ' ' + 'đồng chẵn'

        return in_word
