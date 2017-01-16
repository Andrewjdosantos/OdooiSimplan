# from odoo.osv import fields, osv
from odoo import fields, models, api, osv, modules
import re
# from odoo import models
# from odoo import SUPERUSER_ID, api, models
import logging
#Get the logger
_logger = logging.getLogger(__name__)

class bufferprofiles(models.Model):
    _name = "bufferprofiles"
    name = fields.Char('ProfileName', help='')
    LVF = fields.Float('LVF', digits=(6,3), help='')
    DVF = fields.Float('DVF', digits=(6,3), help='')

