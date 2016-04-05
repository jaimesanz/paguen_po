from django.contrib.auth import backends
from expenses_manager.models import ProxyUser

class ModelBackend(backends.ModelBackend):
	'''
	Extending to provide a proxy for user
	'''

	def get_user(self, user_id):
		try:
			return ProxyUser.objects.get(pk=user_id)
		except ProxyUser.DoesNotExist:
			return None