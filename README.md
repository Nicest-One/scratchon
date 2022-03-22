# scratchon developer branch (Nothing Works Yet)
The official way to make your own scratchon module! 

### Installation
```
git clone -b developer https://github.com/Nicest-One/scratchon
```

### Get started
Import utilities

```python
from scratchon.build.module_maker import Distribute, Parse, Create, Check
```

### Now you can create your own module.
```python
#check if module name avialable
response = Check(module_name='my_module', check_for="name")
if response:
    code = "your module code (the one obtained from creating your scratchon module"
    Distribute(file="file ex. C:/Users/Python/module.py", auth=code)
else:
    module = Parse("file ex. C:/Users/Python/module.py")
    code, response = Create(module)
    print(code)
    #save the value of the variable code
````

### Support?
#### Discord Server: https://discord.com/invite/tF7j7MswUS
