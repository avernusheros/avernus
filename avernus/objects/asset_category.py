from avernus import objects
from sqlalchemy import Column, Integer, String, ForeignKey, Float, Table
from sqlalchemy.orm import relationship


association_table_positions = Table('category_position', objects.Base.metadata,
    Column('category_id', Integer, ForeignKey('asset_category.id')),
    Column('position_id', Integer, ForeignKey('portfolio_position.id'))
)

association_table_accounts = Table('category_account', objects.Base.metadata,
    Column('category_id', Integer, ForeignKey('asset_category.id')),
    Column('account_id', Integer, ForeignKey('account.id'))
)


class AssetCategory(objects.Base):

    __tablename__ = 'asset_category'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    parent_id = Column(Integer, ForeignKey('asset_category.id'))
    parent = relationship('AssetCategory', remote_side=[id], backref='children')
    target_percent = Column(Float, default=0.0)
    positions = relationship('PortfolioPosition',
                            secondary=association_table_positions,
                            backref="asset_categories")
    accounts = relationship('Account',
                            secondary=association_table_accounts,
                            backref="asset_categories")


def get_root_categories():
    return objects.Session().query(AssetCategory)\
                     .filter_by(parent=None)\
                     .all()


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
            root.delta_percent = root.delta / root.target
        else:
            root.delta_percent = 0.0
        for child in root.children:
            calculate_other(child)

    roots = get_root_categories()
    for root in roots:
        calculate_current(root)
        root.current_percent = 1.0
        root.target = root.current
        root.delta = 0.0
        root.delta_percent = 0.0
        for child in root.children:
            calculate_other(child)
