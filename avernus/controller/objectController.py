from avernus.objects import session

def delete_object(obj):
    session.delete(obj)
    session.commit()
