from avernus import pubsub


class Page():
    
    def get_info(self):
        return []

    def update_page(self):
        pubsub.publish("update_page", self)
