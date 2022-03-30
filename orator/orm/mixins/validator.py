import re

class Validator(object):
    _validation_init = True
    __errors__ = {'code':200, 'errors':[]}

    # @classmethod
    def validate(self, key, require=False, data_type=False,
            regex=False, custom_error=False, *args):
        '''
        Function dedicated to validate if a imput has some values

        param: str key: This is the name of the value that we are looking, is just for us to make the error json
        param: bool require: This tell us if we need to abort if the input is undefined
        param: str data_type: Data type tell us if the input has to be a certain data type so we verified
        param: str regex: String that we could check if we need
        param: function custom_error: you can send a function to build a custom error
        param: *args *args: arguments to go with the function
        return: data response: We can return the value validated or None if the value doest correspont to the statements
        '''
        if self._validation_init:
            self._errors()
            self._validation_init = False
        value = getattr(self, key, None)
        if require and not value:
            self._handle_error('require', key, custom_error=custom_error, *args)
            return self
        if data_type and not isinstance(value, data_type):
            self._handle_error('data type', key, custom_msg='Bad data type on {}'.format(key),
                custom_error=custom_error, *args)
            return self
        if regex and not re.match(regex, value):
            if not require: self.validate(key, require=True)
            self._handle_error('regex', key, custom_error=custom_error, *args)
        return self

    @classmethod
    def _handle_error(cls, type_error, value_name,
            custom_msg=False, custom_error=False, *args):
        '''
        Funtion dedicated to handle errors on the validation

        param: str type_error: this is use for the default msg
        param: str value_name: this is use for the default msg
        param: str custom_msg: is they want to use a custom_msg
        param: function custom_error: Optional to send a custom error
        param: args *args: Values of the custom error
        return: None
        '''
        if custom_error:
            custom_error(*args)
        cls._modify_errors(code=400, msg=custom_msg
                if custom_msg else
                'Error of {} on {}'.format(type_error, value_name)
        )

    @classmethod
    def errors(cls, code=None, msg=None):
        '''
        Function dedicated to delete errors after use

        return: __errors__
        '''
        cls._validation_init = True
        errors = cls.__errors__
        cls.__errors__ = {'code':200, 'errors':[]}
        return errors

    @classmethod
    def _errors(cls, code=None, msg=None):
        '''
        Function dedicated to delete errors after use

        return: __errors__
        '''
        errors = cls.__errors__
        cls.__errors__ = {'code':200, 'errors':[]}
        return errors

    @classmethod
    def _modify_errors(cls, code=None, msg=None):
        '''
        Function dedicated to modify errors

        param: int code: The error code that we will return
        param: str msg: the msg to append to error list
        '''
        if code:
            cls.__errors__['code'] = code
        if msg:
            cls.__errors__['errors'].append({
                'msg': msg
            })
