
from typing import Generator

running_coroutines = {} # {coroutine: timer}

def queue_coroutine(coroutine: Generator) -> Generator:
    '''Queues a coroutine to begin the next time advance_coroutines() is called. \n
    The coroutine parameter should be a generator returned by a function containing one or more yield 
    statements. The value yielded by each statement is the number of frames to wait before continuing execution.'''

    if not coroutine_running(coroutine):
        running_coroutines[coroutine] = 0
    else:
        raise ValueError('Coroutine %s is already running' % coroutine)
    
    return coroutine


def stop_coroutine(coroutine: Generator, raise_exception: bool = False):
    '''Stops the specified coroutine if it is currently running. \n
    If it is not running, nothing happens unless raise_exception is set to true, in which case an exception is raised.'''

    if coroutine_running(coroutine):
        del running_coroutines[coroutine]
    elif raise_exception:
        raise ValueError('Coroutine %s is not currently running' % coroutine)


def coroutine_running(coroutine: Generator) -> bool:
    '''Returns True if the specified coroutine is currently running, otherwise False.'''

    return coroutine in running_coroutines 


def advance_coroutines(amount = 1):
    '''Starts all queued coroutines and advances all running ones. \n
    When used with pygame, this should ideally be called at the end of the game loop.'''

    for coroutine, timer in list(running_coroutines.items()):
        timer -= amount
        if timer <= 0:
            try:
                timer = next(coroutine)
            except StopIteration:
                del running_coroutines[coroutine]
                continue
        running_coroutines[coroutine] = timer