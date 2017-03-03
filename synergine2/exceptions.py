# coding: utf-8


class SynergineException(Exception):
    pass


class NotYetImplemented(SynergineException):
    """
    Like of NotImplementError. Use it to declare method to implement but only if wanted.
    """
