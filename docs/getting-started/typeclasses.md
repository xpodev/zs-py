# TypeClasses


Type classes are very similar to interfaces in other OOP languages, but they differ in a few things:

- You don't need to put the typeclass in your inheritence list when defining a class.
- You can implement a typeclass for any type you want.
- It does not necessarily defines an object API, but also the class API.


To define a type class, we use the `typeclass` keyword. Typeclasses must have a name.
```
typeclass MyTypeclass {

}
```

Inside the typeclass body, you can define the functions you want to be implemented in implementing types.
```
typeclass MyTypeclass {
    fun my_api(this, value: string);
}
```

In order to implement the `MyTypeclass` typeclass for a certain type (say, string), we do this:
```
typeclass MyTypeclass(string) {
    fun my_api(this: string, value: string) {
        print("Typeclass.my_api(string, string) is implemented on string! " + this + value);
    }
}
```

Implementing a typeclass does not change the type. For example, we will not be able to call `my_api` 
on instances of string, even though it does implement the `MyTypeclass` typeclass which defined `my_api`.

So how do we use typeclasses then?

We have to treat instances of implemented types as if they were the type class itself.
```go
var my_typeclass: MyTypeclass = "Hello";
my_typeclass.my_api(", Typeclasses!");  // Output: Typeclass.my_api(string, string) is implemented on string! Hello, Typeclasses!
```
