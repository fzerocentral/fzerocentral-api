from django.db.models import F


def insert_ordered_obj_prep(request, order_field_name, existing_objs):
    """
    Prepare to insert an object in a group of ordered model objects.
    The model can be any model with an integer order field starting with 1.
    """
    order = request.data.get(order_field_name)

    if order is None:
        # By default, order at the end, after all existing objs.
        order = existing_objs.count() + 1
    elif order < 1:
        # Restrict the order to the accepted range.
        order = 1
    elif order > existing_objs.count() + 1:
        # Restrict the order to the accepted range.
        order = existing_objs.count() + 1

    # Change other objs' order as needed to accommodate the new obj. We
    # need to +1 the order of objs coming after this one.
    later_objs = existing_objs.filter(
        **{order_field_name+'__gte': order})
    later_objs.update(**{order_field_name: F(order_field_name)+1})

    request.data[order_field_name] = order
    return request


def reorder_obj_prep(request, order_field_name, obj, all_objs):
    new_order = request.data.get(order_field_name)

    if new_order is None:
        return request

    old_order = getattr(obj, order_field_name)

    # Restrict the order to the accepted range.
    if new_order < 1:
        new_order = 1
    elif new_order > all_objs.count():
        new_order = all_objs.count()

    # Inc/dec the order of objs between this obj's old and new order,
    # then set this obj to the desired order.
    if old_order < new_order:
        # e.g. ABCDEF -> ABDEFC (moved C)
        # Objs in between the old and new positions move backward.
        affected_objs = all_objs.filter(**{
            order_field_name+'__gt': old_order,
            order_field_name+'__lte': new_order})
        affected_objs.update(**{order_field_name: F(order_field_name)-1})
    elif new_order < old_order:
        # e.g. ABCDEF -> ABFCDE (moved F)
        # Objs in between the old and new positions move forward.
        affected_objs = all_objs.filter(**{
            order_field_name+'__lt': old_order,
            order_field_name+'__gte': new_order})
        affected_objs.update(**{order_field_name: F(order_field_name)+1})

    request.data[order_field_name] = new_order
    return request


def delete_ordered_obj_prep(order_field_name, obj, all_objs):
    # Decrement the order of objs coming after this obj.
    obj_order = getattr(obj, order_field_name)
    affected_objs = all_objs.filter(
        **{order_field_name+'__gt': obj_order})
    affected_objs.update(**{order_field_name: F(order_field_name)-1})
