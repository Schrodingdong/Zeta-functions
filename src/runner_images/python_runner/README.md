# Python Runner
This module defines how `python_runner` wrapper is going to be used

## Standards to follow
- File to pass should be: `handler/handler.py`
- The handler file should contain the `main_handler(params)` as a main entry
- The `params` props, if used, should needs to be a dictionnary
- The return of the zeta function could be whathever, but for better standard, use dict

## handler.py example
```python
def do_some_computation():
    # ...

def main_handler(params):
    value = "Default"
    if params["key"] == "someValue":
        value = do_some_computation()
    return {
        "myMessage": "Hello from Zeta !",
        "value": value
    }
```
## Response example
```json
{
    "status": "success",
    "response": {
        "myMessage": "Hello from Zeta !",
        "value": "..." 
    }
}
```