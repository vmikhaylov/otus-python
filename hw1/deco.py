#!/usr/bin/env python
# -*- coding: utf-8 -*-

import itertools

from functools import update_wrapper


def disable(function):
    '''
    Disable a decorator by re-assigning the decorator's name
    to this function. For example, to turn off memoization:

    >>> memo = disable

    '''
    return function


def decorator(deco):
    '''
    Decorate a decorator so that it inherits the docstrings
    and stuff from the function it's decorating.
    '''
    def deco_wrapper(function):
        wrapper = deco(function)
        update_wrapper(wrapper, function)
        return wrapper

    return deco_wrapper


@decorator
def countcalls(function):
    '''Decorator that counts calls made to the function decorated.'''
    def count_wrapper(*args, **kwargs):
        count_wrapper.calls += 1
        return function(*args, **kwargs)

    count_wrapper.calls = 0
    return count_wrapper


@decorator
def memo(function):
    '''
    Memoize a function so that it caches all return values for
    faster future lookups.
    '''
    cache = {}

    def memo_wrapper(*args, **kwargs):
        key = args, frozenset(kwargs.items())
        if key not in cache:
            cache[key] = function(*args, **kwargs)
        update_wrapper(memo_wrapper, function)
        return cache[key]

    return memo_wrapper


@decorator
def n_ary(function):
    '''
    Given binary function f(x, y), return an n_ary function such
    that f(x, y, z) = f(x, f(y,z)), etc. Also allow f(x) = x.
    '''
    def n_ary_wrapper(*args, **kwargs):
        if len(args) == 1:
            return args[0]
        else:
            return function(args[0], n_ary_wrapper(*args[1:]))

    return n_ary_wrapper


def trace(trace_symbols):
    '''Trace calls made to function decorated.

    @trace("____")
    def fib(n):
        ....

    >>> fib(3)
     --> fib(3)
    ____ --> fib(2)
    ________ --> fib(1)
    ________ <-- fib(1) == 1
    ________ --> fib(0)
    ________ <-- fib(0) == 1
    ____ <-- fib(2) == 2
    ____ --> fib(1)
    ____ <-- fib(1) == 1
     <-- fib(3) == 3

    '''
    @decorator
    def trace_deco(function):
        def trace_wrapper(*args, **kwargs):
            func_call_str = _func_call_str(*args, **kwargs)
            print '%s%s%s' % (
                trace_wrapper.recursion_level * trace_symbols,
                ' --> ', func_call_str
            )
            trace_wrapper.recursion_level += 1
            result = function(*args, **kwargs)
            trace_wrapper.recursion_level -= 1
            print '%s%s%s == %s' % (
                trace_wrapper.recursion_level * trace_symbols, ' <-- ',
                func_call_str, result
            )
            return result

        def _func_call_str(*args, **kwargs):
            string = function.__name__
            string += '('
            for index, arg in enumerate(itertools.chain(args, kwargs.values())):
                string += str(arg)
                if index < len(args) - 1:
                    string += ', '
            string += ')'
            return string

        trace_wrapper.recursion_level = 0
        return trace_wrapper

    return trace_deco


@memo
@countcalls
@n_ary
def foo(a, b):
    return a + b


@countcalls
@memo
@n_ary
def bar(a, b):
    return a * b


@countcalls
@trace("####")
@memo
def fib(n):
    """Calculates n-th Fibonacci number"""
    return 1 if n <= 1 else fib(n-1) + fib(n-2)


def main():
    print foo(4, 3)
    print foo(4, 3, 2)
    print foo(4, 3)
    print "foo was called", foo.calls, "times"

    print bar(4, 3)
    print bar(4, 3, 2)
    print bar(4, 3, 2, 1)
    print "bar was called", bar.calls, "times"

    print fib.__doc__
    fib(3)
    print fib.calls, 'calls made'


if __name__ == '__main__':
    main()
