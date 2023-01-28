# Classes

When we build out program, we notice that we need to handle data, and many times, very similar data.

It would be very nice for us, programmers, if we had some way to easily manage data.

Fortunately, the Z# language developer does love helping others, and he came up with a way to do that.
* *The Z# language developer did not invent classes*

To define a class we use the `class` keyword.
```cs
class MyClass {

}
```

Well, the class that we just created - `MyClass` - is not very helpful on its own, as it is empty and
it doesn't have any data to manage.

* *I know that it is actually a **data structure**, but I'm assuming you know what a class is.*

So we can define *fields* in a class. Defining a field in a class is as easy as defining a variable.
```cs
class MyClass {
    var my_field: String;  // (1)!
}
```

1. This will actually error, since the `String` type is not defined yet (only a placeholder).


In order to use our class, we first need to add a constructor.
```fs
class MyClass {
    var my_field: String;

    fun MyClass(this, some_value: String) {
        this.my_field = some_value;
    }
}
```

A few notes here:

- *The constructor name must be the same as the class name.*
- *All instance methods must have a `this` parameter. You can choose whatever name you want tho.*
- *By default, if a parameter type is not specified, it is assumed to be `any` (will change in the future).*
- *By default, if no constructor were to be found, an empty constructor is provided by the compiler.*


Now that we have defined our constructor, we can use it to create our first object;
```
var my_class = MyClass("I'm an object!");

print(my_class.my_field);  // Output: I'm an object!
```
