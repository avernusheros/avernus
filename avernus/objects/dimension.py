from avernus import objects
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship, backref


class Dimension(objects.Base):
    __tablename__ = 'dimension'

    id = Column(Integer, primary_key=True)
    name = Column(String)

    def get_values(self):
        return objects.Session().query(DimensionValue)\
                        .filter_by(dimension=self).all()

    def get_asset_dimension_value(self, asset):
        return objects.Session().query(AssetDimensionValue)\
                           .join(DimensionValue)\
                           .filter(AssetDimensionValue.asset == asset,
                                   DimensionValue.dimension == self)\
                           .all()

    def update_asset_dimension_values(self, asset, dim_vals):
        for adv in self.get_asset_dimension_value(asset):
            adv.delete()
        for dimVal, value in dim_vals:
            AssetDimensionValue(asset=asset,
                                dimension_value=dimVal,
                                value=value)


class DimensionValue(objects.Base):
    __tablename__ = 'dimension_value'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    dimension_id = Column(Integer, ForeignKey('dimension.id'))
    dimension = relationship('Dimension',
                    backref=backref('values', cascade="all,delete"))


class AssetDimensionValue(objects.Base):
    __tablename__ = 'asset_dimension_value'

    id = Column(Integer, primary_key=True)
    value = Column(Float)
    asset_id = Column(Integer, ForeignKey('asset.id'))
    dimension_value_id = Column(Integer, ForeignKey('dimension_value.id'))
    asset = relationship('Asset',
                  backref=backref("dimension_values", cascade="all,delete"))
    dimension_value = relationship('DimensionValue')

    def get_text(self):
        res = self.dimension_value.name
        if self.value != 100:
            res += ":" + str(self.value)
        return res


def get_all_dimensions():
    return objects.session.query(Dimension).all()
