from avernus.objects import session

def delete_object(obj):
    try:
        session.delete(obj)
    except:
        session.expunge(obj)
    session.commit()
