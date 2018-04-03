# -*- coding: UTF-8 -*-
# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

from trytond.pyson import Eval
from trytond.pool import Pool, PoolMeta

from trytond.model import ModelView, ModelSQL, fields
from trytond.config import config

__all__ = ['New_products', 'Template', 'Product']

STATES = {
    'readonly': ~Eval('active', True),
}
DEPENDS = ['active']
TYPES = [
    ('goods', u'商品'),
    ('assets', u'服务'),
    ('service', u'资产'),
]
COST_PRICE_METHODS = [
    ('fixed', u'固定'),
    ('average', u'平均'),
]
price_digits = (16, config.getint('product', 'price_decimal', default=4))


class Template:
    "Product Template"
    __metaclass__ = PoolMeta
    __name__ = 'product.template'

    manufacturers_code = fields.Char('Manufacturers_code')
    medical_insurance_code = fields.Char('Medical_insurance_code', select=True)
    attach = fields.Char('Attach', select=True)
    concentration = fields.Char('Concentration', select=True)  #
    concentration_unit = fields.Char('Concentration_unit', select=True)
    dose = fields.Char('Dose', select=True)  #
    dose_unit = fields.Char('Dose_unit', select=True)
    retrieve_the_code = fields.Char('Retrieve_the_code', select=True, required=True)
    capacity = fields.Char('Capacity', select=True, required=False)  #
    drug_specifications = fields.Function(fields.Char('Drug_specifications', select=True, readonly=True),
                                          'get_drug_specifications')
    is_direct_sending = fields.Boolean('Is_direct_sending', select=True)
    is_antimicrobials = fields.Boolean('Is_antimicrobials', select=True)
    a_charge = fields.Integer('A_charge', select=True)
    drup_level = fields.Char('Drup_level', select=True)
    compound_dose = fields.Float('Compound_dose', select=True)
    purchase_code = fields.Char('purchase_code', select=True, required=True)
    retail_package = fields.Many2One('product.uom', 'Retail Package')
    medical_insurance_description = fields.Char('Medical_insurance_description', select=True)
    new_term = fields.Char('new_term', select=True)
    state = fields.Char('State', select=True, required=False)
    min_Package = fields.Many2One('product.uom', 'Min_Package', required=True)
    dosage_form_description = fields.Char('Dosage_form_description', select=True)
    manufacturers_describtion = fields.Char('Manufacturers_describtion', select=True, required=False)
    poison_hemp_spirit = fields.Selection([
        ('common', u'普通'),
        ('narcosis', u'麻醉'),
        ('spirit_one', u'精神1'),
        ('spirit_two', u'精神2')
    ], 'Poison_hemp_spirit', select=True)
    national_essential_medicines = fields.Boolean('National_essential_medicines', select=True)
    interim = fields.Selection([
        ('1', u''),
        ('2', u'是')], 'interim', select=True)
    approval_number = fields.Char('Approval number')
    is_atict = fields.Boolean('is_atict')
    homemade = fields.Boolean('homemade')

    def get_drug_specifications(self, name):
        if self.dose != None and self.dose_unit != '':
            drug_specificationss = str(self.dose.encode('utf-8')) + str((self.dose_unit).encode('utf-8')) + '*' + str(
                (self.capacity).encode('utf-8')) + str(self.min_Package.name.encode('utf-8'))
        elif self.concentration != None and self.concentration_unit != None:
            drug_specificationss = str(self.concentration).encode('utf-8') + (self.concentration_unit).encode(
                'utf-8') + '*' + str((self.capacity).encode('utf-8')) + str(self.min_Package.name.encode('utf-8'))
        else:
            drug_specificationss = '*' + str((self.capacity).encode('utf-8')) + str(
                self.min_Package.name.encode('utf-8'))
        return drug_specificationss


class Product:
    "Product Variant"
    __metaclass__ = PoolMeta
    __name__ = "product.product"
    _order_name = 'rec_name'

    @classmethod
    def search_rec_name(cls, name, clause):
        if clause[1].startswith('!') or clause[1].startswith('not '):
            bool_op = 'AND'
        else:
            bool_op = 'OR'
        return [bool_op,
                ('code',) + tuple(clause[1:]),
                ('template.name',) + tuple(clause[1:]),
                ('template.retrieve_the_code',) + tuple(clause[1:]),
                ]

    def get_rec_name(self, name):
        if self.code:
            return '[' + self.code + '] ' + self.name
        else:
            return self.name


class New_products(ModelSQL, ModelView):
    "New_product"
    __name__ = "hrp_product.new_products"
    _order_name = 'rec_name'
    manufacturers_code = fields.Function(fields.Char('Manufacturers_code'), 'get_manufacturers_code',
                                         'set_manufacturers_code')
    medical_insurance_code = fields.Function(fields.Char('Medical_insurance_code', select=True),
                                             'get_medical_insurance_code', 'set_medical_insurance_code')
    attach = fields.Function(fields.Char('Attach', select=True), 'get_attach', 'set_attach')
    concentration = fields.Function(fields.Char('Concentration', select=True), 'get_concentration', 'set_concentration')
    concentration_unit = fields.Function(fields.Char('Concentration_unit', select=True), 'get_concentration_unit',
                                         'set_concentration_unit')
    dose = fields.Function(fields.Char('Dose', select=True), 'get_dose', 'set_dose')
    dose_unit = fields.Function(fields.Char('Dose_unit', select=True), 'get_dose_unit', 'set_dose_unit')
    retrieve_the_code = fields.Function(fields.Char('Retrieve_the_code', select=True, required=True),
                                        'get_retrieve_the_code', 'set_retrieve_the_code', 'search_retrieve_the_code')
    capacity = fields.Function(fields.Char('Capacity', select=True), 'get_capacity', 'set_capacity')
    drug_specifications = fields.Function(fields.Char('Drug_specifications', select=True, readonly=True),
                                          'get_drug_specifications', 'set_drug_specifications')
    is_direct_sending = fields.Function(fields.Boolean('Is_direct_sending', select=True), 'get_is_direct_sending',
                                        'set_is_direct_sending')
    is_antimicrobials = fields.Function(fields.Boolean('Is_antimicrobials', select=True), 'get_is_antimicrobials',
                                        'set_is_antimicrobials')
    a_charge = fields.Function(fields.Integer('A_charge', select=True, readonly=False), 'get_a_charge', 'set_a_charge')
    drup_level = fields.Function(fields.Char('Drup_level', select=True), 'get_drup_level', 'set_drup_level')
    compound_dose = fields.Function(fields.Float('Compound_dose', select=True), 'get_compound_dose',
                                    'set_compound_dose')
    purchase_code = fields.Function(fields.Char('purchase_code', select=True, required=True), 'get_purchase_code',
                                    'set_purchase_code')
    retail_package = fields.Function(fields.Many2One('product.uom', 'Retail Package'), 'get_retail_package',
                                     'set_retail_package')
    medical_insurance_description = fields.Function(fields.Char('Medical_insurance_description', select=True),
                                                    'get_medical_insurance_description',
                                                    'set_medical_insurance_description')
    new_term = fields.Function(fields.Char('new_term', select=True), 'get_new_term', 'set_new_term')
    state = fields.Function(fields.Char('State', select=True, required=False), 'get_state', 'set_state')
    min_Package = fields.Function(fields.Many2One('product.uom', 'Min_Package', required=False), 'get_min_Package',
                                  'set_min_Package')
    uom_min_Package = fields.Function(fields.Char('Uom Min Package', required=True), 'get_uom_min_Package',
                                      'set_uom_min_Package')
    dosage_form_description = fields.Function(fields.Char('Dosage_form_description', select=True),
                                              'get_dosage_form_description', 'set_dosage_form_description')
    manufacturers_describtion = fields.Function(fields.Char('Manufacturers_describtion', required=False, select=True),
                                                'get_manufacturers_describtion', 'set_manufacturers_describtion')
    poison_hemp_spirit = fields.Function(fields.Selection([
        ('common', u'普通'),
        ('narcosis', u'麻醉'),
        ('spirit_one', u'精神1'),
        ('spirit_two', u'精神2')
    ], 'Poison_hemp_spirit', select=True), 'get_poison_hemp_spirit', 'set_poison_hemp_spirit')
    national_essential_medicines = fields.Function(fields.Boolean('National_essential_medicines', select=True),
                                                   'get_national_essential_medicines',
                                                   'set_national_essential_medicines')
    interim = fields.Function(fields.Selection([
        ('1', u''),
        ('2', u'是')], 'interim', select=True), 'get_interim', 'set_interim')
    #############################
    mark = fields.Many2One('product.template', 'Mark', select=True)
    name = fields.Function(fields.Char("Name", size=None, required=True, translate=True,
                                       select=True, states=STATES, depends=DEPENDS), "get_name", "set_name",
                           "searcher_name")
    active = fields.Function(fields.Boolean('Active', select=False, readonly=True), "get_active", "set_active",
                             'seacher_active')
    type = fields.Function(fields.Selection(TYPES, 'Type', required=True, states=STATES,
                                            depends=DEPENDS), "get_type", "set_type")
    default_uom = fields.Function(fields.Many2One('product.uom', 'Default UOM', required=False,
                                                  states=STATES, depends=DEPENDS), 'get_default_uom', 'set_default_uom')
    uom_default_uom = fields.Function(fields.Char('Uom Default UOM', required=True,
                                                  states=STATES, depends=DEPENDS), 'get_uom_default_uom',
                                      'set_uom_default_uom')
    code = fields.Function(fields.Char("Code", size=None, required=True, states=STATES,
                                       depends=DEPENDS), 'get_code', 'set_code')
    list_price = fields.Function(fields.Property(fields.Numeric('List Price',
                                                                states={
                                                                    'readonly': False
                                                                    # Eval('drug_specifications') != '',
                                                                },
                                                                digits=price_digits, depends=['active', 'default_uom'],
                                                                required=True)), 'get_list_price', 'set_list_price')
    cost_price = fields.Function(fields.Property(fields.Numeric('Cost Price', states={
        'readonly': False  # Eval('drug_specifications') != '',
    },
                                                                digits=price_digits, depends=DEPENDS, required=True)),
                                 'get_list_price', 'set_cost_price')
    cost_price_method = fields.Function(fields.Property(fields.Selection(COST_PRICE_METHODS,
                                                                         'Cost Method', required=True, states=STATES,
                                                                         depends=DEPENDS)), 'get_cost_price_method',
                                        'set_cost_price_method')
    categories = fields.Function(
        fields.Many2One('product.category', 'Categories', required=True, states=STATES, depends=DEPENDS),
        'get_categories', 'set_categories', 'search_categories')
    salable = fields.Function(fields.Boolean('Salable', states={
        'readonly': ~Eval('active', True),
    }, depends=['active']), 'get_salable', 'set_salable')
    purchasable = fields.Function(fields.Boolean('Purchasable', states={
        'readonly': ~Eval('active', True),
    }, depends=['active']), 'get_purchasable', 'set_purchasable')

    consumable = fields.Function(fields.Boolean('Consumable',
                                                states={
                                                    'readonly': True,
                                                    'invisible': Eval('type', 'goods') != 'goods',
                                                },
                                                depends=['active', 'type']), 'get_consumable', 'set_consumable')
    party = fields.Function(fields.Many2One('party.party', 'Supplier', domain=[
        ('type_', '=', 'supplier')
    ], required=True,
                                            ondelete='CASCADE', select=True), 'get_party', 'set_party')
    approval_number = fields.Function(fields.Char('Approval number'), 'get_approa_number', 'set_approval_number')
    is_atict = fields.Function(fields.Boolean('is_atict'), 'get_is_atict', 'set_is_atict')
    homemade = fields.Function(fields.Boolean('homemade'), 'get_homemade', 'set_homemade')

    @classmethod
    def searcher_name(cls, name, clause):
        New_products = Pool().get("hrp_product.new_products")
        product = New_products.search([])
        ids = []
        for i in product:
            if clause[2].strip('%') in i.name:
                ids.append(i.id)
        return [('id', 'in', ids)]

    @classmethod
    def search_categories(cls, name, clause):
        New_products = Pool().get("hrp_product.new_products")
        product = New_products.search([])
        ids = []
        for i in product:
            if clause[2].strip('%') == i.categories.name:
                ids.append(i.id)
        return [('id', 'in', ids)]

    @classmethod
    def search_retrieve_the_code(cls, name, clause):
        pass

    def get_homemade(self, name):
        return self.mark.homemade

    @classmethod
    def set_homemade(cls, homemade, name, value):
        pass

    def get_is_atict(self, name):
        return self.mark.is_atict

    @classmethod
    def set_is_atict(cls, set_is_atict, name, value):
        pass

    def get_approa_number(self, name):
        return self.mark.approval_number

    @classmethod
    def set_approval_number(cls, set_approval_number, name, value):
        pass

    def get_manufacturers_code(self, name):
        return self.mark.manufacturers_code

    def get_party(self, name):
        party = self.mark.product_suppliers
        if party:
            party = party[0].party.id
            return party

    def get_national_essential_medicines(self, name):
        return self.mark.national_essential_medicines

    def get_interim(self, name):
        return self.mark.interim

    def get_poison_hemp_spirit(self, name):
        return self.mark.poison_hemp_spirit

    def get_manufacturers_describtion(self, name):
        return self.mark.manufacturers_describtion

    def get_dosage_form_description(self, name):
        return self.mark.dosage_form_description

    def get_uom_min_Package(self, name):
        return self.mark.min_Package.name

    def get_min_Package(self, name):
        return self.mark.min_Package.id

    def get_state(self, name):
        return self.mark.state

    def get_medical_insurance_description(self, name):
        return self.mark.medical_insurance_description

    def get_new_term(self, name):
        return self.mark.new_term

    def get_retail_package(self, name):
        return self.mark.retail_package.id

    def get_purchase_code(self, name):
        return self.mark.purchase_code

    def get_compound_dose(self, name):
        return self.mark.compound_dose

    def get_drup_level(self, name):
        return self.mark.drup_level

    def get_a_charge(self, name):
        return self.mark.a_charge

    def get_is_direct_sending(self, name):
        return self.mark.is_direct_sending

    def get_is_antimicrobials(self, name):
        return self.mark.is_antimicrobials

    def get_drug_specifications(self, name):
        return self.mark.drug_specifications

    def get_capacity(self, name):
        return self.mark.capacity

    def get_retrieve_the_code(self, name):
        return self.mark.retrieve_the_code

    def get_dose_unit(self, name):
        return self.mark.dose_unit

    def get_dose(self, name):
        return self.mark.dose

    def get_concentration_unit(self, name):
        return self.mark.concentration_unit

    def get_concentration(self, name):
        return self.mark.concentration

    def get_attach(self, name):
        return self.mark.attach

    def get_medical_insurance_code(self, name):
        return self.mark.medical_insurance_code

    def get_name(self, name):
        return self.mark.name

    def get_active(self, name):
        return self.mark.active

    def get_type(self, name):
        return self.mark.type

    def get_uom_default_uom(self, name):
        return self.mark.default_uom.name

    def get_default_uom(self, name):  ###
        return self.mark.default_uom.id

    def get_code(self, name):
        return self.mark.products[0].code

    def get_list_price(self, name):
        list_price = self.mark.list_price
        list_prices = self.mark.cost_price
        if name == 'cost_price':
            return list_prices
        if name == 'list_price':
            return list_price

    def get_cost_price(self, name):
        return self.mark.cost_price

    def get_cost_price_method(self, name):
        return self.mark.cost_price_method

    def get_categories(self, name):
        categories = self.mark.categories
        if categories:
            ids = categories[0].id
            return ids

    def get_salable(self, name):
        return self.mark.salable

    def get_purchasable(self, name):
        return self.mark.purchasable

    def get_consumable(self, name):
        return self.mark.consumable

    @classmethod
    def set_name(cls, set_name, name, value):
        pass

    @classmethod
    def set_is_antimicrobials(cls, set_is_antimicrobials, name, value):
        pass

    @classmethod
    def set_party(cls, set_party, name, value):
        pass

    @classmethod
    def set_manufacturers_code(cls, set_manufacturers_code, name, value):
        pass

    @classmethod
    def set_medical_insurance_code(cls, set_medical_insurance_code, name, value):
        pass

    @classmethod
    def set_get_manufacturers_code(cls, get_manufacturers_code, name, value):
        pass

    @classmethod
    def set_attach(cls, set_attach, name, value):
        pass

    @classmethod
    def set_concentration(cls, set_concentration, name, value):
        pass

    @classmethod
    def set_concentration_unit(cls, set_concentration_unit, name, value):
        pass

    @classmethod
    def set_dose(cls, set_dose, name, value):
        pass

    @classmethod
    def set_dose_unit(cls, set_dose_unit, name, value):
        pass

    @classmethod
    def set_retrieve_the_code(cls, set_retrieve_the_code, name, value):
        pass

    @classmethod
    def set_capacity(cls, set_capacity, name, value):
        pass

    @classmethod
    def set_drug_specifications(cls, set_drug_specifications, name, value):
        pass

    @classmethod
    def set_is_direct_sending(cls, set_is_direct_sending, name, value):
        pass

    @classmethod
    def set_a_charge(cls, set_a_charge, name, value):
        pass

    @classmethod
    def set_drup_level(cls, set_drup_level, name, value):
        pass

    @classmethod
    def set_compound_dose(cls, set_compound_dose, name, value):
        pass

    @classmethod
    def set_purchase_code(cls, set_purchase_code, name, value):
        pass

    @classmethod
    def set_retail_package(cls, set_retail_package, name, value):
        pass

    @classmethod
    def set_medical_insurance_description(cls, set_medical_insurance_description, name, value):
        pass

    @classmethod
    def set_new_term(cls, set_new_term, name, value):
        pass

    @classmethod
    def set_state(cls, set_state, name, value):
        pass

    @classmethod
    def set_min_Package(cls, set_min_Package, name, value):
        pass

    @classmethod
    def set_uom_min_Package(cls, set_min_Package, name, value):
        pass

    @classmethod
    def set_dosage_form_description(cls, set_dosage_form_description, name, value):
        pass

    @classmethod
    def set_manufacturers_describtion(cls, set_manufacturers_describtion, name, value):
        pass

    @classmethod
    def set_poison_hemp_spirit(cls, set_poison_hemp_spirit, name, value):
        pass

    @classmethod
    def set_national_essential_medicines(cls, set_national_essential_medicines, name, value):
        pass

    @classmethod
    def set_interim(cls, set_interim, name, value):
        pass

    @classmethod
    def set_code(cls, set_code, name, value):
        pass

    @classmethod
    def set_active(cls, set_active, name, value):
        pass

    @classmethod
    def set_type(cls, set_type, name, value):
        pass

    @classmethod
    def set_default_uom(cls, set_default_uom, name, value):
        pass

    @classmethod
    def set_uom_default_uom(cls, set_default_uom, name, value):
        pass

    @classmethod
    def set_list_price(cls, set_list_price, name, value):
        pass

    @classmethod
    def set_cost_price(cls, set_cost_price, name, value):
        pass

    @classmethod
    def set_cost_price_method(cls, set_cost_price_method, name, value):
        pass

    @classmethod
    def set_categories(cls, set_categories, name, value):
        pass

    @classmethod
    def set_salable(cls, set_salable, name, value):
        pass

    @classmethod
    def set_purchasable(cls, set_purchasable, name, value):
        pass

    @classmethod
    def set_consumable(cls, set_consumable, name, value):
        pass

    @classmethod
    def seacher_active(cls, name, clause):
        pass

    @staticmethod
    def default_salable():
        return True

    @staticmethod
    def default_cost_price_method():
        return 'fixed'

    @staticmethod
    def default_purchasable():
        return True

    @staticmethod
    def default_approval_number():
        return ''

    @staticmethod
    def default_interim():
        return '00'

    @staticmethod
    def default_active():
        return True

    @staticmethod
    def default_consumable():
        return False

    @staticmethod
    def default_type():
        return 'goods'

    @fields.depends('code')
    def on_change_code(self, name=None):
        if self.code:
            for ch in self.code:
                if u'\u4e00' <= ch <= u'\u9fff':
                    raise TypeError("'Can't be Chinese")

    @classmethod
    def create(cls, vlist):
        pool = Pool()
        UomCategory = Pool().get('product.uom.category')
        Uom = Pool().get('product.uom')
        product_templates = pool.get("product.template")
        product_products = pool.get("product.product")
        product_supplier = pool.get("purchase.product_supplier")
        product_configurations = pool.get("product.configuration")
        product_configuration = product_configurations.search([])
        for value in vlist:
            product_codes = product_products.search([('name', '=', value['code'])])
            if product_codes:
                cls.raise_user_error(u'%s已经存在！') % value['name']
            uom_category = UomCategory.create([{'name': value['name'] + '/' + value['code']}])
            uom_min_Package = Uom.create([{
                u'category': uom_category[0].id,
                u'digits': 2,
                u'name': value['uom_min_Package'],
                u'rounding': 1,
                u'symbol': value['uom_min_Package'],
                u'rate': 1.0,
                u'factor': 1.0,
                u'active': True
            }])
            uom_default_uom = Uom.create([{
                u'category': uom_category[0].id,
                u'digits': 2,
                u'name': value['uom_default_uom'],
                u'rounding': 0.01,
                u'symbol': value['uom_default_uom'],
                u'rate': round(1 / float(int(value['capacity'])), 12),
                u'factor': float(value['capacity']),
                u'active': True
            }])
            print value['name']
            is_antimicrobials = value['is_antimicrobials']
            party = value['party']
            medical_insurance_code = value['medical_insurance_code']
            attach = value['attach']
            concentration = value['concentration']
            concentration_unit = value['concentration_unit']
            dose_unit = value['dose_unit']
            retrieve_the_code = value['retrieve_the_code']
            capacity = value['capacity']
            is_direct_sending = value['is_direct_sending']
            approval_number = value['approval_number']
            a_charge = value['a_charge']
            drup_level = value['drup_level']
            compound_dose = value['compound_dose']
            purchase_code = value['purchase_code']
            retail_package = uom_min_Package[0].id  # value['retail_package']
            medical_insurance_description = value['medical_insurance_description']
            new_term = value['new_term']
            state = value['state']
            min_Package = Uom(uom_min_Package[0].id)
            dosage_form_description = value['dosage_form_description']
            interim = value['interim']
            national_essential_medicines = value['national_essential_medicines']
            poison_hemp_spirit = value['poison_hemp_spirit']
            manufacturers_describtion = value['manufacturers_describtion']
            name = value['name']
            active = True
            type = value['type']
            default_uom = uom_default_uom[0].id
            code = value['code']
            list_price = value['list_price']
            cost_price = value['cost_price']
            cost_price_method = value['cost_price_method']
            categories = [[u'add', [value['categories']]]]
            salable = value['salable']
            purchasable = value['purchasable']
            manufacturers_code = value['manufacturers_code']
            consumable = value['consumable']
            dose = value['dose']
            if 'dose' in value and dose != None:
                drug_specificationss = str(value['dose'].encode('utf-8')) + str(
                    (value['dose_unit']).encode('utf-8')) + '*' + str((value['capacity']).encode('utf-8')) + str(
                    min_Package)
            elif 'concentration' in value and concentration != None:
                drug_specificationss = str(value['concentration']).encode('utf-8') + (
                    value['concentration_unit']).encode('utf-8') + '*' + str((value['capacity']).encode('utf-8')) + str(
                    min_Package)
            else:
                drug_specificationss = '*' + str((value['capacity']).encode('utf-8')) + str(min_Package)
            value['drug_specifications'] = str(drug_specificationss)
            add_each = [{'is_antimicrobials': is_antimicrobials,
                         'medical_insurance_code': medical_insurance_code,
                         'attach': attach,
                         'concentration': concentration,
                         'concentration_unit': concentration_unit,
                         'dose': dose,
                         'dose_unit': dose_unit,
                         'retrieve_the_code': retrieve_the_code,
                         'capacity': capacity,
                         'is_direct_sending': is_direct_sending,
                         'a_charge': a_charge,
                         'drup_level': drup_level,
                         'compound_dose': compound_dose,
                         'purchase_code': purchase_code,
                         'retail_package': retail_package,
                         'medical_insurance_description': medical_insurance_description,
                         'new_term': new_term,
                         'state': state,
                         'manufacturers_code': manufacturers_code,
                         'min_Package': min_Package,
                         'dosage_form_description': dosage_form_description,
                         'manufacturers_describtion': manufacturers_describtion,
                         'poison_hemp_spirit': poison_hemp_spirit,
                         'national_essential_medicines': national_essential_medicines,
                         'interim': interim,
                         'drug_specifications': drug_specificationss,
                         'name': name,
                         'active': active,
                         'type': type,
                         'default_uom': default_uom,
                         'list_price': list_price,
                         'cost_price': cost_price,
                         'cost_price_method': cost_price_method,
                         'categories': categories,
                         'approval_number': approval_number,
                         'salable': salable,
                         'purchasable': purchasable,
                         'consumable': consumable,
                         'sale_uom': default_uom,
                         'purchase_uom': default_uom,
                         }]
            account_revenue = product_configuration[0].account_revenue
            shelf_life_state = product_configuration[0].shelf_life_state
            account_expense = product_configuration[0].account_expense
            expiration_state = product_configuration[0].expiration_state
            if account_revenue == None:
                raise ValueError('Please fill in the product configuration')
            else:
                add_each[0]['account_revenue'] = int(account_revenue)
            if shelf_life_state == None:
                raise ValueError('Please fill in the product configuration')
            else:
                add_each[0]['shelf_life_state'] = str(shelf_life_state)
            if account_expense == None:
                raise ValueError('Please fill in the product configuration')
            else:
                add_each[0]['account_expense'] = int(account_expense)
            if expiration_state == None:
                raise ValueError('Please fill in the product configuration')
            else:
                add_each[0]['expiration_state'] = str(expiration_state)

            product_template = product_templates.create(add_each)
            marks = int(product_template[0].id)
            product_product = product_products.create([{'template': marks, 'code': code, 'active': True}])
            product_supplier.create([{'product': marks, 'party': party}])
            value['mark'] = marks
        return super(New_products, cls).create(vlist)

    @classmethod
    def delete(cls, records):
        pool = Pool()
        UomCategory = Pool().get('product.uom.category')
        Uom = Pool().get('product.uom')
        product_templates = pool.get("product.template")
        product_products = pool.get("product.product")
        for value in records:
            mark = int(value.mark)
            product_template = product_templates.search([
                ('id', '=', mark)
            ])
            uom_uom_default_uom = Uom.search([('category', '=', product_template[0].default_uom.category.id)])
            uom_category = UomCategory.search([('id', '=', product_template[0].default_uom.category.id)])
            product_templates.delete(product_template)
            Uom.delete(uom_uom_default_uom)
            # UomCategory.delete(uom_category)
        return super(New_products, cls).delete(records)

    @classmethod
    def write(cls, records, values, *args):
        pool = Pool()
        UomCategory = Pool().get('product.uom.category')
        Uom = Pool().get('product.uom')
        product_templates = pool.get("product.template")
        product_products = pool.get("product.product")
        product_suppliers = pool.get("purchase.product_supplier")
        for ids in records:
            mark = int(ids.mark)
            product_template = product_templates.search([
                ('id', '=', mark)
            ])
            product_product = product_products.search([
                ('template', '=', mark)
            ])
            product_supplier = product_suppliers.search([
                ('product', '=', mark)
            ])
            uom_uom_min_Package = Uom.search([('id', '=', product_template[0].min_Package.id)])
            uom_uom_default_uom = Uom.search([('id', '=', product_template[0].default_uom.id)])
            uom_category = UomCategory.search([('id', '=', product_template[0].default_uom.category.id)])
            lv = {}
            lvc = {}
            uom_min_Package = {}
            uom_default_uom = {}
            if 'name' in values:
                UomCategory.write(uom_category, {'name': values['name'] + uom_category[0].name.split('/')[1]})
            if 'uom_min_Package' in values:
                uom_min_Package['name'] = values['uom_min_Package']
                uom_min_Package['symbol'] = values['uom_min_Package']
                values.pop('uom_min_Package')
                Uom.write(uom_uom_min_Package, uom_min_Package)
            if 'uom_default_uom' in values:
                uom_default_uom['name'] = values['uom_default_uom']
                uom_default_uom['symbol'] = values['uom_default_uom']
                values.pop('uom_default_uom')
            if 'capacity' in values:
                Uom.write(uom_uom_default_uom, {'active': False})
                uom_uom_default_uom = Uom.create([{
                    u'category': uom_category[0].id,
                    u'digits': 2,
                    u'name': uom_uom_default_uom[0].name,
                    u'rounding': 0.01,
                    u'symbol': uom_uom_default_uom[0].name,
                    u'rate': round(1 / float(values['capacity']), 12),
                    u'factor': float(values['capacity']),
                    u'active': True
                }])
                values['sale_uom'] = uom_uom_default_uom[0].id
                values['purchase_uom'] = uom_uom_default_uom[0].id
                values['default_uom'] = uom_uom_default_uom[0].id
            if uom_default_uom:
                Uom.write(uom_uom_default_uom, uom_default_uom)
            if 'party' in values:
                lvc['party'] = values['party']
                values.pop('party')
            if lvc != {}:
                product_suppliers.write(product_supplier, lvc)
            if 'code' in values:
                UomCategory.write(uom_category, {'name': uom_category[0].name.split('/')[0] + values['name']})
                lv['code'] = values['code']
                values.pop('code')
            if 'template' in values:
                lv['template'] = values[mark]
                values.pop('template')
            if lv != {}:
                product_products.write(product_product, lv)
            if 'mark' in values:
                values.pop('mark')
            if 'categories' in values:
                values['categories'] = [[u'add', [values['categories']]],
                                        [u'remove', [product_template[0].categories[0].id]]]
            if values != {}:
                product_templates.write(product_template, values)
            if 'sale_uom' in values:
                values.pop('sale_uom')
            if 'purchase_uom' in values:
                values.pop('purchase_uom')
        return super(New_products, cls).write(records, values)
