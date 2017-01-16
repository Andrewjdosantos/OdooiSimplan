# from odoo.osv import fields, osv
from odoo import fields, models, api, osv, modules
import re
# from odoo import models
# from odoo import SUPERUSER_ID, api, models
import logging
#Get the logger
_logger = logging.getLogger(__name__)

class prod(models.Model):
    _name = "prod"
#    _inherit = "mrp.production"
    #_inherit = "product.template"
#    @api.depends("deps")
#    def _calcDemand(self):
#        twop = self.env.cr.execute("SELECT SUM(product_qty) FROM mrp_production WHERE product_id = " + self.deps + ";")
#        self.twop = self.env.cr.fetchone()[0]

#    def get_journals(cr, uid, context=None):
#        journal_obj = self.pool.get('product.product')
#        journal_ids = journal_obj.search(cr, uid, [], context=context)
#        lst = []
#        for journal in journal_obj.browse(cr, uid, journal_ids, context=context):
#            lst.append((journal.id, journal.name_template))
#        return lst
#    slections = ((1,1),(2,2),(3,3))
    Product = fields.Many2one('product.product')
    ProfileName = fields.Many2one('bufferprofiles')
    LVF = fields.Float('LVF', digits=(6,3), help='')
    DVF = fields.Float('DVF', digits=(6,3), help='')
    SupplyOrders = fields.Char('SupplyOrders', size = 80, help='')
    QoH = fields.Integer('QoH', size = 80, help='')
    SOD = fields.Integer('SOD', size=80, help='')
    ADU = fields.Float('ADU', digits=(6,3), help='')
    LT = fields.Float('LT', digits=(6,3), help='')
    YellowZ = fields.Float('YellowZ', digits=(6,3), help='')
    GreenZ = fields.Float('GreenZ', digits=(6,3), help='')
    BaseRedZ = fields.Float('BaseRedZ', digits=(6,3), help='')
    SafetyRedZ = fields.Float('SafetyRedZ', digits=(6,3), help='')
    TOG = fields.Float('TOG', digits=(6,3), help='')
    POG = fields.Float('POG', digits=(6,3), help='')
    POY = fields.Float('POY', digits=(6,3), help='')
    POBR = fields.Float('POBR', digits=(6,3), help='')
    POSR = fields.Float('POSR', digits=(6,3), help='')
    AvailableStock = fields.Float('AvailableStock', digits=(6,3), help='')
    SuggestedOrderQuant = fields.Float('SuggestedOrderQuant',digits=(6,3), help='')
    is_green = fields.Boolean(default=False,store=True)
    is_yellow = fields.Boolean(default=False,store=True)
    is_baseRed = fields.Boolean(default=False,store=True)
    is_safetyRed = fields.Boolean(default=False,store=True)
    is_blue = fields.Boolean(default=False,store=True)
    # def newMethod(self):
    #     self.process_demo_scheduler_queue("cr","uid")
#   
    @api.model
    def _newMethof(self):
        _logger.debug(self)
        """ Method called by cron to fetch mails from servers """
        self.search([]).process_demo_scheduler_queue()

    @api.model
    def process_demo_scheduler_queue(self):
        _logger.debug("////////////////////////////////////////////////////////////////////////////////")
        for record in self:
            _logger.debug("///")
            _id = re.sub("[^0-9]", "",str(record.Product))
            _logger.debug(_id)
        # for record in self.search([]):
#Get Total Supply Order = to purchase orders and manufacturing orders
            self.env.cr.execute("SELECT SUM(product_qty) FROM mrp_production WHERE product_id = " + _id + " AND state = 'confirmed' OR state = 'progress';")
            try:
                ManufacturingOrders = self.env.cr.fetchone()[0]+0
            except(TypeError):
                ManufacturingOrders = 0;
                _logger.debug("No Manufacturing Orders Found for id:" + _id)
            self.env.cr.execute("SELECT SUM(product_qty) FROM purchase_order_line WHERE product_id = " + _id + " AND state = 'purchase';")
            try:
                PurchaseOrders = self.env.cr.fetchone()[0]+0
            except(TypeError):
                PurchaseOrders = 0;
                _logger.debug("No Purchase Orders Found for id:" + _id)
            SupplyOrders = PurchaseOrders+ManufacturingOrders
            record.write({'SupplyOrders': SupplyOrders})
# Get Quantity on hand
            self.env.cr.execute("SELECT qty FROM stock_quant WHERE product_id = " + _id + ";")
            try:
                QoH = self.env.cr.fetchone()[0]+0
            except(TypeError):
                QoH = 0;
                _logger.debug("No Quantity on Hand Found for id:" +_id)
            _logger.debug(QoH)
            record.write({'QoH': QoH})
#Get total demand = sales orders+manufacturing orders
            self.env.cr.execute("SELECT sum(qty_to_invoice) FROM sale_order_line INNER JOIN sale_order ON sale_order_line.order_id = sale_order.id INNER JOIN stock_picking ON sale_order.name = stock_picking.origin WHERE product_id =" + _id + "AND max_date <= (current_date+90) AND max_date >= current_date and sale_order_line.state = 'sale';")
            try:
                SOD = self.env.cr.fetchone()[0]+0
            except(TypeError):
                SOD = 0;
                _logger.debug("No Sales Order Demand Foundfor id:"+_id)
            record.write({'SOD': SOD})
# Calculate Average Daily Usage
            ADU = SOD/90 #REPLACE IN SETTINGS
            record.write({'ADU': ADU})
# Find Lead time,purchase lead time for purchases items and manufacturing for make items, the maximum
            self.env.cr.execute("SELECT sum(route_id) from stock_route_product where product_id =" + _id +";")
            try:
                make_buy = self.env.cr.fetchone()[0]+0
            except(TypeError):
                _logger.debug("No Make or Buy found for id:"+_id)
                LT =0

            if make_buy == 5:
                self.env.cr.execute("SELECT produce_delay from product_template where id =" + _id +";")
                _logger.debug("Found make Item")
                try:
                    LT = self.env.cr.fetchone()[0]+0
                except(TypeError):
                    LT = 0;
                    _logger.debug("No Make Lead Time Found Found for id:"+_id)
            if make_buy == 6:
                self.env.cr.execute("SELECT max(delay) from product_supplierinfo where product_tmpl_id =" + _id +";")
                _logger.debug("Found buy item")
                try:
                    LT = self.env.cr.fetchone()[0]+0
                except(TypeError):
                    LT = 0;
                    _logger.debug("No Buy Lead Time Found Found for id:"+_id)
            if make_buy > 6:
                make_buy_list = []
                _logger.debug("Found Make and Buy item")
                self.env.cr.execute("SELECT produce_delay from product_template where id =" + _id +";")
                try:
                    make = self.env.cr.fetchone()[0]+0
                    make_buy_list.append(make)
                except(TypeError):
                    make = 0
                    make_buy_list.append(make)
                    _logger.debug("Route Id greater than 6 but no make LT found for id:"+_id)
                self.env.cr.execute("SELECT max(delay) from product_supplierinfo where product_tmpl_id =" + _id +";")
                try:
                    buy = self.env.cr.fetchone()[0]+0
                    make_buy_list.append(buy)
                except(TypeError):
                    buy = 0
                    make_buy_list.append(buy)
                    _logger.debug("Route Id greater than 6 but no buy LT found for id:"+_id)
                LT = max(make_buy_list)

            record.write({'LT': LT})
            #Calculate Buffers
            try:
                YellowZ = ADU * LT
                record.write({'YellowZ': YellowZ})
                BaseRedZ = YellowZ * record.LVF
                record.write({'BaseRedZ': BaseRedZ})
                SafetyRedZ = YellowZ * record.DVF
                record.write({'SafetyRedZ': SafetyRedZ})
                GreenZ = YellowZ * record.DVF
                record.write({'GreenZ': GreenZ})
                TOG = YellowZ + GreenZ + SafetyRedZ + BaseRedZ
                record.write({'TOG': TOG})
                POG = (GreenZ/TOG)
                record.write({'POG': POG})
                POY = (YellowZ/TOG)
                record.write({'POY': POY})
                POBR = (BaseRedZ/TOG)
                record.write({'POBR': POBR})
                POSR = (SafetyRedZ/TOG)
                record.write({'POSR': POSR})
                AvailableStock = QoH + SupplyOrders - SOD #still need to add spike
                record.write({'AvailableStock': AvailableStock})
                SuggestedOrderQuant = TOG - AvailableStock
                if SuggestedOrderQuant <0:
                    SuggestedOrderQuant = 0
                record.write({'SuggestedOrderQuant': SuggestedOrderQuant})
                if AvailableStock >= TOG:
                    record.write({'is_blue':True})
                    record.write({'is_green':False})
                    record.write({'is_yellow':False})
                    record.write({'is_baseRed':False})
                    record.write({'is_safetyRed':False})
                if AvailableStock < TOG and AvailableStock > (YellowZ+BaseRedZ+SafetyRedZ):
                    record.write({'is_blue':False})
                    record.write({'is_green':True})
                    record.write({'is_yellow':False})
                    record.write({'is_baseRed':False})
                    record.write({'is_safetyRed':False})
                if AvailableStock < (YellowZ+BaseRedZ+SafetyRedZ) and AvailableStock > (BaseRedZ+SafetyRedZ):
                    record.write({'is_blue':False})
                    record.write({'is_green':False})
                    record.write({'is_yellow':True})
                    record.write({'is_baseRed':False})
                    record.write({'is_safetyRed':False})
                if AvailableStock < (BaseRedZ+SafetyRedZ) and AvailableStock > (BaseRedZ):
                    record.write({'is_blue':False})
                    record.write({'is_green':False})
                    record.write({'is_yellow':False})
                    record.write({'is_baseRed':False})
                    record.write({'is_safetyRed':True})
                if AvailableStock < (BaseRedZ):
                    record.write({'is_blue':False})
                    record.write({'is_green':False})
                    record.write({'is_yellow':False})
                    record.write({'is_baseRed':True})
                    record.write({'is_safetyRed':False}) 
            except(ZeroDivisionError,TypeError):
                _logger.debug("Missing Data for id:"+_id)
                record.write({'is_blue':False})
                record.write({'is_green':False})
                record.write({'is_yellow':False})
                record.write({'is_baseRed':False})
                record.write({'is_safetyRed':False})

