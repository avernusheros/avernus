from avernus import objects
from sqlalchemy import Column, Integer, String, ForeignKey, Float
from sqlalchemy.orm import relationship


class AssetCategory(objects.Base):

    __tablename__ = 'asset_category'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    parent_id = Column(Integer, ForeignKey('asset_category.id'))
    parent = relationship('AssetCategory', remote_side=[id], backref='children')
    target_percent = Column(Float)
    positions = relationship('PortfolioPosition', backref="asset_category")
    accounts = relationship('Account', backref="asset_category")


def get_root_category():
    return objects.session.query(AssetCategory)\
                     .filter_by(parent=None)\
                     .one()


def calculate_values():
    def calculate_current(root):
        root.current = 0.0
        root.current += sum([pos.current_value for pos in root.positions])
        root.current += sum([acc.balance for acc in root.accounts])
        for child in root.children:
            calculate_current(child)
            root.current += child.current

    def calculate_other(root):
        if root.parent.current:
            root.current_percent = root.current / root.parent.current
        else:
            root.current_percent = 1.0
        root.target = root.target_percent * root.parent.current
        root.delta = root.current - root.target
        if root.target:
            root.delta_percent = root.current / root.target
        else:
            root.delta_percent = 0.0
        for child in root.children:
            calculate_other(child)

    root = get_root_category()
    calculate_current(root)
    root.current_percent = 1.0
    root.target = root.current
    root.delta = 0.0
    root.delta_percent = 0.0
    for child in root.children:
        calculate_other(child)
