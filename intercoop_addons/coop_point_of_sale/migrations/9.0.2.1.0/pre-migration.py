# -*- coding: utf-8 -*-
from openerp import pooler, SUPERUSER_ID


def migrate(cr, version):
    if not version:
        return

    pool = pooler.get_pool(cr.dbname)
    cr.execute('''
        SELECT
        id from pos_order 
        where picking_id is null 
              and state in ('paid', 'done', 'invoiced')
        ''')
    order_obj = pool['pos.order']
    picking_obj = pool['stock.picking']
    move_obj = pool['stock.move']
    for order_id in cr.dictfetchall():
        print ('order:::', order_id)
        order = order_obj.browse(cr, SUPERUSER_ID, order_id['id'])
        order_picking_ids = picking_obj.search(
            cr, SUPERUSER_ID, [('origin', '=', order.name),
                               ('state', '=', 'draft')])
        print ('order_picking_ids::::', order_picking_ids)
        for picking in picking_obj.browse(cr, SUPERUSER_ID, order_picking_ids):
            move_list = []
            for line in order.lines:
                if line.product_id and \
                        line.product_id.type not in ['product', 'consu']:
                    continue
                move_id = move_obj.create(cr, SUPERUSER_ID, {
                    'name': line.name,
                    'product_uom': line.product_id.uom_id.id,
                    'picking_id': picking.id,
                    'picking_type_id': picking.picking_type_id.id,
                    'product_id': line.product_id.id,
                    'product_uom_qty': abs(line.qty),
                    'state': 'draft',
                    'location_id': picking.location_id.id,
                    'location_dest_id': picking.location_dest_id.id,
                })
                move_list.append(move_id)
            order_obj.write(cr, SUPERUSER_ID, [order.id],
                            {'picking_id': picking.id})
            order_obj._force_picking_done(cr, SUPERUSER_ID, picking.id)
    return True
