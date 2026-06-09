import asyncio, inspect, traceback, logging, functools, sys
from typing import Optional, Any, Callable, Awaitable
    

class LogUtils:
    @staticmethod
    def init(filename : str | None = 'info.log', to_stderr : bool = True):
        handlers = []
        if to_stderr:
            handlers.append(
                logging.StreamHandler(stream=sys.stderr), # prints to console 
            )
        if filename is not None:
            handlers.append(
                logging.FileHandler(filename=filename, mode='a') # prints to info.log also
            )
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=handlers 
        )

    # errors and logging
    RAISE = True
    LOG_VERBOSE = False
    LOG_ARGS = False
    LOG_RETURNS = False # haha

    #TODO: fully implement log_verbose
    
    def auto_log(func):
        # Logs calls and results for instance, class, and static methods.

        # Detect if this is a staticmethod or classmethod
        is_static = isinstance(func, staticmethod)
        is_class = isinstance(func, classmethod)

        # Extract the actual function if wrapped in staticmethod/classmethod
        actual_func = func.__func__ if (is_static or is_class) else func

        @functools.wraps(actual_func)
        def wrapper(*args, **kwargs):
            # Determine class name if possible
            if args and not is_static:
                maybe_self_or_cls = args[0]
                if hasattr(maybe_self_or_cls, "__class__"):
                    class_name = maybe_self_or_cls.__class__.__name__
                elif isinstance(maybe_self_or_cls, type):
                    class_name = maybe_self_or_cls.__name__
                else:
                    class_name = "<unknown>"
            else:
                class_name = "<static>"

            
            if LogUtils.LOG_ARGS:
                call_str = f'called with args={args}, kwargs={kwargs}'
            else:
                call_str = 'called'    

            logging.info(f"[{class_name}.{actual_func.__name__}] {call_str}")

            result = actual_func(*args, **kwargs)


            if LogUtils.LOG_RETURNS:   
                ret_str = f'returned {result}'
            else:
                ret_str = 'returned'

            logging.info(f"[{class_name}.{actual_func.__name__}] {ret_str}")
            
            return result

        # Wrap appropriately
        if is_static:
            return staticmethod(wrapper)
        elif is_class:
            return classmethod(wrapper)
        else:
            return wrapper


    @staticmethod
    def read_exc(e : Exception, tr=False):
        return type(e).__name__, (f'{e}' + (f' : {traceback.format_exc()}' if tr else ''))

    @staticmethod
    def dict_exc(e : Exception, tr=False):
        t, m = LogUtils.read_exc(e, tr)
        return {'type' : t, 'msg' : m}
    
    @staticmethod
    def handle(e : Exception, message : Optional[str] = None):
        etype, emsg = LogUtils.read_exc(e)

        error_str = f"[{etype}] {emsg}"
        if message:
            error_str = error_str + f"\n{message}"

        logging.error(error_str)
        
        if LogUtils.RAISE:
            raise
    
    @staticmethod
    def handle_dict(e : Exception, message : Optional[str] = None):
        etype, emsg = LogUtils.read_exc(e, True)

        error_str = f"[{etype}] {emsg}"
        if message:
            error_str = error_str + f"\n{message}"

        logging.error(error_str)
        
        return LogUtils.dict_exc(e, False)
        

# boolean helper functions
def impl(_if : bool, _then : bool) -> bool:
    return _then if _if else True


# waiting function
async def wait_for(condition : Callable[[], bool | Awaitable[bool]], check_interval : float =0.4, timeout : Optional[float] = None):
    """
    Asynchronously wait until condition returns True.
    
    Args:
        condition (Callable): A no-arg function returning a boolean.
        check_interval (float): Time in seconds between condition checks.
        timeout (float or None): Max wait time in seconds. If None, wait indefinitely.
    
    Raises:
        asyncio.TimeoutError: If timeout is reached before condition is True.
    """
    
    start = asyncio.get_running_loop().time()

    async def wait():
        if timeout is not None and (asyncio.get_running_loop().time() - start) > timeout:
            raise asyncio.TimeoutError("Condition not met within timeout.")
        await asyncio.sleep(check_interval)

    if inspect.iscoroutinefunction(condition):
        while not await condition():
            await wait()
    else:
        while not condition():
            await wait()
    

# if input is not function, returns.
# if input is argless function, calls it and returns result.
def collapse(foo : Any | Callable[[], Any]) -> Any:
    return foo() if callable(foo) else foo