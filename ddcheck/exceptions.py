class DdCheckError(Exception): pass

class InvalidCredentialsError(DdCheckError): pass

class ZoneDoesNotExistError(DdCheckError): pass

class InvalidUrlFormat(DdCheckError): pass
