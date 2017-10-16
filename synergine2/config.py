# coding: utf-8
import typing

import re

from synergine2.exceptions import SynergineException

DEFAULT_VALUE = '__DEFAULT_VALUE__'


class Config(dict):
    def __init__(
            self,
            seq: typing.Union[dict, None]=None,
            **kwargs: typing.Any
    ) -> None:
        seq = seq or {}
        super().__init__(seq, **kwargs)
        """
        Regular expression used to find key access, example of matching
        strings:
          * foo[0]
          * bar.buz[1]
        Not working strings (see blsi.common.config.Config#get TODO):
          * bad[0][1]

        Literal translation of expression is:
          * Group "(.+)" Everything with minimum 1 char
          * Group "(\[([0-9])+\])" numeric number into brackets
        """
        self._index_re = re.compile(r'(.+)(\[([0-9])+\])')

    def resolve(
        self,
        k: str,
        d: object=DEFAULT_VALUE,
    ) -> typing.Union[None, str, float, int, bool, dict, list]:
        """
        Allow to get dict value with following expression:
        config.get('foo[0].bar.baz'), so '.' for dict keys, and [x] for
        list index.
        TODO BS 20170124: Actually don't work with multiple indexes "foo[0][0]"
        :param k: key
        :param d: default value
        :return:
        """
        if '.' in k:
            try:
                parts = k.split('.')
                value = self
                for part in parts:
                    index_search = re.search(self._index_re, part)
                    if index_search is not None:
                        groups = index_search.groups()
                        part = groups[0]
                        index = int(groups[2])
                        value = value.get(part)  # type: ignore
                        value = value[index]
                    else:
                        value = value.get(part, d)  # type: ignore
                return value
            except IndexError:
                value = d  # type: ignore
            except KeyError:
                value = d  # type: ignore
            except AttributeError:
                value = d  # type: ignore

            if value == DEFAULT_VALUE:
                raise SynergineException(
                    'No configuration found for "{}"'.format(k)
                )
            elif value == DEFAULT_VALUE:
                return None

            return value
        else:

            value = super().get(k, d)

            if value == DEFAULT_VALUE:
                raise SynergineException(
                    'No configuration found for "{}"'.format(k)
                )
            elif value == DEFAULT_VALUE:
                return None

            return value
