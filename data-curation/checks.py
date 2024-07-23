
import pandas as pd

class CheckException(Exception):
	'''Meant to be raised by Check objects if the parameters are flawed or other issues related to the Check itself'''
	pass

class CheckReturn:
	'''
	Base class for all the results of a check
	'''
	def __init__(self, message=None):
		'''CheckReturn objects can be instanciated with a string or an Exception'''
		if isinstance(message, Exception):
			self.message = type(message).__name__
			if len(message.args) > 0:
				self.message += ' : '
			if len(message.args) == 1:
				try:
					self.message += str(message.args[0])
				except:
					self.message += repr(message.args[0])
			else:
				self.message += str(message.args)
		elif type(message) == str:
			self.message = str(message)
		elif message is None:
			self.message = message
		else:
			raise TypeError(f'{type(self)}.__init__ : message must be a string or an exception')

class CheckSuccess(CheckReturn):
	pass
class CheckWarning(CheckReturn):
	pass
class CheckError(CheckReturn):
	pass

class Check:
	'''Instances of this class are meant to be used directly as decorator in the following manner :
	@Check(name=..., description=...)
	def function(*args, **kwargs):
		...
		return CheckReturn(...)

	The decorated function will be wrapped for safety and used as a property of the instance that can be accessed by name using the class method "get". To add fixing functions, use the method "add_fix" of the instance as a decorator like this :
	@Check.get('some_check_name').add_fix
	def fix1(value):
		if ...: # value can be fixed
			return True, new_value
		return False, None # value could not be fixed
	@Check.get('some_check_name').add_fix
	def fix2(value):
		if ...: # value can be fixed
			return True, new_value
		return False, None # value could not be fixed

	Those fixing functions can be used later to curate a dataset
	'''
	instances = dict()
	def __init_subclass__(cls):
		cls.instances = dict()
	def __init__(self, *, name, description=None):
		if type(name) != str:
			raise TypeError(f'VariableCheck : name must be str')
		self.name = name
		self.description = description
		self.function = None 
		self.fixes = list()		
		if name in Check.instances: 
			raise ValueError(f'Check : already known name "{name}"')
		Check.instances[name] = self
		if type(self) != Check:
			if name in type(self).instances:
				raise ValueError(f'{type(self).__name__} : already known name "{name}"')
			type(self).instances[name] = self
	@classmethod
	def get(cls, name):
		if type(name) != str:
			raise TypeError(f'VariableCheck : name must be str')
		return cls.instances[name]
	def as_condition(self, parameters):
		return lambda value: (lambda result: result is None or isinstance(result, (CheckError, CheckWarning)))(self(value, parameters))
	def add_fix(self, function):
		def safe_function(obj, parameters):
			result = function(obj, parameters)
			if not (type(result) == tuple and len(result) == 2 and type(result[0]) == bool):
				raise TypeError(f'Fixing function of check "{self.name}" should return a 2 long tuple with first element being a bool (indicating if the curation process was sucessfull)')
			return result
		self.fixes.append(safe_function)
		return function


class EntryCheck(Check):
	'''EntryCheck is meant to ensure the quality of an entry considering all its variable and will decorate specific functions taking pd.Serie object as input'''
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
	def __call__(self, row_or_function):
		if self.function is None:
			if not callable(row_or_function):
				raise ValueError(f'EntryCheck : function has not be initialized, this istance must call a function as a decorator')
			self.function = row_or_function
			if self.function.__code__.co_argcount != 1:
				raise ValueError(f'EntryCheck : decorated function must take one argument, a pd.Series')
		else:
			if not isinstance(row_or_function, pd.Series):
				raise TypeError(f'EntryCheck() : arguement must be an instance of pd.Series')
			result = self.function(row_or_function)
			if result is not None and not isinstance(result, CheckReturn):
				raise TypeError(f'EntryCheck() : result must be an instance of CheckRetur, not {type(result)}')
			return result

class VariableCheck(Check):
	'''EntryCheck is meant to ensure the quality of an entry considering all its variable and will decorate specific functions taking an object and a set of parameters as input'''
	def __init__(self, *, mandatory_parameters=None, optional_parameters=None, **kwargs):
		'''mandatory_parameters are a list of string parameter names and optional_parameters a dict of default values for optional parameters'''
		super().__init__(**kwargs)
		self.mandatory_parameters = mandatory_parameters or list()
		self.optional_parameters = optional_parameters or dict()
		if type(self.mandatory_parameters) != list or not set(map(type, self.mandatory_parameters)).issubset({str}):
			raise TypeError(f'VariableCheck : mandatory_parameters must be a list of str objects, not {self.mandatory_parameters}')
		if type(self.optional_parameters) != dict or not set(map(type, optional_parameters)).issubset({str}):
			raise TypeError(f'VariableCheck : optional_parameters must be a dict with str keys, not {optional_parameters}')
		self.function = None
	def __call__(self, value_or_function, parameters=None):
		if self.function is None:
			if not callable(value_or_function):
				raise ValueError(f'VariableCheck : function has not be initialized, this istance must call a function as a decorator')
			self.function = value_or_function
			if self.function.__code__.co_argcount != 2 :
				raise TypeError(f'VariableCheck : decorated function must take 2 arguments, value and parameters, not {self.function.__code__.co_argcount}')
			return self.function
		else:
			if type(parameters) != dict or not set(map(type, parameters)).issubset({str}):
				raise TypeError('VariableCheck : parameters must be a dict with str keys')
			parameters = self.optional_parameters | (parameters or dict())
			result = self.function(value_or_function, parameters)
			if result is not None and not isinstance(result, CheckReturn):
				raise TypeError(f'decorated function {self.function} did not return None or an instance of CheckReturn')
			return result