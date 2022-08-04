class groceries:

	def __init__(self, **kwargs):
		self.grocery_list = []

	def __iter__(self):
		return self

	def add_groceries(self, items):
		for grocery in items:
			self.grocery_list.append({"item" : grocery, "price" : 0})

	def get_grocery_list(self):
		return self.grocery_list
