from avernus.objects import session, Session
from avernus.objects.dimension import Dimension
from avernus.objects.dimension import DimensionValue
from avernus.objects.dimension import AssetDimensionValue
from avernus.controller.object_controller import delete_object


def new_dimension(name):
    d = Dimension(name=name)
    session.add(d)
    return d

def new_dimension_value(*args, **kwargs):
    dv = DimensionValue(**kwargs)
    session.add(dv)
    return dv

def new_asset_dimension_value(*args, **kwargs):
    adv = AssetDimensionValue(**kwargs)
    session.add(adv)
    return adv

def get_all_dimensions():
    res = session.query(Dimension).all()
    return res

def get_asset_dimension_value_text(asset_dimension_value):
    res = asset_dimension_value.dimension_value.name
    if asset_dimension_value.value != 100:
        res += ":"+str(asset_dimension_value.value)
    return res

def get_values_for_dimension(dimension):
    return Session().query(DimensionValue).filter_by(dimension=dimension).all()


def get_asset_dimension_value(asset, dimension):
    return Session().query(AssetDimensionValue).join(DimensionValue).filter(AssetDimensionValue.asset==asset,
                                                                DimensionValue.dimension==dimension).all()

def update_asset_dimension_values(asset, dimension, dimVals):
    for adv in get_asset_dimension_value(asset, dimension):
        delete_object(adv)
    for dimVal, value in dimVals:
        new_asset_dimension_value(asset=asset, dimension_value=dimVal, value=value)
